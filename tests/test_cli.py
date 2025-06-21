import json
import pytest
from pathlib import Path
from rdflib import Graph, Literal
from rdflib.namespace import RDFS, RDF
from typer.testing import CliRunner

from jrt.cli import app

runner = CliRunner()


def test_convert_command_with_ontology(json_input, teapot_ontology_file, tmp_path):
    output = tmp_path / "output.rdf"

    result = runner.invoke(
        app,
        [
            "convert",
            str(json_input),
            "--output", str(output),
            "--ontology", str(teapot_ontology_file),
            "--base-uri", "http://example.org/resource/"
        ]
    )

    assert result.exit_code == 0
    assert output.exists()

    g = Graph()
    g.parse(output, format="xml")

    # Check that the main subject exists with expected label
    subjects = list(g.subjects(RDFS.label, Literal("Teapot")))
    assert len(subjects) == 1

    # Ensure RDF type was resolved from ontology
    s = subjects[0]
    assert (s, RDF.type, None) in g


def test_convert_command_without_ontology(json_input, tmp_path):
    output = tmp_path / "out.rdf"

    result = runner.invoke(
        app,
        [
            "convert",
            str(json_input),
            "--output", str(output)
        ]
    )

    assert result.exit_code == 0
    assert output.exists()

    g = Graph()
    g.parse(output, format="xml")

    # Should include the basic RDF structure even without ontology
    subjects = list(g.subjects(RDFS.label, Literal("Teapot")))
    assert len(subjects) == 1
