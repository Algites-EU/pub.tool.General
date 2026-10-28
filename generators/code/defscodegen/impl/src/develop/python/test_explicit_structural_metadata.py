"""Regression tests for the separation of source structure from validation assertions."""

from __future__ import annotations

import json
from pathlib import Path

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_json_schema_reader import AIcJsonSchemaReader
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


def _request(path: Path) -> AIcdDefinitionLoadRequest:
    return AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS,
                                    AIcAlgitesNamingProfiles.python_profile())


def test_validation_allof_does_not_declare_fields(tmp_path: Path) -> None:
    source = tmp_path / 'child_1.jsondef.schema.json'
    schema = {'type': 'object', 'properties': {'own': {'type': 'string'}},
              'allOf': [{'properties': {'notOwned': {'type': 'integer'}},
                         'required': ['notOwned']}]}
    source.write_text(json.dumps(schema))
    result = AIcJsonSchemaReader().read(schema, _request(source), AInDefinitionSourceKind.JSONDEFS,
                                       '', '', '')
    assert [field.source_name for field in result.data_type.properties] == ['own']
    units = []
    AIcSchemaContractBindingsGenerator()._collect(schema, '', 'child', 'child.json', schema, {}, units)
    assert not any('allOf' in unit.pointer for unit in units)


def test_explicit_parent_is_independent_from_validation_allof(tmp_path: Path) -> None:
    source = tmp_path / 'child_1.jsondef.schema.json'
    schema = {'type': 'object', 'properties': {'own': {'type': 'string'}},
              '$defs': {'Parent': {'type': 'object', 'properties': {'parent': {'type': 'string'}}}},
              'x-algites-defscodegen-extends': ['#/$defs/Parent'],
              'allOf': [{'properties': {'validationOnly': {'type': 'integer'}}}]}
    source.write_text(json.dumps(schema))
    repository = tmp_path.resolve()
    units = []
    bindings = AIcSchemaContractBindingsGenerator()
    bindings._collect(schema, '', 'child', source.name, schema, {}, units)
    index = {(unit.schema, unit.pointer): unit for unit in units}
    parents = bindings._parent_units(index[(source.name, '')], index, repository)
    assert len(parents) == 1
    assert parents[0].pointer == '/$defs/Parent'
    assert all('allOf' not in unit.pointer for unit in units)
    schema.pop('x-algites-defscodegen-extends')
    units.clear()
    bindings._collect(schema, '', 'child', source.name, schema, {}, units)
    index = {(unit.schema, unit.pointer): unit for unit in units}
    assert bindings._parent_units(index[(source.name, '')], index, repository) == ()


def test_choice_comes_only_from_metadata_and_uses_nominal_variants(tmp_path: Path) -> None:
    source = tmp_path / 'variants_1.jsondef.schema.json'
    schema = {'type': 'object',
              '$defs': {
                  'Text': {'type': 'object', 'properties': {'text': {'type': 'string'}}},
                  'Count': {'type': 'object', 'properties': {'count': {'type': 'integer'}}},
                  'Payload': {'x-algites-defscodegen-choice': {
                      'alternatives': ['#/$defs/Text', '#/$defs/Count']},
                      'oneOf': [{'$ref': '#/$defs/Text'}, {'$ref': '#/$defs/Count'}]}},
              'properties': {'payload': {'$ref': '#/$defs/Payload'}}}
    source.write_text(json.dumps(schema))
    reader = AIcJsonSchemaReader()
    loaded = reader.read(schema, _request(source), AInDefinitionSourceKind.JSONDEFS, '', '', '')
    prop = loaded.data_type.properties[0]
    assert prop.data_type.kind is AInDataTypeKind.REFERENCE
    assert prop.data_type.reference.target_data_type.kind is AInDataTypeKind.ONE_OF
    schema['$defs']['Payload'].pop('x-algites-defscodegen-choice')
    source.write_text(json.dumps(schema))
    assert reader._recursive_type(schema['$defs']['Payload'], _request(source)).kind is AInDataTypeKind.ANY


def test_supported_homogeneous_arrays_are_draft_independent(tmp_path: Path) -> None:
    reader = AIcJsonSchemaReader()
    source = tmp_path / 'values_1.jsondef.schema.json'
    for draft in ('https://json-schema.org/draft-06/schema#',
                  'http://json-schema.org/draft-07/schema#',
                  'https://json-schema.org/draft/2019-09/schema',
                  'https://json-schema.org/draft/2020-12/schema'):
        schema = {'$schema': draft, 'type': 'array', 'items': {'type': 'string'}}
        source.write_text(json.dumps(schema))
        result = reader.read(schema, _request(source), AInDefinitionSourceKind.JSONDEFS,
                             '', '', '')
        assert result.data_type.kind is AInDataTypeKind.ARRAY
        assert result.data_type.element_type.kind is AInDataTypeKind.STRING


def test_positional_arrays_cannot_silently_lose_types(tmp_path: Path) -> None:
    import pytest
    reader = AIcJsonSchemaReader()
    source = tmp_path / 'values_1.jsondef.schema.json'
    for value in ({'$schema': 'https://json-schema.org/draft/2020-12/schema',
                   'type': 'array', 'prefixItems': [{'type': 'integer'}, {'type': 'string'}]},
                  {'$schema': 'http://json-schema.org/draft-07/schema#',
                   'type': 'array', 'items': [{'type': 'integer'}, {'type': 'string'}]}):
        source.write_text(json.dumps(value))
        with pytest.raises(ValueError, match='POSITIONAL_VALUE'):
            reader.read(value, _request(source), AInDefinitionSourceKind.JSONDEFS, '', '', '')
