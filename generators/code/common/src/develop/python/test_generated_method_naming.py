"""Cross-generator method naming contract and schema regression tests."""
from pathlib import Path
import json
import yaml
import pytest
from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog


ROOT = Path(__file__).resolve().parents[7]
LIB = ROOT / 'pub.lib.General'
TOOL = ROOT / 'pub.tool.General'
LIB_CONFIG = LIB / 'naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention'
METHOD_CONFIG = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention'
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
        'algites-java-codegen-standard_1']['StructureNaming']) == set(EXPECTED)
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
    from jsonschema import Draft202012Validator
    source_root = LIB / f'naming/convention/intf/src/product/{family}'
    method_root = TOOL / f'generators/code/common/src/product/{family}'
    definitions = [json.loads(path.read_text(encoding='utf-8'))
                   for base in (source_root, method_root)
                   for path in base.rglob('*.schema.json')]
    resources = Registry().with_resources((item['$id'], Resource.from_contents(item))
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
    assert f'classpath:algites-{technology}-codegen-method-conventions.yml' in settings

@pytest.mark.parametrize('suffix', ('url', 'identifier', 'version'))
def test_method_catalog_rejects_enabled_wire_field_without_schema_source(tmp_path, suffix):
    """The output mapping cannot emit a schema value which has no declared source."""
    instance = yaml.safe_load((METHOD_CONFIG/'algites-python-codegen-method-conventions.yml').read_text())
    method = instance['GeneratedDataObjectMethodNameConventions']['NameConventions'][
        'algites-python-codegen-standard_1']
    method[f'schema_source_schema_{suffix}'] = ''
    method[f'data_source_schema_{suffix}'] = f'$output_{suffix}'
    path = tmp_path/'inconsistent.yml'
    path.write_text(yaml.safe_dump(instance), encoding='utf-8')
    with pytest.raises(ValueError, match=f'data_source_schema_{suffix} requires schema_source_schema_{suffix}'):
        AIcNameConventionCatalog.load(path)


@pytest.mark.parametrize('technology', ('java', 'python'))
def test_default_method_profile_metadata_matches_algites(technology):
    """The selected output method profile includes all six explicit wire mappings."""
    source = yaml.safe_load((METHOD_CONFIG/f'algites-{technology}-codegen-method-conventions.yml').read_text())
    name = f'algites-{technology}-codegen-standard_1'
    method = source['GeneratedDataObjectMethodNameConventions']['NameConventions'][name]
    assert {key: method[key] for key in ('schema_source_schema_url',
        'schema_source_schema_identifier', 'schema_source_schema_version',
        'data_source_schema_url', 'data_source_schema_identifier',
        'data_source_schema_version')} == {
            'schema_source_schema_url': '$id',
            'schema_source_schema_identifier': '$x-algites-schema-id',
            'schema_source_schema_version': '$x-algites-schema-version',
            'data_source_schema_url': '$schema',
            'data_source_schema_identifier': '', 'data_source_schema_version': ''}
