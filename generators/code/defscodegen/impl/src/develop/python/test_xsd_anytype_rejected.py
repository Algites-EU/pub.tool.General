"""Validate the intentionally unsupported untyped XSD value construct."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend


def test_explicit_anytype_rejected(tmp_path):
    p = tmp_path / 'explicit_1.xsd'
    p.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                 '<xs:element name="Something" type="xs:anyType"/>'
                 '</xs:schema>')
    with pytest.raises(ValueError, match='xs:anyType.*explicit_1.xsd'):
        AIcXmlDefsFrontend()._parse(p)


def test_implicit_anytype_rejected(tmp_path):
    p = tmp_path / 'implicit_1.xsd'
    p.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                 '<xs:element name="Something"/>'
                 '</xs:schema>')
    with pytest.raises(ValueError, match='implicit XSD anyType.*Something'):
        AIcXmlDefsFrontend()._parse(p)


def test_named_complex_type_allowed(tmp_path):
    p = tmp_path / 'typed_1.xsd'
    p.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                 '<xs:complexType name="Typed"><xs:sequence>'
                 '<xs:element name="Value" type="xs:string"/>'
                 '</xs:sequence></xs:complexType></xs:schema>')
    AIcXmlDefsFrontend()._parse(p)
