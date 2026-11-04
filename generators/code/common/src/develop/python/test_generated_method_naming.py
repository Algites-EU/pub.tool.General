"""Cross-generator method naming contract and schema regression tests."""
from pathlib import Path
import json
import yaml
import pytest
from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog


ROOT = Path(__file__).resolve().parents[7]
LIB = ROOT / 'pub.lib.General'
TOOL = ROOT / 'pub.tool.General'
LIB_CONFIG = LIB / 'naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
METHOD_CONFIG = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
EXPECTED = {'standard_getter': 'getName',
            'standard_setter': 'setName',
            'raw_getter': '_getRaw_Name',
            'raw_presence_checker_method': '_isPresent_Name',
            'raw_unsetter': '_unset_Name'}


@pytest.mark.parametrize('technology', ('java', 'python'))
def test_shared_method_naming_composes_using_existing_catalog(technology):
    """DO/SDO method profiles are independent of source-file naming profiles."""
    catalog = AIcNameConventionCatalog.load_many([
        LIB_CONFIG / f'algites-{technology}-name-conventions.yml',
        METHOD_CONFIG / f'algites-{technology}-codegen-method-conventions.yml'])
    assert len(catalog.names) == 59
    assert catalog.generated_method_names == (f'algites-{technology}-codegen-standard_1',)
    profile = f'algites-{technology}-codegen-standard_1'
    selected = catalog.with_generated_method_profile(profile)
    for kind, expected in EXPECTED.items():
        assert selected.format(profile, kind, {'identifier': 'Name'}, 'upper_camel_case_1') == expected
    assert selected.format(f'algites-{technology}-gen-intf-versioned_1',
                           'getter_method_name', {'identifier':'Name'},
                           'upper_camel_case_1') == 'getName'
    assert selected.generated_method_names == catalog.generated_method_names
    assert selected.names == catalog.names


def test_user_defined_composition_is_not_forced_to_add_technical_prefix(tmp_path):
    """There is no generator-side implicit underscore or method-name manipulation."""
    selected = yaml.safe_load((METHOD_CONFIG / 'algites-python-codegen-method-conventions.yml').read_text())
    selected['NameCompositions']['custom-presence'] = {
        'Segments': [{'Kind': 'constant_string', 'Value': 'present'},
                     {'Kind': 'identifier', 'Convention': 'upper_camel_case_1'}]}
    mapping = selected['GeneratedDataObjectMethodNameConventions']['NameConventions']
    item = mapping.pop('algites-python-codegen-standard_1')
    item['StructureNaming']['raw_presence_checker_method'] = 'custom-presence'
    mapping['user-profile'] = item
    override = tmp_path / 'custom.yml'
    override.write_text(yaml.safe_dump(selected))
    catalog = AIcNameConventionCatalog.load_many([
        LIB_CONFIG / 'algites-python-name-conventions.yml', override])
    catalog = catalog.with_generated_method_profile('user-profile')
    assert catalog.format('user-profile', 'raw_presence_checker_method',
                          {'identifier': 'Name'}, 'upper_camel_case_1') == 'presentName'
    assert catalog.format('algites-python-gen-intf-versioned_1', 'getter_method_name',
                          {'identifier':'Name'}, 'upper_camel_case_1') == 'getName'


def test_source_profiles_are_nested_without_redefining_filename_patterns():
    source = yaml.safe_load((LIB_CONFIG/'algites-java-name-conventions.yml').read_text())
    assert 'NameConventions' not in source
    assert 'NameConventions' in source['SourceStructureNameConventions']
    methods = yaml.safe_load((METHOD_CONFIG/'algites-java-codegen-method-conventions.yml').read_text())
    assert set(methods['GeneratedDataObjectMethodNameConventions']['NameConventions'][
        'algites-java-codegen-standard_1']['StructureNaming']) == set(EXPECTED) | {
        'multi_mapped_list_key_synthetic_getter',
        'multi_mapped_list_value_synthetic_getter'}
    assert 'ContainerStructureType' not in str(methods)


def test_invalid_mode_is_rejected():
    from eu.algites.lib.data.smartdataobject.impl.standard.aic_smart_data_object import AIcSmartDataObject
    obj=AIcSmartDataObject()
    with pytest.raises(TypeError):
        obj._toMapping(None)
    with pytest.raises(TypeError):
        obj._getValidationIssues(None)


@pytest.mark.parametrize('family', ('yamldefs', 'jsondefs'))
@pytest.mark.parametrize('technology', ('java', 'python'))
def test_both_catalog_families_validate_against_composed_schemas(family, technology):
    """Every new shared schema reference must resolve without fetching remote definitions."""
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
    from jsonschema import Draft202012Validator
    source_root = LIB / f'naming/convention/sourcecode/src/product/{family}'
    base_schema_root = LIB / f'naming/convention/intf/src/product/{family}'
    method_root = TOOL / f'generators/code/common/src/product/{family}'
    definitions = [json.loads(path.read_text(encoding='utf-8'))
                   for base in (base_schema_root, source_root, method_root)
                   for path in base.rglob('*.schema.json')]
    resources = Registry().with_resources((item['$id'], Resource.from_contents(item, default_specification=DRAFT202012))
                                          for item in definitions)
    for catalog_type, catalog_file, schema_name in (
        ('source', LIB_CONFIG / f'algites-{technology}-name-conventions.yml',
         f'source-structure-name-conventions_1.{"yamldef" if family == "yamldefs" else "jsondef"}.schema.json'),
        ('methods', METHOD_CONFIG / f'algites-{technology}-codegen-method-conventions.yml',
         f'data-object-naming-conventions_1.{"yamldef" if family == "yamldefs" else "jsondef"}.schema.json'),
    ):
        schema = next(item for item in definitions if item['$id'].endswith('/' + schema_name))
        instance = yaml.safe_load(catalog_file.read_text(encoding='utf-8'))
        validator = Draft202012Validator(schema, registry=resources)
        validator.validate(instance)
        if catalog_type == 'methods':
            instance['GeneratedDataObjectMethodNameConventions']['NameConventions'][
                f'algites-{technology}-codegen-standard_1']['StructureNaming'].pop('raw_unsetter')
            assert validator.is_valid(instance)  # Optional raw methods must remain schema-valid.
            instance['GeneratedDataObjectMethodNameConventions']['NameConventions'][
                f'algites-{technology}-codegen-standard_1']['StructureNaming'].pop('standard_getter')
            assert not validator.is_valid(instance)


@pytest.mark.parametrize('technology', ('java', 'python'))
def test_generated_method_catalog_has_editor_schema_header(technology):
    """Packaged method catalogs use the same editor hints as the source catalogs."""
    url = ('https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/'
           'codegen/common/naming/data-object-naming-conventions_1.yamldef.schema.json')
    path = METHOD_CONFIG / f'algites-{technology}-codegen-method-conventions.yml'
    header = path.read_text(encoding='utf-8').splitlines()[:2]
    assert header == [f'# yaml-language-server: $schema={url}',
                      f'# $schema: {url}']


@pytest.mark.parametrize('technology', ('java', 'python'))
def test_unresolved_cross_catalog_composition_is_reported(technology):
    """A standalone method catalog must not silently invent source compositions."""
    catalog = AIcNameConventionCatalog.load(
        METHOD_CONFIG / f'algites-{technology}-codegen-method-conventions.yml')
    profile = f'algites-{technology}-codegen-standard_1'
    catalog = catalog.with_generated_method_profile(profile)
    with pytest.raises(ValueError, match='Unknown NameFragment or NameComposition'):
        catalog.format(profile, 'standard_getter',
                       {'identifier': 'Name'}, 'upper_camel_case_1')


@pytest.mark.parametrize('technology', ('java', 'python'))
@pytest.mark.parametrize('generator', ('defs', 'sdo'))
def test_default_settings_load_both_method_and_source_catalogs(technology, generator):
    """Algites build profile supplies the cross-catalog references for both codegens."""
    artifact = 'defscodegen' if generator == 'defs' else 'sdocodegen'
    path = (TOOL / f'generators/code/profile/algites/src/product/config/eu/'
            f'algites/tool/codegen/{generator}/{artifact}-{technology}.settings')
    settings = path.read_text(encoding='utf-8')
    assert f'classpath:algites-{technology}-name-conventions.yml' in settings
    assert (f'--naming-conventions-file:codegen_common=classpath:algites-{technology}'
            '-common-codegen-conventions.yml') in settings
    assert (f'--naming-conventions-file:codegen_{generator}=classpath:algites-{technology}'
            f'-{generator}-codegen-conventions.yml') in settings
    assert f'--common-codegen-naming-convention:{technology}=algites-{technology}-codegen-common_1' in settings
    assert (f'--{generator}-codegen-naming-convention:{technology}='
            f'algites-{technology}-{generator}codegen-standard_1') in settings
    assert '--generated-dataobject-method-naming-convention' not in settings

@pytest.mark.parametrize('suffix', ('url', 'identifier', 'version'))
def test_common_profile_rejects_enabled_wire_field_without_schema_source(suffix):
    """The semantic rule belongs to the new Common resolver, not the generic catalog."""
    from eu.algites.tool.codegen.common.naming_profiles import resolve_codegen_naming_profiles
    path = (TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
            / 'algites-python-common-codegen-conventions.yml')
    common = yaml.safe_load(path.read_text())
    profile = common['CommonCodegenNameConventions']['NameConventions']['algites-python-codegen-common_1']
    profile['SchemaMetadataNaming'][f'schema_source_schema_{suffix}'] = ''
    profile['SchemaMetadataNaming'][f'data_source_schema_{suffix}'] = f'$output_{suffix}'
    with pytest.raises(ValueError, match=f'data_source_schema_{suffix} requires source metadata mapping'):
        resolve_codegen_naming_profiles(common, 'algites-python-codegen-common_1')


@pytest.mark.parametrize('technology', ('java', 'python'))
def test_default_method_profile_metadata_matches_algites(technology):
    """The selected output method profile includes all six explicit wire mappings."""
    source = yaml.safe_load((METHOD_CONFIG/f'algites-{technology}-codegen-method-conventions.yml').read_text())
    name = f'algites-{technology}-codegen-standard_1'
    method = source['GeneratedDataObjectMethodNameConventions']['NameConventions'][name]
    assert {key: method['SchemaMetadataNaming'][key] for key in ('schema_source_schema_url',
        'schema_source_schema_identifier', 'schema_source_schema_version',
        'data_source_schema_url', 'data_source_schema_identifier',
        'data_source_schema_version')} == {
            'schema_source_schema_url': '$id',
            'schema_source_schema_identifier': 'x-algites-schema-id',
            'schema_source_schema_version': 'x-algites-schema-version',
            'data_source_schema_url': '$schema',
            'data_source_schema_identifier': '', 'data_source_schema_version': ''}


@pytest.mark.parametrize('technology', ('java', 'python'))
def test_common_profile_metadata_roles_require_their_typed_namespace(technology):
    """Semantic metadata role validation belongs to the Common role resolver."""
    from eu.algites.tool.codegen.common.naming_profiles import resolve_codegen_naming_profiles
    path = (TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
            / f'algites-{technology}-common-codegen-conventions.yml')
    common = yaml.safe_load(path.read_text())
    name = f'algites-{technology}-codegen-common_1'
    entry = common['CommonCodegenNameConventions']['NameConventions'][name]
    entry['schema_source_schema_url'] = entry['SchemaMetadataNaming'].pop('schema_source_schema_url')
    assert 'schema_source_schema_url' not in entry['SchemaMetadataNaming']
    # The generic YAML catalog only parses; the new role resolver performs semantic checks.
    entry.pop('schema_source_schema_url')
    entry['SchemaMetadataNaming']['unknown_role'] = 'misconfigured'
    with pytest.raises(ValueError, match='Unknown schema metadata role'):
        resolve_codegen_naming_profiles(common, name)


@pytest.mark.parametrize('family,suffix', (('yamldefs', 'yamldef'), ('jsondefs', 'jsondef')))
def test_schema_metadata_enum_and_validation_are_consistent(family, suffix):
    """The six enum keys constrain the metadata mapping, not the five method names."""
    base = TOOL / 'generators/code/common/src/product' / family / 'eu/algites/tool/codegen/common/naming'
    kind = json.loads((base / f'generated-dataobject-schema-metadata-kind_1.{suffix}.schema.json').read_text())
    assert set(kind['enum']) == {
        f'{side}_schema_{part}' for side in ('schema_source', 'data_source')
        for part in ('url', 'identifier', 'version')}
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
    from jsonschema import Draft202012Validator
    sources = [json.loads(path.read_text()) for folder in (
        LIB / f'naming/convention/intf/src/product/{family}',
        LIB / f'naming/convention/sourcecode/src/product/{family}', base)
        for path in folder.rglob('*.schema.json')]
    registry = Registry().with_resources((obj['$id'], Resource.from_contents(obj, default_specification=DRAFT202012)) for obj in sources)
    schema = next(obj for obj in sources if obj['$id'].endswith(f'data-object-naming-conventions_1.{suffix}.schema.json'))
    obj = yaml.safe_load((METHOD_CONFIG / 'algites-java-codegen-method-conventions.yml').read_text())
    entry = obj['GeneratedDataObjectMethodNameConventions']['NameConventions']['algites-java-codegen-standard_1']
    validator = Draft202012Validator(schema, registry=registry)
    validator.validate(obj)
    entry['SchemaMetadataNaming']['nonsense'] = '$bad'
    assert not validator.is_valid(obj)
    entry['SchemaMetadataNaming'].pop('nonsense')
    entry['SchemaMetadataNaming']['schema_source_schema_url'] = ''
    assert not validator.is_valid(obj)
    entry['SchemaMetadataNaming']['data_source_schema_url'] = ''
    assert validator.is_valid(obj)
