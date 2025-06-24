# JRT – JSON to RDF Transformer


[![Tests](https://img.shields.io/github/actions/workflow/status/bloodbee/jrt/tests.yml)](https://github.com/bloodbee/jrt/actions/workflows/tests.yml)
[![Pypi](https://img.shields.io/pypi/v/jrt)](https://pypi.org/project/jrt/)
[![Python version](https://img.shields.io/static/v1?label=Python&message=3.10|3.11&color=blue)](https://www.python.org/downloads/)

> Convert any JSON document to RDF/XML (or other RDF serializations) from the command line or as a library, while automatically leveraging OWL/RDFS ontologies you supply.

---

## Features
- **Ontology‑aware mapping** – classes & properties found in your OWL/RDFS ontologies are resolved first; public namespaces (FOAF, DC, …) are used only as fallback.
- **UUID subject strategy** – stable UUID‑v5 URIs when an id key is present, random UUID‑v4 otherwise.
- **Heuristics out of the box** – automatic rdfs:label, rdfs:comment, list handling, object‑property linking by literal label.
- **Clean Typer CLI** – jrt convert input.json --ontology path/ --output out.rdf.
- **Extensible library API** – integrate OntologyLoader, OntologyResolver, or GraphBuilder directly in Python code.
- **100 % PyPI‑ready** – MIT‑licensed, tested with pytest, zero runtime dependencies outside rdflib & typer.

---

## Quick start

### 1 – Install

```bash
# PyPI:
pip install jrt

# Or with Poetry:
poetry add jrt
```

### 2 – CLI usage

```bash
jrt convert data.json \
  --output dist/data.rdf \
  --ontology path/to/ontologies/file_or_directory \
  --base-uri "http://example.org/resource/"
  --format ttl
```

*--ontology can be a single RDF/OWL file or a directory; all .rdf, .owl, .xml, .ttl files are loaded.*

*Supported output formats (--format) : xml (default), ttl, nt, json‑ld*

### 3 – Library usage

You can find several examples in the [dedicated folder](/examples/)

#### Building

```python
from pathlib import Path
import json
from jrt.ontology import OntologyLoader
from jrt.builder import GraphBuilder

loader = OntologyLoader()
ontologies = loader.load(Path("path/to/ontologies"))

data = json.loads(Path("input.json").read_text())

builder = GraphBuilder(data=data, ontologies=ontologies,
                       base_uri="http://example.org/resource/")

graph = builder.build()
print(graph.serialize(format="turtle"))
```

#### Add serialization rules

This library offers the possibility of adding serialization rules to extend its capabilities and avoid the need for additional post-build work.

To do this, use the `add_rule` method:

```python
from rdflib import Literal, URIRef
from jrt.builder import GraphBuilder
from typing import Union, List

json_data = {
  "id": "thing123",
  "name": "MyThing",
  "custom": "This is a custom value",
  "list": ["key1", "key2", "unknown"],
  "dict": {
    "valid": "This is valid"
  }
}

def dynamic_rule(key, value) -> Union[tuple, List(tuple)]:
  # Apply transformation to elements in value.
  # You can return a tuple (ex: (key, new_value))
  # or a list of triples (ex: [(s1, p1, new_value_1), (s2, p2, new_value_2)])
  ...

static_rule_uri = URIRef(...)
static_rule_literal = Literal(..., datatype=...)

builder = GraphBuilder(data=json_data, ...)

# Add new rules
builder.add_rule('custom', static_rule_literal)
builder.add_rule('dict', static_rule_uri)
builder.add_rule('list', dynamic_rule)

graph = builder.build()
```

---

## Running the CLI from source

```bash
poetry run jrt convert examples/jsons/simple.json --output output.rdf
```

---

## Development

```bash
git clone https://github.com/bloodbee/jrt.git
cd jrt-python
poetry install --with dev

# run tests
pytest -q
```

---

## Contributing

1. Fork the repo and create your feature branch (git checkout -b feat/my‑feature).
2. Commit your changes with clear messages.
3. Ensure all tests pass (pytest).
4. Submit a pull request.

---

## License

Released under the MIT License. See [LICENSE](/LICENSE) for the full text.

---

© 2025 Mathieu Dufour. All trademarks and names are property of their respective owners.