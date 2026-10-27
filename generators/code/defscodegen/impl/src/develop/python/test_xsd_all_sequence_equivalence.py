"""The canonical XML DataType does not distinguish xs:all from xs:sequence."""

import pytest

from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend


def _source(tmp_path, compositor, content):
    path = tmp_path / ('composition_' + compositor + '_1.xsd')
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:compositors" targetNamespace="urn:compositors"
        elementFormDefault="qualified" version="1">
        <xs:complexType name="Base"><xs:''' + compositor + '''>
        <xs:element name="first" type="xs:string"/>
        <xs:element name="second" type="xs:int" minOccurs="0"/>
        </xs:''' + compositor + '''></xs:complexType>''' + content + '''</xs:schema>''')
    return path


def _load(path, name):
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
                                       AIcAlgitesNamingProfiles.python_profile())
    return AIcXmlDefsFrontend().load_named_type(request, name).data_type


def test_all_and_sequence_produce_identical_canonical_properties(tmp_path):
    ordered = _load(_source(tmp_path, 'sequence', ''), 'Base')
    unordered = _load(_source(tmp_path, 'all', ''), 'Base')
    assert ordered == unordered
    assert [field.source_name for field in ordered.properties] == ['first', 'second']
    assert ordered.properties[0].presence is AInFieldPresenceKind.REQUIRED
    assert ordered.properties[1].presence is AInFieldPresenceKind.ALLOWED


@pytest.mark.parametrize('base_group,restricted_group', [
    ('sequence', 'sequence'), ('all', 'all'), ('all', 'sequence'), ('sequence', 'all')])
def test_flat_restriction_uses_same_rules_for_both_compositors(tmp_path, base_group, restricted_group):
    derived = '''<xs:complexType name="Derived"><xs:complexContent>
        <xs:restriction base="tns:Base"><xs:''' + restricted_group + '''>
        <xs:element name="first" type="xs:string"/>
        </xs:''' + restricted_group + '''></xs:restriction>
        </xs:complexContent></xs:complexType>'''
    fields = _load(_source(tmp_path, base_group, derived), 'Derived').properties
    assert [field.source_name for field in fields] == ['first', 'second']
    assert fields[1].presence is AInFieldPresenceKind.FORBIDDEN
