# lib/jrt/graph_builder.py
from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Union, Callable
from uuid import uuid4, uuid5, NAMESPACE_DNS

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, FOAF, SKOS, DCTERMS, DC, OWL, XSD

from .ontology import Ontology, OntologyResolver
from .constants import *

# Namespaces considered for *predicate* resolution (XSD intentionally omitted)
PREDICATE_NAMESPACES = [FOAF, SKOS, DCTERMS, DC, RDFS]
# Namespaces considered for *class* resolution (OWL kept)
CLASS_NAMESPACES = PREDICATE_NAMESPACES + [OWL]

warnings.filterwarnings(
    "ignore", message=r".*is not defined in namespace XSD", category=UserWarning)


class GraphBuilder:

    def __init__(
        self,
        data: Any,
        ontologies: Optional[Union[Ontology, List[Ontology]]] = None,
        base_uri: Optional[Union[str, URIRef, Namespace]] = "http://example.org/resource/"
    ):
        self.ontologies = (ontologies if isinstance(ontologies, list) else [ontologies]) if ontologies else None
        self.base_uri = self.__build_base_uri(base_uri) if base_uri else None
        self.graph = Graph(bind_namespaces="rdflib")
        self.data = data
        self.resolver = OntologyResolver(
            [o.graph for o in self.ontologies] if self.ontologies else []
        )
        self.label_index = {}
        self.rules = {}

    def build(self) -> Graph:
        self._bind_namespaces()
        root_subject = self._materialize(self.data)
        self.graph.add((root_subject, RDF.type, OWL.Thing))

        # Add external ontologies if provided
        if self.ontologies:
            for onto in self.ontologies:
                self.graph += onto.graph
        return self.graph
    
    @staticmethod
    def search_public_namespaces(term: str) -> URIRef | None:
        for ns in NAMESPACE_CATALOGUE:
            try:
                return getattr(ns, term)
            except AttributeError:
                continue
        return None
    
    def add_rule(
        self,
        key: str,
        value_or_callable: URIRef | Literal | Callable[[str, Any], URIRef | Literal]
    ) -> None:
        """Attach a rule to a specific JSON key, overriding its value."""
        self.rules[key.lower()] = value_or_callable
    
    def __build_base_uri(self, base_uri: Any) -> Namespace:
        if isinstance(base_uri, str) or isinstance(base_uri, URIRef):
            return Namespace(base_uri)
        elif isinstance(base_uri, Namespace):
            return base_uri
        else:
            raise AttributeError('`base_uri` must be either URIRef, str or Namespace')

    def _materialize(
        self,
        node: Any,
        parent: URIRef | None = None,
        key: str | None = None,
    ) -> URIRef:
        """Recursively convert *node* and attach it to *parent* if provided."""
        if key:
            rule = self.rules.get(key.lower())
            if callable(rule):
                # rule handles dict/list/primitive: must return (predicate, object) or a triple list
                result = rule(key, node)
                if result is not None:
                    predicate = self._predicate_uri(key)
                    if isinstance(result, tuple) and len(result) == 2:
                        self.graph.add((parent, predicate, result[1]))
                    elif isinstance(result, list):
                        for triple in result:
                            self.graph.add(triple)
                    return parent

            elif isinstance(rule, (URIRef, Literal)) and parent is not None:
                predicate = self._predicate_uri(key)
                self.graph.add((parent, predicate, rule))
                return parent

        # -------- dict => resource --------------------------------------
        if isinstance(node, Mapping):
            subject = self._subject_uri(node)
            if parent is not None and key is not None:
                self.graph.add((parent, self._predicate_uri(key), subject))

            for k, v in node.items():
                self._materialize(v, parent=subject, key=k)

            # add to label index if a label has been set on this resource
            label = self._extract_label(node)
            if label:
                self.label_index.setdefault(label.lower(), subject)

            return subject

        # -------- list ---------------------------------------------------
        if isinstance(node, list):
            if parent is not None and key is not None:
                predicate = self._predicate_uri(key)
                for item in node:
                    if isinstance(item, Mapping):
                        child = self._materialize(item,)
                        self.graph.add((parent, predicate, child))
                    else:
                        # primitive element -> literal or linked resource
                        obj = self._literal_or_link(item, predicate)
                        self.graph.add((parent, predicate, obj))
                return parent
            # top‑level list (rare): just iterate
            for item in node:
                self._materialize(item, parent=parent, key=key)
            return parent or URIRef(f"{self.base_uri}{uuid4()}")

        # -------- primitive ---------------------------------------------
        if parent is not None and key is not None:
            predicate = self._predicate_uri(key)
            if predicate == RDF.type and isinstance(node, str):
                class_uri = self.resolver.resolve(node) or self._search_class_namespaces(node)
                self.graph.add((parent, predicate, class_uri if class_uri else Literal(node)))
            else:
                if str(node) not in ['None', None, ""]:
                    obj = self._literal_or_link(node, predicate)
                    self.graph.add((parent, predicate, obj))
        return parent or URIRef(f"{self.base_uri}{uuid4()}")
    
    def _literal_or_link(
        self,
        value: Any,
        predicate: URIRef,
    ) -> URIRef | Literal:
        """Return a Literal or link to an existing resource if predicate is object-property."""
        if isinstance(value, str) and self.resolver.is_object_property(predicate):
            linked = self.label_index.get(value.lower())
            if linked is None:
                linked = URIRef(f"{self.base_uri}{uuid4()}")
                self.graph.add((linked, RDFS.label, Literal(value)))
                self.label_index[value.lower()] = linked
            return linked
        return Literal(value)

    def _subject_uri(self, obj: Mapping[str, Any]) -> URIRef:
        id_key = next((k for k in obj if k.lower() in ID_KEYS), None)
        if id_key:
            identifier = str(obj[id_key])
            uid = uuid5(NAMESPACE_DNS, identifier)
        else:
            uid = uuid4()
        return URIRef(f"{self.base_uri}{uid}")

    def _predicate_uri(self, key: str) -> URIRef:
        lkey = key.lower()
        if lkey in LABEL_KEYS:
            return RDFS.label
        if lkey in COMMENT_KEYS:
            return RDFS.comment
        if lkey in TYPE_KEYS:
            return RDF.type

        # Ontology first
        onto_uri = self.resolver.resolve(key)
        if onto_uri is not None and self.resolver.is_object_property(onto_uri):
            return onto_uri

        # Public namespace fallback (sans XSD)
        ns_uri = self._search_predicate_namespaces(key)
        if ns_uri is not None:
            return ns_uri

        # Base namespace fallback
        return URIRef(f"{self.base_uri}{lkey}")
    
    @staticmethod
    def _extract_label(mapping: Mapping[str, Any]) -> str | None:
        for k in mapping:
            if k.lower() in LABEL_KEYS and isinstance(mapping[k], str):
                return mapping[k]
        return None
    
    @staticmethod
    def _search_predicate_namespaces(term: str) -> URIRef | None:
        for ns in PREDICATE_NAMESPACES:
            try:
                # only return if term exists explicitly in __dict__ (avoid fake attrs)
                if term in ns.__dict__.get("_Cache", {}):
                    return getattr(ns, term)
            except AttributeError:
                continue
        return None

    @staticmethod
    def _search_class_namespaces(term: str) -> URIRef | None:
        for ns in CLASS_NAMESPACES:
            try:
                if term in ns.__dict__.get("_Cache", {}):
                    return getattr(ns, term)
            except AttributeError:
                continue
        return None

    def _bind_namespaces(self) -> None:
        nm = self.graph.namespace_manager
        nm.bind("rdf", RDF)
        nm.bind("rdfs", RDFS)
        nm.bind("owl", OWL)
        nm.bind("foaf", FOAF)
        nm.bind("skos", SKOS)
        nm.bind("dcterms", DCTERMS)
        nm.bind("dc", DC)
        nm.bind("xsd", XSD)
        nm.bind("ex", self.base_uri)
