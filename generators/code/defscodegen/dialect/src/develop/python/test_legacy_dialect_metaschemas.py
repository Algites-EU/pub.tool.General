"""Regression tests for historical JSON Schema dialect resources.

The JSON Schema Draft-03/04/06/07 metaschemas are self-recursive. The Algites
legacy dialects retain the original recursion and add separate, typed Algites
keyword references, so nested use is validated without requiring $vocabulary.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft3Validator, Draft4Validator, Draft6Validator, Draft7Validator
from referencing import Registry, Resource


ROOT = (Path(__file__).resolve().parents[2] / 'product' / 'jsonmetadefs' /
        'eu' / 'algites' / 'tool' / 'codegen' / 'defs' / 'jsonmetadef')
DRAFTS = {
    'draft-03': Draft3Validator,
    'draft-04': Draft4Validator,
    'draft-06': Draft6Validator,
    'draft-07': Draft7Validator,
}
KEYS = ('x-algites-defscodegen-extends', 'x-algites-defscodegen-choice')
COMMON_KEYS = ('x-algites-schema-id', 'x-algites-schema-version')


def _documents(draft: str):
    return tuple(json.loads((ROOT / draft / f'{name}_1.jsonmetadef.schema.json').read_text('utf-8'))
                 for name in ('dialect', 'vocabulary'))


def _validation(draft: str):
    dialect, vocabulary = _documents(draft)
    registry = Registry()
    for document in (dialect, vocabulary):
        registry = registry.with_resource(document.get('$id', document.get('id')),
                                          Resource.from_contents(document))
    lib = next(parent for parent in ROOT.parents if parent.name == 'pub.tool.General').parent / 'pub.lib.General'
    common = (lib / 'common/defs/jsonmetadefs/src/product/jsonmetadefs'
              / 'eu/algites/lib/common/defs' / draft / 'vocabulary_1.jsonmetadef.schema.json')
    doc = json.loads(common.read_text(encoding='utf-8'))
    registry = registry.with_resource(doc.get('$id', doc.get('id')), Resource.from_contents(doc))
    return DRAFTS[draft](dialect, registry=registry)


def _nested_schema():
    return {
        'type': 'object',
        'properties': {
            'Container': {'type':'object',
                          'properties': {
                              'Variant': {
                                  'type': 'object',
                                  KEYS[0]: ['../base.json', '#/definitions/LocalBase'],
                                  KEYS[1]: {'alternatives': ['#A', '#B']},
                              }
                          }
            }
        }
    }


@pytest.mark.parametrize('draft', DRAFTS)
def test_legacy_dialect_is_valid_and_preserves_standard_recursive_schema(draft):
    dialect, vocabulary = _documents(draft)
    validator = DRAFTS[draft]
    validator.check_schema(dialect)
    validator.check_schema(vocabulary)
    assert '$vocabulary' not in dialect
    assert dialect['$schema'] == validator.META_SCHEMA['$schema']
    identity_key = 'id' if draft in ('draft-03', 'draft-04') else '$id'
    assert identity_key in dialect and identity_key in vocabulary
    for k in KEYS:
        assert dialect['properties'][k] == {'$ref': f"{vocabulary[identity_key]}#/properties/{k}"}
    standard = copy.deepcopy(validator.META_SCHEMA)
    for k in KEYS + COMMON_KEYS:
        standard['properties'].pop(k, None)
    for k in (identity_key, 'title', 'description'):
        standard.pop(k, None)
    copy_of_ours = copy.deepcopy(dialect)
    for k in KEYS + COMMON_KEYS:
        copy_of_ours['properties'].pop(k, None)
    for k in (identity_key, 'title', 'description'):
        copy_of_ours.pop(k, None)
    assert standard == copy_of_ours
    for name in ('dialect', 'vocabulary'):
        f=ROOT/draft/f'{name}_1.jsonmetadef.schema.json'
        sidecar=Path(str(f)+'.meta.yml').read_text('utf-8')
        assert f'/{draft}/{f.name}' in sidecar


@pytest.mark.parametrize('draft', DRAFTS)
def test_legacy_dialect_checks_nested_annotations(draft):
    validator = _validation(draft)
    good = _nested_schema()
    assert validator.is_valid(good)
    wrong_kind = copy.deepcopy(good)
    wrong_kind['properties']['Container']['properties']['Variant'][KEYS[0]] = 'not a list'
    assert not validator.is_valid(wrong_kind)
    duplicate_parent = copy.deepcopy(good)
    duplicate_parent['properties']['Container']['properties']['Variant'][KEYS[0]] = ['#A', '#A']
    assert not validator.is_valid(duplicate_parent)
    one_alternative = copy.deepcopy(good)
    one_alternative['properties']['Container']['properties']['Variant'][KEYS[1]]['alternatives'] = ['#A']
    assert not validator.is_valid(one_alternative)
    missing_alternatives = copy.deepcopy(good)
    missing_alternatives['properties']['Container']['properties']['Variant'][KEYS[1]] = {}
    assert not validator.is_valid(missing_alternatives)
    unknown_alternative_option = copy.deepcopy(good)
    unknown_alternative_option['properties']['Container']['properties']['Variant'][KEYS[1]]['unknown'] = 'invalid'
    assert not validator.is_valid(unknown_alternative_option)


@pytest.mark.parametrize('draft', DRAFTS)
def test_legacy_dialect_retains_its_own_standard_schema_restrictions(draft):
    validator=_validation(draft)
    assert not validator.is_valid({'properties': 'not-an-object'})
    schema = _nested_schema()
    schema['x-algites-defscodegen-extends'] = ['#D']
    assert validator.is_valid(schema)
