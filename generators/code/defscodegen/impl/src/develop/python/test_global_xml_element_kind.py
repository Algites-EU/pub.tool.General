"""Root xs:element and local xs:key share the typed canonical collection model.

No JSONDEFS/YAMLDEFS declaration is required: XML-only ELEMENT contracts must
survive canonical normalization and both Java and Python source emitters.
"""
from __future__ import annotations

import pytest

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdList_1 as ListNode,
    AIngSourceInputKind_1 as Kind,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcdDefsCodegenSourceDocument as Document,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter as Emitter,
    AIcdDefsCodegenEmissionName as Names,
)
from test_canonical_source_emitter import _profile, _pipeline


def _xml(xpath='tns:Person'):
    return f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:person" targetNamespace="urn:person"
        elementFormDefault="qualified">
      <xs:complexType name="PersonType"><xs:attribute name="Id" type="xs:string" use="required"/></xs:complexType>
      <xs:element name="Persons"><xs:complexType><xs:sequence>
        <xs:element name="Person" type="tns:PersonType" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence></xs:complexType>
      <xs:key name="UniquePersonId"><xs:selector xpath="{xpath}"/>
        <xs:field xpath="@Id"/></xs:key>
      </xs:element>
    </xs:schema>'''


def _render(xml):
    linked = _pipeline().process((Document(Kind.XMLDEFS, 'people.xsd', xml),))
    names = {node.identity: Names('AIig' + node.name, 'AIig' + node.name,
                                   'aiig_' + node.name.lower())
             for node in linked.types}
    return linked, Emitter(_profile(), names, 'test.output').render(linked.types)


def test_root_element_is_typed_indexed_object_in_both_languages():
    linked, outputs = _render(_xml())
    root = next(node for node in linked.types if node.name == 'Persons')
    assert root.source_bindings[Kind.XMLDEFS][0].representation_kind == 'xs:element'
    indexed = root.structure.children[0]
    assert isinstance(indexed, ListNode)
    assert indexed.key_definitions[0].identifier == 'UniquePersonId'
    assert indexed.key_definitions[0].selector == 'Person'
    java = next(out.content for out in outputs if out.language == 'java' and 'Persons' in out.relative_path)
    python = next(out.content for out in outputs if out.language == 'python' and 'persons' in out.relative_path)
    assert 'AInXmlObjectDefinitionKind.ELEMENT' in java
    assert 'namespaceLocalName = "Persons"' in java
    assert 'getPersonList()' in java
    assert 'AIiMultiMappedList' in java
    assert 'AInXmlObjectDefinitionKind.ELEMENT' in python
    assert "namespace_local_name='Persons'" in python
    assert 'getPersonList' in python
    assert 'AIiMultiMappedList' in python
    assert 'wildcardNamespace' not in java
    assert 'wildcard_namespace' not in python
    assert 'AInXmlObjectDefinitionKind.TYPE' in next(o.content for o in outputs if o.language == 'java' and 'PersonType' in o.relative_path)


def test_key_selector_wrong_namespace_is_not_silently_accepted():
    with pytest.raises(ValueError, match='Unbound XSD key selector prefix'):
        _render(_xml('bad:Person'))


def test_element_and_named_type_same_name_have_distinct_symbols():
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:person" targetNamespace="urn:person">
       <xs:complexType name="Record"><xs:sequence>
          <xs:element name="Id" type="xs:string"/>
       </xs:sequence></xs:complexType>
       <xs:element name="Record" type="tns:Record"/>
    </xs:schema>'''
    linked, outputs = _render(xsd)
    assert {node.name for node in linked.types} == {'Record', 'RecordElement'}
    element_java = next(o.content for o in outputs if o.language == 'java' and 'RecordElement' in o.relative_path)
    assert 'AInXmlObjectDefinitionKind.ELEMENT' in element_java
    assert 'namespaceLocalName = "Record"' in element_java


def test_simple_root_is_not_falsely_emitted_as_dataobject():
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
     targetNamespace="urn:person"><xs:complexType name="Holder">
       <xs:sequence><xs:element name="Id" type="xs:string"/></xs:sequence>
     </xs:complexType><xs:element name="title" type="xs:string"/></xs:schema>'''
    linked, _ = _render(xsd)
    assert [node.name for node in linked.types] == ['Holder']
