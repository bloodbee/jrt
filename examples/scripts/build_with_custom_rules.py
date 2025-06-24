from rdflib import Literal
from pathlib import Path
import json
from jrt.ontology import OntologyLoader
from jrt.builder import GraphBuilder

current_file = Path(__file__)
dist_path = current_file.parent.parent.parent / Path("dist")
ontology_path = current_file.parent.parent / Path("load_ontology/stuff.xml")
data_stuff = json.loads((current_file.parent.parent / Path("jsons/stuff.json")).read_text())

# Verify that dist directory exists
if not dist_path.exists():
    dist_path.mkdir(exists_ok=True)

# Working with stuff.json data, simple ontology and custom rules
destination = current_file.parent.parent.parent / Path("dist/output_stuff_with_custom_rules.xml")

def upper_label(key, value):
    return (key, Literal(value.upper()))

loader = OntologyLoader()
ontology = loader.load(ontology_path)
builder = GraphBuilder(data=data_stuff, ontologies=ontology)

# Add custom rules
builder.add_rule("label", upper_label)
builder.add_rule("description", Literal("This is a new description"))

# Build
graph = builder.build()

graph.serialize(destination=destination, format="xml")