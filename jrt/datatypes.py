"""Heuristic detection of XSD datatypes for JSON *string* values.

Native JSON scalars (int, float, bool) are already typed correctly by rdflib
when wrapped in a :class:`~rdflib.Literal`. This module only handles string
values that carry an implicit datatype -- ISO dates / date-times, booleans and
HTTP(S) URIs -- and deliberately leaves everything else (including
numeric-looking strings such as identifiers, zip codes or phone numbers) as a
plain ``xsd:string`` to avoid silently corrupting data.
"""

from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlparse

from rdflib import Literal, URIRef
from rdflib.namespace import XSD

# Anchored, structural patterns. Range/semantic validity (e.g. month <= 12) is
# then confirmed by rdflib itself, so the emitted lexical form is always valid.
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$")
_URI_SCHEMES = {"http", "https"}


def _is_valid(value: str, datatype: URIRef) -> bool:
    """True if *value* is a valid lexical form for *datatype* (per rdflib)."""
    return Literal(value, datatype=datatype).value is not None


def _is_uri(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in _URI_SCHEMES and bool(parsed.netloc)


def detect_datatype(value: str) -> Optional[URIRef]:
    """Return the XSD datatype implied by *value*, or ``None`` for a plain string."""
    if value in ("true", "false"):
        return XSD.boolean
    if _DATETIME_RE.match(value) and _is_valid(value, XSD.dateTime):
        return XSD.dateTime
    if _DATE_RE.match(value) and _is_valid(value, XSD.date):
        return XSD.date
    if _is_uri(value):
        return XSD.anyURI
    return None


def to_literal(value: Any, detect: bool = True) -> Literal:
    """Wrap *value* in a Literal, inferring an XSD datatype for typed strings."""
    if detect and isinstance(value, str):
        datatype = detect_datatype(value)
        if datatype is not None:
            return Literal(value, datatype=datatype)
    return Literal(value)
