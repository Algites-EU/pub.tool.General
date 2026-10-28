"""Named local XSD complex types retain nominal getters and compatible common inheritance."""

from pathlib import Path
import shutil

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


def test_xml_local_named_complex_type_is_a_reference_not_opaque_map(tmp_path):
    """A local named complex type should resolve as a generated nominal type."""
    xsd = tmp_path / 'items_1.xsd'
    xsd.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
            xmlns:tns="urn:items" targetNamespace="urn:items" version="1">
        <xs:complexType name="ItemType"><xs:sequence>
            <xs:element name="code" type="xs:string"/>
        </xs:sequence></xs:complexType>
        <xs:complexType name="ItemsType"><xs:sequence>
            <xs:element name="items" type="tns:ItemType" maxOccurs="unbounded"/>
        </xs:sequence></xs:complexType>
        <xs:element name="items-document" type="tns:ItemsType"/>
    </xs:schema>''', encoding='utf-8')
    frontend = AIcXmlDefsFrontend()
    request = AIcdDefinitionLoadRequest(xsd, AInDefinitionSourceKind.XMLDEFS,
        AIcAlgitesNamingProfiles.python_profile())
    definition = frontend.load(request)
    items = next(f for f in definition.data_type.properties if f.source_name == 'items')
    assert items.data_type.kind is AInDataTypeKind.ARRAY
    item = items.data_type.element_type
    assert item.kind is AInDataTypeKind.REFERENCE
    assert item.reference.identity == '#@type/ItemType'
    assert item.reference.logical_name == 'item-type'
    assert item.reference.target_data_type.kind is AInDataTypeKind.OBJECT


def test_three_formats_keep_typed_common_and_named_xml_items(tmp_path):
    """XML `bindings` and JSON/YAML inline items can narrow the same common getter."""
    repository = Path(__file__).resolve().parents[7]
    source = repository / 'generators/code/defscodegen/intf/src/product'
    destination = tmp_path / 'intf/src/product'
    stem = 'eu/algites/tool/codegen/defs/schema-field-bindings_1'
    for kind, suffix in [('jsondefs', '.jsondef.schema.json'),
                         ('yamldefs', '.yamldef.schema.json'), ('xmldefs', '.xsd')]:
        target = destination / kind / (stem + suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / kind / (stem + suffix), target)
    profiles = {'java': 'algites-java', 'python': 'algites-python'}
    manifest = {
        'artifact': 'intf', 'languages': ['java', 'python'],
        'schema_inputs': [{'kind': kind, 'directory': f'intf/src/product/{kind}'}
                          for kind in ['jsondefs', 'yamldefs', 'xmldefs']],
        'schema_input_naming_conventions': {
            'jsondefs': 'algites-jsondef-schema-versioned_1',
            'yamldefs': 'algites-yamldef-schema-versioned_1',
            'xmldefs': 'algites-xmldef-schema-versioned_1',
        },
        'technology_outputs': {kind: f'intf/src/product/{kind}.gen' for kind in profiles},
        'technology_output_naming_conventions': {
            language: {
                'common': f'{prefix}-gen-intf-versioned_1',
                'jsondefs': f'{prefix}-gen-json-intf-versioned_1',
                'yamldefs': f'{prefix}-gen-yaml-intf-versioned_1',
                'xmldefs_type': f'{prefix}-gen-xml-type-intf-versioned_1',
                'xmldefs_element': f'{prefix}-gen-xml-element-intf-versioned_1',
                'xmldefs_namespace': f'{prefix}-gen-xml-namespace-intf_1',
            } for language, prefix in profiles.items()},
        'technology_enum_output_naming_conventions': {
            lang: f'{prefix}-gen-enum-versioned_1' for lang, prefix in profiles.items()},
        'generated_dataobject_method_naming_conventions': {
            lang: f'{prefix}-codegen-standard_1' for lang, prefix in profiles.items()},
        'naming_convention_files': ['resource:' + name for name in (
            'standard-conventions.yml', 'algites-java-name-conventions.yml',
            'algites-python-name-conventions.yml', 'algites-jsondef-name-conventions.yml',
            'algites-yamldef-name-conventions.yml', 'algites-xmldef-name-conventions.yml',
            'algites-java-codegen-method-conventions.yml',
            'algites-python-codegen-method-conventions.yml')],
    }
    AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, manifest)
    output = destination / 'java.gen/eu/algites/tool/codegen/defs'
    parent = (output / 'AIigSchemaFieldBindings_1.java').read_text()
    xml_root = (output / 'AIig_xSchemaFieldBindings_1.java').read_text()
    xml_item = (output / 'AIig_xFieldBindingType_1.java').read_text()
    assert 'List<? extends AIigSchemaFieldBindingsBindingsItems_1> getBindings()' in parent
    assert 'List<? extends AIig_xFieldBindingType_1> getBindings()' in xml_root
    assert 'AIigSchemaFieldBindingsBindingsItems_1' in xml_item
    assert 'Map<String, Object> getBindings()' not in xml_root
    for prefix in ('j', 'y'):
        child = (output / f'AIig_{prefix}SchemaFieldBindings_1.java').read_text()
        assert f'AIig_{prefix}SchemaFieldBindingsBindingsItems_1> getBindings()' in child
    py_output = destination / 'python.gen/eu/algites/tool/codegen/defs'
    py_xml_item = (py_output / 'aiig__x_field_binding_type_1.py').read_text()
    assert 'AIigSchemaFieldBindingsBindingsItems_1' in py_xml_item
