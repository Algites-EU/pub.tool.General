"""Regression tests for the immutable generated CHOICE and live canonical SDO bridge."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass
import json
from pathlib import Path

import pytest

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdType_1, AIcgdScalar_1, AIngScalarKind_1, AIngTypeOrigin_1,
    AIngSourceInputKind_1, AIcgdSourceBinding_1,
    _bindings_object, _bindings_mapping, _schema_choice_from_field,
)
from test_canonical_schema_frontend import frontend
from eu.algites.tool.codegen.defs.impl.standard.canonical_contract_payload import _generated_data_tree


TOOL = Path(__file__).resolve().parents[7]
LIB = TOOL.parent / 'pub.lib.General'
BOOTSTRAP_READ = TOOL / 'generators/code/defscodegen/intf/src/product'
BOOTSTRAP_SDO = TOOL / 'generators/code/defscodegen/impl/src/product'


def test_bootstrap_choice_variants_are_generated_immutable_non_sdo():
    """A CHOICE has sealed records/frozen variants, never a mutable SDO class."""
    for name, getter in [('Type', 'getContent'), ('Element', 'getStructure'),
                         ('ElementList', 'getChildrenList')]:
        contract = _schema_choice_from_field(name, getter)
        assert contract.__module__.startswith('eu.algites.tool.codegen.defs.bootstrap.model.')
        assert contract.__xml_choice_variant_imports__
        for entry in contract.__xml_choice_variant_imports__:
            module, _ = entry.split(':', 1)
            assert module.startswith('eu.algites.tool.codegen.defs.bootstrap.model.'), entry
    for stem in ('TypeContent', 'Structure', 'ElementListChild'):
        for sub in ('java.extgen', 'python.extgen'):
            sdo_path = BOOTSTRAP_SDO / sub
            assert not list(sdo_path.rglob(f'AIigd{stem}_1.java'))
            assert not list(sdo_path.rglob(f'AIcgd{stem}_1.java'))
            assert not list(sdo_path.rglob('aiigd_' + ''.join('_' + c.lower() if c.isupper() else c for c in stem).lstrip('_') + '_1.py'))
    variant = AIcgdType_1('urn:here', 'Here', AIngTypeOrigin_1.DECLARED,
                             target_identity='urn:there').getContent()
    assert is_dataclass(variant)
    assert variant.__class__.__module__.startswith('eu.algites.tool.codegen.defs.bootstrap.model.')
    with pytest.raises(FrozenInstanceError):
        variant.field1 = 'modified'
    java = BOOTSTRAP_READ / 'java.extgen/eu/algites/tool/codegen/defs/bootstrap/model/AIigTypeContent_1.java'
    assert 'interface AIigTypeContent_1' in java.read_text(encoding='utf-8')
    # First-stage seed may use a non-sealed ABI interface; the fresh output
    # must be sealed because the set of alternatives is closed.
    generated = (BOOTSTRAP_READ / 'java.gen/eu/algites/tool/codegen/defs/model/AIigTypeContent_1.java')
    if generated.exists():
        assert 'sealed interface AIigTypeContent_1' in generated.read_text(encoding='utf-8')
    records = list(java.parent.glob('AIigTypeContentVariant*.java'))
    assert len(records) == 2
    assert all('public record ' in path.read_text(encoding='utf-8') for path in records)


def test_generated_type_content_preserves_both_variants_and_wire_names():
    """An alternative is selected once; serialization uses its declared field."""
    scalar = AIcgdScalar_1(AIngScalarKind_1.STRING)
    structured = AIcgdType_1('urn:test', 'Test', AIngTypeOrigin_1.DECLARED,
                               structure=scalar)
    referenced = AIcgdType_1('urn:ref', 'Ref', AIngTypeOrigin_1.DECLARED,
                               target_identity='urn:test')
    assert structured.structure is scalar
    assert _generated_data_tree(structured)['content']['structure']['Scalar']['scalar_kind'] == 'STRING'
    assert referenced.target_identity == 'urn:test'
    assert _generated_data_tree(referenced)['content'] == {'target_identity': 'urn:test'}


def test_source_bindings_assigns_full_required_list_in_one_operation():
    """Do not insert an invalid transient empty BindingList into generated SDO."""
    source = AIcgdSourceBinding_1('a.json', '#/properties/v', 'properties')
    bindings = _bindings_object({AIngSourceInputKind_1.JSONDEFS: [source]})
    assert _bindings_mapping(bindings)[AIngSourceInputKind_1.JSONDEFS] == (source,)


def test_actual_naming_json_can_create_generated_key_definitions():
    """Guard the exact first-stage bootstrap crash in canonical Element.__init__."""
    source = LIB / ('naming/convention/intf/src/product/jsondefs/eu/algites/lib/'
                    'naming/convention/common-naming-conventions_1.jsondef.schema.json')
    from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
        AIngSourceInputKind_1 as SourceKind,
    )
    roots = frontend().load_json_or_yaml_types(
        json.loads(source.read_text(encoding='utf-8')), str(source), SourceKind.JSONDEFS)
    assert any(node.name == 'IdentifierConventions' for node in roots)
