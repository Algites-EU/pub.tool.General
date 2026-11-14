"""Exercise local JSON Schema definitions through both JSONDEFS and YAMLDEFS."""
import json

import pytest
from jsonschema import Draft202012Validator

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from explicit_legacy_naming import configured_load as AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.old.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.old.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.old.impl.standard.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.old.impl.standard.aic_yaml_defs_frontend import AIcYamlDefsFrontend
from eu.algites.tool.codegen.defs.old.impl.standard.aic_json_schema_reader import AIcJsonSchemaReader


def _schema():
    """A named structural choice with two explicit, typed alternatives."""
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        'type': 'object',
        'properties': {'Title': {'$ref': '#/$defs/DisplayText'}},
        '$defs': {'DisplayText': {
            'type': 'object', 'x-algites-defscodegen-choice': True,
            'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False,
            'properties': {
                'PlainText': {'type': 'string', 'minLength': 1},
                'Resource': {
                    'type': 'object', 'additionalProperties': False,
                    'properties': {
                        'Text': {'type': 'string', 'minLength': 1},
                        'ResourceKey': {'type': 'string', 'minLength': 1}},
                    'minProperties': 1,
                    'anyOf': [{'required': ['Text']}, {'required': ['ResourceKey']}]}
            }}}
    }


@pytest.mark.parametrize('kind,frontend,suffix', [
    (AInDefinitionSourceKind.JSONDEFS, AIcJsonDefsFrontend, 'jsondef'),
    (AInDefinitionSourceKind.YAMLDEFS, AIcYamlDefsFrontend, 'yamldef'),
])
def test_named_choice_reference_and_closed_object_presence(tmp_path, kind, frontend, suffix):
    path = tmp_path / f'security-bootstrap_1.{suffix}.schema.json'
    document = _schema()
    path.write_text(json.dumps(document), encoding='utf-8')
    request = AIcdDefinitionLoadRequest(path, kind, AIcAlgitesNamingProfiles.python_profile())
    definition = frontend().load(request)
    ref = definition.data_type.properties[0].data_type.reference
    assert ref is not None
    assert ref.target_data_type.kind is AInDataTypeKind.ONE_OF
    text_branch, resource_branch = ref.target_data_type.alternatives
    assert text_branch.kind is resource_branch.kind is AInDataTypeKind.OBJECT
    assert text_branch.properties[0].source_name == 'PlainText'
    assert text_branch.properties[0].data_type.kind is AInDataTypeKind.STRING
    obj = resource_branch.properties[0].data_type
    assert obj.kind is AInDataTypeKind.OBJECT
    assert obj.constraints.min_properties == 1
    assert {p.source_name for p in obj.properties} == {'Text', 'ResourceKey'}
    validator = Draft202012Validator(document)
    for valid in ({'PlainText': 'hello'}, {'Resource': {'Text': 'hello'}},
                  {'Resource': {'ResourceKey': 'key'}},
                  {'Resource': {'Text': 'hello', 'ResourceKey': 'key'}}):
        validator.validate({'Title': valid})
    for invalid in ('', {}, {'PlainText': ''}, {'Resource': {}},
                    {'Resource': {'Text': ''}}, {'Unrecognized': 'key'},
                    {'PlainText': 'ok', 'Resource': {'Text': 'also'}}):
        assert not validator.is_valid({'Title': invalid})


def test_arbitrary_any_of_is_validation_only_not_a_generated_choice(tmp_path):
    path = tmp_path / 'presence_1.jsondef.schema.json'
    schema = {'type': 'object', 'properties': {'A': {'type': 'string'}, 'B': {'type': 'string'},
                'Optional': {'type': 'string'}}, 'additionalProperties': False,
              'anyOf': [{'required': ['A']}, {'required': ['B']}]}
    path.write_text(json.dumps(schema), encoding='utf-8')
    reader = AIcJsonSchemaReader()
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS,
        AIcAlgitesNamingProfiles.python_profile())
    # Arbitrary anyOf validates a document but does not define a structural
    # Choice contract. Its ordinary object fields remain first-class fields.
    parsed = reader._recursive_type(schema, request)
    assert parsed.kind is AInDataTypeKind.OBJECT
    assert {p.source_name for p in parsed.properties} == {'A', 'B', 'Optional'}
    validator = Draft202012Validator(schema)
    assert validator.is_valid({'A': 'value'})
    assert validator.is_valid({'B': 'value'})
    assert not validator.is_valid({'Optional': 'value'})


def test_explicit_min_properties_remains_canonical(tmp_path):
    path = tmp_path / 'minimum_1.jsondef.schema.json'
    schema = {'type': 'object', 'properties': {'A': {'type': 'string'}}, 'minProperties': 1}
    path.write_text(json.dumps(schema), encoding='utf-8')
    definition = AIcJsonDefsFrontend().load(AIcdDefinitionLoadRequest(path,
        AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles.python_profile()))
    assert definition.data_type.constraints.min_properties == 1


def test_json_yaml_named_choice_canonical_parity(tmp_path):
    from eu.algites.tool.codegen.defs.old.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger

    representations = []
    for kind, frontend, suffix in (
        (AInDefinitionSourceKind.JSONDEFS, AIcJsonDefsFrontend, 'jsondef'),
        (AInDefinitionSourceKind.YAMLDEFS, AIcYamlDefsFrontend, 'yamldef'),
    ):
        path = tmp_path / f'security-bootstrap_1.{suffix}.schema.json'
        path.write_text(json.dumps(_schema()), encoding='utf-8')
        request = AIcdDefinitionLoadRequest(path, kind, AIcAlgitesNamingProfiles.python_profile())
        representations.append(frontend().load(request))
    AIcCanonicalDefinitionMerger.validate(representations)


def test_referenced_choice_and_object_variant_generate_for_both_technologies(tmp_path):
    from eu.algites.tool.codegen.defs.old.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
    from explicit_naming_fixture import explicit_legacy_generic_manifest

    folder = tmp_path / 'intf/src/product/jsondefs/example/choices'
    folder.mkdir(parents=True)
    (folder / 'security-bootstrap_1.jsondef.schema.json').write_text(json.dumps(_schema()), encoding='utf-8')
    manifest = tmp_path / 'bindings.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({'artifact': 'intf', 'languages': ['java', 'python']})))
    generated = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    # The manifest lists owning contracts, while each named choice additionally
    # emits two payload types and two sealed selected wrappers per language.
    assert len(generated) == 4
    java = tmp_path / 'intf/src/product/java.gen/example/choices'
    python = tmp_path / 'intf/src/product/python.gen/example/choices'
    assert (java / 'AIigDisplayText_1.java').exists()
    assert (java / 'AIigDisplayTextSelectedResource_1.java').exists()
    assert (python / 'aiig_display_text_1.py').exists()
    assert (python / 'aiig_display_text_selected_resource_1.py').exists()
