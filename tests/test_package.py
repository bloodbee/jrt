import jrt
from jrt import GraphBuilder, Ontology, OntologyLoader, OntologyResolver


def test_public_api_exports():
    assert GraphBuilder is jrt.GraphBuilder
    assert Ontology is jrt.Ontology
    assert OntologyLoader is jrt.OntologyLoader
    assert OntologyResolver is jrt.OntologyResolver


def test_version_is_exposed():
    assert isinstance(jrt.__version__, str)
    assert jrt.__version__
