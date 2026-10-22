"""Regressions for independently scoped no-targetNamespace XML documents."""
from __future__ import annotations

from importlib import import_module
from pathlib import Path

from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import (
    AIcSchemaContractBindingsGenerator,
)


def _schema(root: Path, stem: str, field: str, namespace: str = '') -> None:
    """Create independently valid XSDs that intentionally reuse XML QNames."""
    folder = root / 'src/product/xmldefs/example/modustro'
    folder.mkdir(parents=True, exist_ok=True)
    ns = f' targetNamespace="{namespace}"' if namespace else ''
    (folder / (stem + '_1.xsd')).write_text(f"""<xs:schema
        xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1"{ns}>
        <xs:complexType name="DocumentContentType"><xs:sequence>
            <xs:element name="Enabled" type="xs:boolean"/>
            <xs:element name="{field}" type="xs:string"/>
        </xs:sequence></xs:complexType>
        <xs:element name="CapabilityConfiguration" type="DocumentContentType"/>
    </xs:schema>""", encoding='utf-8')


def _options(languages=('python',)):
    """Use the actual Algites output profiles for every tested language."""
    return {'artifact': '.', 'schema_inputs': [
        {'kind': 'xmldefs', 'directory': 'src/product/xmldefs'}],
        'schema_input_naming_conventions': {
            'xmldefs': 'algites-xmldef-schema-versioned_1'},
        'technology_outputs': {lang: 'src/product/' + lang + '.gen' for lang in languages},
        'technology_output_naming_conventions': {lang: {
            'common': f'algites-{lang}-gen-intf-versioned_1',
            'xmldefs_type': f'algites-{lang}-gen-xml-type-intf-versioned_1',
            'xmldefs_element': f'algites-{lang}-gen-xml-element-intf-versioned_1',
            'xmldefs_namespace': f'algites-{lang}-gen-xml-namespace-intf_1'}
            for lang in languages},
        'naming_convention_files': [f'resource:{name}' for name in (
            'standard-conventions.yml', 'algites-python-name-conventions.yml',
            'algites-java-name-conventions.yml', 'algites-xmldef-name-conventions.yml')],
        'languages': list(languages)}


def test_duplicate_anonymous_xml_qnames_generate_separate_contracts_and_import(tmp_path, monkeypatch):
    """Three distinct XSDs sharing a package and XML local names must not alias."""
    documents = {'docs-site-content': 'Javadoc',
        'publication-of-docs-site': 'PublicationDestinations',
        'publication-of-global-schemas': 'SourceKinds'}
    for stem, own_field in documents.items():
        _schema(tmp_path, stem, own_field)
    outputs = AIcSchemaContractBindingsGenerator().generate_manifest(
        tmp_path, _options(('python', 'java')))
    element_outputs = [item for item in outputs if item['pointer'].startswith('@element/')]
    assert len(element_outputs) == 6
    for stem, own_field in documents.items():
        scoped_package = 'xmlschema_' + stem.replace('-', '_') + '_1'
        for lang, ext, element_name in (
            ('java', 'java', 'AIig_xeCapabilityConfiguration_1'),
            ('python', 'py', 'aiig__xe_capability_configuration_1')):
            root = tmp_path / 'src/product' / (lang + '.gen') / 'example/modustro'
            special = root / scoped_package
            element_file = special / f'{element_name}.{ext}'
            assert element_file.is_file()
            own_contracts = [path.read_text(encoding='utf-8') for path in special.glob('*.' + ext)]
            assert any(own_field in source for source in own_contracts)
            for unrelated in set(documents.values()) - {own_field}:
                assert all(unrelated not in source for source in own_contracts)
            # Cross-format common contracts remain in the original package.
            assert (root / ('AIigDocsSiteContent_1.java' if lang == 'java'
                else 'aiig_docs_site_content_1.py')).is_file()
    monkeypatch.syspath_prepend(str(tmp_path / 'src/product/python.gen'))
    classes = []
    for stem in documents:
        scoped_package = 'xmlschema_' + stem.replace('-', '_') + '_1'
        mod = import_module('example.modustro.' + scoped_package
            + '.aiig__xe_capability_configuration_1')
        marker = import_module('example.modustro.' + scoped_package
            + '.aiig__xn_xml_data_object_local').AIig_xnXmlDataObjectLocal
        assert issubclass(mod.AIig_xeCapabilityConfiguration_1, marker)
        type_module = import_module('example.modustro.' + scoped_package
            + '.aiig__x_' + stem.replace('-', '_') + '_1')
        assert issubclass(getattr(type_module, 'AIig_x' + ''.join(part.title()
            for part in stem.split('-')) + '_1'), marker)
        classes.append(mod.AIig_xeCapabilityConfiguration_1)
    assert len(set(classes)) == 3
    assert AIcSchemaContractBindingsGenerator().generate_manifest(
        tmp_path, _options(('python', 'java')), check=True) == outputs


def test_unique_anonymous_xml_qname_keeps_legacy_package(tmp_path):
    """An unambiguous no-namespace XML type must not need a new package."""
    _schema(tmp_path, 'docs-site-content', 'EnabledDescription')
    AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, _options())
    generated = tmp_path / 'src/product/python.gen/example/modustro'
    assert (generated / 'aiig__xe_capability_configuration_1.py').exists()
    assert not list(generated.glob('xmlschema_*'))
