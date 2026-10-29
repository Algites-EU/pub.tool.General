"""Verify the split domain-specific profiles against published library schema sources.

Profiles are prepared for the tool's next generator-interface migration, while
legacy method catalogs remain available to the current codegen bootstrap.
"""
from pathlib import Path
import json
import yaml
import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[7]
LIB = ROOT / 'pub.lib.General/naming/convention'
TOOL = ROOT / 'pub.tool.General/generators/code'

@pytest.mark.parametrize('family', ('jsondefs', 'yamldefs'))
@pytest.mark.parametrize('profile', ('algites', 'standardprefix', 'standardpostfix'))
@pytest.mark.parametrize('language', ('java', 'python'))
@pytest.mark.parametrize('domain', ('dataobject', 'smartdataobject'))
def test_split_naming_catalog_schema_parity(family, profile, language, domain):
    """Validate every profile and ensure unrelated method/metadata roles are absent."""
    schemas = []
    suffix = 'jsondef' if family == 'jsondefs' else 'yamldef'
    for module in ('intf', 'sourcecode'):
        for path in (LIB / module / 'src/product' / family).rglob(f'*.{suffix}.schema.json'):
            schemas.append(json.loads(path.read_text(encoding='utf-8')))
    registry = Registry().with_resources((item['$id'], Resource.from_contents(
        item, default_specification=DRAFT202012)) for item in schemas)
    path = (TOOL / 'profile' / profile / 'src/product/config/eu/algites/lib/naming/convention/sourcecode'
            / f'{profile}-{language}-{domain}-conventions.yml')
    document = yaml.safe_load(path.read_text(encoding='utf-8'))
    schema_url = document['$schema']
    if family == 'jsondefs':
        schema_url = schema_url.replace('/yamldefs/', '/jsondefs/').replace(
            '.yamldef.schema.json', '.jsondef.schema.json')
    schema = next(item for item in schemas if item['$id'] == schema_url)
    Draft202012Validator(schema, registry=registry).validate(document)
    field = ('DataObjectNameConventions' if domain == 'dataobject'
             else 'SmartDataObjectNameConventions')
    assert field in document
    assert ('SmartDataObjectNameConventions' if domain == 'dataobject'
            else 'DataObjectNameConventions') not in document
    name, profile_body = next(iter(document[field]['NameConventions'].items()))
    assert name == f'{profile}-{language}-' + ('defscodegen' if domain == 'dataobject' else 'sdocodegen') + '-standard_1'
    roles = profile_body['StructureNaming']
    if domain == 'dataobject':
        assert roles['data_source_schema_url'] == '$schema'
        assert roles['schema_source_schema_url'] == '$id'
        assert roles['schema_source_schema_identifier'] == 'x-algites-schema-id'
        assert roles['data_source_schema_identifier'] == ''
        assert 'raw_getter' not in roles
    else:
        assert roles['standard_getter']
        assert roles['raw_getter']
        assert 'data_source_schema_url' not in roles
