"""XML xs:any is typed by namespace-specific interfaces, never a scalar fragment."""
from __future__ import annotations
import importlib
import json
from pathlib import Path
import re

import pytest

from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
from explicit_naming_fixture import explicit_legacy_generic_manifest


def _build(tmp_path: Path, constraint: str):
    xml_dir = tmp_path / 'src/product/xmldefs/example/contracts'
    xml_dir.mkdir(parents=True)
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:tns="urn:builder:technology" targetNamespace="urn:builder:technology"
      elementFormDefault="qualified" version="1">
      <xs:complexType name="ExtensionsType"><xs:sequence>
        <xs:any namespace="''' + constraint + '''" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence></xs:complexType>
      <xs:element name="Extensions" type="tns:ExtensionsType"/>
    </xs:schema>'''
    (xml_dir / 'extensions_1.xsd').write_text(schema)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({'artifact': '.', 'languages': ['java', 'python']})))
    result = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    return result, (tmp_path / 'src/product/java.gen/example/contracts'), (tmp_path / 'src/product/python.gen/example/contracts')


@pytest.mark.parametrize('constraint,namespace_interface', [
    ('##targetNamespace', 'AIig_xnXmlDataObjectUrnBuilderTechnology'),
    ('urn:external:plugin', 'AIig_xnXmlDataObjectUrnExternalPlugin'),
    ('##any', 'AIiXmlDataObject'),
    ('##other', 'AIiXmlDataObject'),
    ('##local', 'AIiXmlDataObject'),
])
def test_xsd_any_contract_signatures_and_xml_marker_inheritance(tmp_path, monkeypatch, constraint, namespace_interface):
    generated, java, python = _build(tmp_path, constraint)
    java_contract = (java / 'AIigExtensions_1.java').read_text()
    python_contract = (python / 'aiig_extensions_1.py').read_text()
    expected = 'java.util.List<? extends ' + (
        'eu.algites.lib.data.dataobject.xmldefs.' if namespace_interface == 'AIiXmlDataObject'
        else 'example.contracts.') + namespace_interface + '>'
    assert expected in java_contract
    assert 'java.util.List<String>' not in java_contract
    assert 'tuple[' + namespace_interface + ', ...]' in python_contract
    java_marker = java / 'AIig_xnXmlDataObjectUrnBuilderTechnology.java'
    assert java_marker.exists()
    assert 'extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObjectNamespace' in java_marker.read_text()
    assert 'namespace = "urn:builder:technology"' in java_marker.read_text()
    assert 'AIig_xnXmlDataObjectUrnBuilderTechnology' in java_contract
    assert 'AIig_xnXmlDataObjectUrnBuilderTechnology' in (
        java / 'AIig_xeExtensions_1.java').read_text()
    assert (python / 'aiig__xn_xml_data_object_urn_builder_technology.py').is_file()
    monkeypatch.syspath_prepend(str(tmp_path / 'src/product/python.gen'))
    module = importlib.import_module('example.contracts.aiig_extensions_1')
    assert issubclass(module.AIigExtensions_1,
        importlib.import_module('example.contracts.aiig__xn_xml_data_object_urn_builder_technology')
            .AIig_xnXmlDataObjectUrnBuilderTechnology)
    assert len([r for r in generated if r['pointer'].startswith('@namespace/')]) == (
        4 if constraint == 'urn:external:plugin' else 2)

@pytest.mark.parametrize('language', ['java', 'python'])
def test_namespace_naming_role_is_independent_from_xml_element_naming(language, tmp_path):
    """Explicit namespace naming ID must control the type/file, not XML element naming."""
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
    from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
    from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
    from eu.algites.tool.codegen.defs.impl.standard.aic_selected_naming_catalog import AIcSelectedNamingCatalog
    from eu.algites.tool.codegen.defs.impl.standard import aic_xml_namespace_contracts
    from eu.algites.tool.codegen.defs.impl.standard.aic_xml_namespace_contracts import namespace_contract

    catalog = AIcNameConventionCatalog.load_resource(f'algites-{language}-name-conventions.yml')
    namespace_id = f'algites-{language}-gen-data-xml-namespace-intf_1'
    element_id = f'algites-{language}-gen-xml-element-intf-versioned_1'
    roles = {
        AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE: namespace_id,
        AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM: namespace_id,
        AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE: element_id,
        AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM: element_id,
    }
    from types import SimpleNamespace
    request = SimpleNamespace(naming_profile=AIcSelectedNamingCatalog(catalog, roles),
        target=AInCodeGenerationTarget(language), package_name='example.contracts',
        definition=SimpleNamespace(version=1))
    name, stem, module = namespace_contract(request, 'urn:builder:technology')
    assert name == 'AIigd_xnXmlDataObjectUrnBuilderTechnology'
    assert stem == (name if language == 'java' else 'aiigd__xn_xml_data_object_urn_builder_technology')
    assert module == 'example.contracts.' + stem
    assert catalog.format(element_id, 'main_container_name', {'identifier': 'invoice', 'version': '1'},
        'lower_kebab_case_1') == 'AIig_xeInvoice_1'
    # The namespace contract uses the selected namespace convention rather than
    # an XML element prefix, and does not acquire the version suffix of the element.
    source = aic_xml_namespace_contracts.source(request, 'urn:builder:technology')[2]
    assert name in source
    assert '_xe' not in source
    assert '_1' not in name


def test_batch_naming_role_override_reaches_namespace_and_wildcard_types(tmp_path):
    """CLI-style role selection must affect every generated reference, in both languages."""
    root = tmp_path / 'src/product/xmldefs/example/contracts'
    root.mkdir(parents=True)
    (root / 'extensions_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
       xmlns:tns="urn:builder:technology" targetNamespace="urn:builder:technology"
       version="1"><xs:complexType name="ExtensionsType"><xs:sequence>
       <xs:any namespace="##targetNamespace" minOccurs="0" maxOccurs="unbounded"/>
       </xs:sequence></xs:complexType>
       <xs:element name="Extensions" type="tns:ExtensionsType"/>
       </xs:schema>''', encoding='utf-8')
    outputs = {language: {
        'xmldefs_type': f'algites-{language}-gen-xml-type-intf-versioned_1',
        'xmldefs_element': f'algites-{language}-gen-xml-element-intf-versioned_1',
        'xmldefs_namespace': f'algites-{language}-gen-data-xml-namespace-intf_1',
    } for language in ('java', 'python')}
    catalog_files = [f'resource:{name}' for name in (
        'standard-conventions.yml', 'algites-java-name-conventions.yml',
        'algites-python-name-conventions.yml', 'algites-xmldef-name-conventions.yml')]
    manifest = {
        'artifact': '.',
        'schema_inputs': [{'kind': 'xmldefs', 'directory': 'src/product/xmldefs'}],
        'schema_input_naming_conventions': {'xmldefs': 'algites-xmldef-schema-versioned_1'},
        'technology_outputs': {'java': 'src/product/java.gen', 'python': 'src/product/python.gen'},
        'technology_output_naming_conventions': outputs,
        'naming_convention_files': catalog_files,
        'languages': ['java', 'python'],
    }
    generated = AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, manifest)
    for language in ('java', 'python'):
        output = tmp_path / f'src/product/{language}.gen/example/contracts'
        suffix = ('AIigd_xnXmlDataObjectUrnBuilderTechnology.java' if language == 'java'
                  else 'aiigd__xn_xml_data_object_urn_builder_technology.py')
        assert (output / suffix).is_file()
        contents = '\n'.join(p.read_text() for p in output.iterdir() if p.is_file())
        assert 'AIigd_xnXmlDataObjectUrnBuilderTechnology' in contents
        assert 'AIig_xeExtensions_1' in contents
        assert not any(p.name.startswith('AIig_xnXmlDataObject')
                       or p.name.startswith('aiig__xn_xml_data_object') for p in output.iterdir())
        assert any(item['pointer'].startswith('@namespace/') and suffix in item['path']
                   for item in generated if item['language'] == language)

@pytest.mark.parametrize('language', ['java', 'python'])
def test_xml_namespace_fixed_name_parts_come_from_catalog_not_generator(language):
    """A custom XML namespace composition can omit XmlDataObject without changing codegen."""
    from copy import deepcopy
    from types import SimpleNamespace
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
    from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
    from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
    from eu.algites.tool.codegen.defs.impl.standard.aic_selected_naming_catalog import AIcSelectedNamingCatalog
    from eu.algites.tool.codegen.defs.impl.standard.aic_xml_namespace_contracts import namespace_contract

    original = AIcNameConventionCatalog.load_resource(f'algites-{language}-name-conventions.yml')
    configuration = deepcopy(original._config)
    prefix = f'algites-{language}-gen-xml-namespace-intf'
    for suffix in ('_1', '-file_1'):
        segments = configuration['NameCompositions'][prefix + suffix]['Segments']
        segments[:] = [segment for segment in segments if segment.get('Ref') not in
                       ('xml-data-object-marker_1', 'xml-data-object-file-marker_1')]
    custom = AIcNameConventionCatalog(configuration)
    roles = {
        AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE: prefix + '_1',
        AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM: prefix + '_1',
    }
    request = SimpleNamespace(naming_profile=AIcSelectedNamingCatalog(custom, roles),
        target=AInCodeGenerationTarget(language), package_name='example.contracts')
    type_name, stem, _ = namespace_contract(request, 'urn:builder:technology')
    assert type_name == 'AIig_xnUrnBuilderTechnology'
    assert stem == ('AIig_xnUrnBuilderTechnology' if language == 'java'
                    else 'aiig__xn_urn_builder_technology')
