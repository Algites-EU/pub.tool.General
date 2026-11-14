"""Integration checks for the independent source-to-canonical frontends."""
import sys
from pathlib import Path
import yaml
import pytest

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
for path in (TOOL / 'generators/code/common/src/product/python',
             TOOL / 'generators/code/defscodegen/intf/src/product/python',
             TOOL / 'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(path))

from eu.algites.tool.codegen.common.naming_profiles import resolve_codegen_naming_profiles
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIngStructureKind_1 as Kind, AIngMapKind_1 as MapKind,
    AIngComposition_1 as Composition, AIngSourceInputKind_1 as SourceKind,
    AIngResolutionState_1 as Resolution, AIngTypeOrigin_1 as Origin)
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import AIcDefsCodegenCanonicalSchemaFrontend


def frontend():
    config = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
    c = yaml.safe_load((config/'algites-java-common-codegen-conventions.yml').read_text())
    d = yaml.safe_load((config/'algites-java-defs-codegen-conventions.yml').read_text())
    return AIcDefsCodegenCanonicalSchemaFrontend(resolve_codegen_naming_profiles(c,
        'algites-java-codegen-common_1', d, 'algites-java-defscodegen-standard_1'))


class TestSchemaFrontendSemantics:
    """Functional tests grouped by the business contract, not a snapshot number."""

    @staticmethod
    @pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
    def test_object_fields_integrated_map_and_precise_source_binding(kind):
        source = {'$id':'https://example.org/a','title':'Person','type':'object','properties':{
            'first/name':{'type':'string'}, 'contact':{'type':'object','properties':{'age':{'type':'integer'}}}},
            'additionalProperties':{'type':'boolean'}}
        root = frontend().load_json_or_yaml(source, 'person.schema.json', kind)
        assert root.kind == Kind.TYPE and root.identity == 'https://example.org/a'
        assert root.structure.kind == Kind.ELEMENTLIST
        name, contact, additional = root.structure.children
        assert name.name == 'first/name'
        assert name.source_bindings[kind][0].source_pointer == '#/properties/first~1name'
        assert contact.structure.origin == Origin.SYNTHETIC
        assert contact.structure.name == 'PersonPropertyContact'
        assert additional.kind == Kind.MAP
        assert additional.map_kind == MapKind.INTEGRATED_PROPERTY_MAP
        assert additional.value_type.kind == Kind.SCALAR
        assert additional.source_bindings[kind][0].source_pointer == '#/additionalProperties'

    @staticmethod
    @pytest.mark.parametrize('start', (0, 1))
    def test_tuple_accessor_and_synthetic_type_numbering(start):
        config = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
        common = yaml.safe_load((config/'algites-java-common-codegen-conventions.yml').read_text())
        defs = yaml.safe_load((config/'algites-java-defs-codegen-conventions.yml').read_text())
        next(entry for entry in common['CommonCodegenNameConventions']['NameConventions']['NameConvention']
             if entry['name'] == 'algites-java-codegen-common_1')['IndexesStartingFrom'] = start
        naming = resolve_codegen_naming_profiles(common, 'algites-java-codegen-common_1',
                                                  defs, 'algites-java-defscodegen-standard_1')
        root = AIcDefsCodegenCanonicalSchemaFrontend(naming).load_json_or_yaml(
            {'type':'array', 'prefixItems':[{'type':'string'}, {'type':'boolean'}],
             'items':{'type':'integer'}}, 'tuple.json', SourceKind.JSONDEFS)
        first, second, rest = root.structure.children
        assert [first.name, second.name] == [f'getItem{start}', f'getItem{start+1}']
        assert first.structure.name == f'tuplePositionItem{start}'
        assert first.structure.origin == Origin.SYNTHETIC
        assert rest.kind == Kind.LIST and rest.item.kind == Kind.SCALAR

    @staticmethod
    def test_oneof_reference_and_no_implicit_choice_for_array():
        """Validation-only oneOf cannot define or replace structural members."""
        source = {'title':'ChoiceHolder','type':'object','properties':{
            'value':{'oneOf':[{'type':'integer'}, {'$ref':'#/$defs/item'}]},
            'items':{'type':'array','items':{'type':'string'}}}}
        with pytest.warns(UserWarning, match='oneOf'):
            root = frontend().load_json_or_yaml(source,'schema.json',SourceKind.JSONDEFS)
        assert root.structure.composition == Composition.SEQUENCE
        assert root.structure.children[0].structure.kind == Kind.SCALAR
        assert root.structure.children[1].structure.kind == Kind.LIST

    @staticmethod
    def test_xsd_sequence_all_and_repetition_without_map():
        xml = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:complexType name="Person"><xs:sequence>
          <xs:element name="Name" type="xs:string"/>
          <xs:element name="Children" type="xs:integer" maxOccurs="unbounded"/>
          <xs:choice><xs:element name="Postal" type="xs:string"/>
            <xs:element name="Email" type="xs:string"/></xs:choice>
        </xs:sequence></xs:complexType>
        <xs:complexType name="Config"><xs:all>
          <xs:element name="Enabled" type="xs:boolean"/>
          <xs:element name="Count" type="xs:int"/>
        </xs:all></xs:complexType></xs:schema>'''
        a,b = frontend().load_xsd(xml, 'schema.xsd')
        assert [a.name,b.name] == ['Person', 'Config']
        assert a.structure.composition == Composition.SEQUENCE
        assert [x.kind for x in a.structure.children] == [Kind.ELEMENT, Kind.LIST, Kind.ELEMENT]
        assert a.structure.children[2].structure.structure.composition == Composition.CHOICE
        assert b.structure.composition == Composition.ALL
        assert [x.name for x in b.structure.children] == ['Enabled','Count']
        assert not any(x.kind == Kind.MAP for x in a.structure.children)

    @staticmethod
    @pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
    @pytest.mark.parametrize('fragment,diagnostic', (
        ({'type': ['string', 'integer']}, 'type unions'),
        ({'type': 'unsupported'}, 'Unknown JSON Schema type'),
        ({'enum': [1, True]}, 'Mixed or incompatible enum scalar kinds'),
        ({'type': 'string', 'enum': ['a', 1]}, 'Mixed or incompatible enum scalar kinds'),
        ({'type': 'array', 'items': False}, 'Boolean items'),
    ))
    def test_unsupported_json_semantics_are_not_silently_discarded(kind, fragment, diagnostic):
        with pytest.raises((ValueError, NotImplementedError), match=diagnostic):
            frontend().load_json_or_yaml(fragment, 'invalid.schema.json', kind)

    @staticmethod
    @pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
    def test_unconstrained_array_is_not_misrepresented_as_empty_tuple(kind):
        result = frontend().load_json_or_yaml({'type': 'array'}, 'array.schema.json', kind)
        assert result.structure.kind == Kind.LIST
        assert result.structure.item.kind == Kind.SCALAR
        result = frontend().load_json_or_yaml(
            {'type': 'array', 'prefixItems': [{'type': 'string'}]},
            'tuple.schema.json', kind)
        assert result.structure.kind == Kind.ELEMENTLIST
        assert result.structure.children[-1].kind == Kind.LIST


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
@pytest.mark.parametrize('literal,declared,base,wire', (
    ('https://example.org/schema', 'string', 'STRING', 'https://example.org/schema'),
    ('ready', None, 'STRING', 'ready'),
    (7, 'integer', 'INTEGER', '7'),
    (7, 'number', 'INTEGER', '7'),
    (True, 'boolean', 'BOOLEAN', 'true'),
))
def test_scalar_const_is_lossless_singleton_enum(kind, literal, declared, base, wire):
    """Both dialects retain the fixed scalar restriction in the canonical model."""
    const_schema = {'const': literal}
    if declared is not None:
        const_schema['type'] = declared
    root = frontend().load_json_or_yaml(
        {'type': 'object', 'properties': {'fixed': const_schema}}, 'fixed.json', kind)
    field = root.structure.children[0]
    assert field.structure.origin == Origin.SYNTHETIC
    assert field.structure.structure.kind == Kind.ENUM
    assert field.structure.structure.base_scalar_type.name == base
    assert [item.wire_value for item in field.structure.structure.values] == [wire]


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
@pytest.mark.parametrize('fixed,extra,reason', (
    (7, {'type': 'string'}, 'conflicts with declared type'),
    ('ready', {'enum': ['waiting']}, 'not allowed by enum'),
    (True, {'enum': [1]}, 'not allowed by enum'),
    ({'a': 1}, {}, 'Structured JSON Schema const'),
    ([1, 2], {}, 'Structured JSON Schema const'),
    (None, {}, 'Null const'),
    (1.5, {}, 'Non-integer numeric const'),
))
def test_unsupported_or_contradictory_const_fails_closed(kind, fixed, extra, reason):
    """A fixed value must not silently become a string or lose constraints."""
    with pytest.raises((ValueError, NotImplementedError), match=reason):
        frontend().load_json_or_yaml({'const': fixed, **extra}, 'fixed.json', kind)


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
def test_configured_schema_metadata_is_not_generated_as_a_field(kind):
    """The configured $schema field is metadata, not a DataObject getter."""
    root = frontend().load_json_or_yaml({
        'type': 'object',
        'properties': {
            '$schema': {'type': 'string', 'const': 'urn:representation-specific'},
            'fixed': {'type': 'string', 'const': 'business-value'},
        },
        'required': ['$schema', 'fixed'],
    }, 'metadata.json', kind)
    assert [item.name for item in root.structure.children] == ['fixed']
    assert root.structure.children[0].structure.structure.values[0].wire_value == 'business-value'


def test_local_xsd_key_on_named_complex_type_is_element_scoped():
    """A named xs:complexType can be keyed at one element usage only."""
    source = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:tns="urn:keys" targetNamespace="urn:keys">
      <xs:complexType name="Container"><xs:sequence>
        <xs:element name="Keyed" type="tns:Entries"><xs:key name="ByName">
          <xs:selector xpath="Entry"/><xs:field xpath="@name"/>
        </xs:key></xs:element>
        <xs:element name="Ordinary" type="tns:Entries"/>
      </xs:sequence></xs:complexType>
      <xs:complexType name="Entries"><xs:sequence>
        <xs:element name="Entry" maxOccurs="unbounded"><xs:complexType>
          <xs:attribute name="name" type="xs:string" use="required"/>
        </xs:complexType></xs:element>
      </xs:sequence></xs:complexType>
    </xs:schema>'''
    types = {item.name: item for item in frontend().load_xsd(source, 'named-keys.xsd')}
    keyed, ordinary = types['Container'].structure.children
    # A locally scoped xs:key belongs to the referring element occurrence,
    # never a synthetic clone of its referenced nominal type.
    assert keyed.structure.origin == Origin.DECLARED
    assert keyed.key_definitions[0].identifier == 'ByName'
    assert keyed.key_definitions[0].selector == 'Entry'
    assert ordinary.structure.identity == types['Entries'].identity
    assert not types['Entries'].structure.children[0].key_definitions


def test_local_xsd_key_on_unknown_complex_type_is_explicitly_rejected():
    """An imported type is not silently dereferenced without its declaration."""
    source = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:ext="urn:external" targetNamespace="urn:local">
      <xs:complexType name="Owner"><xs:sequence>
        <xs:element name="Keyed" type="ext:Entries"><xs:key name="ByName">
          <xs:selector xpath="Entry"/><xs:field xpath="@name"/>
        </xs:key></xs:element>
      </xs:sequence></xs:complexType></xs:schema>'''
    with pytest.raises(NotImplementedError, match=r'named-keys.xsd.*ext:Entries'):
        # QName verified as imported, but its definition is not part of this XSD.
        selected = frontend()
        selected.external_xsd_types = frozenset({'{urn:external}Entries'})
        selected.load_xsd(source, 'named-keys.xsd')


def test_xsd_choice_sequence_is_one_atomic_alternative():
    """A Name/Regexp pair must not become two independent choice branches."""
    xml = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Choice"><xs:choice>
        <xs:element name="Literal" type="xs:string"/>
        <xs:sequence><xs:element name="Name" type="xs:string"/>
          <xs:element name="Regexp" type="xs:string"/></xs:sequence>
      </xs:choice></xs:complexType></xs:schema>'''
    root, = frontend().load_xsd(xml, 'choice-group.xsd')
    choices = root.structure.children
    assert [item.name for item in choices] == ['Literal', 'NameRegexp']
    group = choices[1].structure.structure.children[0].structure.structure
    assert [item.name for item in group.children] == ['Name', 'Regexp']


def test_actual_naming_conventions_xsd_parses_with_keys():
    """The actual ABI seed XSD must pass the new frontend, not only fixtures."""
    library = TOOL.parent / 'pub.lib.General'
    source = library / ('naming/convention/intf/src/product/xmldefs/eu/algites/lib/'
                        'naming/convention/common-naming-conventions_1.xsd')
    # In a standalone tool checkout, this sibling may not be available.
    if not source.exists():
        pytest.skip('pub.lib.General checkpoint unavailable')
    nodes = frontend().load_xsd(source.read_text(), str(source))
    common = next(node for node in nodes if node.name == 'CommonNamingConventions')
    keys = [member.key_definitions for member in common.structure.children
            if member.name in ('IdentifierConventions', 'VersionConventions',
                               'NameFragments', 'NameCompositions')]
    assert len(keys) == 4 and all(len(definitions) == 1 for definitions in keys)


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
def test_inline_property_enum_uses_dialect_neutral_naming_role(kind):
    """An inline JSON/YAML enum follows the same owner+member name as XSD."""
    source = {'title': 'Person', 'type': 'object', 'properties': {
        'Status': {'type': 'string', 'enum': ['active', 'inactive']},
        'Level': {'type': 'integer', 'enum': [1, 2]},
        'Fixed': {'type': 'string', 'const': 'yes'},
        'Details': {'type': 'object', 'properties': {'name': {'type': 'string'}}},
    }}
    root = frontend().load_json_or_yaml(source, 'inline-enum.schema.json', kind)
    status, level, fixed, details = root.structure.children
    assert [x.structure.name for x in (status, level, fixed)] == [
        'PersonStatus', 'PersonLevel', 'PersonFixed']
    for field in (status, level, fixed):
        assert field.structure.origin == Origin.SYNTHETIC
        assert field.structure.structure.kind == Kind.ENUM
        assert field.structure.path_segments[1] == 'synthetic_inline_enum_type'
        assert field.structure.source_bindings[kind][0].source_pointer.startswith('#/properties/')
    assert details.structure.name == 'PersonPropertyDetails'
    assert details.structure.path_segments[1] == 'synthetic_property_type'


def test_inline_property_enum_name_matches_xml_enum():
    """XSD and JSON use the same naming convention rather than hardcoded names."""
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Person"><xs:sequence>
        <xs:element name="Status"><xs:simpleType><xs:restriction base="xs:string">
          <xs:enumeration value="active"/><xs:enumeration value="inactive"/>
        </xs:restriction></xs:simpleType></xs:element>
      </xs:sequence></xs:complexType>
    </xs:schema>'''
    (person,) = frontend().load_xsd(xsd, 'person.xsd')
    xml_enum = person.structure.children[0].structure
    assert xml_enum.name == 'PersonStatus'
    assert xml_enum.path_segments[1] == 'synthetic_inline_enum_type'
    for kind in (SourceKind.JSONDEFS, SourceKind.YAMLDEFS):
        root = frontend().load_json_or_yaml({
            'title': 'Person', 'type': 'object',
            'properties': {'Status': {'type': 'string', 'enum': ['active', 'inactive']}},
        }, 'person.json', kind)
        json_enum = root.structure.children[0].structure
        assert json_enum.name == xml_enum.name
        assert json_enum.path_segments[1] == xml_enum.path_segments[1]
        assert json_enum.structure.values == xml_enum.structure.values


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
def test_named_enum_reference_does_not_gain_inline_enum_type(kind):
    """A $defs enum has its own declared identity; no synthetic enum is added."""
    source = {'$id': 'urn:types', '$defs': {
        'Person': {'type': 'object', 'properties': {'Status': {'$ref': '#/$defs/Status'}}},
        'Status': {'type': 'string', 'enum': ['active', 'inactive']}}}
    types = frontend().load_json_or_yaml_types(source, 'named.json', kind)
    assert [node.name for node in types] == ['Person', 'Status']
    status = types[1]
    assert status.origin == Origin.DECLARED
    assert status.structure.kind == Kind.ENUM
    assert types[0].structure.children[0].structure.kind != Kind.ENUM


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
def test_inline_object_key_enum_uses_inline_enum_role(kind):
    """Indexed JSON/YAML object keys are also anonymous enum declarations."""
    source = {'title': 'Person', 'type': 'object', 'properties': {
        'Entries': {'type': 'object',
                    'x-algites-defscodegen-key': {'id': 'ByCode', 'field-name': 'Code'},
                    'propertyNames': {'type': 'string', 'enum': ['A', 'B']},
                    'additionalProperties': {'type': 'string'}}}}
    root = frontend().load_json_or_yaml(source, 'keyed.schema.json', kind)
    indexed = root.structure.children[0]
    assert indexed.kind == Kind.LIST
    key = indexed.item.structure.children[0].structure
    assert key.name == 'PersonCode'
    assert key.path_segments[1] == 'synthetic_inline_enum_type'
    assert key.structure.kind == Kind.ENUM


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
def test_synthetic_types_inherit_own_document_filename_version(kind):
    """Nested object and enum TYPEs must not use another document's version."""
    instance = frontend()
    for version in ('1', '7'):
        resource = f'person_{version}.schema.json'
        types = instance.load_json_or_yaml_types({
            '$id': f'https://example.org/person_{version}',
            'type': 'object',
            'properties': {
                'state': {'type': 'string', 'enum': ['on', 'off']},
                'details': {'type': 'object', 'properties': {'name': {'type': 'string'}}},
            },
            '$defs': {'Detail': {'type': 'object', 'properties': {
                'status': {'type': 'string', 'enum': ['on', 'off']},
            }}},
        }, resource, kind, root_name='Person', source_version=version)
        root, detail = types
        assert root.schema_version == version
        assert detail.schema_version == version
        for node in (root, detail):
            for field in node.structure.children:
                if field.structure.origin == Origin.SYNTHETIC:
                    assert field.structure.schema_version == version, (
                        resource, node.name, field.name, field.structure.name)


def test_xsd_inline_types_inherit_own_document_filename_version():
    """XSD inline synthetic types use the version of the containing XSD."""
    instance = frontend()
    for version in ('1', '7'):
        xml = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
          targetNamespace="urn:test"><xs:complexType name="Person"><xs:sequence>
          <xs:element name="State"><xs:simpleType>
            <xs:restriction base="xs:string"><xs:enumeration value="on"/>
              <xs:enumeration value="off"/></xs:restriction>
          </xs:simpleType></xs:element>
          <xs:element name="Details"><xs:complexType><xs:sequence>
            <xs:element name="Name" type="xs:string"/>
          </xs:sequence></xs:complexType></xs:element>
        </xs:sequence></xs:complexType></xs:schema>'''
        (root,) = instance.load_xsd(xml, f'person_{version}.xsd',
                                     source_version=version)
        assert root.schema_version == version
        for field in root.structure.children:
            assert field.structure.origin == Origin.SYNTHETIC
            assert field.structure.schema_version == version
