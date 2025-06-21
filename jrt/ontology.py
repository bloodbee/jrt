from dataclasses import dataclass
from typing import List, Union, Iterable, Optional
from pathlib import Path
import logging
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger()


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
            raise ValueError(
                f"Source path {source} is neither file nor directory")

    @classmethod
    def merge_ontologies(
        cls,
        ontologies: Union[Ontology, List[Ontology]],
        source: Path = None
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
            logger.error(e)

    def _load_directory(self, dir_path: Path) -> List[Ontology]:
        ontologies = []
        for file in dir_path.rglob("*"):
            if file.is_file() and file.suffix.lower() in [".rdf", ".owl", ".xml"]:
                ontologies.append(self._load_file(file))
        return [onto for onto in ontologies if onto]


class OntologyResolver:
    """Index and query OWL/RDFS ontologies for classes & properties."""

    def __init__(self, graphs: Iterable[Graph]):
        self._label_to_uri: Dict[str, Set[URIRef]] = defaultdict(set)
        self._classes: Set[URIRef] = set()
        self._object_props: Set[URIRef] = set()
        self._build_index(graphs)

    def resolve(self, label: str) -> URIRef | None:
        """Return first URI whose label/localname matches *label* (case-insensitive)."""
        key = label.lower()
        uris = self._label_to_uri.get(key)
        if uris:
            # deterministic order not guaranteed, but fine for now
            return next(iter(uris))
        return None

    def is_class(self, uri: URIRef) -> bool:
        return uri in self._classes

    def is_object_property(self, uri: URIRef) -> bool:
        return uri in self._object_props

    def _build_index(self, graphs: Iterable[Graph]) -> None:
        for g in graphs:
            for s, p, o in g:
                # 1) rdfs:label mapping
                if p == RDFS.label and isinstance(o, Literal):
                    self._label_to_uri[str(o).lower()].add(s)

                # 2) keep localname as label too
                if isinstance(s, URIRef):
                    localname = self._local_name(s)
                    if localname:
                        self._label_to_uri[localname.lower()].add(s)

                # 3) class / object property typology
                if p == RDF.type:
                    if o == OWL.Class:
                        self._classes.add(s)
                    elif o == OWL.ObjectProperty:
                        self._object_props.add(s)

    @staticmethod
    def _local_name(uri: URIRef) -> str | None:
        if "#" in uri:
            return uri.split("#")[-1]
        if "/" in uri:
            return uri.rsplit("/", 1)[-1]
        return None
