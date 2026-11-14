"""Naming XMLDEFS, JSONDEFS and YAMLDEFS produce one named contract.

The regression exercises the actual published schemas, not an ad-hoc copy
of the problematic IdentifierConventions definition.
"""
from __future__ import annotations

import json
from pathlib import Path
import warnings

import pytest

from test_canonical_schema_frontend import frontend
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIngComposition_1 as Composition,
    AIngSourceInputKind_1 as SourceKind,
    AIngTypeOrigin_1 as Origin,
    AIngResolutionState_1 as Resolution,
)


LIB = next(parent for parent in Path(__file__).resolve().parents
           if parent.name == 'pub.tool.General').parent / 'pub.lib.General'
SCHEMAS = LIB / 'naming/convention/intf/src/product'
SUFFIX = 'eu/algites/lib/naming/convention/common-naming-conventions_1'
NAMED_ITEMS = {
    'IdentifierConventions': 'IdentifierConvention',
    'VersionConventions': 'VersionConvention',
    'NameFragments': 'NameFragment',
    'NameCompositions': 'NameComposition',
}


def _types(kind):
    root = SCHEMAS / kind
    if kind == 'xmldefs':
        source = root / (SUFFIX + '.xsd')
        result = frontend().load_xsd(source.read_text(), str(source))
    else:
        source = root / (SUFFIX + '.' + ('jsondef' if kind == 'jsondefs' else 'yamldef') + '.schema.json')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            result = frontend().load_json_or_yaml_types(json.loads(source.read_text()), str(source),
                SourceKind.JSONDEFS if kind == 'jsondefs' else SourceKind.YAMLDEFS)
    return {item.name: item for item in result}


@pytest.mark.parametrize('kind', ('xmldefs', 'jsondefs', 'yamldefs'))
def test_named_list_items_preserve_explicit_type_and_field(kind):
    """Neither dialect may synthesize ItemItem for a named repeated element."""
    types = _types(kind)
    for parent, item in NAMED_ITEMS.items():
        assert parent in types and item in types
        assert types[item].origin == Origin.DECLARED
        fields = [field for field in types[parent].structure.children if field.name == item]
        assert len(fields) == 1
        collection = fields[0]
        assert collection.name == item
        assert collection.item.name == item
        assert collection.item.resolution_state == Resolution.REFERENCE
    assert not any('ItemItem' in name for name in types)


@pytest.mark.parametrize('kind', ('xmldefs', 'jsondefs', 'yamldefs'))
def test_explicit_content_and_name_regexp_have_same_named_types(kind):
    """The choice is a named Content member; no synthetic Choice2 is exposed."""
    types = _types(kind)
    for name in ('NameFragmentsSegmentValue', 'NameFragmentsSegmentValueContent', 'NameRegexp'):
        assert name in types
        assert types[name].origin == Origin.DECLARED
    segment = types['NameFragmentsSegmentValue'].structure
    assert [field.name for field in segment.children] == ['Kind', 'Content']
    assert segment.children[1].structure.name == 'NameFragmentsSegmentValueContent'
    content = types['NameFragmentsSegmentValueContent'].structure
    assert content.composition == Composition.CHOICE
    assert [field.name for field in content.children] == [
        'Value', 'Convention', 'CustomConventionRegexp', 'NameRegexp']
    assert [field.name for field in types['NameRegexp'].structure.children] == ['Name', 'Regexp']
