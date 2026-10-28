"""Offline conformance tests for the independent JSON meta-definitions artifact."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft201909Validator, Draft202012Validator
from jsonschema_specifications import REGISTRY
from referencing import Resource


SOURCES = Path(__file__).resolve().parents[2] / 'product' / 'jsonmetadefs' / 'eu' / 'algites' / 'tool' / 'codegen' / 'defs' / 'jsonmetadef'
VERSIONS = {'2019-09': Draft201909Validator, '2020-12': Draft202012Validator}


def _load(draft: str, name: str) -> dict:
    return json.loads((SOURCES / draft / (name + '_1.jsonmetadef.schema.json')).read_text(encoding='utf-8'))


def _registry(draft: str):
    registry = REGISTRY
    for name in ('dialect', 'vocabulary'):
        schema = _load(draft, name)
        registry = registry.with_resource(schema['$id'], Resource.from_contents(schema))
    return registry


@pytest.mark.parametrize('draft', sorted(VERSIONS))
def test_dialect_and_keyword_schemas_valid(draft):
    cls = VERSIONS[draft]
    for name in ('dialect', 'vocabulary'):
        schema = _load(draft, name)
        assert schema['$schema'] == cls.META_SCHEMA['$id']
        cls.check_schema(schema)
    dialect = _load(draft, 'dialect')
    assert dialect['$vocabulary']['https://json-schema.org/draft/' + draft + '/vocab/core'] is True
    assert [value for key, value in dialect['$vocabulary'].items() if key.endswith('vocabulary_1.md')] == [False]


@pytest.mark.parametrize('draft', sorted(VERSIONS))
def test_custom_dialect_validates_nested_keyword_shapes(draft):
    cls = VERSIONS[draft]
    registry = _registry(draft)
    meta = _load(draft, 'dialect')
    val = cls(meta, registry=registry)
    good = {'$schema':meta['$id'], '$id':'https://example.org/child',
            'type':'object', 'properties':{'Nested':{'type':'object',
                'x-algites-defscodegen-extends':['https://example.org/base'],
                'x-algites-defscodegen-choice': {'alternatives':['#/$defs/A','#/$defs/B']}}}}
    val.validate(good)
    bad = json.loads(json.dumps(good))
    bad['properties']['Nested']['x-algites-defscodegen-extends'] = 'base'
    assert not val.is_valid(bad)
    bad = json.loads(json.dumps(good))
    bad['properties']['Nested']['x-algites-defscodegen-choice']['alternatives'] = ['#/$defs/A']
    assert not val.is_valid(bad)


def test_one_shared_semantic_vocabulary_and_versioned_keyword_syntaxes():
    vocab = (SOURCES / 'vocabulary_1.md').read_text(encoding='utf-8')
    assert 'x-algites-defscodegen-extends' in vocab
    assert 'x-algites-defscodegen-choice' in vocab
    for name in ('extends', 'choice'):
        assert name in vocab
    keyword_sets = [_load(draft, 'vocabulary')['properties'] for draft in sorted(VERSIONS)]
    assert keyword_sets[0] == keyword_sets[1]
    assert _load('2019-09','dialect')['$vocabulary'] != _load('2020-12','dialect')['$vocabulary']
