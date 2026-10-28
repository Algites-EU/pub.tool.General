"""Regression tests for ordinal closed-choice contracts in repeated XSD particles."""
from __future__ import annotations

import json
from pathlib import Path

from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from explicit_naming_fixture import explicit_legacy_generic_manifest


def _schema(tmp_path: Path) -> Path:
    directory = tmp_path / 'src/product/xmldefs/example/contracts'
    directory.mkdir(parents=True)
    path = directory / 'events_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
      <xs:complexType name="ProfileType"><xs:sequence>
        <xs:choice minOccurs="1" maxOccurs="unbounded">
          <xs:element name="Basic" type="xs:string"/>
          <xs:element name="Bearer" type="xs:string"/>
        </xs:choice>
        <xs:choice minOccurs="0" maxOccurs="2">
          <xs:element name="Certificate" type="xs:string"/>
          <xs:element name="ApiKey" type="xs:string"/>
        </xs:choice>
      </xs:sequence><xs:attribute name="Id" type="xs:string" use="required"/></xs:complexType>
      <xs:element name="Profiles" type="ProfileType"/>
    </xs:schema>''', encoding='utf-8')
    return path


def test_ordinal_types_and_bounds_in_canonical_xml_model(tmp_path):
    path = _schema(tmp_path)
    frontend = AIcXmlDefsFrontend()
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
                                        AIcAlgitesNamingProfiles.python_profile())
    assert frontend.additional_named_type_names(path) == (
        'ProfileTypeChoice1', 'ProfileTypeChoice2')
    parent = frontend.load_named_type(request, 'ProfileType').data_type
    assert [field.source_name for field in parent.properties] == ['Choice1', 'Choice2', 'Id']
    for ordinal, minimum, maximum in ((1, 1, None), (2, 0, 2)):
        field = parent.properties[ordinal - 1]
        assert field.data_type.kind is AInDataTypeKind.ARRAY
        assert (field.data_type.constraints.min_items, field.data_type.constraints.max_items) == (minimum, maximum)
        assert field.data_type.element_type.reference.logical_name == f'profile-type-choice{ordinal}'
        item = frontend.load_named_type(request, f'ProfileTypeChoice{ordinal}').data_type
        assert item.kind is AInDataTypeKind.ONE_OF
        assert len(item.alternatives) == 2
        assert all(alt.properties[0].xml_field is not None for alt in item.alternatives)
        assert frontend.is_synthetic_choice_type_name(path, f'ProfileTypeChoice{ordinal}')


def test_java_and_python_generate_named_sealed_choices(tmp_path, monkeypatch):
    _schema(tmp_path)
    manifest = explicit_legacy_generic_manifest({'artifact': '.', 'languages': ['java', 'python']})
    manifest['schema_inputs'] = [{'kind': 'xmldefs', 'directory': 'src/product/xmldefs'}]
    manifest['technology_outputs'] = {
        'java': 'src/product/java.gen', 'python': 'src/product/python.gen'}
    config = tmp_path / 'manifest.json'
    config.write_text(json.dumps(manifest), encoding='utf-8')
    generated = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, config)
    for language in ('java', 'python'):
        assert all(any(item['pointer'] == '@type/' + name and item['language'] == language
                       for item in generated) for name in ('ProfileTypeChoice1', 'ProfileTypeChoice2'))
    java = tmp_path / 'src/product/java.gen/example/contracts'
    python = tmp_path / 'src/product/python.gen/example/contracts'
    root = (java / 'AIigEvents_1.java').read_text()
    assert 'List<? extends AIigProfileTypeChoice1_1>' in root
    assert 'List<? extends AIigProfileTypeChoice2_1>' in root
    assert 'public sealed interface AIigProfileTypeChoice1_1' in (
        java / 'AIigProfileTypeChoice1_1.java').read_text()
    assert 'public sealed interface AIigProfileTypeChoice2_1' in (
        java / 'AIigProfileTypeChoice2_1.java').read_text()
    assert (python / 'aiig_profile_type_choice1_1.py').exists()
    assert (python / 'aiig_profile_type_choice2_1.py').exists()
    assert '__xml_data_object__' not in (python / 'aiig_profile_type_choice1_1.py').read_text()
    import importlib
    import sys
    monkeypatch.syspath_prepend(str(tmp_path / 'src/product/python.gen'))
    module = importlib.import_module('example.contracts.aiig_profile_type_choice1_1')
    assert module.AIigProfileTypeChoice1_1.__closed_choice_mode__ == 'oneOf'
    branch = importlib.import_module('example.contracts.aiig_profile_type_choice1_alternative1_1')
    assert issubclass(branch.AIigProfileTypeChoice1Alternative1_1, module.AIigProfileTypeChoice1_1)
