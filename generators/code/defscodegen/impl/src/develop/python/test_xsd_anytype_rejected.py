"""Validate the intentionally unsupported untyped XSD value construct."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from eu.algites.tool.codegen.defs.old.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend


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


def test_full_builtins_parity_fixture_is_not_a_bootstrap_generation_input():
    """Keep all three unconstrained parity schemata as test fixtures, not build inputs."""
    import json

    develop = Path(__file__).resolve().parents[1]
    examples = develop / "examples" / "parity-builtins"
    xsd = examples / "xmldefs" / "parity-builtins_1.xsd"
    with pytest.raises(ValueError, match=r"Unsupported XSD xs:anyType.*parity-builtins_1.xsd"):
        AIcXmlDefsFrontend()._parse(xsd)
    for source_kind in ("jsondefs", "yamldefs"):
        path = examples / source_kind / (
            "parity-builtins_1." + (
                "jsondef.schema.json" if source_kind == "jsondefs" else "yamldef.schema.json"
            )
        )
        definition = json.loads(path.read_text(encoding="utf-8"))
        assert "type" not in definition["properties"]["anyType"]
        assert "x-test-xsd-type" not in definition["properties"]["anyType"]
        assert "x-modustro-datatype" not in definition["properties"]["anyType"]
        assert "type" not in definition["properties"]["anySimpleType"]
    for source_kind in ("jsondefs", "yamldefs", "xmldefs"):
        assert not (develop / source_kind / (
            "parity-builtins_1." + (
                "xsd" if source_kind == "xmldefs"
                else "jsondef.schema.json" if source_kind == "jsondefs"
                else "yamldef.schema.json"
            )
        )).exists()


def test_unconstrained_root_parity_fixture_is_not_a_bootstrap_generation_input():
    """Preserve unconstrained cross-format fixtures as negative tests outside build-source roots."""
    import json

    develop = Path(__file__).resolve().parents[1]
    examples = develop / "examples" / "parity-root"
    xsd = examples / "xmldefs" / "parity-root_1.xsd"
    with pytest.raises(ValueError, match=r"Unsupported XSD xs:anyType.*parity-root_1.xsd"):
        AIcXmlDefsFrontend()._parse(xsd)
    for kind in ("jsondefs", "yamldefs"):
        suffix = "jsondef.schema.json" if kind == "jsondefs" else "yamldef.schema.json"
        schema = json.loads((examples / kind / f"parity-root_1.{suffix}").read_text(encoding="utf-8"))
        assert "type" not in schema["properties"]["anything"]
        assert not (develop / kind / f"parity-root_1.{suffix}").exists()
    assert not (develop / "xmldefs" / "parity-root_1.xsd").exists()
