import pytest
from rdflib import Literal
from rdflib.namespace import XSD

from jrt.datatypes import detect_datatype, to_literal


class TestDetectDatatype:

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("2024-01-15", XSD.date),
            ("2024-01-15T10:30:00", XSD.dateTime),
            ("2024-01-15T10:30:00Z", XSD.dateTime),
            ("2024-01-15T10:30:00+02:00", XSD.dateTime),
            ("2024-01-15T10:30:00.123", XSD.dateTime),
            ("true", XSD.boolean),
            ("false", XSD.boolean),
            ("http://example.org/x", XSD.anyURI),
            ("https://example.org/x?y=1", XSD.anyURI),
        ],
    )
    def test_typed_strings(self, value, expected):
        assert detect_datatype(value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            "hello world",
            "12345",  # numeric-looking id / zip -> must stay a plain string
            "-42",
            "3.14",
            "True",  # only exact lowercase true/false are booleans
            "2024-13-45",  # structurally date-like but invalid -> plain string
            "2024-01-15T99:99:99",  # invalid time
            "ftp://example.org",  # non-http(s) scheme not coerced
            "just:a:string",
            "",
        ],
    )
    def test_plain_strings(self, value):
        assert detect_datatype(value) is None


class TestToLiteral:

    def test_typed_string_gets_datatype(self):
        lit = to_literal("2024-01-15")
        assert lit.datatype == XSD.date

    def test_detection_can_be_disabled(self):
        lit = to_literal("2024-01-15", detect=False)
        assert lit.datatype is None
        assert lit == Literal("2024-01-15")

    def test_non_string_values_untouched(self):
        # rdflib already types native scalars; we must not interfere
        assert to_literal(5).datatype == XSD.integer
        assert to_literal(True).datatype == XSD.boolean
