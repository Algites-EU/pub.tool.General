"""Regression: externally referenced naming-role enums share nominal types.

The published JSONDEFS/YAMLDEFS top-level enum uses its filename-derived
name, while XMLDEFS uses a declared ``xs:simpleType``. If those differ, a
shared DataObject getter cannot return one stable Java enum type.

@author linhart1
"""
from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest


REPOSITORY = Path(__file__).resolve().parents[2]
XS = '{http://www.w3.org/2001/XMLSchema}'


@pytest.mark.parametrize('area,domain,stem', [
    ('defscodegen', 'defs', 'defscodegen-structure-kind'),
    ('sdocodegen', 'sdo', 'sdocodegen-structure-kind'),
])
def test_naming_role_enum_has_identical_name_and_values_in_three_dialects(
        area: str, domain: str, stem: str) -> None:
    """A schema-root enum must have the same nominal name in every dialect."""
    base = REPOSITORY / f'generators/code/{area}/intf/src/product'
    suffix = f'eu/algites/tool/codegen/{domain}/naming/{stem}_1'
    xml_file = base / 'xmldefs' / (suffix + '.xsd')
    schema = ET.parse(xml_file).getroot()
    xsd_types = schema.findall(f'{XS}simpleType')
    assert len(xsd_types) == 1

    # These published filename conventions treat "defscodegen" and
    # "sdocodegen" as one identifier segment, not two words.
    expected_name = ''.join(part.capitalize() for part in stem.split('-'))
    assert xsd_types[0].get('name') == expected_name
    xsd_values = [e.get('value') for e in xsd_types[0].iter(f'{XS}enumeration')]

    naming_xsd = (base / 'xmldefs' /
                  f'eu/algites/tool/codegen/{domain}/naming/{area}-naming-conventions_1.xsd')
    naming_xml = ET.parse(naming_xsd).getroot()
    assert any(attr.get('name') == 'kind' and
               attr.get('type') == f'kind:{expected_name}'
               for attr in naming_xml.iter(f'{XS}attribute'))

    for dialect, extension in (('jsondefs', 'jsondef'), ('yamldefs', 'yamldef')):
        enum_file = base / dialect / (suffix + f'.{extension}.schema.json')
        typed_enum = json.loads(enum_file.read_text(encoding='utf-8'))
        assert typed_enum['type'] == 'string'
        assert typed_enum['enum'] == xsd_values
        naming_file = (base / dialect /
                       f'eu/algites/tool/codegen/{domain}/naming/{area}-naming-conventions_1.{extension}.schema.json')
        naming_schema = json.loads(naming_file.read_text(encoding='utf-8'))
        expected_ref = typed_enum['$id']
        assert naming_schema['$defs'][
            'DefsCodegenStructureNamingRule' if area == 'defscodegen'
            else 'SdoCodegenStructureNamingRule']['properties']['kind']['$ref'] == expected_ref
