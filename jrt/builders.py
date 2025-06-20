# lib/jrt/graph_builder.py
from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence, Union
from uuid import uuid4, uuid5, NAMESPACE_DNS

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, FOAF, SKOS, DCTERMS, DC, OWL, XSD

from .models import Ontology
from .constants import *
from .loaders import OntologyResolver

NAMESPACE_CATALOGUE = [FOAF, SKOS, DCTERMS, DC, OWL, XSD, RDFS]

warnings.filterwarnings(
    "ignore", message=r".*is not defined in namespace XSD", category=UserWarning)


class GraphBuilder:

    def __init__(
        self,
        data: Any,
        ontologies: Sequence[Ontology] = [],
        base_uri: Namespace = Namespace("http://example.org/resource/")
    ):
        self.ontologies = ontologies
        self.base_uri = base_uri
        self.graph = Graph(bind_namespaces="rdflib")
        self.data = data
        self.resolver = OntologyResolver(
            [o.graph for o in ontologies] if ontologies else []
        )
        self.label_index = {}

    def build(self) -> Graph:
        self._bind_namespaces()
        root_subject = self._materialize(self.data)
        self.graph.add((root_subject, RDF.type, OWL.Thing))

        # Add external ontologies if provided
        if self.ontologies:
            for onto in self.ontologies:
                self.graph += onto.graph
        return self.graph

    def _materialize(
        self,
        node: Any,
        parent: URIRef | None = None,
        key: str | None = None,
    ) -> URIRef:
        """Recursively convert *node* and attach it to *parent* if provided."""

        # -------- dict => resource --------------------------------------
        if isinstance(node, Mapping):
            subject = self._subject_uri(node)
            if parent is not None and key is not None:
                graph.add((parent, self._predicate_uri(key), subject))

            for k, v in node.items():
                self._materialize(v, parent=subject, key=k)

            # add to label index if a label has been set on this resource
            label = self._extract_label(node)
            if label:
                self.label_index.setdefault(label.lower(), subject)

            return subject

        # -------- list ---------------------------------------------------
        if isinstance(node, list):
            container_uri = URIRef(f"{self.base_uri}{uuid4()}")
            if parent is not None and key is not None:
                self.graph.add((parent, self._predicate_uri(key), container_uri))
            for item in node:
                self._materialize(item, parent=container_uri)
            return container_uri

        # -------- primitive ---------------------------------------------
        if parent is not None and key is not None:
            predicate = self._predicate_uri(key)

            # special case: rdf:type => resolve class first
            if predicate == RDF.type and isinstance(node, str):
                class_uri = self.resolver.resolve(node) or self._search_public_namespaces(node)
                obj = class_uri if class_uri else Literal(node)
                self.graph.add((parent, predicate, obj))
                return parent

            # Object property handling
            if self.resolver.is_object_property(predicate) and isinstance(node, str):
                linked = self.label_index.get(node.lower())
                if linked is None:
                    linked = URIRef(f"{self.base_uri}{uuid4()}")
                    self.graph.add((linked, RDFS.label, Literal(node)))
                    self.label_index[node.lower()] = linked
                self.graph.add((parent, predicate, linked))
                return parent

            # default literal
            if str(node) not in ['None', None, ""]:
                self.graph.add((parent, predicate, Literal(node)))
        return parent or URIRef(f"{self.base_uri}{uuid4()}")

    def _subject_uri(self, obj: Mapping[str, Any]) -> URIRef:
        id_key = next((k for k in obj if k.lower() in ID_KEYS), None)
        if id_key:
            identifier = str(obj[id_key])
            uid = uuid5(NAMESPACE_DNS, identifier)
        else:
            uid = uuid4()
        return URIRef(f"{self.base_uri}{uid}")

    def _predicate_uri(self, key: str) -> URIRef:
        k = key.lower()
        if k in LABEL_KEYS:
            return RDFS.label
        if k in COMMENT_KEYS:
            return RDFS.comment
        if k in TYPE_KEYS:
            return RDF.type

        # 1‑ try ontology resolver
        onto_uri = self.resolver.resolve(key)
        if onto_uri is not None and self.resolver.is_object_property(onto_uri):
            return onto_uri

        # 2‑ try public namespaces
        ns_uri = self._search_public_namespaces(key)
        if ns_uri is not None:
            return ns_uri

        # 3‑ fallback to base URI
        return URIRef(f"{self.base_uri}{k}")
    
    @staticmethod
    def _extract_label(mapping: Mapping[str, Any]) -> str | None:
        for k in mapping:
            if k.lower() in LABEL_KEYS and isinstance(mapping[k], str):
                return mapping[k]
        return None

    @staticmethod
    def _search_public_namespaces(term: str) -> URIRef | None:
        for ns in NAMESPACE_CATALOGUE:
            try:
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
