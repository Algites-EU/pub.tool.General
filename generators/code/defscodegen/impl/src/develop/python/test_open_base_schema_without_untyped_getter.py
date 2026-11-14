"""Regression: reusable naming bases remain open without emitting untyped maps.

The base schema is extended via ``allOf`` by named profile-specific schema
contracts. Its openness is a validation rule, not a declaration of a new
semantic property. JSON Schema already defaults to allowing unknown keys;
explicit ``additionalProperties: true`` was incorrectly emitted as a Map
with an untyped Object/Any value.

@author linhart1
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from test_canonical_schema_frontend import frontend, SourceKind, Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter as Emitter,
)


TOOL = next(path for path in Path(__file__).resolve().parents
            if path.name == 'pub.tool.General')
LIB = TOOL.parent / 'pub.lib.General'


@pytest.mark.parametrize('kind,suffix', (
    ('jsondefs', 'jsondef.schema.json'),
    ('yamldefs', 'yamldef.schema.json'),
))
def test_open_base_naming_schema_does_not_invent_an_untyped_map(kind, suffix):
    """Unknown profile extension keys remain legal but are not generated fields."""
    path = (LIB / 'naming/convention/intf/src/product' / kind
            / 'eu/algites/lib/naming/convention'
            / f'common-naming-conventions_1.{suffix}')
    schema = json.loads(path.read_text(encoding='utf-8'))
    assert 'additionalProperties' not in schema, str(path)
    Draft202012Validator.check_schema(schema)
    # The common naming schema is reused through allOf; closing it with
    # additionalProperties:false would reject legitimate derived profile data.
    Draft202012Validator(schema).validate({
        'StandardConventionsFile': 'standard-conventions.yml',
        'FutureProfileSpecificProperty': {'value': 1},
    })

    kind_value = SourceKind.JSONDEFS if kind == 'jsondefs' else SourceKind.YAMLDEFS
    node = frontend().load_json_or_yaml(schema, str(path), kind_value)
    assert node.structure.kind == Kind.ELEMENTLIST
    assert 'additionalProperties' not in {field.name for field in node.structure.children}
    assert 'IdentifierConventions' in {field.name for field in node.structure.children}


def test_explicit_untyped_additional_properties_warn_and_omit_getter():
    """Explicit untyped values are omitted with a source-located warning.

    Ordinary declared properties must still be present, and the emitted
    interface must never expose an Object/Any getter for extra values.
    """
    source = {'type': 'object', 'properties': {'Name': {'type': 'string'}},
              'additionalProperties': True}
    with pytest.warns(UserWarning, match='DEFS-UNTYPED-ADDITIONAL-PROPERTIES') as warnings:
        root = frontend().load_json_or_yaml(source, 'bad-naming.json', SourceKind.JSONDEFS)
    assert 'bad-naming.json' in str(warnings[0].message)
    assert '/additionalProperties' in str(warnings[0].message)
    assert 'additionalProperties' not in {item.name for item in root.structure.children}
    assert 'Name' in {item.name for item in root.structure.children}
