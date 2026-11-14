"""Self-referencing named $defs contracts remain nominal in the recursive model."""
import json

import pytest

from explicit_legacy_naming import catalog, configured_load
from eu.algites.tool.codegen.defs.old.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.old.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.old.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.old.impl.standard.aic_json_schema_reader import AIcJsonSchemaReader


def _read(tmp_path, schema):
    path = tmp_path / 'recursive-finalization_1.jsondef.schema.json'
    path.write_text(json.dumps(schema), encoding='utf-8')
    return AIcJsonSchemaReader().read(schema,
        configured_load(path, AInDefinitionSourceKind.JSONDEFS, catalog('python')),
        AInDefinitionSourceKind.JSONDEFS, 'x-jsondefs-id', 'x-jsondefs-version', 'x-jsondefs-name')


def test_recursive_named_object_keeps_nominal_identity(tmp_path):
    schema = {'type': 'object', 'properties': {'Action': {'$ref': '#/$defs/FinalizationAction'}},
        '$defs': {'FinalizationAction': {'type': 'object', 'properties': {
            'Id': {'type': 'string'},
            'FinalizationActions': {'type': 'array',
                'items': {'$ref': '#/$defs/FinalizationAction'}}}}}}
    reference = _read(tmp_path, schema).data_type.properties[0].data_type.reference
    assert reference.logical_name == 'finalization-action'
    assert reference.target_data_type.kind is AInDataTypeKind.OBJECT


def test_recursive_named_choice_preserves_alternatives_and_back_edge(tmp_path):
    schema = {'type': 'object', 'properties': {'Value': {'$ref': '#/$defs/Node'}},
        '$defs': {'Node': {'type': 'object', 'x-algites-defscodegen-choice': True,
             'properties': {'Text': {'type': 'string'},
                            'Linked': {'type': 'object', 'properties': {'Next': {'$ref': '#/$defs/Node'}}}},
             'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False}}}
    union = _read(tmp_path, schema).data_type.properties[0].data_type.reference.target_data_type
    assert union.kind is AInDataTypeKind.ONE_OF
    assert union.alternatives[0].properties[0].data_type.kind is AInDataTypeKind.STRING
    back_edge = union.alternatives[1].properties[0].data_type.properties[0].data_type.reference
    assert back_edge is not None
    assert back_edge.target_data_type is None


def test_circular_inline_alias_is_reported(tmp_path):
    schema = {'type': 'object', 'properties': {'Value': {'$ref': '#/$defs/Alias'}},
        '$defs': {'Alias': {'$ref': '#/$defs/Alias'}}}
    with pytest.raises(ValueError, match='Circular inline schema alias'):
        _read(tmp_path, schema)
