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
    AIigStructureKind_1 as Kind, AIigMapKind_1 as MapKind,
    AIigComposition_1 as Composition, AIigSourceInputKind_1 as SourceKind,
    AIigResolutionState_1 as Resolution, AIigTypeOrigin_1 as Origin)
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
        common['CommonCodegenNameConventions']['NameConventions']['algites-java-codegen-common_1']['IndexesStartingFrom'] = start
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
        source = {'title':'ChoiceHolder','type':'object','properties':{
            'value':{'oneOf':[{'type':'integer'}, {'$ref':'#/$defs/item'}]},
            'items':{'type':'array','items':{'type':'string'}}}}
        root = frontend().load_json_or_yaml(source,'schema.json',SourceKind.JSONDEFS)
        variant = root.structure.children[0].structure
        assert variant.origin == Origin.SYNTHETIC
        assert variant.structure.composition == Composition.CHOICE
        ref = variant.structure.children[1].structure.structure
        assert ref.kind == Kind.TYPE and ref.resolution_state == Resolution.REFERENCE
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
        assert [x.kind for x in a.structure.children] == [Kind.ELEMENT, Kind.LIST, Kind.ELEMENTLIST]
        assert a.structure.children[2].composition == Composition.CHOICE
        assert b.structure.composition == Composition.ALL
        assert [x.name for x in b.structure.children] == ['Enabled','Count']
        assert not any(x.kind == Kind.MAP for x in a.structure.children)

    @staticmethod
    @pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
    @pytest.mark.parametrize('fragment,diagnostic', (
        ({'type': ['string', 'integer']}, 'type unions'),
        ({'type': ['string', 'null']}, 'nullable'),
        ({'type': 'unsupported'}, 'Unknown JSON Schema type'),
        ({'enum': [1, True]}, 'Mixed or incompatible enum scalar kinds'),
        ({'type': 'string', 'enum': ['a', 1]}, 'Mixed or incompatible enum scalar kinds'),
        ({'type': 'object', 'additionalProperties': True}, 'additionalProperties:true'),
        ({'type': 'array', 'items': False}, 'Boolean items'),
        ({'oneOf': [{'type': 'string'}], 'anyOf': [{'type': 'integer'}]}, 'oneOf/anyOf'),
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
