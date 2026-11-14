"""Shared XSD named-list group semantics: Python frontend and Java parity contract."""
from pathlib import Path
import pytest

from test_canonical_schema_frontend import frontend
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
    AIcDefsCodegenCanonicalSchemaFrontend,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdElementList_1 as ElementList,
    AIcgdList_1 as ListNode,
    AIcgdType_1 as TypeNode,
)

XSD = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:coordinates" targetNamespace="urn:coordinates">
    <xs:group name="CoordinatesGroup">
      <xs:sequence>
        <xs:element name="X" type="xs:decimal"/>
        <xs:element name="Y" type="xs:decimal"/>
      </xs:sequence>
    </xs:group>
    <xs:group name="CoordinatesGroupList">
      <xs:sequence>
        <xs:group ref="tns:CoordinatesGroup"
                  minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:group>
    <xs:complexType name="Points">
      <xs:group ref="tns:CoordinatesGroupList"/>
    </xs:complexType>
</xs:schema>'''


def test_named_outer_group_is_list_not_extra_item_or_xml_wire():
    """A named wrapper chooses a getter name; inner group supplies item TYPE."""
    result = frontend().load_xsd(XSD, 'points.xsd')
    assert [node.name for node in result] == ['Points', 'CoordinatesGroup']
    points = next(node for node in result if node.name == 'Points')
    fields = points.structure.children
    assert len(fields) == 1
    item = fields[0]
    assert isinstance(item, ListNode)
    assert item.name == 'CoordinatesGroupList'
    assert (item.min_item_count, item.max_item_count) == (0, -1)
    assert item.xml_wire is None  # Neither xs:group declares a wrapper element.
    assert isinstance(item.item, TypeNode)
    assert item.item.identity == '{urn:coordinates}CoordinatesGroup'
    group = next(node for node in result if node.name == 'CoordinatesGroup')
    assert isinstance(group.structure, ElementList)
    assert [part.name for part in group.structure.children] == ['X', 'Y']


def test_undeclared_named_group_ref_is_diagnosed_with_location():
    broken = XSD.replace('ref="tns:CoordinatesGroupList"', 'ref="tns:MissingGroup"')
    with pytest.raises(NotImplementedError, match=r'points.xsd.*MissingGroup'):
        frontend().load_xsd(broken, 'points.xsd')


def test_java_and_python_frontends_own_identical_group_structural_contract():
    """Verify presence of corresponding group support in the two source frontends."""
    root = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
    java = (root / 'generators/code/defscodegen/impl/src/product/java/eu/algites/tool'
            '/codegen/defs/impl/standard/AIcDefsCodegenCanonicalSchemaFrontend.java').read_text()
    python = (root / 'generators/code/defscodegen/impl/src/product/python/eu/algites/tool'
              '/codegen/defs/impl/standard/canonical_schema_frontend.py').read_text()
    assert 'xmlNamedListGroup' in java and 'xmlGroupReference' in java
    assert '_xml_list_group' in python and '_xml_group_ref' in python
    assert 'AIngElementKind_1.EMBEDDED' in java and 'ElementKind.EMBEDDED' in python
