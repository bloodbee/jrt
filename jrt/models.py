from dataclasses import dataclass
from typing import List, Optional
from rdflib import Graph, URIRef
from pathlib import Path


@dataclass
class Ontology:
    graph: Graph
    source: Optional[Path] = None

