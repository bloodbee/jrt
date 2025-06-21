# JRT‑Python – JSON → RDF Transformer

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
pip install jrt-python

# Or with Poetry:
poetry add jrt-python
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

```python
from pathlib import Path
import json
from jrt.ontology import OntologyLoader
from jrt.graph_builder import GraphBuilder

loader = OntologyLoader()
ontologies = loader.load(Path("path/to/ontologies"))

data = json.loads(Path("input.json").read_text())

builder = GraphBuilder(data=data, ontologies=ontologies,
                       base_uri="http://example.org/resource/")

graph = builder.build()
print(graph.serialize(format="turtle"))
```

---

## Development

```bash
git clone https://github.com/bloodbee/jrt-python.git
cd jrt-python
poetry install --with dev

# run tests
pytest -q
```

---

## Running the CLI from source

```bash
poetry run jrt convert examples/jsons/simple.json --output output.rdf
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