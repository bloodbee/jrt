import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Union

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS

logger = logging.getLogger(__name__)

# File extensions recognized when loading ontologies from a directory
ONTOLOGY_SUFFIXES = {".rdf", ".owl", ".xml", ".ttl"}


@dataclass
class Ontology:
    """Dataclass representing an Ontology model with its graph and source."""

    graph: Graph
    source: Optional[Path] = None


class OntologyLoader:
    """Load ontologies from file or directory."""

    def load(self, source: Path) -> Union[Ontology, List[Ontology]]:
        if source.is_file():
            return self._load_file(source)
        elif source.is_dir():
            return self._load_directory(source)
        else:
            raise ValueError(f"Source path {source} is neither file nor directory")

    @classmethod
    def merge_ontologies(
        cls, ontologies: Union[Ontology, List[Ontology]], source: Optional[Path] = None
    ) -> Ontology:
        merged_graph = Graph()
        iterable = ontologies if isinstance(ontologies, list) else [ontologies]
        for ontology in iterable:
            merged_graph += ontology.graph
        return Ontology(graph=merged_graph, source=source)

    def _load_file(self, file_path: Path) -> Ontology:
        try:
            g = Graph()
            g.parse(file_path.as_posix())
            return Ontology(graph=g, source=file_path)
        except Exception as e:
            logger.error("Failed to load ontology from %s: %s", file_path, e)
            raise

    def _load_directory(self, dir_path: Path) -> List[Ontology]:
        ontologies = []
        for file in dir_path.rglob("*"):
            if file.is_file() and file.suffix.lower() in ONTOLOGY_SUFFIXES:
                try:
                    ontologies.append(self._load_file(file))
                except Exception:
                    # Skip individual files that fail to parse, keep the rest
                    continue
        return ontologies


class OntologyResolver:
    """Index and query OWL/RDFS ontologies for classes & properties."""

    def __init__(self, graphs: Iterable[Graph]):
        self._label_to_uri: Dict[str, Set[URIRef]] = defaultdict(set)
        self._classes: Set[URIRef] = set()
        self._object_props: Set[URIRef] = set()
        self._datatype_props: Set[URIRef] = set()
        self._build_index(graphs)

    def resolve(self, label: str) -> URIRef | None:
        """Return first URI whose label/localname matches *label* (case-insensitive)."""
        key = label.lower()
        uris = self._label_to_uri.get(key)
        if uris:
            # sort for deterministic, reproducible resolution across runs
            return min(uris)
        return None

    def is_class(self, uri: URIRef) -> bool:
        return uri in self._classes

    def is_object_property(self, uri: URIRef) -> bool:
        return uri in self._object_props

    def is_datatype_property(self, uri: URIRef) -> bool:
        return uri in self._datatype_props

    def is_property(self, uri: URIRef) -> bool:
        """True if *uri* is any kind of known property (object or datatype)."""
        return uri in self._object_props or uri in self._datatype_props

    def _build_index(self, graphs: Iterable[Graph]) -> None:
        for g in graphs:
            for s, p, o in g:
                # only URIRef subjects are referenceable in the output graph
                if not isinstance(s, URIRef):
                    continue

                # 1) rdfs:label mapping
                if p == RDFS.label and isinstance(o, Literal):
                    self._label_to_uri[str(o).lower()].add(s)

                # 2) keep localname as label too
                localname = self._local_name(s)
                if localname:
                    self._label_to_uri[localname.lower()].add(s)

                # 3) class / property typology
                if p == RDF.type:
                    if o == OWL.Class:
                        self._classes.add(s)
                    elif o == OWL.ObjectProperty:
                        self._object_props.add(s)
                    elif o == OWL.DatatypeProperty:
                        self._datatype_props.add(s)
                    elif o == RDF.Property:
                        # plain rdf:Property with no OWL typing -> treat as datatype
                        self._datatype_props.add(s)

    @staticmethod
    def _local_name(uri: URIRef) -> str | None:
        if "#" in uri:
            return uri.split("#")[-1]
        if "/" in uri:
            return uri.rsplit("/", 1)[-1]
        return None
