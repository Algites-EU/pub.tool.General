"""Check JSONDEFS/YAMLDEFS key metadata against the actual XSD identity declarations."""
from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == 'pub.tool.General').parent
XS = '{http://www.w3.org/2001/XMLSchema}'
SOURCES = (
    ('pub.lib.General/naming/convention/intf/src/product', 'common-naming-conventions_1'),
    ('pub.lib.General/naming/convention/sourcecode/src/product', 'source-structure-name-conventions_1'),
    ('pub.lib.General/naming/convention/sourcecode/src/product', 'dataobject-naming-conventions_1'),
    ('pub.lib.General/naming/convention/sourcecode/src/product', 'smartdataobject-naming-conventions_1'),
    ('pub.tool.General/generators/code/common/src/product', 'data-object-naming-conventions_1'),
    ('pub.tool.General/generators/code/common/src/product', 'codegen-common-naming-conventions_1'),
    ('pub.tool.General/generators/code/defscodegen/intf/src/product', 'defscodegen-naming-conventions_1'),
    ('pub.tool.General/generators/code/sdocodegen/intf/src/product', 'sdocodegen-naming-conventions_1'),
)


def keyed_maps(source):
    """Find all explicitly keyed JSON/YAML object maps without assuming schema depth."""
    found = []
    def walk(node, pointer):
        if isinstance(node, dict):
            marker = node.get('x-algites-defscodegen-key')
            if marker is not None:
                assert node.get('type') == 'object', pointer
                assert isinstance(node.get('additionalProperties'), dict), pointer
                found.append((pointer, marker))
            for name, value in node.items():
                if name != 'x-algites-defscodegen-key':
                    walk(value, pointer + '/' + name)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, pointer + '/' + str(index))
    walk(source, '')
    return found


@pytest.mark.parametrize('base,name', SOURCES)
def test_paired_schemas_have_identical_keys_and_xml_field_names(base, name):
    """Every explicit index ID and field name is copied from one xs:key, not invented."""
    folder = ROOT / base
    xsd, = tuple(folder.glob(f'xmldefs/**/{name}.xsd'))
    xml = ET.parse(xsd).getroot()
    constraints = {}
    for parent in xml.iter(XS + 'element'):
        for key in parent.findall(XS + 'key'):
            fields = key.findall(XS + 'field')
            selector = key.find(XS + 'selector')
            if selector is not None and len(fields) == 1:
                constraints.setdefault(key.get('name'), set()).add(
                    fields[0].get('xpath').removeprefix('@'))
    known = None
    for kind in ('jsondefs', 'yamldefs'):
        paths = tuple(folder.glob(f'{kind}/**/{name}.' +
                    ('jsondef' if kind == 'jsondefs' else 'yamldef') + '.schema.json'))
        assert len(paths) == 1
        values = keyed_maps(json.loads(paths[0].read_text()))
        assert values, (kind, name)
        for pointer, marker in values:
            assert marker['field-name'] in constraints.get(marker['id'], set()), (name, pointer, marker)
        as_dict = {pointer: marker for pointer, marker in values}
        if known is None:
            known = as_dict
        else:
            assert as_dict == known


def test_typed_property_names_are_enum_schema_refs():
    """The explicit key identifies a field; propertyNames still provides enum typing."""
    folder = ROOT / 'pub.tool.General/generators/code/defscodegen/intf/src/product/jsondefs'
    schema, = tuple(folder.glob('**/defscodegen-naming-conventions_1.jsondef.schema.json'))
    root = json.loads(schema.read_text())
    mapping = (root['properties']['DefsCodegenNameConventions']['properties']
               ['NameConventions']['additionalProperties']['properties']['StructureNaming'])
    assert mapping['x-algites-defscodegen-key'] == {
        'id': 'UniqueStructureRoles', 'field-name': 'kind'}
    assert mapping['propertyNames']['$ref'].endswith(
        '/defscodegen-structure-kind_1.jsondef.schema.json')
    enum, = tuple(folder.glob('**/defscodegen-structure-kind_1.jsondef.schema.json'))
    assert json.loads(enum.read_text())['enum']
