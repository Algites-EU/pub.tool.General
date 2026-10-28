"""Regression coverage for semantic common contracts and format-owned members."""
from dataclasses import replace
import pytest

from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_common_contract_projection import merge_common
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


def _field(name, kind, presence=AInFieldPresenceKind.ALLOWED):
    return AIcdPropertyDefinition(name, AIcdDataType(kind, element_type=AIcdDataType(AInDataTypeKind.STRING))
                                   if kind is AInDataTypeKind.ARRAY else AIcdDataType(kind), presence)


def _definition(kind, identity, fields):
    return AIcdCanonicalDefinition(identity, 1, 'capability-definition', kind,
        'src/product/' + kind.value.lower() + '/example/capability-definition_1.schema',
        'An explicitly shared capability definition.', AIcdDataType(AInDataTypeKind.OBJECT,
        properties=tuple(fields)), (), 'Capability definition')


def test_common_intersection_keeps_format_specific_members_outside_common():
    """XML singular scope and YAML/JSON plural scopes do not silently merge."""
    common = _field('Capability', AInDataTypeKind.STRING, AInFieldPresenceKind.REQUIRED)
    schema_id = _field('ConfigurationSchemaId', AInDataTypeKind.STRING)
    xml = _definition(AInDefinitionSourceKind.XMLDEFS,
        'urn:algites:modustro:builder:model:capability-definition:1',
        [common, schema_id, _field('AllowedScope', AInDataTypeKind.ARRAY)])
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS,
        'urn:algites:modustro:builder:yamldef:model:capability-definition:1',
        [common, schema_id, _field('AllowedScopes', AInDataTypeKind.ARRAY),
         _field('$schema', AInDataTypeKind.STRING)])
    json = replace(yaml, source_kind=AInDefinitionSourceKind.JSONDEFS,
        identity='urn:algites:modustro:builder:jsondef:model:capability-definition:1')
    projected = merge_common([xml, yaml, json])
    assert {f.source_name for f in projected.data_type.properties} == {
        'Capability', 'ConfigurationSchemaId'}
    assert projected.identity == xml.identity
    assert 'YAMLDEFS' in projected.description and 'JSONDEFS' in projected.description
    assert {f.source_name for f in yaml.data_type.properties} == {
        'Capability', 'ConfigurationSchemaId', 'AllowedScopes', '$schema'}
    assert {f.source_name for f in xml.data_type.properties} == {
        'Capability', 'ConfigurationSchemaId', 'AllowedScope'}


def test_unrelated_scalar_types_rejected():
    """Common property name alone does not make integer and string compatible."""
    xml = _definition(AInDefinitionSourceKind.XMLDEFS, 'urn:algites:account:1',
                      [_field('Mode', AInDataTypeKind.STRING)])
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS, 'urn:algites:account:1',
                       [_field('Mode', AInDataTypeKind.INTEGER)])
    with pytest.raises(ValueError, match='Incompatible common field type.*Mode'):
        merge_common([xml, yaml])


def test_common_urn_alias_uses_technology_kind_only():
    """Normalization must not rewrite unrelated URN segments or arbitrary URLs."""
    generator = AIcSchemaContractBindingsGenerator
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS,
        'urn:algites:modustro:builder:yamldef:model:capability-definition:1', ())
    xml = _definition(AInDefinitionSourceKind.XMLDEFS,
        'urn:algites:modustro:builder:model:capability-definition:1', ())
    assert generator._common_identity(yaml, 'example.contracts', ('explicit', yaml.identity, 1)) == (
        'explicit', xml.identity, 1)
    other = replace(yaml, identity='urn:foreign:yamldef:unrelated:1')
    assert generator._common_identity(other, 'example.contracts', ('explicit', other.identity, 1)) == (
        'explicit', other.identity, 1)


def test_structural_supertype_for_format_specific_objects():
    """An XML anyType and a concrete YAML object share only an Any-typed API."""
    xml = _definition(AInDefinitionSourceKind.XMLDEFS, 'urn:algites:example:1',
        [_field('Configuration', AInDataTypeKind.ANY)])
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS, 'urn:algites:example:1',
        [_field('Configuration', AInDataTypeKind.OBJECT)])
    merged = merge_common([xml, yaml])
    assert merged.data_type.properties[0].data_type.kind is AInDataTypeKind.ANY
    assert yaml.data_type.properties[0].data_type.kind is AInDataTypeKind.OBJECT


def test_batch_produces_common_and_independent_schema_interfaces(tmp_path, monkeypatch):
    """Both native formats must emit their own complete API and inherit common."""
    import json
    from importlib import import_module
    for kind, source_marker, own_field in (
            ('jsondefs', 'jsondef', 'JsonOnly'), ('yamldefs', 'yamldef', 'YamlOnly')):
        directory = tmp_path / 'src/product' / kind / 'example/contracts'
        directory.mkdir(parents=True)
        name = f'capability-definition_1.{source_marker}.schema.json'
        document = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
            '$id': f'urn:algites:modustro:builder:{source_marker}:model:capability-definition:1',
            'type': 'object', 'properties': {'Capability': {'type': 'string'},
            own_field: {'type': 'integer'}}, 'required': ['Capability']}
        (directory / name).write_text(json.dumps(document), encoding='utf-8')
    options = {
        'artifact': '.',
        'schema_inputs': [dict(kind=k, directory='src/product/' + k)
                          for k in ('jsondefs', 'yamldefs')],
        'schema_input_naming_conventions': {
            'jsondefs': 'algites-jsondef-schema-versioned_1',
            'yamldefs': 'algites-yamldef-schema-versioned_1'},
        'technology_outputs': {'python': 'src/product/python.gen'},
        'technology_output_naming_conventions': {'python': {
            'common': 'algites-python-gen-intf-versioned_1',
            'yamldefs': 'algites-python-gen-yaml-intf-versioned_1',
            'jsondefs': 'algites-python-gen-json-intf-versioned_1'}},
        'naming_convention_files': [f'resource:{x}' for x in (
            'standard-conventions.yml', 'algites-python-name-conventions.yml',
            'algites-yamldef-name-conventions.yml', 'algites-jsondef-name-conventions.yml')],
        'languages': ['python']}
    result = AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, options)
    assert len(result) == 4
    output = tmp_path / 'src/product/python.gen/example/contracts'
    common = (output / 'aiig_capability_definition_1.py').read_text()
    yaml = (output / 'aiig__y_capability_definition_1.py').read_text()
    json_source = (output / 'aiig__j_capability_definition_1.py').read_text()
    assert 'Capability' in common and 'JsonOnly' not in common and 'YamlOnly' not in common
    assert 'YamlOnly' in yaml and 'JsonOnly' not in yaml
    assert 'JsonOnly' in json_source and 'YamlOnly' not in json_source
    monkeypatch.syspath_prepend(str(tmp_path / 'src/product/python.gen'))
    common_class = import_module('example.contracts.aiig_capability_definition_1').AIigCapabilityDefinition_1
    assert issubclass(import_module('example.contracts.aiig__y_capability_definition_1')
                      .AIig_yCapabilityDefinition_1, common_class)
    assert issubclass(import_module('example.contracts.aiig__j_capability_definition_1')
                      .AIig_jCapabilityDefinition_1, common_class)


def test_implicit_json_yaml_and_qualified_xml_common_id_are_equivalent():
    """XML namespace used as a qualified root name is an exact implicit ID alias."""
    match = AIcSchemaContractBindingsGenerator._common_explicit_matches_implicit
    implicit = ('implicit', 'eu.algites.lib.naming.convention', 'common-naming-conventions', 1, '')
    qualified = ('explicit', 'eu.algites.lib.naming.convention.common-naming-conventions', 1)
    assert match(qualified, implicit)
    assert match(('explicit', 'urn:algites:model:common-naming-conventions:1', 1), implicit)
    assert not match(('explicit', 'eu.other.convention.common-naming-conventions', 1), implicit)
    assert not match(('explicit', 'eu.algites.lib.naming.convention.other', 1), implicit)
    assert not match(('explicit', qualified[1], 2), implicit)
    assert not match(qualified, ('implicit', implicit[1], implicit[2], 1,
                                 '/properties/Nested'))
    assert not match(('explicit', 'urn:foreign:model:common-naming-conventions:1', 1), implicit)


def test_exact_algites_xml_namespace_alias_matches_dotted_common_schema_id():
    """The same Defs schema expressed as XML/JSON/YAML merges only for exact URNs."""
    generator = AIcSchemaContractBindingsGenerator
    xml = _definition(AInDefinitionSourceKind.XMLDEFS,
        'urn:eu:algites:tool:codegen:defs:input-profile:1', ())
    xml = replace(xml, logical_name='input-profile')
    assert generator._common_identity(xml, 'eu.algites.tool.codegen.defs',
        ('explicit', xml.identity, 1)) == (
            'explicit', 'eu.algites.tool.codegen.defs.input-profile', 1)
    assert generator._common_identity(xml, 'eu.algites.tool.codegen.other',
        ('explicit', xml.identity, 1)) == ('explicit', xml.identity, 1)
    changed_version = replace(xml, version=2)
    assert generator._common_identity(changed_version, 'eu.algites.tool.codegen.defs',
        ('explicit', xml.identity, 2)) == ('explicit', xml.identity, 2)


def test_string_closed_choice_relaxes_only_common_scalar_contract():
    """A finite JSON choice of strings and XML string share a String getter."""
    strings = AIcdDataType(AInDataTypeKind.ONE_OF, alternatives=(
        AIcdDataType(AInDataTypeKind.STRING), AIcdDataType(AInDataTypeKind.STRING)))
    xml = _definition(AInDefinitionSourceKind.XMLDEFS, 'urn:algites:options:1',
        [AIcdPropertyDefinition('Languages', AIcdDataType(AInDataTypeKind.ARRAY,
            element_type=AIcdDataType(AInDataTypeKind.STRING)))])
    json = _definition(AInDefinitionSourceKind.JSONDEFS, 'urn:algites:options:1',
        [AIcdPropertyDefinition('Languages', AIcdDataType(AInDataTypeKind.ARRAY,
            element_type=strings))])
    merged = merge_common([json, xml])
    assert merged.data_type.properties[0].data_type.element_type.kind is AInDataTypeKind.STRING
    invalid = replace(xml, data_type=AIcdDataType(AInDataTypeKind.OBJECT, properties=(
        AIcdPropertyDefinition('Languages', AIcdDataType(AInDataTypeKind.ARRAY,
            element_type=AIcdDataType(AInDataTypeKind.INTEGER))),)))
    with pytest.raises(ValueError, match='Incompatible common field type.*Languages'):
        merge_common([json, invalid])


def test_shared_string_and_literal_enum_have_covariant_java_types():
    """A format-specific enum getter must refine, not contradict, a shared field."""
    from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
    string = AIcdDataType(AInDataTypeKind.STRING)
    choices = AIcdDataType.choice(AInDataTypeKind.ONE_OF, (
        AIcdDataType(AInDataTypeKind.STRING,
            constraints=AIcdValueConstraints(enum_values=('java',))),
        AIcdDataType(AInDataTypeKind.STRING,
            constraints=AIcdValueConstraints(enum_values=('python',))),
    ))
    base = AIcdDataType(AInDataTypeKind.ARRAY, element_type=string)
    specialization = AIcdDataType(AInDataTypeKind.ARRAY, element_type=choices)
    field = _field('Languages', AInDataTypeKind.ARRAY)
    xml = _definition(AInDefinitionSourceKind.XMLDEFS, 'urn:algites:languages:1',
        [replace(field, data_type=base)])
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS, 'urn:algites:languages:1',
        [replace(field, data_type=specialization)])
    merged = merge_common((xml, yaml))
    assert merged.data_type.properties[0].data_type.element_type.kind is AInDataTypeKind.ANY
    assert yaml.data_type.properties[0].data_type.element_type.kind is AInDataTypeKind.ONE_OF
