"""Imported named XSD types retain identity under occurrence-scoped indexes.

The xs:key belongs to the referencing element, not a synthesized or copied
DataObject TYPE. Each use of the shared type may have its own local indexes.
"""
from test_canonical_schema_frontend import frontend
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
    AIcDefsCodegenCanonicalSchemaFrontend,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdType_1 as TypeNode,
)

XS = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:common="urn:common" targetNamespace="urn:common">
    <xs:complexType name="Entries"><xs:sequence>
      <xs:element name="Entry" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType><xs:attribute name="name" type="xs:string"/></xs:complexType>
      </xs:element>
    </xs:sequence></xs:complexType>
</xs:schema>'''
LOCAL = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:common="urn:common" targetNamespace="urn:local">
    <xs:import namespace="urn:common" schemaLocation="common.xsd"/>
    <xs:complexType name="Root"><xs:sequence>
       <xs:element name="Entries" type="common:Entries">
          <xs:key name="ByName"><xs:selector xpath="Entry"/><xs:field xpath="@name"/></xs:key>
       </xs:element>
    </xs:sequence></xs:complexType>
</xs:schema>'''


def test_imported_key_keeps_original_nominal_type_and_scoped_index():
    base = frontend()
    loader = AIcDefsCodegenCanonicalSchemaFrontend(
        base.naming, external_xsd_types=frozenset({'{urn:common}Entries'}),
        external_xsd_documents={'common.xsd': XS.encode()})
    root = loader.load_xsd(LOCAL, 'local.xsd')[0]
    field = root.structure.children[0]
    assert isinstance(field.structure, TypeNode)
    assert field.structure.identity == '{urn:common}Entries'
    assert field.structure.structure is None
    assert field.key_definitions[0].identifier == 'ByName'
    assert field.key_definitions[0].selector == 'Entry'
    assert field.key_definitions[0].fields == ('@name',)
    # No synthetic TYPE, and no mutation of the imported declaration.
    assert len(loader.load_xsd(LOCAL, 'local.xsd')) == 1
    imported = loader.load_xsd(XS, 'common.xsd')
    assert len(imported) == 1
    assert imported[0].identity == '{urn:common}Entries'
    assert imported[0].structure.children[0].key_definitions == ()


def test_same_nominal_type_two_occurrences_have_independent_constraints():
    loader = AIcDefsCodegenCanonicalSchemaFrontend(
        frontend().naming, external_xsd_types=frozenset({'{urn:common}Entries'}),
        external_xsd_documents={'common.xsd': XS.encode()})
    second = LOCAL.replace('''       </xs:element>''', '''       </xs:element>
       <xs:element name="Other" type="common:Entries"/>''')
    root = loader.load_xsd(second, 'local.xsd')[0]
    selected, unselected = root.structure.children
    assert selected.structure.identity == unselected.structure.identity
    assert len(selected.key_definitions) == 1
    assert unselected.key_definitions == ()


def test_real_naming_conventions_import_retains_scoped_keys_and_original_type():
    """Parse/link both published naming XSDs without cloning common:IdentifierConventions."""
    import json
    from pathlib import Path
    from xml.etree import ElementTree as ET
    from test_canonical_source_emitter import _profile
    from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
        AIcDefsCodegenCanonicalPipeline as Pipeline,
        AIcdDefsCodegenSourceDocument as SourceDocument,
    )
    from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
        AIngSourceInputKind_1 as SourceKind,
    )

    tool = next(parent for parent in Path(__file__).resolve().parents
                if parent.name == 'pub.tool.General')
    lib = tool.parent / 'pub.lib.General'
    source_dir = lib / 'naming/convention/intf/src/product/xmldefs/eu/algites/lib/naming/convention'
    common_source = source_dir / 'common-naming-conventions_1.xsd'
    standard_source = source_dir / 'standard-conventions_1.xsd'
    common_xml = common_source.read_text()
    standard_xml = standard_source.read_text()
    common_root = ET.fromstring(common_xml)
    common_namespace = common_root.get('targetNamespace')
    common_ids = frozenset('{' + common_namespace + '}' + child.get('name')
        for child in common_root
        if child.tag == '{http://www.w3.org/2001/XMLSchema}complexType'
        and child.get('name'))
    schema_path = tool / ('generators/code/defscodegen/intf/src/product/jsondefs/'
        'eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')
    processor = Pipeline(_profile(), json.loads(schema_path.read_text()),
        external_xsd_types=common_ids,
        external_xsd_documents={str(common_source): common_xml.encode()})
    result = processor.process((
        SourceDocument(SourceKind.XMLDEFS, str(common_source), common_xml),
        SourceDocument(SourceKind.XMLDEFS, str(standard_source), standard_xml),
    ))
    lookup = {node.identity: node for node in result.types}
    identity = '{' + common_namespace + '}IdentifierConventions'
    shared = lookup[identity]
    standard = next(node for node in result.types if node.name == 'StandardConventions')
    common_owner = next(node for node in result.types if node.name == 'CommonNamingConventions')
    reference_in_standard = next(child for child in standard.structure.children
                                 if child.name == 'IdentifierConventions')
    reference_in_common = next(child for child in common_owner.structure.children
                               if child.name == 'IdentifierConventions')
    assert reference_in_standard.structure.identity == identity
    assert reference_in_common.structure.identity == identity
    assert len(reference_in_standard.key_definitions) == 1
    assert len(reference_in_common.key_definitions) == 1
    assert reference_in_standard.key_definitions[0].selector == 'IdentifierConvention'
    assert reference_in_common.key_definitions[0].selector == 'IdentifierConvention'
    assert shared.structure.children[0].key_definitions == ()
    assert not any('#synthetic:' in node.identity and 'IdentifierConventions' in node.name
                   for node in result.types)
