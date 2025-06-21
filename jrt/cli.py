import typer
from pathlib import Path
import logging
import json

from .ontology import OntologyLoader
from .builder import GraphBuilder

app = typer.Typer(help="JSON to RDF Transformer (JRT)", pretty_exceptions_enable=False)


def build_format(fmt: str):
    if fmt in ["xml", "ttl", "nt", "json-ld"]:
        return fmt
    else:
        typer.echo(f"WARNING - Output format `{fmt}` is not recognized, using xml.")
        return "xml"

@app.command()
def convert(
    input: Path = typer.Argument(..., help="JSON input file"),
    output: Path = typer.Option("dist/output.xml", help="RDF output file"),
    base_uri: str = typer.Option("http://example.org/resource/", help="Base URI for RDF resources"),
    ontology: Path = typer.Option(None, help="RDF/OWL ontology to enrich mapping - could be a file or a directory"),
    format: str = typer.Option("xml", help="RDF serialization format (e.g., xml, ttl, nt, json-ld)")
):
    """
    Convert a JSON in RDF/XML.
    """

    fmt = build_format(format)
    loader = OntologyLoader()
    ontologies = []
    if ontology:
        ontologies = loader.load(ontology)
        if isinstance(ontologies, list):
            typer.echo(f"Loaded {len(ontologies)} ontologies from directory {ontology.resolve()}")
        else:
            typer.echo(f"Loaded ontology from file {ontology.resolve()}")
    
    with input.open() as f:
        data = json.load(f)

    builder = GraphBuilder(data=data, ontologies=ontologies, base_uri=base_uri)
    graph = builder.build()

    graph.serialize(destination=output, format=fmt)


@app.command()
def info():
    """Fake info to make command works with 'jrt convert ...'"""
    pass

if __name__ == "__main__":
    app()
