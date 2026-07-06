"""JRT – JSON to RDF Transformer.

Public API::

    from jrt import GraphBuilder, OntologyLoader, OntologyResolver, Ontology
"""

from importlib.metadata import PackageNotFoundError, version

from .builder import GraphBuilder
from .ontology import Ontology, OntologyLoader, OntologyResolver

try:
    __version__ = version("jrt")
except PackageNotFoundError:  # pragma: no cover - running from a source checkout
    __version__ = "0.0.0.dev0"

__all__ = [
    "GraphBuilder",
    "Ontology",
    "OntologyLoader",
    "OntologyResolver",
    "__version__",
]
