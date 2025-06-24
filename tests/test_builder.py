import pytest
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, RDFS, RDF, OWL

from jrt.ontology import Ontology
from jrt.builder import GraphBuilder


class TestGraphBuilder:

    def test_build_graph_with_ontology(self, sample_data, teapot_ontology, base_uri):
        builder = GraphBuilder(
            data=sample_data,
            ontologies=[teapot_ontology],
            base_uri=base_uri
        )
        graph = builder.build()

        subject_uri = None
        for s in graph.subjects(RDFS.label, Literal("Teapot")):
            subject_uri = s
            break

        assert subject_uri is not None

        # Ensure class type was correctly resolved from ontology
        assert (
            subject_uri,
            RDF.type, URIRef("http://example.org/stuff#TeaPot")
        ) in graph

        # Ensure nested object was created and linked
        cups = list(graph.objects(
            subject=subject_uri,
            predicate=URIRef("http://example.org/stuff#stuffs")
        ))
        assert len(cups) == 1
        assert (cups[0], RDFS.label, Literal("Cup")) in graph

    def test_build_graph_without_ontology(self, sample_data, base_uri):
        builder = GraphBuilder(
            data=sample_data,
            ontologies=[],
            base_uri=base_uri
        )
        graph = builder.build()

        # Class fallback should use example.org namespace
        subject_uri = None
        for s in graph.subjects(RDFS.label, Literal("Teapot")):
            subject_uri = s
            break

        assert subject_uri is not None
        assert (subject_uri, RDF.type, OWL.Thing) in graph or (
            subject_uri, RDF.type, Literal("TeaPot")) in graph

        # Predicate fallback
        fallback_pred = URIRef("http://example.org/resource/stuffs")
        cups = list(graph.objects(
            subject=subject_uri,
            predicate=fallback_pred
        ))
        assert len(cups) == 1
        assert (cups[0], RDFS.label, Literal("Cup")) in graph
    
    def test_add_rule(self, sample_data, base_uri):
        fixed_literal = Literal("FORCED DESCRIPTION")

        # Règle 2 : fonction qui retourne un URIRef basé sur la valeur
        def dynamic_rule(key, value):
            return (key, URIRef(f"http://custom.org/id/{value[0]['name']}"))

        # Création du builder avec règles
        builder = GraphBuilder(
            data=sample_data,
            ontologies=[],
            base_uri=base_uri
        )
        builder.add_rule("description", fixed_literal)
        builder.add_rule("stuffs", dynamic_rule)

        graph = builder.build()

        triples = list(graph)

        print(triples)

        # Test présence de la valeur forcée
        assert any(
            p == URIRef(RDFS.comment) and o == fixed_literal
            for _, p, o in triples
        )

        # Test transformation dynamique via URIRef
        assert any(
            p == URIRef(f"{base_uri}stuffs") and o == URIRef("http://custom.org/id/Cup")
            for _, p, o in triples
        )

        # Test que le champ "name" est toujours converti normalement
        assert any(
            p == URIRef(RDFS.label) and o == Literal("Teapot")
            for _, p, o in triples
        )
