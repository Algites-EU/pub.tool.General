"""Keep technology-specific read contracts covariant with common contracts."""

import json
from pathlib import Path

from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import (
    AIcSchemaContractBindingsGenerator,
)


def test_root_alias_choice_and_anchored_content_are_nominal(tmp_path):
    """A named choice and root alias must not create incompatible Java getters."""
    folder = tmp_path / 'src/product/yamldefs/example/contracts'
    folder.mkdir(parents=True)
    schemas = {
        'version_1.yamldef.schema.json': {
            '$defs': {'VersionRequirement': {'oneOf': [
                {'type': 'string'}, {'type': 'integer'}]}},
            '$ref': '#/$defs/VersionRequirement',
        },
        'credentials_1.yamldef.schema.json': {
            '$defs': {
                'DocumentContent': {'type': 'object', 'properties': {
                    'Name': {'type': 'string'}}},
                'EmbeddedContent': {'$anchor': 'EmbeddedContent', 'allOf': [
                    {'$ref': '#/$defs/DocumentContent'}],
                    'unevaluatedProperties': False},
            },
            '$ref': '#/$defs/DocumentContent',
        },
        'artifact_1.yamldef.schema.json': {
            'type': 'object', 'properties': {
                'VersionRequirement': {'$ref': 'version_1.yamldef.schema.json'},
                'CredentialProfiles': {'$ref': 'credentials_1.yamldef.schema.json#EmbeddedContent'},
                'OptionalChoice': {'oneOf': [
                    {'type': 'null'}, {'$ref': 'version_1.yamldef.schema.json'}]},
            },
        },
    }
    for name, contents in schemas.items():
        (folder / name).write_text(json.dumps(contents), encoding='utf-8')
    options = {
        'artifact': '.',
        'schema_inputs': [{'kind': 'yamldefs', 'directory': 'src/product/yamldefs'}],
        'schema_input_naming_conventions': {'yamldefs': 'algites-yamldef-schema-versioned_1'},
        'technology_outputs': {'java': 'src/product/java.gen'},
        'technology_output_naming_conventions': {'java': {
            'common': 'algites-java-gen-intf-versioned_1',
            'yamldefs': 'algites-java-gen-yaml-intf-versioned_1'}},
        'naming_convention_files': [f'resource:{name}' for name in (
            'standard-conventions.yml', 'algites-java-name-conventions.yml',
            'algites-yamldef-name-conventions.yml')],
        'languages': ['java'],
    }
    AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, options)
    output = tmp_path / 'src/product/java.gen/example/contracts'
    def read(name):
        return (output / name).read_text(encoding='utf-8')
    version = read('AIig_yVersion_1.java')
    assert 'AIigVersion_1' in version and ' extends ' in version
    named_choice = read('AIig_yVersionDefinitionVersionRequirement_1.java')
    assert 'sealed interface' in named_choice
    assert 'extends example.contracts.AIigVersionDefinitionVersionRequirement_1' in named_choice
    common_choice = read('AIigVersionDefinitionVersionRequirement_1.java')
    assert 'public interface ' in common_choice
    artifact = read('AIigArtifact_1.java')
    assert 'AIigCredentialsDefinitionDocumentContent_1 getCredentialProfiles()' in artifact
    assert 'ArtifactCredentialProfiles' not in artifact
    yaml_artifact = read('AIig_yArtifact_1.java')
    assert 'AIig_yCredentialsDefinitionDocumentContent_1 getCredentialProfiles()' in yaml_artifact
    assert 'extends example.contracts.AIigArtifact_1' in yaml_artifact
    assert not list(output.glob('*ArtifactCredentialProfiles*.java'))

    # The Python target uses a class declaration without parentheses for
    # schema choices. It must still inherit the common nominal contract.
    py_options = dict(options)
    py_options['languages'] = ['python']
    py_options['technology_outputs'] = {'python': 'src/product/python.gen'}
    py_options['technology_output_naming_conventions'] = {'python': {
        'common': 'algites-python-gen-intf-versioned_1',
        'yamldefs': 'algites-python-gen-yaml-intf-versioned_1'}}
    py_options['naming_convention_files'] = [f'resource:{name}' for name in (
        'standard-conventions.yml', 'algites-python-name-conventions.yml',
        'algites-yamldef-name-conventions.yml')]
    AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, py_options)
    py_output = tmp_path / 'src/product/python.gen/example/contracts'
    py_choice = (py_output / 'aiig__y_version_definition_version_requirement_1.py').read_text()
    assert 'class AIig_yVersionDefinitionVersionRequirement_1(AIigVersionDefinitionVersionRequirement_1):' in py_choice
