"""Ensure all three Common/Defs/SDO naming domains use their own closed role vocabulary.

The old combined generated-dataobject-method-kind is a compatibility schema and
must not be consulted by the new frontend or the new naming profiles.
"""
from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree

import pytest
import yaml


CODE_ROOT = Path(__file__).resolve().parents[5]
ROLES = {
    'common': {'standard_getter', 'standard_setter',
               'positional_item_synthetic_getter',
               'multi_mapped_list_key_synthetic_getter',
               'multi_mapped_list_value_synthetic_getter', 'const_container_interface'},
    'defs': {'synthetic_property_type', 'synthetic_list_item_type',
             'synthetic_map_value_type', 'synthetic_positional_item_type',
             'synthetic_choice_variant_type', 'synthetic_group_type',
             'string_enum_item', 'non_string_enum_item'},
    'sdo': {'raw_getter', 'raw_presence_checker_method', 'raw_unsetter'},
}
SCHEMAS = {
    'common': ('common', 'src/product', 'common/naming',
               'codegen-common', 'CommonCodegenNameConventions'),
    'defs': ('defscodegen/intf', 'src/product', 'defs/naming',
             'defscodegen', 'DefsCodegenNameConventions'),
    'sdo': ('sdocodegen/intf', 'src/product', 'sdo/naming',
            'sdocodegen', 'SdoCodegenNameConventions'),
}


def _schema_root(domain: str, source_kind: str) -> tuple[Path, str, str]:
    artifact, source, package, prefix, container = SCHEMAS[domain]
    return (CODE_ROOT / artifact / source / source_kind / 'eu/algites/tool/codegen' / package,
            prefix, container)


@pytest.mark.parametrize('domain', ROLES)
@pytest.mark.parametrize('source_kind,suffix', [
    ('jsondefs', 'jsondef.schema.json'),
    ('yamldefs', 'yamldef.schema.json'),
])
def test_role_enum_and_structural_naming_key_reference(domain: str, source_kind: str, suffix: str):
    base, prefix, container = _schema_root(domain, source_kind)
    roles = json.loads((base / f'{prefix}-structure-kind_1.{suffix}').read_text('utf-8'))
    assert set(roles['enum']) == ROLES[domain]
    naming = json.loads((base / f'{prefix}-naming-conventions_1.{suffix}').read_text('utf-8'))
    structure = (naming['properties'][container]['properties']['NameConventions']
                 ['additionalProperties']['properties']['StructureNaming'])
    assert structure['propertyNames']['$ref'].endswith(f'/{prefix}-structure-kind_1.{suffix}')
    if domain == 'common':
        assert set(structure['required']) == {'standard_getter', 'standard_setter'}
    else:
        assert 'standard_getter' not in structure.get('properties', {})


@pytest.mark.parametrize('domain', ROLES)
def test_xsd_enum_and_typed_map_key(domain: str):
    base, prefix, _ = _schema_root(domain, 'xmldefs')
    namespace = {'xs': 'http://www.w3.org/2001/XMLSchema'}
    enum = ElementTree.parse(base / f'{prefix}-structure-kind_1.xsd')
    assert {e.attrib['value'] for e in enum.findall('.//xs:enumeration', namespace)} == ROLES[domain]
    naming = ElementTree.parse(base / f'{prefix}-naming-conventions_1.xsd')
    assert any(e.attrib.get('name') == 'StructureNaming'
               for e in naming.findall('.//xs:element', namespace))


@pytest.mark.parametrize('profile', ['algites', 'standardprefix', 'standardpostfix'])
@pytest.mark.parametrize('language', ['java', 'python'])
def test_profiles_only_use_known_method_roles(profile: str, language: str):
    directory = CODE_ROOT / 'profile' / profile / 'src/product/config/eu/algites/tool/codegen'
    for domain, roles in ROLES.items():
        path = directory / f'{profile}-{language}-{domain}-codegen-conventions.yml'
        document = yaml.safe_load(path.read_text('utf-8'))
        root = {'common': 'CommonCodegenNameConventions',
                'defs': 'DefsCodegenNameConventions',
                'sdo': 'SdoCodegenNameConventions'}[domain]
        entries = document[root]['NameConventions']
        assert entries
        for spec in entries.values():
            actual = set(spec['StructureNaming'])
            assert actual <= roles, (profile, language, domain, actual - roles)
            if domain == 'common':
                assert {'standard_getter', 'standard_setter'} <= actual
            else:
                assert spec['CommonNamingConvention'] in yaml.safe_load(
                    (directory / f'{profile}-{language}-common-codegen-conventions.yml')
                    .read_text('utf-8'))['CommonCodegenNameConventions']['NameConventions']


class TestLanguageProfileEquivalence:
    """Profiles may spell names differently, but must configure identical roles."""

    @pytest.mark.parametrize('profile', ['algites', 'standardprefix', 'standardpostfix'])
    @pytest.mark.parametrize('domain,root', [
        ('common', 'CommonCodegenNameConventions'),
        ('defs', 'DefsCodegenNameConventions'),
        ('sdo', 'SdoCodegenNameConventions'),
    ])
    def test_java_and_python_offer_same_naming_capabilities(self, profile, domain, root):
        """Prevent silently missing Python roles that are implemented by Java."""
        directory = CODE_ROOT / 'profile' / profile / 'src/product/config/eu/algites/tool/codegen'
        specs = {}
        for language in ('java', 'python'):
            path = directory / f'{profile}-{language}-{domain}-codegen-conventions.yml'
            document = yaml.safe_load(path.read_text(encoding='utf-8'))
            entries = document[root]['NameConventions']
            assert len(entries) == 1
            specs[language] = next(iter(entries.values()))
        assert set(specs['java']['StructureNaming']) == set(specs['python']['StructureNaming'])
        if domain == 'common':
            assert specs['java']['SchemaMetadataNaming'] == specs['python']['SchemaMetadataNaming']
            assert specs['java']['IndexesStartingFrom'] == specs['python']['IndexesStartingFrom']
        else:
            assert specs['java']['CommonNamingConvention'].replace('-java-', '-LANGUAGE-') == (
                specs['python']['CommonNamingConvention'].replace('-python-', '-LANGUAGE-'))
