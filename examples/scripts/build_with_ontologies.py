from pathlib import Path
import json
from jrt.ontology import OntologyLoader
from jrt.builder import GraphBuilder

current_file = Path(__file__)
dist_path = current_file.parent.parent.parent / Path("dist")
simple_ontology_path = current_file.parent.parent / Path("load_ontology/stuff.xml")
multiple_ontologies_path = current_file.parent.parent / Path("load_ontologies")
data_stuff = json.loads((current_file.parent.parent / Path("jsons/stuff.json")).read_text())

# Verify that dist directory exists
if not dist_path.exists():
    dist_path.mkdir(exists_ok=True)

# Working with stuff.json data and simple ontology
destination_simple = current_file.parent.parent.parent / Path("dist/output_stuff_with_simple_ontology.xml")

loader_simple = OntologyLoader()
ontology = loader_simple.load(simple_ontology_path)
builder_stuff = GraphBuilder(data=data_stuff, ontologies=ontology)
graph_stuff = builder_stuff.build()

graph_stuff.serialize(destination=destination_simple, format="xml")

# Working with stuff.json data and multiple ontologies
destination_multiple = current_file.parent.parent.parent / Path("dist/output_stuff_with_multiple_ontologies.xml")

loader_multiple = OntologyLoader()
ontologies = loader_multiple.load(multiple_ontologies_path)
builder_stuff = GraphBuilder(data=data_stuff, ontologies=ontologies)
graph_stuff = builder_stuff.build()

graph_stuff.serialize(destination=destination_multiple, format="xml")