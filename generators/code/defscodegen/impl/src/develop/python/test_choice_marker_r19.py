"""Regression tests for the explicit-property, boolean Algites Choice metadata."""
from __future__ import annotations

import pytest

from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.impl.standard.aic_json_schema_reader import AIcJsonSchemaReader


def _choice() -> dict:
    """Return a portable JSON Schema 2020-12 choice with two scalar alternatives."""
    return {
        'type': 'object',
        'x-algites-defscodegen-choice': True,
        'properties': {'StringValue': {'type': 'string'},
                       'BooleanValue': {'type': 'boolean'}},
        'minProperties': 1,
        'maxProperties': 1,
        'additionalProperties': False,
    }


def test_explicit_choice_controls_structural_type() -> None:
    """Never infer a generated choice merely from standard JSON constraints."""
    reader = AIcJsonSchemaReader()
    declared = _choice()
    reader._validate_choice_placements(declared)
    data_type = reader._recursive_type(declared, None)
    assert data_type.kind is AInDataTypeKind.ONE_OF
    assert [alternative.kind for alternative in data_type.alternatives] == [
        AInDataTypeKind.OBJECT, AInDataTypeKind.OBJECT]
    assert [alternative.properties[0].source_name for alternative in data_type.alternatives] == [
        'StringValue', 'BooleanValue']
    assert [alternative.properties[0].data_type.kind for alternative in data_type.alternatives] == [
        AInDataTypeKind.STRING, AInDataTypeKind.BOOLEAN]
    declared.pop('x-algites-defscodegen-choice')
    assert reader._recursive_type(declared, None).kind is AInDataTypeKind.OBJECT


@pytest.mark.parametrize('location', [
    'properties', '$defs', 'items', 'prefixItems', 'additionalProperties',
    'patternProperties', 'additionalItems'])
def test_choice_in_supported_structure_locations(location: str) -> None:
    """Choice metadata belongs to structural schema nodes, including tuple slots."""
    reader = AIcJsonSchemaReader()
    value = [_choice()] if location == 'prefixItems' else {'Variant': _choice()} \
        if location in {'properties', '$defs', 'patternProperties'} else _choice()
    reader._validate_choice_placements({location: value})


@pytest.mark.parametrize('location', [
    'oneOf', 'anyOf', 'allOf', 'not', 'if', 'then', 'else',
    'contains', 'dependentSchemas', 'propertyNames'])
def test_choice_rejected_inside_validation_only_location(location: str) -> None:
    """A validation-only branch must not introduce a new generated type."""
    reader = AIcJsonSchemaReader()
    value = [_choice()] if location in ('oneOf', 'anyOf', 'allOf') else \
        {'field': _choice()} if location == 'dependentSchemas' else _choice()
    with pytest.raises(ValueError, match='validation-only subschema'):
        reader._validate_choice_placements({location: value})


@pytest.mark.parametrize('mutation', [
    ('maxProperties', 2), ('minProperties', 0),
    ('additionalProperties', True), ('x-algites-defscodegen-choice', False),
    ('properties', {'OnlyOne': {'type': 'string'}}),
    ('patternProperties', {'.*': {'type': 'string'}}),
    ('required', ['StringValue']),
])
def test_choice_rejects_invalid_standard_interoperability_constraints(mutation) -> None:
    """A marker is not allowed to contradict portable exclusive-choice validation."""
    choice = _choice()
    key, value = mutation
    choice[key] = value
    with pytest.raises(ValueError, match='Invalid x-algites-defscodegen-choice'):
        AIcJsonSchemaReader()._validate_choice_placements(choice)
