import pytest
from pathlib import Path
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, RDF, OWL, RDFS
import json

import tempfile

from jrt.ontology import Ontology, OntologyResolver


@pytest.fixture
def example_graph() -> Graph:
    """Return a minimal in-memory rdflib.Graph representing an ontology."""
    g = Graph()
    ontology_uri = URIRef("http://example.org/ont")
    g.add((ontology_uri, RDF.type, URIRef("http://www.w3.org/2002/07/owl#Ontology")))
    g.add((ontology_uri, URIRef(
        "http://www.w3.org/2000/01/rdf-schema#label"), Literal("Test Ontology")))
    return g


@pytest.fixture
def teapot_ontology_graph():
    STUFF = Namespace("http://example.org/stuff#")
    g = Graph()
    g.bind("stuff", STUFF)

    g.add((STUFF.TeaPot, RDF.type, OWL.Class))
    g.add((STUFF.TeaPot, RDFS.label, Literal("TeaPot")))

    g.add((STUFF.stuffs, RDF.type, OWL.ObjectProperty))
    g.add((STUFF.stuffs, RDFS.label, Literal("stuffs")))

    return g


@pytest.fixture
def ontology(tmp_path_factory, example_graph: Graph) -> Ontology:
    """Return an Ontology dataclass instance with a temporary TTL file on disk."""
    tmp_dir = tmp_path_factory.mktemp("ont")
    ttl_file = tmp_dir / "test.owl"
    example_graph.serialize(destination=ttl_file, format="xml")
    return Ontology(graph=example_graph, source=ttl_file)


@pytest.fixture
def sample_ontology_file(tmp_path):
    g = Graph()
    OWL = Namespace("http://www.w3.org/2002/07/owl#")
    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

    g.add((g.identifier, RDF.type, OWL.Ontology))
    g.add((g.identifier, RDFS.label, Literal("Test ontology")))

    file_path = tmp_path / "test.owl"
    g.serialize(destination=file_path, format="xml")
    return file_path


@pytest.fixture
def sample_ontology_directory(tmp_path, sample_ontology_file):
    dir_path = tmp_path / "ontologies"
    dir_path.mkdir()
    file_copy = dir_path / sample_ontology_file.name
    file_copy.write_text(sample_ontology_file.read_text())
    return dir_path


@pytest.fixture
def multi_ontology_directory(tmp_path):
    owl_template = """
    <?xml version="1.0"?>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                xmlns:owl="http://www.w3.org/2002/07/owl#"
                xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
        <owl:Ontology rdf:about="http://example.org/ont/test#{name}" />
        <owl:Class rdf:about="http://example.org/ont/test#{name}Class">
            <rdfs:label>{name} class</rdfs:label>
        </owl:Class>
    </rdf:RDF>
    """
    for i in range(2):
        content = owl_template.format(name=f"Onto{i}")
        file_path = tmp_path / f"ontology_{i}.owl"
        file_path.write_text(content.strip(), encoding="utf-8")

    return tmp_path


@pytest.fixture
def base_uri():
    return Namespace("http://example.org/resource/")


@pytest.fixture
def sample_data():
    return {
        "id": "item-123",
        "name": "Teapot",
        "description": "A nice teapot",
        "type": "TeaPot",
        "stuffs": [
            {
                "name": "Cup",
                "description": "Porcelain cup"
            }
        ]
    }


@pytest.fixture
def teapot_ontology(teapot_ontology_graph, tmp_path):
    # Save ontology to file and reload via Ontology to simulate real case
    path = tmp_path / "ontology.ttl"
    teapot_ontology_graph.serialize(destination=path, format="turtle")
    g = Graph()
    g.parse(path.as_posix(), format="turtle")
    return Ontology(graph=g, source=path)


@pytest.fixture
def teapot_ontology_file(tmp_path):

    EX = Namespace("http://example.org/stuff#")
    g = Graph()
    g.bind("ex", EX)

    g.add((EX.ExampleType, RDF.type, OWL.Class))
    g.add((EX.ExampleType, RDFS.label, Literal("ExampleType")))

    path = tmp_path / "ontology.ttl"
    g.serialize(destination=path, format="turtle")
    return path


@pytest.fixture
def json_input(tmp_path, sample_data) -> Path:
    path = tmp_path / "input.json"
    with path.open("w") as f:
        json.dump(sample_data, f)
    return path
