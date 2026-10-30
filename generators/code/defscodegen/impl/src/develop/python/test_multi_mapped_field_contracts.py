"""Regression tests for typable mapped collections and XSD identity constraints."""
from __future__ import annotations

import json

import pytest

from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from explicit_legacy_naming import configured_load as AIcdDefinitionLoadRequest


def _load(path, kind):
    return AIcdDefinitionLoadRequest(path, kind, AIcAlgitesNamingProfiles.python_profile())


def test_json_object_map_preserves_typed_value_and_virtual_key(tmp_path):
    source = tmp_path / 'records_1.jsondef.schema.json'
    source.write_text(json.dumps({'type': 'object', 'properties': {
        'Records': {'type': 'object', 'additionalProperties': {'type': 'object',
            'properties': {'Label': {'type': 'string'}}}}}}))
    contract = AIcJsonDefsFrontend().load(_load(source, AInDefinitionSourceKind.JSONDEFS))
    mapped = contract.data_type.properties[0].data_type
    assert mapped.kind is AInDataTypeKind.OBJECT
    assert mapped.keyed_value_type.kind is AInDataTypeKind.OBJECT
    assert mapped.keyed_value_type.properties[0].source_name == 'Label'
    assert len(mapped.key_definitions) == 1
    assert mapped.key_definitions[0].virtual


def test_positionally_typed_json_array_retains_both_position_types(tmp_path):
    source = tmp_path / 'tuple_1.jsondef.schema.json'
    source.write_text(json.dumps({'type': 'object', 'properties': {
        'Tuple': {'type': 'array', 'prefixItems': [{'type': 'string'},
            {'type': 'integer'}], 'items': {'type': 'boolean'}}}}))
    contract = AIcJsonDefsFrontend().load(_load(source, AInDefinitionSourceKind.JSONDEFS))
    array = contract.data_type.properties[0].data_type
    assert array.kind is AInDataTypeKind.ARRAY
    assert [type_.kind for type_ in array.position_types] == [
        AInDataTypeKind.STRING, AInDataTypeKind.INTEGER]
    assert array.element_type.kind is AInDataTypeKind.BOOLEAN


def _xml_schema(keys):
    return '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:contract" targetNamespace="urn:contract"
        elementFormDefault="qualified" version="1">
      <xs:complexType name="employees"><xs:sequence>
        <xs:element name="Employees"><xs:complexType><xs:sequence>
          <xs:element name="Employee" minOccurs="0" maxOccurs="unbounded">
            <xs:complexType><xs:sequence>
              <xs:element name="Label" type="xs:string"/>
            </xs:sequence>
              <xs:attribute name="Id" type="xs:int" use="required"/>
              <xs:attribute name="Region" type="xs:string" use="required"/>
            </xs:complexType>
          </xs:element>
        </xs:sequence></xs:complexType>''' + keys + '''</xs:element>
      </xs:sequence></xs:complexType></xs:schema>'''


def test_xml_composite_key_and_second_index_are_preserved(tmp_path):
    source = tmp_path / 'employees_1.xsd'
    source.write_text(_xml_schema('''
      <xs:key name="ByRegionAndId"><xs:selector xpath="tns:Employee"/>
        <xs:field xpath="@Region"/><xs:field xpath="@Id"/></xs:key>
      <xs:key name="ById"><xs:selector xpath="tns:Employee"/>
        <xs:field xpath="@Id"/></xs:key>'''))
    frontend = AIcXmlDefsFrontend()
    request = _load(source, AInDefinitionSourceKind.XMLDEFS)
    frontend.load(request)
    owner = frontend.load_named_type(request, 'employeesEmployees')
    mapped = owner.data_type.properties[0].data_type
    assert mapped.kind is AInDataTypeKind.ARRAY
    assert [key.fields for key in mapped.key_definitions] == [('Region', 'Id'), ('Id',)]
    assert all(key.unique for key in mapped.key_definitions)
    employee = frontend.load_named_type(request, 'employeesEmployeesEmployee')
    assert {field.source_name for field in employee.data_type.properties} == {'Id', 'Region', 'Label'}


def test_xml_key_selector_with_missing_namespace_is_rejected(tmp_path):
    source = tmp_path / 'employees_1.xsd'
    source.write_text(_xml_schema('''
      <xs:key name="ById"><xs:selector xpath="Employee"/>
        <xs:field xpath="@Id"/></xs:key>'''))
    frontend = AIcXmlDefsFrontend()
    with pytest.raises(ValueError, match='Unqualified XSD XPath'):
        frontend.load_named_type(_load(source, AInDefinitionSourceKind.XMLDEFS), 'employeesEmployees')


def test_non_type_preserving_pattern_properties_fails_loudly(tmp_path):
    source = tmp_path / 'patterns_1.jsondef.schema.json'
    source.write_text(json.dumps({'type': 'object', 'properties': {
        'Records': {'type': 'object', 'patternProperties': {
            '^x': {'type': 'integer'}}}}}))
    with pytest.raises(ValueError, match='patternProperties'):
        AIcJsonDefsFrontend().load(_load(source, AInDefinitionSourceKind.JSONDEFS))


@pytest.mark.parametrize('target', ['java', 'python'])
def test_mapped_getter_uses_interface_not_concrete_implementation(tmp_path, target):
    """The read contract exposes AIiMultiMappedList regardless of source format."""
    from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
    from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
    from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
    from eu.algites.tool.codegen.defs.impl.standard.aic_selected_naming_catalog import AIcSelectedNamingCatalog
    source = tmp_path / 'products_1.jsondef.schema.json'
    source.write_text(json.dumps({'type': 'object', 'properties': {
        'Products': {'type': 'object', 'additionalProperties': {'type': 'object',
            'properties': {'Name': {'type': 'string'}}}}}}))
    technology = AInCodeGenerationTarget.JAVA if target == 'java' else AInCodeGenerationTarget.PYTHON
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
    tool = next(p for p in __import__('pathlib').Path(__file__).resolve().parents if p.name == 'pub.tool.General')
    library = tool.parent / 'pub.lib.General'
    language = 'java' if target == 'java' else 'python'
    profile = AIcNameConventionCatalog.load_many([
        library / 'naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode' / f'algites-{language}-name-conventions.yml',
        tool / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode' / f'algites-{language}-codegen-method-conventions.yml',
    ]).with_generated_method_profile(f'algites-{language}-codegen-standard_1')
    definition = AIcJsonDefsFrontend().load(AIcdDefinitionLoadRequest(
        source, AInDefinitionSourceKind.JSONDEFS, profile))
    profile_id = ('algites-java-gen-intf-versioned_1' if target == 'java'
                  else 'algites-python-gen-intf-versioned_1')
    selected = AIcSelectedNamingCatalog(profile, {role: profile_id for role in (
        AInDefsNameRole.INTERFACE_TYPE, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)})
    result = AIcSchemaContractInterfaceGenerator().generate(AIcdCodeGenerationRequest(
        definition, technology, 'example.products', selected, contract_role='common'))
    assert 'AIiMultiMappedList<' in result.source if target == 'java' else 'AIiMultiMappedList[' in result.source
    assert 'AIcMultiMappedList' not in result.source


def test_nested_xml_key_field_preserves_typed_nullable_path(tmp_path):
    """A nested optional key source survives as a canonical field path."""
    source = tmp_path / 'employees_1.xsd'
    schema = _xml_schema('''
      <xs:key name="ByNestedCode"><xs:selector xpath="tns:Employee"/>
        <xs:field xpath="tns:Properties/tns:Identity/tns:Code"/></xs:key>''')
    schema = schema.replace('<xs:element name="Label" type="xs:string"/>', '''
              <xs:element name="Properties" minOccurs="0"><xs:complexType><xs:sequence>
                <xs:element name="Identity" minOccurs="0"><xs:complexType><xs:sequence>
                  <xs:element name="Code" type="xs:string" minOccurs="0"/>
                </xs:sequence></xs:complexType></xs:element>
              </xs:sequence></xs:complexType></xs:element>
              <xs:element name="Label" type="xs:string"/>''')
    source.write_text(schema)
    frontend = AIcXmlDefsFrontend()
    request = _load(source, AInDefinitionSourceKind.XMLDEFS)
    frontend.load(request)
    owner = frontend.load_named_type(request, 'employeesEmployees')
    assert owner.data_type.properties[0].data_type.key_definitions[0].fields == (
        'Properties.Identity.Code',)


def test_nested_xml_key_rejects_unknown_and_repeating_intermediate(tmp_path):
    """Nested key paths are validated against declarations, not merely split."""
    source = tmp_path / 'employees_1.xsd'
    schema = _xml_schema('''<xs:key name="ByCode"><xs:selector xpath="tns:Employee"/>
        <xs:field xpath="tns:Properties/tns:Code"/></xs:key>''')
    schema = schema.replace('<xs:element name="Label" type="xs:string"/>', '''
        <xs:element name="Properties" maxOccurs="unbounded"><xs:complexType><xs:sequence>
          <xs:element name="Code" type="xs:string"/>
        </xs:sequence></xs:complexType></xs:element>''')
    source.write_text(schema)
    with pytest.raises(ValueError, match='Repeated intermediate'):
        AIcXmlDefsFrontend().load_named_type(_load(source, AInDefinitionSourceKind.XMLDEFS),
                                               'employeesEmployees')
    source.write_text(schema.replace('name="Properties" maxOccurs="unbounded"', 'name="Properties" maxOccurs="1"').replace('tns:Code', 'tns:Absent'))
    with pytest.raises(ValueError, match='Unresolved or ambiguous'):
        AIcXmlDefsFrontend().load_named_type(_load(source, AInDefinitionSourceKind.XMLDEFS),
                                               'employeesEmployees')


@pytest.mark.parametrize('target', ['java', 'python'])
def test_synthetic_value_getter_is_configured_and_typed(tmp_path, target):
    """Primitive additionalProperties values require a typed virtual getter."""
    from dataclasses import replace
    from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
    from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
    from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
    from eu.algites.tool.codegen.defs.impl.standard.aic_selected_naming_catalog import AIcSelectedNamingCatalog
    source = tmp_path / 'numbers_1.jsondef.schema.json'
    source.write_text(json.dumps({'type': 'integer'}))
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
    tool = next(p for p in __import__('pathlib').Path(__file__).resolve().parents if p.name == 'pub.tool.General')
    library = tool.parent / 'pub.lib.General'
    language = 'java' if target == 'java' else 'python'
    profile = AIcNameConventionCatalog.load_many([
        library / 'naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode' / f'algites-{language}-name-conventions.yml',
        tool / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode' / f'algites-{language}-codegen-method-conventions.yml',
    ]).with_generated_method_profile(f'algites-{language}-codegen-standard_1')
    definition = AIcJsonDefsFrontend().load(AIcdDefinitionLoadRequest(
        source, AInDefinitionSourceKind.JSONDEFS, profile))
    definition = replace(definition, source_resource=str(source) + '#/additionalProperties')
    profile_id = 'algites-java-gen-intf-versioned_1' if target == 'java' else 'algites-python-gen-intf-versioned_1'
    selected = AIcSelectedNamingCatalog(profile, {role: profile_id for role in (
        AInDefsNameRole.INTERFACE_TYPE, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)})
    result = AIcSchemaContractInterfaceGenerator().generate(AIcdCodeGenerationRequest(
        definition, AInCodeGenerationTarget.JAVA if target == 'java' else AInCodeGenerationTarget.PYTHON,
        'example.numbers', selected, contract_role='format'))
    assert '_getValue' in result.source
    assert 'java.math.BigInteger _getValue()' in result.source if target == 'java' else 'def _getValue(self) -> int:' in result.source
    assert '_getKey' in result.source


@pytest.mark.parametrize('target', ['java', 'python'])
def test_synthetic_value_getter_retains_object_array_item_contract(tmp_path, target):
    """Map-valued arrays remain one keyed entry with a typed list value."""
    from dataclasses import replace
    from pathlib import Path
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
    from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
    from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
    from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
    from eu.algites.tool.codegen.defs.impl.standard.aic_selected_naming_catalog import AIcSelectedNamingCatalog

    source = tmp_path / 'records_1.jsondef.schema.json'
    source.write_text(json.dumps({'type': 'array', 'items': {
        'type': 'object', 'properties': {'something': {'type': 'string'}}}}))
    language = target
    tool = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
    library = tool.parent / 'pub.lib.General'
    catalog = AIcNameConventionCatalog.load_many([
        library / 'naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode' / f'algites-{language}-name-conventions.yml',
        tool / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode' / f'algites-{language}-codegen-method-conventions.yml',
    ]).with_generated_method_profile(f'algites-{language}-codegen-standard_1')
    definition = AIcJsonDefsFrontend().load(AIcdDefinitionLoadRequest(
        source, AInDefinitionSourceKind.JSONDEFS, catalog))
    definition = replace(definition, source_resource=str(source) + '#/additionalProperties')
    profile_id = f'algites-{language}-gen-intf-versioned_1'
    selected = AIcSelectedNamingCatalog(catalog, {role: profile_id for role in (
        AInDefsNameRole.INTERFACE_TYPE, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)})
    result = AIcSchemaContractInterfaceGenerator().generate(AIcdCodeGenerationRequest(
        definition, AInCodeGenerationTarget.JAVA if target == 'java' else AInCodeGenerationTarget.PYTHON,
        'example.records', selected, contract_role='format'))
    if target == 'java':
        assert 'java.util.List<? extends ' in result.source
    else:
        assert 'tuple[' in result.source
    assert '_getValue' in result.source
    assert 'Object _getValue()' not in result.source
    assert 'def _getValue(self) -> Any:' not in result.source


def test_xml_unique_identity_constraint_remains_explicitly_unsupported(tmp_path):
    """The optional-key structure of xs:unique is not yet implemented."""
    source = tmp_path / 'employees_1.xsd'
    identity = ('<xs:unique name="ByRegion">'
                '<xs:selector xpath="tns:Employee"/>'
                '<xs:field xpath="@Region"/></xs:unique>')
    source.write_text(_xml_schema(identity))
    with pytest.raises(ValueError, match='Unsupported xs:unique'):
        AIcXmlDefsFrontend().load_named_type(
            _load(source, AInDefinitionSourceKind.XMLDEFS), 'employeesEmployees')


def test_xml_keyref_does_not_affect_structural_indexes(tmp_path):
    """Ignore reference constraints while preserving concrete key indexes."""
    source = tmp_path / 'employees_1.xsd'
    source.write_text(_xml_schema('''
      <xs:key name="ById"><xs:selector xpath="tns:Employee"/>
        <xs:field xpath="@Id"/></xs:key>
      <xs:keyref name="ReferringEmployee" refer="tns:ById">
        <xs:selector xpath="tns:Employee"/>
        <xs:field xpath="@Region"/></xs:keyref>'''))
    mapped = AIcXmlDefsFrontend().load_named_type(
        _load(source, AInDefinitionSourceKind.XMLDEFS), 'employeesEmployees'
    ).data_type.properties[0].data_type
    assert [key.name for key in mapped.key_definitions] == ['ById']
    employee = AIcXmlDefsFrontend().load_named_type(
        _load(source, AInDefinitionSourceKind.XMLDEFS), 'employeesEmployeesEmployee')
    assert {field.source_name for field in employee.data_type.properties} == {'Id', 'Region', 'Label'}


def test_xml_keyref_alone_creates_no_index(tmp_path):
    """A referential constraint is not a storage or lookup structure."""
    source = tmp_path / 'employees_1.xsd'
    source.write_text(_xml_schema('''
      <xs:keyref name="RefOnly" refer="tns:Unknown">
        <xs:selector xpath="tns:Employee"/>
        <xs:field xpath="@Id"/></xs:keyref>'''))
    contract = AIcXmlDefsFrontend().load(_load(source, AInDefinitionSourceKind.XMLDEFS))
    assert not contract.data_type.properties[0].data_type.key_definitions
