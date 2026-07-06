import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD, Namespace

from jrt.builder import GraphBuilder
from jrt.ontology import Ontology


class TestGraphBuilder:

    def test_build_graph_with_ontology(self, sample_data, teapot_ontology, base_uri):
        builder = GraphBuilder(data=sample_data, ontologies=[teapot_ontology], base_uri=base_uri)
        graph = builder.build()

        subject_uri = None
        for s in graph.subjects(RDFS.label, Literal("Teapot")):
            subject_uri = s
            break

        assert subject_uri is not None

        # Ensure class type was correctly resolved from ontology
        assert (subject_uri, RDF.type, URIRef("http://example.org/stuff#TeaPot")) in graph

        # Ensure nested object was created and linked
        cups = list(
            graph.objects(subject=subject_uri, predicate=URIRef("http://example.org/stuff#stuffs"))
        )
        assert len(cups) == 1
        assert (cups[0], RDFS.label, Literal("Cup")) in graph

    def test_build_graph_without_ontology(self, sample_data, base_uri):
        builder = GraphBuilder(data=sample_data, ontologies=[], base_uri=base_uri)
        graph = builder.build()

        # Class fallback should use example.org namespace
        subject_uri = None
        for s in graph.subjects(RDFS.label, Literal("Teapot")):
            subject_uri = s
            break

        assert subject_uri is not None
        assert (subject_uri, RDF.type, OWL.Thing) in graph or (
            subject_uri,
            RDF.type,
            Literal("TeaPot"),
        ) in graph

        # Predicate fallback
        fallback_pred = URIRef("http://example.org/resource/stuffs")
        cups = list(graph.objects(subject=subject_uri, predicate=fallback_pred))
        assert len(cups) == 1
        assert (cups[0], RDFS.label, Literal("Cup")) in graph

    def test_add_rule(self, sample_data, base_uri):
        fixed_literal = Literal("FORCED DESCRIPTION")

        # Règle 2 : fonction qui retourne un URIRef basé sur la valeur
        def dynamic_rule(key, value):
            return (key, URIRef(f"http://custom.org/id/{value[0]['name']}"))

        # Création du builder avec règles
        builder = GraphBuilder(data=sample_data, ontologies=[], base_uri=base_uri)
        builder.add_rule("description", fixed_literal)
        builder.add_rule("stuffs", dynamic_rule)

        graph = builder.build()

        triples = list(graph)

        print(triples)

        # Test présence de la valeur forcée
        assert any(p == URIRef(RDFS.comment) and o == fixed_literal for _, p, o in triples)

        # Test transformation dynamique via URIRef
        assert any(
            p == URIRef(f"{base_uri}stuffs") and o == URIRef("http://custom.org/id/Cup")
            for _, p, o in triples
        )

        # Test que le champ "name" est toujours converti normalement
        assert any(p == URIRef(RDFS.label) and o == Literal("Teapot") for _, p, o in triples)

    def test_add_rule_returning_triple_list(self, sample_data, base_uri):
        s = URIRef("http://custom.org/s")
        p = URIRef("http://custom.org/p")
        o = Literal("explicit")

        def triples_rule(key, value):
            return [(s, p, o)]

        builder = GraphBuilder(data=sample_data, ontologies=[], base_uri=base_uri)
        builder.add_rule("stuffs", triples_rule)
        graph = builder.build()

        # The explicit triple returned by the rule must be present verbatim
        assert (s, p, o) in graph

    def test_datatype_property_resolved_from_ontology(self, base_uri):
        EX = Namespace("http://example.org/stuff#")
        onto_graph = Graph()
        # "color" is a datatype property -> must be used as predicate over the
        # base-URI fallback that a plain unknown key would get.
        onto_graph.add((EX.color, RDF.type, OWL.DatatypeProperty))
        onto_graph.add((EX.color, RDFS.label, Literal("color")))

        data = {"id": "x1", "name": "Teapot", "color": "blue"}
        builder = GraphBuilder(
            data=data,
            ontologies=[Ontology(graph=onto_graph)],
            base_uri=base_uri,
        )
        graph = builder.build()

        # The datatype property from the ontology is used as the predicate,
        # and the value stays a literal (datatype props are not object-linked).
        assert (None, EX.color, Literal("blue")) in graph
        # And it must NOT have fallen back to the base-URI predicate.
        assert (None, URIRef(f"{base_uri}color"), Literal("blue")) not in graph

    def test_smart_datatypes_are_inferred(self, base_uri):
        data = {
            "id": "e1",
            "name": "Event",
            "startDate": "2024-01-15",
            "createdAt": "2024-01-15T10:30:00Z",
            "homepage": "https://example.org/e1",
            "active": "true",
            "reference": "12345",  # numeric-looking -> must stay a plain string
        }
        graph = GraphBuilder(data=data, ontologies=[], base_uri=base_uri).build()

        # rdflib canonicalizes typed lexical forms, so assert on the datatypes
        datatypes = {o.datatype for _, _, o in graph if isinstance(o, Literal)}
        assert XSD.date in datatypes
        assert XSD.dateTime in datatypes
        assert XSD.anyURI in datatypes
        assert XSD.boolean in datatypes

        # numeric-looking reference stays an untyped string
        ref = next(o for _, _, o in graph if isinstance(o, Literal) and str(o) == "12345")
        assert ref.datatype is None

    def test_smart_datatypes_can_be_disabled(self, base_uri):
        data = {"id": "e1", "name": "Event", "startDate": "2024-01-15"}
        graph = GraphBuilder(
            data=data, ontologies=[], base_uri=base_uri, detect_datatypes=False
        ).build()

        obj = next(o for _, _, o in graph if isinstance(o, Literal) and str(o) == "2024-01-15")
        assert obj.datatype is None
