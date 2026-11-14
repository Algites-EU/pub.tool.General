"""XML QName/attribute identity retained through the new seven-kind canonical model."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import replace

import jsonschema
import pytest

TOOL = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
LIB = TOOL.parent / 'pub.lib.General'
for rel in ('generators/code/common/src/product/python',
            'generators/code/defscodegen/intf/src/product/python',
            'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(TOOL / rel))

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdElement_1 as Element,
    AIcgdList_1 as ListNode,
    AIcgdXmlWireName_1 as Wire,
    AIngSourceInputKind_1 as Kind,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcdDefsCodegenSourceDocument as Document,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_model_merger import (
    AIcDefsCodegenCanonicalModelMerger as Merger,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_contract_payload import (
    AIcDefsCodegenCanonicalContractPayload as Payload,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter as Emitter,
    AIcdDefsCodegenEmissionName as Names,
)
from test_canonical_source_emitter import _profile, _pipeline

XSD = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    targetNamespace="urn:doc" elementFormDefault="qualified"
    attributeFormDefault="unqualified">
  <xs:complexType name="Doc"><xs:sequence>
    <xs:element name="Name" type="xs:string"/>
    <xs:element name="Line" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
    <xs:element name="Unqualified" form="unqualified" type="xs:integer"/>
  </xs:sequence>
  <xs:attribute name="code" type="xs:string" use="required"/>
  <xs:attribute name="flag" type="xs:boolean" form="qualified"/>
  </xs:complexType>
</xs:schema>'''


def _compiled(xml=XSD):
    result = _pipeline().process((Document(Kind.XMLDEFS, 'doc.xsd', xml),))
    names = {root.identity: Names('AIigDoc', 'AIigDoc', 'aiig_doc') for root in result.types}
    return result, Emitter(_profile(), names, 'test.output').render(result.types)


def test_xml_qname_and_attribute_forms_survive_canonical_contract_and_normalization():
    """Distinguish semantic field IDs, expanded QNames, form defaults, and original order."""
    result, sources = _compiled()
    fields = result.types[0].structure.children
    assert [node.name for node in fields] == ['Name', 'Line', 'Unqualified', 'code', 'flag']
    assert [node.xml_wire for node in fields] == [
        Wire('urn:doc', 'Name'), Wire('urn:doc', 'Line'),
        Wire('', 'Unqualified'), Wire('', 'code', 'ATTRIBUTE'),
        Wire('urn:doc', 'flag', 'ATTRIBUTE')]
    assert isinstance(fields[1], ListNode)
    assert all(isinstance(node, Element) for node in (fields[0], *fields[2:]))
    payload = Payload.emit(result.types)
    schema = (TOOL / 'generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool'
              '/codegen/defs/model/canonical-model_1.jsondef.schema.json')
    jsonschema.Draft202012Validator(json.loads(schema.read_text())).validate(payload)
    members = payload['types'][0]['content']['structure']['ElementList']['children']
    assert members[1]['List']['xml_wire']['namespace_uri'] == 'urn:doc'
    assert members[3]['Element']['xml_wire']['value_kind'] == 'ATTRIBUTE'
    merged = Merger.merge((result.types[0], result.types[0]))[0].structure.children
    assert [item.xml_wire for item in merged] == [item.xml_wire for item in fields]
    assert len(next(iter(merged[0].source_bindings.values()))) == 2


def test_generated_java_and_python_xml_field_metadata_matches_real_runtime(tmp_path):
    """Emit namespaced element/attribute annotations using real library contracts."""
    result, output = _compiled()
    java = next(item.content for item in output if item.language == 'java')
    python = next(item.content for item in output if item.language == 'python')
    assert 'namespace = "urn:doc", namespaceLocalName = "Name"' in java
    assert 'namespaceLocalName = "code", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ATTRIBUTE' in java
    assert 'minItemCount = 0, maxItemCount = -1' in java
    assert "'Unqualified': AIaXmlDataObjectField(namespace=''" in python
    assert "'flag': AIaXmlDataObjectField(namespace='urn:doc'" in python
    assert "__xml_repeated_fields__ = ('Line',)" in python
    modules = {}
    for item in output:
        path = tmp_path / item.language / item.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item.content)
        if item.language == 'python':
            compile(item.content, str(path), 'exec')
            exec(item.content, modules)
    cls = modules['AIigDoc']
    assert cls.__xml_data_object_fields__['code'].value_kind.name == 'ATTRIBUTE'
    assert cls.__xml_data_object_fields__['Name'].namespace == 'urn:doc'
    meta = LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs'
    build = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                            str(tmp_path / 'java/test/output/AIigDoc.java'),
                            str(meta / 'AIaXmlDataObjectField.java'),
                            str(meta / 'AInXmlValueKind.java')], capture_output=True, text=True)
    assert build.returncode == 0, build.stderr


def test_xml_qname_conflicts_cannot_be_merged():
    """Conflicting expanded QNames or field kinds are not equivalent declarations."""
    result, _ = _compiled()
    first = result.types[0]
    original = first.structure.children[3]
    for different_wire in (Wire('urn:doc', 'code', 'ATTRIBUTE'),
                           Wire('', 'code', 'ELEMENT'),
                           Wire('', 'different', 'ATTRIBUTE')):
        modified = replace(first, structure=replace(
            first.structure, children=tuple(
                replace(node, xml_wire=different_wire) if i == 3 else node
                for i, node in enumerate(first.structure.children))))
        with pytest.raises(ValueError, match='XML QName'):
            Merger.merge((first, modified))


def test_invalid_xml_form_defaults_fail_even_without_fields():
    """Reject malformed schema-level defaults on an otherwise empty complex type."""
    minimal = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" '
               '{attribute}="maybe"><xs:complexType name="Empty"/></xs:schema>')
    for attribute in ('elementFormDefault', 'attributeFormDefault'):
        with pytest.raises(ValueError, match='form default'):
            _compiled(minimal.format(attribute=attribute))


def test_unsupported_xml_forms_fail_instead_of_losing_qnames():
    """Invalid XSD forms/cardinality fail; attribute defaults survive as metadata."""
    with pytest.raises(ValueError, match='form default'):
        _compiled(XSD.replace('elementFormDefault="qualified"', 'elementFormDefault="unknown"'))
    with pytest.raises(ValueError, match='form'):
        _compiled(XSD.replace('form="qualified"', 'form="maybe"'))
    # XML attributes default on absence (not on explicit empty content).
    # This was once unsupported, but is now part of the agreed DataObject
    # default contract and must survive the canonical model and emitters.
    result, emitted = _compiled(XSD.replace('name="code" type="xs:string"',
                                            'name="code" default="abc" type="xs:string"'))
    code = result.types[0].structure.children[3]
    assert code.default_kind == 'IF_FIELD_VALUE_NOT_PRESENT'
    assert code.default_value == 'abc'
    assert any('IF_FIELD_VALUE_NOT_PRESENT' in item.content
               and 'abc' in item.content for item in emitted)
    with pytest.raises(ValueError, match='attributes'):
        Wire('urn:doc', 'attr', 'ATTRIBUTE') and replace(
            _compiled()[0].types[0].structure.children[3], max_item_count=2)



def test_numeric_xsd_fixed_is_emitted_as_typed_constraint_in_both_languages():
    """XSD fixed constrains assignments, not the effective value of an absent field."""
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Doc"><xs:sequence>
        <xs:element name="Count" type="xs:integer" fixed="1"/>
      </xs:sequence></xs:complexType>
    </xs:schema>'''
    result, emitted = _compiled(xsd)
    field = result.types[0].structure.children[0]
    assert field.default_kind == 'CONSTRAINT_DEFAULT'
    assert field.default_value == '1'
    assert not field.is_empty_allowed
    java = next(item.content for item in emitted if item.language == 'java')
    python = next(item.content for item in emitted if item.language == 'python')
    assert 'AInDataObjectFieldDefaultKind.CONSTRAINT_DEFAULT' in java
    assert 'value = "1"' in java
    assert 'AInDataObjectFieldDefaultKind.CONSTRAINT_DEFAULT' in python
    assert "value='1'" in python
    assert 'expected_type=int' in python


def test_attribute_only_xsd_type_is_emittable():
    """An attribute-only complexType must stay an ELEMENTLIST, not become an ELEMENT root."""
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Flags"><xs:attribute name="active" type="xs:boolean"/></xs:complexType>
    </xs:schema>'''
    result, source = _compiled(xsd)
    assert result.types[0].structure.children[0].xml_wire == Wire('', 'active', 'ATTRIBUTE')
    assert 'getActive()' in next(s.content for s in source if s.language == 'java')


def test_generated_python_xml_contract_drives_real_sdo_round_trip():
    """Inherited generated QName/attribute metadata is consumed by the XML SDO runtime."""
    from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
    from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject
    from eu.algites.lib.data.smartdataobject.impl.xmldefs.aic_xml_smart_data_object import AIcXmlSmartDataObject
    from eu.algites.lib.text.format.ais_text_format_profiles import AIsTextFormatProfiles

    _, output = _compiled()
    generated = next(item.content for item in output if item.language == 'python')
    namespace = {'__name__': 'test.output.generated'}
    exec(generated, namespace)
    contract = namespace['AIigDoc']
    field_types = {'Name': str, 'Line': list, 'Unqualified': int, 'code': str, 'flag': bool}
    members = {
        '__xml_data_object__': AIaXmlDataObject(namespace='urn:doc', namespace_local_name='Doc'),
    }
    # Supply only the concrete field storage. All QName, ordering, repetition and
    # occurrence metadata must come from the generated read-only Defs contract.
    for field in field_types:
        method = field[0].upper() + field[1:]
        members['get' + method] = lambda self, name=field: self.get_RawField(name)
        members['set' + method] = lambda self, value, name=field: self.set_RawField(name, value)
    concrete = type('Doc', (AIcXmlSmartDataObject, contract), members)
    xml = ('<d:Doc xmlns:d="urn:doc" code="AB" d:flag="true">'
           '<d:Name>Mia</d:Name><d:Line>A</d:Line><d:Line>B</d:Line>'
           '<Unqualified>5</Unqualified></d:Doc>')
    parsed = concrete.from_xml(xml)
    assert parsed.to_mapping() == {'code': 'AB', 'flag': True, 'Name': 'Mia',
                                   'Line': ['A', 'B'], 'Unqualified': 5}
    encoded = parsed.toString_RawValues(AIsTextFormatProfiles.XML_XSD)
    assert concrete.from_xml(encoded).to_mapping() == parsed.to_mapping()
    assert 'code="AB"' in encoded
    assert 'Unqualified>5</Unqualified>' in encoded
    assert 'Line>A</' in encoded
