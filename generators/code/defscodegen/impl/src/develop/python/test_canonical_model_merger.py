"""Regression coverage of canonical source-representation merge semantics."""
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
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIigSourceInputKind_1 as Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import AIcDefsCodegenCanonicalSchemaFrontend
from eu.algites.tool.codegen.defs.impl.standard.canonical_model_merger import AIcDefsCodegenCanonicalModelMerger
from eu.algites.tool.codegen.defs.impl.standard.canonical_model_linker import AIcDefsCodegenCanonicalModelLinker


def frontend():
    path = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/tool/codegen'
    c = yaml.safe_load((path / 'algites-java-common-codegen-conventions.yml').read_text())
    d = yaml.safe_load((path / 'algites-java-defs-codegen-conventions.yml').read_text())
    return AIcDefsCodegenCanonicalSchemaFrontend(resolve_codegen_naming_profiles(
        c, 'algites-java-codegen-common_1', d, 'algites-java-defscodegen-standard_1'))


def test_identical_json_and_yaml_definitions_merge_every_nested_binding():
    schema = {'x-algites-schema-id': 'customer', 'title': 'Customer', 'type': 'object',
              'properties': {'addresses': {'type': 'array', 'items': {
                  'type': 'object', 'properties': {'zip': {'type': 'string'}}}},
                'choice': {'oneOf': [{'type': 'string'}, {'type': 'integer'}]}},
              'additionalProperties': {'type': 'integer'}}
    a = frontend().load_json_or_yaml(schema, 'a.json', Kind.JSONDEFS)
    b = frontend().load_json_or_yaml(schema, 'b.yaml', Kind.YAMLDEFS)
    merged, = AIcDefsCodegenCanonicalModelMerger.merge((a, b))
    assert merged.identity == 'customer'
    assert list(merged.source_bindings) == [Kind.JSONDEFS, Kind.YAMLDEFS]
    fields = merged.structure.children
    assert set(fields[0].source_bindings) == {Kind.JSONDEFS, Kind.YAMLDEFS}
    assert set(fields[0].structure.item.source_bindings) == {Kind.JSONDEFS, Kind.YAMLDEFS}
    assert set(fields[0].structure.item.structure.children[0].source_bindings) == {Kind.JSONDEFS, Kind.YAMLDEFS}
    assert set(fields[2].source_bindings) == {Kind.JSONDEFS, Kind.YAMLDEFS}
    assert set(fields[1].structure.source_bindings) == {Kind.JSONDEFS, Kind.YAMLDEFS}
    assert len(AIcDefsCodegenCanonicalModelLinker.link((merged,))) == 1


def test_same_technology_multiple_bindings_are_appended_in_input_order():
    schema = {'x-algites-schema-id': 'customer', 'title': 'Customer', 'type': 'object',
              'properties': {'id': {'type': 'string'}}}
    a = frontend().load_json_or_yaml(schema, 'a.json', Kind.JSONDEFS)
    b = frontend().load_json_or_yaml(schema, 'b.json', Kind.JSONDEFS)
    merged, = AIcDefsCodegenCanonicalModelMerger.merge((a, b))
    assert [b.source_resource for b in merged.source_bindings[Kind.JSONDEFS]] == ['a.json', 'b.json']
    assert [b.source_resource for b in merged.structure.children[0].source_bindings[Kind.JSONDEFS]] == ['a.json', 'b.json']


def test_conflicting_scalar_types_fail_with_property_path():
    a = frontend().load_json_or_yaml({'$id': 'urn:a', 'title': 'A', 'type': 'object',
        'properties': {'v': {'type': 'string'}}}, 'a.json', Kind.JSONDEFS)
    b = frontend().load_json_or_yaml({'$id': 'urn:a', 'title': 'A', 'type': 'object',
        'properties': {'v': {'type': 'integer'}}}, 'b.yaml', Kind.YAMLDEFS)
    with pytest.raises(ValueError, match=r'urn:a/structure/children/0/v.*scalar'):
        AIcDefsCodegenCanonicalModelMerger.merge((a, b))


def test_conflicting_child_counts_fail_closed():
    a = frontend().load_json_or_yaml({'$id': 'urn:a', 'title': 'A', 'type': 'object',
        'properties': {'v': {'type': 'string'}}}, 'a.json', Kind.JSONDEFS)
    b = frontend().load_json_or_yaml({'$id': 'urn:a', 'title': 'A', 'type': 'object',
        'properties': {'v': {'type': 'string'}, 'other': {'type': 'string'}}}, 'b.yaml', Kind.YAMLDEFS)
    with pytest.raises(ValueError, match='child count differs'):
        AIcDefsCodegenCanonicalModelMerger.merge((a, b))


def test_named_defs_merge_across_json_and_yaml_using_logical_id():
    schema = {'x-algites-schema-id': 'urn:shared', '$defs': {
        'Node': {'type': 'object', 'properties': {'parent': {'$ref': '#/$defs/Node'}}}}}
    java = frontend().load_json_or_yaml_types(schema, 'models.json', Kind.JSONDEFS)
    yaml_defs = frontend().load_json_or_yaml_types(schema, 'models.yaml', Kind.YAMLDEFS)
    assert java[0].identity == yaml_defs[0].identity == 'urn:shared#/$defs/Node'
    merged, = AIcDefsCodegenCanonicalModelMerger.merge(java + yaml_defs)
    assert set(merged.source_bindings) == {Kind.JSONDEFS, Kind.YAMLDEFS}
    linked, = AIcDefsCodegenCanonicalModelLinker.link((merged,))
    assert linked.structure.children[0].structure.target_identity == 'urn:shared#/$defs/Node'
    assert set(linked.structure.children[0].structure.source_bindings) == {Kind.JSONDEFS, Kind.YAMLDEFS}
