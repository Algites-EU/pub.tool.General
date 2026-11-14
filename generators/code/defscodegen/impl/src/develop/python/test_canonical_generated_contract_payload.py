"""The source frontend output must fit the contract generated from canonical-model_1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

TOOL = next(path for path in Path(__file__).resolve().parents if path.name == 'pub.tool.General')
for root in ('generators/code/common/src/product/python',
             'generators/code/defscodegen/intf/src/product/python',
             'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(TOOL / root))

from eu.algites.tool.codegen.common.naming_profiles import resolve_codegen_naming_profiles
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdSourceBinding_1 as Binding, AIngSourceInputKind_1 as Kind,
    AIcgdScalar_1, AIcgdType_1,
    AIcgdElement_1, AIcgdElementList_1,
    AIngScalarKind_1 as ScalarKind,
    AIngComposition_1 as Composition, AIngResolutionState_1 as State,
    AIngTypeOrigin_1 as Origin, freeze_bindings)
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import AIcDefsCodegenCanonicalSchemaFrontend
from eu.algites.tool.codegen.defs.impl.standard.canonical_contract_payload import AIcDefsCodegenCanonicalContractPayload

SCHEMA_FILE = TOOL / ('generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/'
                      'tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')


def _frontend():
    config = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
    common = yaml.safe_load((config / 'algites-java-common-codegen-conventions.yml').read_text())
    defs = yaml.safe_load((config / 'algites-java-defs-codegen-conventions.yml').read_text())
    return AIcDefsCodegenCanonicalSchemaFrontend(resolve_codegen_naming_profiles(
        common, 'algites-java-codegen-common_1', defs, 'algites-java-defscodegen-standard_1'))


@pytest.mark.parametrize('kind', (Kind.YAMLDEFS, Kind.JSONDEFS))
def test_contract_payload_schema_validated_with_choice_map_and_synthetic_types(kind):
    source = {'type': 'object', 'title': 'Person', 'properties': {
        'kind': {'type': 'object', 'x-algites-defscodegen-choice': True,
                 'properties': {'text': {'type': 'string'}, 'number': {'type': 'integer'}},
                 'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False},
        'contacts': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'value': {'type': 'string'}}}}},
        'additionalProperties': {'type': 'boolean'}}
    root = _frontend().load_json_or_yaml(source, 'person.schema.json', kind)
    payload = AIcDefsCodegenCanonicalContractPayload.emit((root,))
    schema = json.loads(SCHEMA_FILE.read_text(encoding='utf-8'))
    Draft202012Validator(schema).validate(payload)
    fields = payload['types'][0]['content']['structure']['ElementList']['children']
    assert fields[0]['Element']['structure']['Type']['origin'] == 'SYNTHETIC'
    assert len(fields[0]['Element']['structure']['Type']['content']['structure']['ElementList']['children']) == 2
    assert fields[2]['Map']['map_kind'] == 'INTEGRATED_PROPERTY_MAP'
    group = fields[2]['Map']['source_bindings']['SourceBindingGroup']
    assert len(group) == 1 and group[0]['InputKind'] == kind.value
    assert group[0]['Binding'][0]['source_pointer'] == '#/additionalProperties'


def test_multiple_bindings_with_same_input_kind_and_duplicate_resource_paths():
    bindings = freeze_bindings({Kind.JSONDEFS: [Binding('x.json', '#/properties/A', 'member'),
                                               Binding('x.json', '#/properties/B', 'member')],
                                Kind.YAMLDEFS: [Binding('y.yaml', '#/properties/A', 'member')]})
    node = AIcgdType_1('id', 'Root', Origin.DECLARED,
        structure=AIcgdElementList_1(Composition.SEQUENCE,
            (AIcgdElement_1('a', AIcgdScalar_1(ScalarKind.STRING), source_bindings=bindings),)),
        source_bindings=bindings)
    emitted = AIcDefsCodegenCanonicalContractPayload.emit((node,))
    Draft202012Validator(json.loads(SCHEMA_FILE.read_text())).validate(emitted)
    groups = emitted['types'][0]['source_bindings']['SourceBindingGroup']
    by_kind = {group['InputKind']: group['Binding'] for group in groups}
    assert [item['source_pointer'] for item in by_kind['JSONDEFS']] == [
        '#/properties/A', '#/properties/B']
    assert len(by_kind['YAMLDEFS']) == 1


def test_unresolved_refs_are_not_silently_serialized_as_any():
    root = _frontend().load_json_or_yaml({'type': 'object', 'properties': {
        'ref': {'$ref': '#/$defs/Node'}}}, 'recursive.json', Kind.JSONDEFS)
    with pytest.raises(ValueError, match='Unresolved canonical TYPE'):
        AIcDefsCodegenCanonicalContractPayload.emit((root,))


def test_duplicate_type_identity_rejected():
    scalar = AIcgdType_1('id', 'Root', Origin.DECLARED, structure=AIcgdScalar_1(ScalarKind.STRING))
    with pytest.raises(ValueError, match='Duplicate canonical TYPE identity'):
        AIcDefsCodegenCanonicalContractPayload.emit([scalar, scalar])
