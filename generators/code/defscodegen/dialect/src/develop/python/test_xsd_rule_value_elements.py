"""Regression coverage for keyed naming Rule items across the XSD vocabularies.

XMLDEFS encodes a keyed map item as a Rule with the `kind` attribute and
explicit `Value` child, which the Defs frontend can model as two properties.
This does not pretend that external schema dependencies are already resolved.
"""
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

XS = '{http://www.w3.org/2001/XMLSchema}'
REPO = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
LIB = REPO.parent / 'pub.lib.General'


def _schemas():
    specs = [
        REPO / 'generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd',
        REPO / 'generators/code/sdocodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/sdo/naming/sdocodegen-naming-conventions_1.xsd',
        REPO / 'generators/code/common/src/product/xmldefs/eu/algites/tool/codegen/common/naming/codegen-common-naming-conventions_1.xsd',
        REPO / 'generators/code/common/src/product/xmldefs/eu/algites/tool/codegen/common/naming/data-object-naming-conventions_1.xsd',
    ]
    if LIB.is_dir():
        specs.extend([
            LIB / 'naming/convention/sourcecode/src/product/xmldefs/eu/algites/lib/naming/convention/sourcecode/source-structure-name-conventions_1.xsd',
            LIB / 'naming/convention/sourcecode/src/product/xmldefs/eu/algites/lib/naming/convention/sourcecode/dataobject/dataobject-naming-conventions_1.xsd',
            LIB / 'naming/convention/sourcecode/src/product/xmldefs/eu/algites/lib/naming/convention/sourcecode/smartdataobject/smartdataobject-naming-conventions_1.xsd',
        ])
    return specs


@pytest.mark.parametrize('path', _schemas(), ids=lambda path: path.name)
def test_keyed_rule_is_an_explicit_value_and_attribute(path):
    """Keep Rule wire fields and xs:key while avoiding unsupported simpleContent."""
    root = ET.parse(path).getroot()
    assert not root.findall('.//' + XS + 'simpleContent'), path
    rules = [node for node in root.findall('.//' + XS + 'element')
             if node.get('name') == 'Rule']
    assert rules, path
    for rule in rules:
        complex_type = rule.find(XS + 'complexType')
        assert complex_type is not None
        names = [n.get('name') for n in complex_type.findall(XS + 'sequence/' + XS + 'element')]
        assert names == ['Value']
        assert complex_type.find(XS + 'sequence/' + XS + 'element').get('type') == 'xs:string'
        attributes = [n for n in complex_type.findall(XS + 'attribute') if n.get('name') == 'kind']
        assert len(attributes) == 1
        assert attributes[0].get('use') == 'required'
    keyed = [element for element in root.iter(XS + 'element')
             if any(key.find(XS + 'selector') is not None
                    and key.find(XS + 'selector').get('xpath') == 'Rule'
                    for key in element.findall(XS + 'key'))]
    assert keyed, path
    for element in keyed:
        for key in element.findall(XS + 'key'):
            if key.find(XS + 'selector') is not None and key.find(XS + 'selector').get('xpath') == 'Rule':
                assert [field.get('xpath') for field in key.findall(XS + 'field')] == ['@kind']
