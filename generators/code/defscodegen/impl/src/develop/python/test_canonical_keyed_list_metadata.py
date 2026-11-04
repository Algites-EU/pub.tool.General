"""Keyed LIST metadata remains lossless until the dedicated index emitter exists."""
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import replace
import json
from pathlib import Path
import sys

import pytest
import jsonschema

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == 'pub.tool.General')
for folder in ('generators/code/defscodegen/intf/src/product/python',
               'generators/code/defscodegen/impl/src/product/python',
               'generators/code/common/src/product/python'):
    sys.path.insert(0, str(ROOT / folder))

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgd_jKeyDefinition_1 as Key,
    AIcgd_jList_1 as Collection,
    AIcgd_jType_1 as Type,
    AIcgd_jScalar_1 as Scalar,
    AIcgd_jElementList_1 as Group,
    AIigTypeOrigin_1 as Origin,
    AIigComposition_1 as Composition,
    AIigScalarKind_1 as ScalarKind,
    normalize_structure,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_contract_payload import (
    AIcDefsCodegenCanonicalContractPayload as Payload,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_model_linker import (
    AIcDefsCodegenCanonicalModelLinker as Linker,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_model_merger import (
    AIcDefsCodegenCanonicalModelMerger as Merger,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter as Emitter,
    AIcdDefsCodegenEmissionName as Names,
)
from test_canonical_source_emitter import _profile

SCHEMA_PATH = ROOT / ('generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/'
                      'tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')


def roots():
    """Composite keys and optional unique constraints on a directly repeated list."""
    constraints = (
        Key('employeeCode', './employee', '/schema/Organization/key[0]',
            ('@department', 'personal/code'), True),
        Key('uniqueAlias', './employee', '/schema/Organization/unique[1]',
            ('@alias',), False),
    )
    collection = Collection('employee', Scalar(ScalarKind.STRING), 0, -1, constraints)
    return (Type('urn:Organization', 'Organization', Origin.DECLARED,
                 ('Organization',), structure=Group(Composition.SEQUENCE, (collection,))),)


def test_keyed_list_preserves_multiple_field_paths_through_link_and_payload():
    """No intermediate step is allowed to discard key fields or requiredness."""
    original, = roots()
    linked, = Linker.link((original,), schema=json.loads(SCHEMA_PATH.read_text()))
    normalized = normalize_structure(linked)
    keys = normalized.structure.children[0].key_definitions
    assert keys == original.structure.children[0].key_definitions
    assert keys[0].fields == ('@department', 'personal/code')
    assert keys[1].required is False
    payload = Payload.emit((normalized,))
    jsonschema.Draft202012Validator(json.loads(SCHEMA_PATH.read_text())).validate(payload)
    exported = payload['types'][0]['structure']['ElementList']['children'][0]['List']['key_definitions']
    assert exported[0]['fields'] == ['@department', 'personal/code']
    assert exported[0]['required'] is True
    assert exported[1]['fields'] == ['@alias']
    assert exported[1]['required'] is False


def test_keyed_list_equivalent_merge_and_conflicts():
    """Two sources may merge only with byte-for-byte equivalent key semantics."""
    original, = roots()
    merged, = Merger.merge((original, original))
    assert merged.structure.children[0].key_definitions == original.structure.children[0].key_definitions
    other = replace(original, structure=replace(original.structure,
                    children=(replace(original.structure.children[0], key_definitions=(
                        replace(original.structure.children[0].key_definitions[0], required=False),
                        original.structure.children[0].key_definitions[1])),)))
    with pytest.raises(ValueError, match='key definitions'):
        Merger.merge((original, other))


def test_emitter_rejects_index_on_scalar_elements_before_returning_sources():
    """Index extraction requires a named structured element, never a scalar."""
    original, = roots()
    names = {original.identity: Names('AIigOrganization', 'AIigOrganization', 'aiig_organization')}
    with pytest.raises(NotImplementedError, match='named TYPE'):
        Emitter(_profile(), names, 'test.output').render((original,))


def test_key_constraints_reject_duplicate_names_and_field_paths():
    """Invalid key declarations fail at model construction, before emission."""
    with pytest.raises(ValueError, match='Duplicate XML key field'):
        Key('index', '.', '/key[1]', ('@id', '@id'))
    key = Key('index', '.', '/key[1]', ('@id',))
    with pytest.raises(ValueError, match='Repeated LIST key'):
        Collection('employee', Scalar(ScalarKind.STRING), 0, -1, (key, key))
    with pytest.raises(ValueError, match='Keyed LIST'):
        Collection('', Scalar(ScalarKind.STRING), 0, -1, (key,))


@pytest.mark.parametrize('constraint', ('key', 'unique', 'keyref'))
def test_global_xsd_identity_constraints_are_not_silently_discarded(constraint):
    """The named-type reader must reject keys on ignored global elements."""
    from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
        AIcDefsCodegenCanonicalSchemaFrontend,
    )
    xml = f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Container"><xs:sequence>
        <xs:element name="entry" type="xs:string" maxOccurs="unbounded"/>
      </xs:sequence></xs:complexType>
      <xs:element name="root" type="Container"><xs:{constraint} name="identity">
        <xs:selector xpath="./entry"/><xs:field xpath="."/>
      </xs:{constraint}></xs:element>
    </xs:schema>'''
    with pytest.raises(NotImplementedError, match='identity constraints|keyref/identityConstraint'):
        AIcDefsCodegenCanonicalSchemaFrontend(_profile()).load_xsd(xml, 'keys.xsd')
