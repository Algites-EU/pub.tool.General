"""Contract, canonical-model, and naming regression tests for the next codegen.

These tests operate only on maintained code/schema sources. Legacy .old codegen,
generated source trees and the production bootstrap remain untouched.
"""
import copy
import json
from pathlib import Path
import sys

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

TOOL = next(x for x in Path(__file__).resolve().parents if x.name == 'pub.tool.General')
ROOT = TOOL.parent
LIB = ROOT / 'pub.lib.General'
for path in (TOOL / 'generators/code/common/src/product/python',
             TOOL / 'generators/code/defscodegen/intf/src/product/python'):
    sys.path.insert(0, str(path))

from eu.algites.tool.codegen.common.naming_profiles import (
    COMMON_ROLES, DEFS_ROLES, SDO_ROLES, resolve_codegen_naming_profiles)
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgd_jElement_1, AIcgd_jElementList_1, AIcgd_jEnum_1,
    AIcgd_jEnumValue_1, AIcgd_jList_1, AIcgd_jMap_1,
    AIcgd_jScalar_1, AIcgd_jSourceBinding_1,
    AIcgd_jType_1, AIigComposition_1,
    AIigMapKind_1, AIigScalarKind_1,
    AIigSourceInputKind_1, AIigTypeOrigin_1,
    AIigStructureKind_1, freeze_bindings, merge_bindings, normalize_structure)

FAM_SUFFIX = {'yamldefs': 'yamldef.schema.json', 'jsondefs': 'jsondef.schema.json'}
NAMES = {'common': ('common', 'common', 'codegen-common'),
         'defs': ('defscodegen/intf', 'defs', 'defscodegen'),
         'sdo': ('sdocodegen/intf', 'sdo', 'sdocodegen')}
ROLE_NAMES = {'common': COMMON_ROLES, 'defs': DEFS_ROLES, 'sdo': SDO_ROLES}
URL_ROOT = 'https://defs.dev.algites.eu/api'


def schema_repository(family):
    suffix = FAM_SUFFIX[family]
    docs = []
    for root in (LIB / 'naming/convention', TOOL / 'generators/code'):
        for path in root.rglob(f'*.{suffix}'):
            if '/src/product/' not in str(path) or '.gen/' in str(path):
                continue
            try:
                doc = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            if '$id' in doc:
                docs.append(doc)
    registry = Registry().with_resources((doc['$id'], Resource.from_contents(doc,
        default_specification=DRAFT202012)) for doc in docs)
    return {doc['$id']: doc for doc in docs}, registry


def profile_docs(profile, language):
    path = TOOL / 'generators/code/profile' / profile / 'src/product/config/eu/algites/lib/naming/convention/sourcecode'
    return {scope: yaml.safe_load((path / f'{profile}-{language}-{scope}-codegen-conventions.yml').read_text())
            for scope in ('common', 'defs', 'sdo')}


@pytest.mark.parametrize('family', FAM_SUFFIX)
@pytest.mark.parametrize('profile', ('algites', 'standardprefix', 'standardpostfix'))
@pytest.mark.parametrize('language', ('java', 'python'))
def test_split_schema_profile_validation(family, profile, language):
    """All 18 profile YAML documents must work with both independent schema families."""
    schemas, registry = schema_repository(family)
    for scope, doc in profile_docs(profile, language).items():
        schema_id = doc['$schema'].replace('/yamldefs/', f'/{family}/').replace(
            '.yamldef.schema.json', f'.{FAM_SUFFIX[family]}')
        Draft202012Validator(schemas[schema_id], registry=registry).validate(doc)
        selected = next(iter(doc[{
            'common': 'CommonCodegenNameConventions',
            'defs': 'DefsCodegenNameConventions',
            'sdo': 'SdoCodegenNameConventions'}[scope]]['NameConventions'].values()))
        assert set(selected['StructureNaming']) == ROLE_NAMES[scope]
        if scope != 'common':
            assert selected['CommonNamingConvention'] == f'{profile}-{language}-codegen-common_1'
        else:
            assert selected['IndexesStartingFrom'] == 1
            assert selected['SchemaMetadataNaming']['data_source_schema_identifier'] == ''


@pytest.mark.parametrize('family', FAM_SUFFIX)
@pytest.mark.parametrize('scope', ('common', 'defs', 'sdo'))
def test_foreign_roles_rejected(family, scope):
    schemas, registry = schema_repository(family)
    doc = copy.deepcopy(profile_docs('algites', 'java')[scope])
    key = {'common': 'CommonCodegenNameConventions', 'defs': 'DefsCodegenNameConventions',
           'sdo': 'SdoCodegenNameConventions'}[scope]
    settings = next(iter(doc[key]['NameConventions'].values()))
    settings['StructureNaming']['forbidden_role'] = 'will-never-exist'
    schema_id = doc['$schema'].replace('/yamldefs/', f'/{family}/').replace(
        '.yamldef.schema.json', f'.{FAM_SUFFIX[family]}')
    with pytest.raises(ValidationError):
        Draft202012Validator(schemas[schema_id], registry=registry).validate(doc)


@pytest.mark.parametrize('family', FAM_SUFFIX)
def test_metadata_source_dependency_rejected(family):
    schemas, registry = schema_repository(family)
    doc = copy.deepcopy(profile_docs('algites', 'java')['common'])
    profile = next(iter(doc['CommonCodegenNameConventions']['NameConventions'].values()))
    profile['SchemaMetadataNaming']['schema_source_schema_identifier'] = ''
    profile['SchemaMetadataNaming']['data_source_schema_identifier'] = 'schema-id'
    schema_id = doc['$schema'].replace('/yamldefs/', f'/{family}/').replace(
        '.yamldef.schema.json', f'.{FAM_SUFFIX[family]}')
    with pytest.raises(ValidationError):
        Draft202012Validator(schemas[schema_id], registry=registry).validate(doc)


@pytest.mark.parametrize('profile', ('algites', 'standardprefix', 'standardpostfix'))
@pytest.mark.parametrize('language', ('java', 'python'))
def test_naming_functions(profile, language):
    documents = profile_docs(profile, language)
    common_id = f'{profile}-{language}-codegen-common_1'
    resolved = resolve_codegen_naming_profiles(documents['common'], common_id, documents['defs'],
        f'{profile}-{language}-defscodegen-standard_1', documents['sdo'],
        f'{profile}-{language}-sdocodegen-standard_1')
    assert resolved.positional_number(0) == 1
    assert resolved.positional_number(2) == 3
    assert resolved.method_name('positional_item_synthetic_getter', position='2') == 'getItem2'
    assert resolved.synthetic_type_name('synthetic_property_type', 'AIiCustomer', 'first_name') == 'AIiCustomerPropertyFirstName'
    assert resolved.synthetic_type_name('synthetic_positional_item_type', 'AIiCustomer', 'address', 0) == 'AIiCustomerPositionAddress1'
    assert resolved.method_name('multi_mapped_list_key_synthetic_getter') == '_getKey'
    assert resolved.method_name('multi_mapped_list_value_synthetic_getter') == '_getValue'
    assert resolved.method_name('raw_unsetter', 'FirstName') == '_unset_FirstName'
    with pytest.raises(KeyError):
        resolved.method_name('forbidden_role')
    with pytest.raises(ValueError):
        resolved.positional_number(-1)


def test_numbering_can_start_at_zero_and_custom_segments_are_not_hardcoded():
    documents = profile_docs('algites', 'java')
    doc = copy.deepcopy(documents['common'])
    entry = next(iter(doc['CommonCodegenNameConventions']['NameConventions'].values()))
    entry['IndexesStartingFrom'] = 0
    defs = copy.deepcopy(documents['defs'])
    id_ = 'algites-java-synthetic_positional_item_type_1'
    defs['NameCompositions'][id_]['Segments'][1]['NameFragmentsSegmentValue']['Value'] = 'TuplePart'
    resolved = resolve_codegen_naming_profiles(doc, 'algites-java-codegen-common_1', defs,
                                                 'algites-java-defscodegen-standard_1')
    assert resolved.synthetic_type_name('synthetic_positional_item_type', 'Customer', 'street', 0) == 'CustomerTuplePartStreet0'


def test_wrong_cross_reference_and_foreign_domain_rejected():
    docs = profile_docs('algites', 'java')
    defs = copy.deepcopy(docs['defs'])
    selected = next(iter(defs['DefsCodegenNameConventions']['NameConventions'].values()))
    selected['CommonNamingConvention'] = 'unknown'
    with pytest.raises(ValueError):
        resolve_codegen_naming_profiles(docs['common'], 'algites-java-codegen-common_1', defs,
                                        'algites-java-defscodegen-standard_1')
    selected['CommonNamingConvention'] = 'algites-java-codegen-common_1'
    selected['StructureNaming']['raw_unsetter'] = 'foreign'
    with pytest.raises(ValueError):
        resolve_codegen_naming_profiles(docs['common'], 'algites-java-codegen-common_1', defs,
                                        'algites-java-defscodegen-standard_1')


def test_canonical_shape_provenance_and_normalization():
    source = AIcgd_jSourceBinding_1('schema.json', '/properties/a', 'properties')
    sources = freeze_bindings({AIigSourceInputKind_1.JSONDEFS: [source, source]})
    assert len(sources[AIigSourceInputKind_1.JSONDEFS]) == 2
    assert len(merge_bindings(sources, sources)[AIigSourceInputKind_1.JSONDEFS]) == 4
    field = AIcgd_jElement_1('name', AIcgd_jScalar_1(AIigScalarKind_1.STRING), source_bindings=sources)
    group = AIcgd_jElementList_1(AIigComposition_1.SEQUENCE, (
        AIcgd_jElementList_1(AIigComposition_1.SEQUENCE, (field,)),
        AIcgd_jElementList_1(AIigComposition_1.CHOICE, (field,)),
        AIcgd_jMap_1('additionalProperties', AIigMapKind_1.INTEGRATED_PROPERTY_MAP,
                           AIcgd_jScalar_1(AIigScalarKind_1.STRING),
                           AIcgd_jScalar_1(AIigScalarKind_1.NUMBER), sources)))
    source_type = AIcgd_jType_1('stable:1', 'Person', AIigTypeOrigin_1.SYNTHETIC,
                                       ('Person', 'Group'), structure=group, source_bindings=sources)
    normalized = normalize_structure(source_type)
    assert normalized.kind == AIigStructureKind_1.TYPE
    assert normalized.origin == AIigTypeOrigin_1.SYNTHETIC
    assert len(normalized.structure.children) == 3
    assert normalized.structure.children[0] == field
    assert normalized.structure.children[1].composition == AIigComposition_1.CHOICE
    assert normalized.structure.children[2].map_kind == AIigMapKind_1.INTEGRATED_PROPERTY_MAP
    assert normalized.source_bindings[AIigSourceInputKind_1.JSONDEFS] == (source, source)
    with pytest.raises(ValueError):
        AIcgd_jElementList_1(AIigComposition_1.SEQUENCE, (AIcgd_jScalar_1(AIigScalarKind_1.ANY),))


def test_enum_and_list_canonical_shapes():
    enum = AIcgd_jEnum_1(AIigScalarKind_1.INTEGER,
                               (AIcgd_jEnumValue_1('1'), AIcgd_jEnumValue_1('2')))
    assert enum.kind == AIigStructureKind_1.ENUM
    assert AIcgd_jList_1('codes', enum).kind == AIigStructureKind_1.LIST
    assert len(AIigStructureKind_1) == 7
