"""Python counterparts of the independent Java Defs CLI regression tests."""
from pathlib import Path
import sys
import pytest

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
LIB = TOOL.parent / 'pub.lib.General'
for source in (
    *sorted(LIB.rglob('src/product/python')),
    TOOL / 'generators/code/common/src/product/python',
    TOOL / 'generators/code/defscodegen/intf/src/product/python',
    TOOL / 'generators/code/defscodegen/intf/src/product/python.extgen',
    TOOL / 'generators/code/defscodegen/impl/src/product/python',
    TOOL / 'generators/code/defscodegen/impl/src/product/python.extgen',
    TOOL / 'generators/code/defscodegen/cli/src/product/python',
    TOOL / 'generators/code/defscodegen/intf/src/product/config',
    TOOL / 'generators/code/profile/algites/src/product/config',
):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import (
    _coalesce_equivalent_enum_sources, _existing_contracts)
from eu.algites.tool.codegen.defs.impl.cli._standard_cli import _effective


def test_unknown_native_cli_argument_is_rejected():
    """Unknown command options are errors in both languages."""
    with pytest.raises((ValueError, KeyError), match='unexpected'):
        _effective(['--defs-codegen-naming-convention:python=algites-python-defscodegen-standard_1',
                    '--unexpected=true'])


def test_python_enum_coalescing_is_order_independent_and_rejects_value_changes():
    """Equivalent JSON/XML enums share values, while conflicting ones fail."""
    json_source = '''from enum import Enum
class Status(str, Enum):
    """JSON value.

    Generated from canonical definition sample#/$defs/Status/1. Source: schemas/jsondefs/example_1.jsondef.schema.json#/$defs/Status. Do not edit manually.
    """
    A = 'a'
    B = 'b'
'''
    xml_source = (json_source.replace('JSON value.', 'XML value.')
                  .replace('sample#/$defs/Status', 'sample#/Status')
                  .replace('schemas/jsondefs/example_1.jsondef.schema.json#/$defs/Status',
                           'schemas/xmldefs/example_1.xsd#/Status'))
    merged = _coalesce_equivalent_enum_sources(json_source, xml_source, 'status.py')
    assert merged == _coalesce_equivalent_enum_sources(xml_source, json_source, 'status.py')
    assert 'Equivalent enum schema:' in merged
    assert _coalesce_equivalent_enum_sources(merged, xml_source, 'status.py') == merged
    with pytest.raises(ValueError, match='status.py'):
        _coalesce_equivalent_enum_sources(json_source,
            xml_source.replace("B = 'b'", "B = 'c'"), 'status.py')


def test_unified_external_contract_index_prefers_derived_read_only_java_python(tmp_path):
    """Derived annotated DO overrides base; writable SDO does not override it."""
    identity = 'https://example.org/schema/shared_1.jsondef.schema.json'
    java = tmp_path / 'owner/src/product/java.gen/demo'
    python = tmp_path / 'owner/src/product/python.gen/demo'
    java.mkdir(parents=True)
    python.mkdir(parents=True)
    for name, base in (('Base', ''), ('Child', ' extends Base')):
        (java / (name + '.java')).write_text('package demo;\n'
            + f'@AIaDataObjectJsonSchema(schemaUrl = "{identity}", schemaId = "shared")\n'
            + f'public interface {name}{base} {{}}\n', encoding='utf-8')
        (python / (name.lower() + '.py')).write_text(
            ('from demo.base import Base\n' if name == 'Child' else '')
            + f'class {name}' + ('(Base)' if name == 'Child' else '') + ':\n'
            + f'    __json_schema__ = AIaDataObjectJsonSchema(schema_url="{identity}", schema_id="shared")\n',
            encoding='utf-8')
    (java / 'Mutable.java').write_text('package demo;\n'
        + f'@AIaDataObjectJsonSchema(schemaUrl = "{identity}", schemaId = "shared")\n'
        + 'public interface Mutable extends Child { void setValue(String value); }\n',encoding='utf-8')
    (python / 'mutable.py').write_text('from demo.child import Child\n'
        + 'class Mutable(Child):\n'
        + f'    __json_schema__ = AIaDataObjectJsonSchema(schema_url="{identity}", schema_id="shared")\n'
        + '    def setValue(self, value): ...\n',encoding='utf-8')
    selected = _existing_contracts((tmp_path,), frozenset({identity}))
    assert selected[identity]['java'] == 'demo.Child'
    assert selected[identity]['python_module'] == 'demo.child'
    assert selected[identity]['python_type'] == 'Child'
