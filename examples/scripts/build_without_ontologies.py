from pathlib import Path
import json
from jrt.builder import GraphBuilder

current_file = Path(__file__)
dist_path = current_file.parent.parent.parent / Path("dist")

# Verify that dist directory exists
if not dist_path.exists():
    dist_path.mkdir(exists_ok=True)


# Working with simple.json data
destination_simple = current_file.parent.parent.parent / Path("dist/output_simple_no_ontologies.xml")
data_simple = json.loads((current_file.parent.parent / Path("jsons/simple.json")).read_text())

builder_simple = GraphBuilder(data=data_simple)
graph_simple = builder_simple.build()

graph_simple.serialize(destination=destination_simple, format="xml")

# Working with stuff.json data
destination_stuff = current_file.parent.parent.parent / Path("dist/output_stuff_no_ontologies.xml")
data_stuff = json.loads((current_file.parent.parent / Path("jsons/stuff.json")).read_text())

builder_stuff = GraphBuilder(data=data_stuff)
graph_stuff = builder_stuff.build()

graph_stuff.serialize(destination=destination_stuff, format="xml")