"""Regression tests for the source-aware, recursion-safe canonical linker."""
import json
import sys
from pathlib import Path

import pytest
import yaml

TOOL = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
for relative in ('generators/code/common/src/product/python',
                 'generators/code/defscodegen/intf/src/product/python',
                 'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(TOOL / relative))

from eu.algites.tool.codegen.common.naming_profiles import resolve_codegen_naming_profiles
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgd_jElement_1, AIcgd_jElementList_1, AIcgd_jScalar_1,
    AIcgd_jType_1, AIigComposition_1, AIigScalarKind_1,
    AIigTypeOrigin_1, AIigSourceInputKind_1 as SourceKind,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
    AIcDefsCodegenCanonicalSchemaFrontend,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_model_linker import (
    AIcDefsCodegenCanonicalModelLinker,
)

SCHEMA = json.loads((TOOL / 'generators/code/defscodegen/intf/src/product/jsondefs'
                     '/eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json').read_text())


def frontend():
    config = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/tool/codegen'
    common = yaml.safe_load((config / 'algites-java-common-codegen-conventions.yml').read_text())
    defs = yaml.safe_load((config / 'algites-java-defs-codegen-conventions.yml').read_text())
    naming = resolve_codegen_naming_profiles(common, 'algites-java-codegen-common_1',
                                              defs, 'algites-java-defscodegen-standard_1')
    return AIcDefsCodegenCanonicalSchemaFrontend(naming)


@pytest.mark.parametrize('kind', [SourceKind.JSONDEFS, SourceKind.YAMLDEFS])
def test_self_recursive_local_pointer_is_symbolic_and_validated(kind):
    source = {'$id': 'urn:tree', 'title': 'Tree', 'type': 'object', 'properties': {
        'next': {'$ref': '#'}}}
    linked, = AIcDefsCodegenCanonicalModelLinker.link(
        frontend().load_json_or_yaml_types(source, 'tree.json', kind), schema=SCHEMA)
    target = linked.structure.children[0].structure
    assert target.identity == 'urn:tree'
    assert target.target_identity == 'urn:tree'
    assert target.structure is None
    assert target.source_bindings[kind][0].source_pointer == '#/properties/next'


def test_mutually_recursive_definitions_and_local_collisions():
    src = {'$defs': {
        'Alpha': {'type': 'object', 'properties': {'beta': {'$ref': '#/$defs/Beta'}}},
        'Beta': {'type': 'object', 'properties': {'alpha': {'$ref': '#/$defs/Alpha'}}},
    }}
    roots = frontend().load_json_or_yaml_types(src, 'a.json', SourceKind.JSONDEFS)
    assert len(roots) == 2
    linked = AIcDefsCodegenCanonicalModelLinker.link(roots, schema=SCHEMA)
    assert linked[0].structure.children[0].structure.target_identity == 'a.json#/$defs/Beta'
    assert linked[1].structure.children[0].structure.target_identity == 'a.json#/$defs/Alpha'
    # An unrelated resource with equally named declarations must not override local pointers.
    more = frontend().load_json_or_yaml_types(src, 'b.json', SourceKind.YAMLDEFS)
    both = AIcDefsCodegenCanonicalModelLinker.link(roots + more, schema=SCHEMA)
    assert both[2].structure.children[0].structure.target_identity == 'b.json#/$defs/Beta'


def test_xml_named_type_resolves_locally_despite_same_name_in_other_resource():
    source = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Node"><xs:sequence>
        <xs:element name="child" type="Node" maxOccurs="unbounded"/>
      </xs:sequence></xs:complexType></xs:schema>'''
    a = frontend().load_xsd(source, 'a.xsd')
    b = frontend().load_xsd(source, 'b.xsd')
    # A concrete duplicate name alone is ambiguous; local XML reference must be qualified.
    # XML QName identity requires the document's namespace; distinct XSDs with
    # an identical type identity are rejected rather than silently overwritten.
    with pytest.raises(ValueError, match='Duplicate canonical TYPE declaration'):
        AIcDefsCodegenCanonicalModelLinker.link(a + b)
    linked, = AIcDefsCodegenCanonicalModelLinker.link(a, schema=SCHEMA)
    assert linked.structure.children[0].item.target_identity == 'Node'


def test_validation_runs_before_normalization():
    original = AIcgd_jType_1('root', 'root', AIigTypeOrigin_1.DECLARED,
        structure=AIcgd_jElementList_1(AIigComposition_1.SEQUENCE, (
            AIcgd_jElementList_1(AIigComposition_1.SEQUENCE, (
                AIcgd_jElement_1('value', AIcgd_jScalar_1(AIigScalarKind_1.STRING)),
            )),
        )))
    class CapturingSchema(dict):
        pass
    # The callback in Python uses the published schema; nested sequence is structurally
    # valid before normalization, and the normalized result has only one direct child.
    linked, = AIcDefsCodegenCanonicalModelLinker.link((original,), schema=SCHEMA)
    assert len(linked.structure.children) == 1
    assert isinstance(linked.structure.children[0], AIcgd_jElement_1)


def test_unresolved_reference_identifies_exact_source_location():
    roots = frontend().load_json_or_yaml_types({'$defs': {
        'A': {'type': 'object', 'properties': {'b': {'$ref': '#/$defs/Missing'}}}
    }}, 'errors.json', SourceKind.JSONDEFS)
    with pytest.raises(ValueError, match=r'errors.json#/\$defs/A/properties/b.*unresolved reference'):
        AIcDefsCodegenCanonicalModelLinker.link(roots, schema=SCHEMA)


def test_inheritance_reference_resolution_and_cycle_rejection():
    types = frontend().load_json_or_yaml_types({'type': 'object', '$id': 'urn:child',
        'allOf': [{'$ref': '#/$defs/Parent'}], '$defs': {
            'Parent': {'type': 'object', 'properties': {'id': {'type': 'integer'}}}
        }}, 'derived.json', SourceKind.JSONDEFS)
    linked = AIcDefsCodegenCanonicalModelLinker.link(types, schema=SCHEMA)
    assert linked[0].inherited_from_types == ('urn:child#/$defs/Parent',)
    a = AIcgd_jType_1('A', 'A', AIigTypeOrigin_1.DECLARED,
            inherited_from_types=('B',), structure=AIcgd_jScalar_1(AIigScalarKind_1.ANY))
    b = AIcgd_jType_1('B', 'B', AIigTypeOrigin_1.DECLARED,
            inherited_from_types=('A',), structure=AIcgd_jScalar_1(AIigScalarKind_1.ANY))
    with pytest.raises(ValueError, match='Cyclic TYPE inheritance'):
        AIcDefsCodegenCanonicalModelLinker.link((a, b))
