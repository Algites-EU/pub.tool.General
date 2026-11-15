"""End-to-end local xs:key / xs:unique emission and deliberate unsupported cases."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import replace

import pytest

ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
LIB = ROOT.parent / 'pub.lib.General'
for suffix in ('generators/code/defscodegen/intf/src/product/python',
               'generators/code/defscodegen/impl/src/product/python',
               'generators/code/common/src/product/python'):
    sys.path.insert(0, str(ROOT / suffix))
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdKeyDefinition_1 as Key,
    AIcgdList_1 as ListNode,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcDefsCodegenCanonicalPipeline as Pipeline,
    AIcdDefsCodegenSourceDocument as Document,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIngSourceInputKind_1 as Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter as Emitter,
    AIcdDefsCodegenEmissionName as Names,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
    AIcDefsCodegenCanonicalSchemaFrontend as Frontend,
)
from test_canonical_source_emitter import _profile, _pipeline

XSD = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:t="urn:employees"
                     targetNamespace="urn:employees">
  <xs:complexType name="Employee"><xs:sequence>
    <xs:element name="department" type="xs:string"/>
    <xs:element name="identity"><xs:complexType><xs:sequence>
      <xs:element name="code" type="xs:string"/>
    </xs:sequence></xs:complexType></xs:element>
  </xs:sequence></xs:complexType>
  <xs:complexType name="Organization"><xs:sequence>
    <xs:element name="staff"><xs:complexType><xs:sequence>
      <xs:element name="employee" type="t:Employee" minOccurs="0" maxOccurs="unbounded"/>
    </xs:sequence></xs:complexType>
      <xs:key name="ByDepartmentAndCode"><xs:selector xpath="./employee"/>
        <xs:field xpath="department"/><xs:field xpath="./identity/code"/>
      </xs:key>
      <xs:unique name="UniqueDepartment"><xs:selector xpath="employee"/>
        <xs:field xpath="department"/>
      </xs:unique>
    </xs:element>
  </xs:sequence></xs:complexType>
</xs:schema>'''


def _emit(xml: str):
    """Use the real canonical parser/linker and external naming context."""
    profile = _profile()
    roots = Frontend(profile).load_xsd(xml, 'staff.xsd')
    linked = _pipeline().process((Document(Kind.XMLDEFS, 'staff.xsd', xml),))
    declarations = Emitter.declarations(linked.types)
    names = {node.identity: Names(f'AIigT{i}', f'AIigT{i}', f'aiig_t{i}')
             for i, node in enumerate(declarations)}
    return linked.types, Emitter(profile, names, 'test.output').render(linked.types), names


def test_composite_keys_from_real_xsd_compile_and_retain_sdo_metadata(tmp_path):
    """A/B XPath field paths become typed list signatures and runtime metadata."""
    types, emitted, names = _emit(XSD)
    assert len(types) == 2
    assert len(emitted) == 8
    java_sources = []
    for file in emitted:
        location = tmp_path / file.language / file.relative_path
        location.parent.mkdir(parents=True, exist_ok=True)
        location.write_text(file.content)
        if file.language == 'java':
            java_sources.append(str(location))
        else:
            compile(file.content, str(location), 'exec')
    java_code = '\n'.join(file.content for file in emitted if file.language == 'java')
    python_code = '\n'.join(file.content for file in emitted if file.language == 'python')
    assert 'AIiMultiMappedList<? extends AIigT' in java_code
    assert 'selector = "employee", fields = {CONSTOrganization.FIELD_NAME__DEPARTMENT, CONSTOrganization.FIELD_NAME__IDENTITY_CODE}, required = true' in java_code
    assert 'selector = "employee", fields = {CONSTOrganization.FIELD_NAME__DEPARTMENT}, required = false' in java_code
    assert "__scoped_key_definitions__ = {" in python_code
    assert 'KEY_ID__BY_DEPARTMENT_AND_CODE = "ByDepartmentAndCode"' in java_code
    assert 'KEY_ID__UNIQUE_DEPARTMENT = "UniqueDepartment"' in java_code
    assert 'name = CONSTOrganization.KEY_ID__BY_DEPARTMENT_AND_CODE' in java_code
    assert 'name = CONSTOrganization.KEY_ID__UNIQUE_DEPARTMENT' in java_code
    assert "KEY_ID__BY_DEPARTMENT_AND_CODE = 'ByDepartmentAndCode'" in python_code
    assert 'ByDepartmentAndCode' in python_code
    # Check the generated metadata resolves back to the exact original XSD strings.
    generated = next(file for file in emitted if file.language == 'python'
                     and 'KEY_ID__BY_DEPARTMENT_AND_CODE' in file.content)
    namespace = {'__name__': 'test.output.generated'}
    exec(generated.content, namespace)
    contract = next(value for name, value in namespace.items() if name.startswith('AIig'))
    assert contract.__scoped_key_definitions__['staff'] == (
        ('employee', 'ByDepartmentAndCode', ('department', 'identity.code'), True),
        ('employee', 'UniqueDepartment', ('department',), False))
    assert not hasattr(contract, '__key_definitions__')
    # Compile the source against the real Java annotation and key-list contracts.
    lib_root = LIB / 'common/util/src/product/java'
    meta_root = LIB / 'data/dataobject/intf/src/product/java'
    dependencies = [
        lib_root / 'eu/algites/lib/common/list/AIiMultiMappedList.java',
        lib_root / 'eu/algites/lib/common/list/AIiKeyDefinition.java',
        meta_root / 'eu/algites/lib/data/dataobject/AIaDataObjectListKeyDefinition.java',
        meta_root / 'eu/algites/lib/data/dataobject/AIaDataObjectListKeyDefinitions.java',
        meta_root / 'eu/algites/lib/data/dataobject/xmldefs/AIaDataObjectFieldXmlSchema.java',
        meta_root / 'eu/algites/lib/data/dataobject/xmldefs/AInXmlValueKind.java',
    ]
    compiled = subprocess.run(['javac', '-sourcepath', ':'.join(map(str, (LIB / 'data/dataobject/intf/src/product/java', LIB / 'common/util/src/product/java'))), '-d', str(tmp_path / 'classes'),
                               *java_sources, *map(str, dependencies)],
                              text=True, capture_output=True)
    assert compiled.returncode == 0, compiled.stderr


def test_unsupported_key_expressions_are_rejected_instead_of_miscompiled():
    """Do not turn namespace-qualified, descendant or predicate XPath into fake getters."""
    for path in ('a:b', './/code', 'employee[1]', 'a/*', '@department', 'a.b'):
        source = XSD.replace('xpath="department"', f'xpath="{path}"')
        with pytest.raises((NotImplementedError, ValueError), match='XPath|selector|resolver|path|attribute'):
            _emit(source)


def test_unresolved_or_global_xsd_keys_fail_closed():
    """Global element constraints remain unsupported by a named-type-only frontend."""
    xml = XSD.replace('<xs:complexType name="Organization">',
                      '<xs:complexType name="Organization">')
    xml = xml.replace('<xs:selector xpath="./employee"/>', '<xs:selector xpath="missing"/>')
    with pytest.raises(NotImplementedError, match='selector'):
        _emit(xml)
    global_schema = XSD.replace('</xs:schema>', '<xs:element name="Root">'
        '<xs:key name="Global"><xs:selector xpath="child"/><xs:field xpath="code"/>'
        '</xs:key></xs:element></xs:schema>')
    with pytest.raises(NotImplementedError, match='Global'):
        _emit(global_schema)


def test_indexed_list_requires_structured_named_items():
    """Keyed scalar collections cannot be indexed by SDO getter extraction."""
    from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
        AIcgdType_1 as Type, AIcgdElementList_1 as Group,
        AIcgdScalar_1 as Scalar, AIngScalarKind_1 as ScalarKind,
        AIngComposition_1 as Composition, AIngTypeOrigin_1 as Origin,
    )
    scalar = Type('urn:x', 'X', Origin.DECLARED, ('X',),
                  structure=Group(Composition.SEQUENCE, (ListNode('employee', Scalar(ScalarKind.STRING),
                      key_definitions=(Key('K', 'employee', '/schema/key', ('code',), True),)),)))
    with pytest.raises(NotImplementedError, match='named TYPE'):
        Emitter(_profile(), {'urn:x': Names('X', 'X', 'x')}, 'test.output').render((scalar,))


def test_rejected_missing_or_non_scalar_key_path():
    """Bad index paths cannot compile to a runtime index with missing getters."""
    with pytest.raises(ValueError, match='Unresolved.*field'):
        _emit(XSD.replace('xpath="./identity/code"', 'xpath="./identity/missing"'))
    with pytest.raises(NotImplementedError, match='typed scalar'):
        _emit(XSD.replace('xpath="./identity/code"', 'xpath="./identity"'))


def test_normalized_index_constant_collision_fails_closed():
    """Distinct XML identifiers must not overwrite a shared generated constant."""
    colliding = XSD.replace('name="UniqueDepartment"', 'name="By_DepartmentAndCode"')
    with pytest.raises(ValueError, match='Conflicting key or field constant'):
        _emit(colliding)


def test_xml_attribute_key_normalizes_to_typed_semantic_field(tmp_path):
    """An XSD @attribute key is indexed by its semantic getter, never by XML text."""
    source = XSD.replace(
        '  </xs:sequence></xs:complexType>\n  <xs:complexType name="Organization">',
        '  </xs:sequence><xs:attribute name="staffName" type="xs:string" use="required"/>'
        '</xs:complexType>\n  <xs:complexType name="Organization">')
    source = source.replace('<xs:field xpath="department"/>\n      </xs:unique>',
                            '<xs:field xpath="@staffName"/>\n      </xs:unique>')
    assert 'xpath="@staffName"' in source and 'name="staffName"' in source
    _, emitted, _ = _emit(source)
    java = '\n'.join(x.content for x in emitted if x.language == 'java')
    python = '\n'.join(x.content for x in emitted if x.language == 'python')
    assert 'FIELD_NAME__STAFF_NAME' in java
    indexed = next(item for item in emitted if item.language == 'python'
                   and 'KEY_ID__UNIQUE_DEPARTMENT' in item.content)
    namespace = {'__name__': 'test.output.generated'}
    exec(indexed.content, namespace)
    contract = next(value for name, value in namespace.items() if name.startswith('AIig'))
    assert ('employee', 'UniqueDepartment', ('staffName',), False) in contract.__scoped_key_definitions__['staff']
    bad = source.replace('xpath="@staffName"', 'xpath="@department"')
    with pytest.raises(ValueError, match='XPath attribute'):
        _emit(bad)
