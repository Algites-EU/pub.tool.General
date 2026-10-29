"""Ensure all Defs/SDO method-naming schema variants use one closed role set."""
from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree

import pytest
import yaml


CODE_ROOT = Path(__file__).resolve().parents[5]
ROLES = {
    'standard_getter', 'standard_setter', 'raw_getter',
    'raw_presence_checker_method', 'raw_unsetter'
}


@pytest.mark.parametrize('source_kind,suffix', [
    ('jsondefs', 'jsondef.schema.json'),
    ('yamldefs', 'yamldef.schema.json'),
])
def test_role_enum_and_structural_naming_key_reference(source_kind: str, suffix: str):
    base = CODE_ROOT / 'common' / 'src' / 'product' / source_kind / 'eu' / 'algites' / 'tool' / 'codegen' / 'common' / 'naming'
    enum = json.loads((base / f'generated-dataobject-method-kind_1.{suffix}').read_text('utf-8'))
    assert set(enum['enum']) == ROLES
    naming = json.loads((base / f'data-object-naming-conventions_1.{suffix}').read_text('utf-8'))
    structure = (naming['properties']['GeneratedDataObjectMethodNameConventions']
                 ['properties']['NameConventions']['additionalProperties']
                 ['properties']['StructureNaming'])
    assert structure['propertyNames']['$ref'] == f'generated-dataobject-method-kind_1.{suffix}'
    assert set(structure['required']) == {'standard_getter', 'standard_setter'}


def test_xsd_enum_and_typed_map_key():
    base = CODE_ROOT / 'common' / 'src' / 'product' / 'xmldefs' / 'eu' / 'algites' / 'tool' / 'codegen' / 'common' / 'naming'
    namespace = {'xs': 'http://www.w3.org/2001/XMLSchema'}
    enum = ElementTree.parse(base / 'generated-dataobject-method-kind_1.xsd')
    assert {e.attrib['value'] for e in enum.findall('.//xs:enumeration', namespace)} == ROLES
    naming = ElementTree.parse(base / 'data-object-naming-conventions_1.xsd')
    assert any(e.attrib.get('type') == 'kind:generated-dataobject-method-kind'
               for e in naming.findall('.//xs:attribute', namespace))
    assert any(e.attrib.get('name') == 'UniqueMethodKinds'
               for e in naming.findall('.//xs:key', namespace))


@pytest.mark.parametrize('profile', ['algites', 'standardprefix', 'standardpostfix'])
@pytest.mark.parametrize('language', ['java', 'python'])
def test_profiles_only_use_known_method_roles(profile: str, language: str):
    prefix = {'algites':'algites','standardprefix':'standard-prefix','standardpostfix':'standard-postfix'}[profile]
    directory = CODE_ROOT / 'profile' / profile / 'src' / 'product' / 'config' / 'eu' / 'algites' / 'lib' / 'naming' / 'convention'
    # Standard profile filenames use standardprefix/standardpostfix without a hyphen,
    # but composition IDs in their contents use the hyphenated spelling.
    name = f'{profile}-{language}-codegen-method-conventions.yml'
    document = yaml.safe_load((directory / name).read_text('utf-8'))
    entries = document['GeneratedDataObjectMethodNameConventions']['NameConventions']
    assert entries
    for role_set in entries.values():
        roles = role_set['StructureNaming']
        assert set(roles) <= ROLES
        assert {'standard_getter', 'standard_setter'} <= set(roles)
        assert {'raw_getter','raw_presence_checker_method','raw_unsetter'} <= set(roles)
