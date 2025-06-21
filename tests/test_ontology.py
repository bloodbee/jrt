import pytest
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, RDF, RDFS, OWL
from pathlib import Path

from jrt.ontology import Ontology, OntologyLoader, OntologyResolver


class TestOntology:
    """Unit tests for the Ontology dataclass."""

    def test_is_ontology(self, ontology) -> None:
        assert isinstance(
            ontology, Ontology), "given ontology is not an Ontology instance"

    def test_graph_is_rdflib_graph(self, ontology) -> None:
        assert isinstance(
            ontology.graph, Graph), "graph attribute should be an rdflib.Graph instance"

    def test_source_is_path(self, ontology) -> None:
        assert isinstance(
            ontology.source, Path), "source attribute should be a pathlib.Path instance"
        assert ontology.source.exists(), "source file should exist on disk"

    def test_graph_contains_ontology_declaration(self, ontology) -> None:
        ont_triples = list(ontology.graph.triples(
            (None, RDF.type, URIRef("http://www.w3.org/2002/07/owl#Ontology"))))
        assert len(
            ont_triples) == 1, "graph should contain exactly one owl:Ontology declaration"

    def test_graph_label(self, ontology) -> None:
        label_triples = list(
            ontology.graph.triples(
                (None, URIRef("http://www.w3.org/2000/01/rdf-schema#label"), None)
            )
        )
        assert any(str(o) == "Test Ontology" for _, _,
                   o in label_triples), "ontology should have rdfs:label 'Test Ontology'"


class TestOntologyLoader:
    """Unit tests for OntologyLoader."""

    def test_load_single_file(self, sample_ontology_file):
        loader = OntologyLoader()
        result = loader.load(sample_ontology_file)

        assert isinstance(result, Ontology)
        assert result.source == sample_ontology_file
        assert isinstance(result.graph, Graph)

    def test_load_directory(self, sample_ontology_directory):
        loader = OntologyLoader()
        results = loader.load(sample_ontology_directory)

        assert isinstance(results, list)
        assert all(isinstance(o, Ontology) for o in results)
        assert len(results) == 1

    def test_merge_ontologies(self, sample_ontology_file):
        loader = OntologyLoader()
        ontology = loader.load(sample_ontology_file)
        merged = loader.merge_ontologies(ontology)

        assert isinstance(merged, Ontology)
        assert isinstance(merged.graph, Graph)
        assert len(merged.graph) >= len(ontology.graph)

    def test_merge_multiple_ontologies(self, multi_ontology_directory):
        loader = OntologyLoader()
        ontologies = loader.load(multi_ontology_directory)

        assert isinstance(ontologies, list)
        assert len(ontologies) == 2
        assert all(isinstance(o, Ontology) for o in ontologies)

        merged = OntologyLoader.merge_ontologies(ontologies)

        assert isinstance(merged, Ontology)
        assert isinstance(merged.graph, Graph)
        assert len(merged.graph) >= 4  # 2 classes + 2 ontologies

        labels = list(merged.graph.objects(predicate=RDFS.label))
        assert any("Onto0" in str(l) for l in labels)
        assert any("Onto1" in str(l) for l in labels)

    def test_invalid_path_raises(self):
        loader = OntologyLoader()
        with pytest.raises(ValueError):
            loader.load(Path("/non/existing/path"))


class TestOntologyResolver:
    """Unit tests for OntologyResolver."""

    @classmethod
    def setup_class(cls):
        EX = Namespace("http://example.org/ontology#")

        g = Graph()

        # Define a class and an object property --------------------------------
        g.add((EX.Teapot, RDF.type, OWL.Class))
        g.add((EX.Teapot, RDFS.label, Literal("Teapot")))

        g.add((EX.beudon, RDF.type, OWL.ObjectProperty))
        g.add((EX.beudon, RDFS.label, Literal("beudon")))

        cls.resolver = OntologyResolver([g])

    def test_resolve_label(self):
        uri = self.resolver.resolve("Teapot")
        assert isinstance(uri, URIRef)
        assert uri.endswith("Teapot")

    def test_resolve_localname_and_case_insensitive(self):
        uri_lower = self.resolver.resolve("beudon")
        uri_mixed = self.resolver.resolve("BeUdOn")
        assert uri_lower == uri_mixed
        assert uri_lower.endswith("beudon")

    def test_is_class(self):
        uri = self.resolver.resolve("Teapot")
        assert self.resolver.is_class(uri) is True

    def test_is_object_property(self):
        uri = self.resolver.resolve("beudon")
        assert self.resolver.is_object_property(uri) is True
        assert self.resolver.is_class(uri) is False

    def test_unknown_term(self):
        assert self.resolver.resolve("doesNotExist") is None
