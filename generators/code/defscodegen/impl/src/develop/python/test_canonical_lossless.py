"""Reject schema constructs until their meaning is representable without loss."""
import sys
from pathlib import Path
import pytest

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
for entry in ('generators/code/common/src/product/python',
              'generators/code/defscodegen/intf/src/product/python',
              'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(TOOL / entry))

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIigSourceInputKind_1 as Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
    AIcDefsCodegenCanonicalSchemaFrontend,
)
from eu.algites.tool.codegen.common.naming_profiles import AIcdCodegenNamingProfile


def frontend():
    return AIcDefsCodegenCanonicalSchemaFrontend(AIcdCodegenNamingProfile(
        'test', {'standard_getter': 'unused', 'standard_setter': 'unused'}, {}, {}, {}, 1, {}))


@pytest.mark.parametrize('keyword,value', [('minLength', 3), ('pattern', '^[A-Z]$'),
    ('minimum', 0), ('multipleOf', 2), ('uniqueItems', True), ('minProperties', 2),
    ('dependentRequired', {'a': ['b']}), ('readOnly', True)])
@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
def test_semantic_constraints_rejected_instead_of_becoming_any(kind, keyword, value):
    with pytest.raises(NotImplementedError, match='Unsupported schema keywords'):
        frontend().load_json_or_yaml({'type': 'string', keyword: value}, 'schema.json', kind)


@pytest.mark.parametrize('node,diagnostic', [
    ('<xs:simpleType name="Tokens"><xs:list itemType="xs:string"/></xs:simpleType>', 'simpleType'),
    ('<xs:simpleType name="Union"><xs:union memberTypes="xs:string xs:int"/></xs:simpleType>', 'simpleType'),
    ('<xs:complexType name="Group"><xs:sequence><xs:any/></xs:sequence></xs:complexType>', 'group child'),
    ('<xs:complexType name="Doc"><xs:sequence><xs:element name="Code" type="xs:string" nillable="true"/></xs:sequence></xs:complexType>', 'facet'),
    ('''<xs:complexType name="Doc"><xs:sequence><xs:element name="Code" type="xs:string">
        <xs:key name="k"><xs:selector xpath="."/><xs:field xpath="@id"/></xs:key>
       </xs:element></xs:sequence></xs:complexType>''', 'Local XSD keys'),
])
def test_unsupported_xml_contract_is_rejected(node, diagnostic):
    xml = '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">' + node + '</xs:schema>'
    with pytest.raises(NotImplementedError, match=diagnostic):
        frontend().load_xsd(xml, 'source.xsd')
