"""Exercise local JSON Schema definitions through both JSONDEFS and YAMLDEFS."""
import json

import pytest
from jsonschema import Draft202012Validator

from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_yaml_defs_frontend import AIcYamlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_json_schema_reader import AIcJsonSchemaReader


def _schema():
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        'type': 'object',
        'properties': {'Title': {'$ref': '#/$defs/displayText'}},
        '$defs': {'displayText': {
            'oneOf': [{'type': 'string', 'minLength': 1}, {
                'type': 'object', 'additionalProperties': False,
                'properties': {'Text': {'type': 'string', 'minLength': 1},
                               'ResourceKey': {'type': 'string', 'minLength': 1}},
                'anyOf': [{'required': ['Text']}, {'required': ['ResourceKey']}]}
            ]}}
    }


@pytest.mark.parametrize('kind,frontend,suffix', [
    (AInDefinitionSourceKind.JSONDEFS, AIcJsonDefsFrontend, 'jsondef'),
    (AInDefinitionSourceKind.YAMLDEFS, AIcYamlDefsFrontend, 'yamldef'),
])
def test_named_choice_reference_and_closed_object_presence(tmp_path, kind, frontend, suffix):
    path = tmp_path / f'security-bootstrap_1.{suffix}.schema.json'
    document = _schema()
    path.write_text(json.dumps(document), encoding='utf-8')
    request = AIcdDefinitionLoadRequest(path, kind, AIcAlgitesNamingProfiles_1.python_profile())
    definition = frontend().load(request)
    ref = definition.data_type.properties[0].data_type.reference
    assert ref is not None
    assert ref.target_data_type.kind is AInDataTypeKind.ONE_OF
    assert ref.target_data_type.alternatives[0].kind is AInDataTypeKind.STRING
    obj = ref.target_data_type.alternatives[1]
    assert obj.kind is AInDataTypeKind.OBJECT
    assert obj.constraints.min_properties == 1
    assert {p.source_name for p in obj.properties} == {'Text', 'ResourceKey'}
    validator = Draft202012Validator(document)
    for valid in ('hello', {'Text': 'hello'}, {'ResourceKey': 'key'},
                  {'Text': 'hello', 'ResourceKey': 'key'}):
        validator.validate({'Title': valid})
    for invalid in ('', {}, {'Text': ''}, {'Unrecognized': 'key'}):
        assert not validator.is_valid({'Title': invalid})


def test_arbitrary_any_of_is_not_silently_rewritten_as_object(tmp_path):
    path = tmp_path / 'presence_1.jsondef.schema.json'
    schema = {'type': 'object', 'properties': {'A': {'type': 'string'}, 'B': {'type': 'string'},
                'Optional': {'type': 'string'}}, 'additionalProperties': False,
              'anyOf': [{'required': ['A']}, {'required': ['B']}]}
    path.write_text(json.dumps(schema), encoding='utf-8')
    reader = AIcJsonSchemaReader()
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS,
        AIcAlgitesNamingProfiles_1.python_profile())
    assert reader._recursive_type(schema, request).kind is AInDataTypeKind.ANY_OF


def test_explicit_min_properties_remains_canonical(tmp_path):
    path = tmp_path / 'minimum_1.jsondef.schema.json'
    schema = {'type': 'object', 'properties': {'A': {'type': 'string'}}, 'minProperties': 1}
    path.write_text(json.dumps(schema), encoding='utf-8')
    definition = AIcJsonDefsFrontend().load(AIcdDefinitionLoadRequest(path,
        AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles_1.python_profile()))
    assert definition.data_type.constraints.min_properties == 1


def test_json_yaml_named_choice_canonical_parity(tmp_path):
    from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger

    representations = []
    for kind, frontend, suffix in (
        (AInDefinitionSourceKind.JSONDEFS, AIcJsonDefsFrontend, 'jsondef'),
        (AInDefinitionSourceKind.YAMLDEFS, AIcYamlDefsFrontend, 'yamldef'),
    ):
        path = tmp_path / f'security-bootstrap_1.{suffix}.schema.json'
        path.write_text(json.dumps(_schema()), encoding='utf-8')
        request = AIcdDefinitionLoadRequest(path, kind, AIcAlgitesNamingProfiles_1.python_profile())
        representations.append(frontend().load(request))
    AIcCanonicalDefinitionMerger.validate(representations)


def test_referenced_choice_and_object_variant_generate_for_both_technologies(tmp_path):
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator

    folder = tmp_path / 'intf/src/product/jsondefs/example/choices'
    folder.mkdir(parents=True)
    (folder / 'security-bootstrap_1.jsondef.schema.json').write_text(json.dumps(_schema()), encoding='utf-8')
    manifest = tmp_path / 'bindings.json'
    manifest.write_text(json.dumps({'artifact': 'intf', 'languages': ['java', 'python']}))
    generated = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    assert len(generated) == 6
    java = tmp_path / 'intf/src/product/java.gen/example/choices'
    python = tmp_path / 'intf/src/product/python.gen/example/choices'
    assert (java / 'AIigSecurityBootstrapDefinitionDisplayText_1.java').exists()
    assert (java / 'AIigSecurityBootstrapDefinitionDisplayTextOneOf1_1.java').exists()
    assert (python / 'aiig_security_bootstrap_definition_display_text_1.py').exists()
    assert (python / 'aiig_security_bootstrap_definition_display_text_one_of1_1.py').exists()
