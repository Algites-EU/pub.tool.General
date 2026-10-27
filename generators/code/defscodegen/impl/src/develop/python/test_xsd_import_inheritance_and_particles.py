"""Cross-source XML extension and lossless particle projection regressions."""
from pathlib import Path
import pytest

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend


def _request(path):
    return AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
        AIcAlgitesNamingProfiles.python_profile())


def test_external_complex_extension_retains_namespaces_and_base_qname(tmp_path):
    base = tmp_path / 'base_1.xsd'
    base.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:base" elementFormDefault="qualified" version="1">
      <xs:complexType name="Base"><xs:sequence><xs:element name="amount" type="xs:int"/></xs:sequence></xs:complexType>
    </xs:schema>''')
    derived = tmp_path / 'derived_1.xsd'
    derived.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:b="urn:base" targetNamespace="urn:derived" elementFormDefault="qualified" version="1">
      <xs:import namespace="urn:base" schemaLocation="base_1.xsd"/>
      <xs:complexType name="Derived"><xs:complexContent><xs:extension base="b:Base">
        <xs:sequence><xs:element name="code" type="xs:string"/></xs:sequence>
      </xs:extension></xs:complexContent></xs:complexType>
    </xs:schema>''')
    frontend = AIcXmlDefsFrontend()
    model = frontend.load(_request(derived))
    assert frontend.root_extension_base_qname(_request(derived)) == '{urn:base}Base'
    assert [(f.source_name, f.xml_field.namespace) for f in model.data_type.properties] == [
        ('amount', 'urn:base'), ('code', 'urn:derived')]


@pytest.mark.parametrize('fragment', [
    '<xs:sequence><xs:element name="x" type="xs:string" minOccurs="2" maxOccurs="1"/></xs:sequence>',
    '<xs:sequence><xs:group ref="other"/></xs:sequence>',
])
def test_unsafe_xml_particles_fail_closed(tmp_path, fragment):
    path = tmp_path / 'invalid_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
      <xs:complexType name="Invalid">''' + fragment + '''</xs:complexType>
    </xs:schema>''')
    with pytest.raises(ValueError, match='(compositor|occurrence interval|wildcard/group|Unknown XSD group)'):
        AIcXmlDefsFrontend().load(_request(path))


def test_external_extension_generates_true_java_and_python_parent(tmp_path):
    """An imported XSD base must be a real nominal parent, never copied getters."""
    import json
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
    from explicit_naming_fixture import explicit_legacy_generic_manifest
    source = tmp_path / 'intf/src/product/xmldefs/example/inherited'
    source.mkdir(parents=True)
    (source / 'base_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:base" elementFormDefault="qualified" version="1">
        <xs:complexType name="Base"><xs:sequence><xs:element name="amount" type="xs:int"/></xs:sequence></xs:complexType>
    </xs:schema>''')
    (source / 'derived_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:b="urn:base" targetNamespace="urn:derived" elementFormDefault="qualified" version="1">
        <xs:import namespace="urn:base" schemaLocation="base_1.xsd"/>
        <xs:complexType name="Derived"><xs:complexContent><xs:extension base="b:Base">
          <xs:sequence><xs:element name="code" type="xs:string"/></xs:sequence>
        </xs:extension></xs:complexContent></xs:complexType>
    </xs:schema>''')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({'artifact': 'intf', 'languages': ['java', 'python']})))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    jsource = (tmp_path / 'intf/src/product/java.gen/example/inherited/AIigDerived_1.java').read_text()
    assert 'extends example.inherited.AIigBase_1' in jsource
    assert 'String getCode' in jsource or 'String code' in jsource
    assert 'amount()' not in jsource
    psource = (tmp_path / 'intf/src/product/python.gen/example/inherited/aiig_derived_1.py').read_text()
    assert 'class AIigDerived_1(AIigBase_1, AIig_xnXmlDataObjectUrnDerived):' in psource
    assert 'from example.inherited.aiig_base_1 import AIigBase_1' in psource
    assert 'def getAmount' not in psource



def test_xsd_extension_without_emitted_base_is_not_silently_flattened(tmp_path):
    """The imported type must be part of the requested output, not just readable."""
    import json
    import os
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
    from explicit_naming_fixture import explicit_legacy_generic_manifest
    source = tmp_path / 'intf/src/product/xmldefs/example/derived'
    source.mkdir(parents=True)
    other = tmp_path / 'unpublished'
    other.mkdir()
    base = other / 'base_1.xsd'
    base.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:base" version="1"><xs:complexType name="Base"/></xs:schema>''')
    path = source / 'derived_1.xsd'
    relative_base = os.path.relpath(base, source)
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:b="urn:base" targetNamespace="urn:derived" version="1">
        <xs:import namespace="urn:base" schemaLocation="''' + relative_base + '''"/>
        <xs:complexType name="Derived"><xs:complexContent>
          <xs:extension base="b:Base"/>
        </xs:complexContent></xs:complexType>
    </xs:schema>''')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({'artifact': 'intf', 'languages': ['python']})))
    with pytest.raises(ValueError, match='no independently emitted contract'):
        AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
