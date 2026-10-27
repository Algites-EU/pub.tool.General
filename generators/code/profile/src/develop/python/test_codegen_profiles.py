"""Regression coverage for all native code generation profiles and their catalogs."""
from __future__ import annotations
from pathlib import Path
import yaml
import pytest

from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog

ROOT = Path(__file__).resolve().parents[7]
LIB = ROOT / 'pub.lib.General/naming/convention'
TOOL = ROOT / 'pub.tool.General/generators/code'
PATH = Path('eu/algites/lib/naming/convention')

@pytest.mark.parametrize('technology', ('java', 'python'))
@pytest.mark.parametrize('style,stem,result', (
    ('standardprefix','standard-prefix','IGDy_Customer_1'),
    ('standardpostfix','standard-postfix','Customer_GenYamlDataIntf_1'),
))
def test_roles_are_composed_without_algites_prefix(style, stem, result, technology):
    """The technology marker and role are independent of user-defined identifiers."""
    catalog = AIcNameConventionCatalog.load(
        LIB/'profile'/style/'src/product/config'/PATH/f'{stem}-{technology}-name-conventions.yml')
    profile = f'{stem}-{technology}-gen-data-yaml-intf-versioned_1'
    assert catalog.format(profile, 'main_container_name',
                          {'identifier':'Customer','version':'1'}, 'upper_camel_case_1') == result
    assert catalog.matches(profile, 'main_container_name', result)

@pytest.mark.parametrize('technology', ('java','python'))
def test_arbitrary_user_name_remains_part_of_the_entity(technology):
    """Postfix role suffix must not discard a legitimate *Impl entity name."""
    catalog = AIcNameConventionCatalog.load(
        LIB/'profile'/'standardpostfix'/'src/product/config'/PATH/
        f'standard-postfix-{technology}-name-conventions.yml')
    profile = f'standard-postfix-{technology}-gen-class-versioned_1'
    assert catalog.format(profile, 'main_container_name',
                          {'identifier':'MyImpl','version':'1'}, 'upper_camel_case_1') == 'MyImpl_GenImpl_1'

@pytest.mark.parametrize('style,stem', (('standardprefix','standard-prefix'),('standardpostfix','standard-postfix'),
                                        ('algites','algites')))
@pytest.mark.parametrize('technology', ('java','python'))
def test_both_generator_settings_select_one_valid_naming_catalog(style, stem, technology):
    """Defs and SDO settings in each profile are complete for either technology kind."""
    config = TOOL/'profile'/style/'src/product/config'
    methods = yaml.safe_load((config/PATH/f'{style}-{technology}-codegen-method-conventions.yml').read_text())
    for item in methods['GeneratedDataObjectMethodNameConventions']['NameConventions'].values():
        assert item['data_source_schema_url'] == '$schema'
        assert item['schema_source_schema_identifier'] == '$x-algites-schema-id'
        assert item['schema_source_schema_version'] == '$x-algites-schema-version'
    for generator,subdir in (('defscodegen','defs'),('sdocodegen','sdo')):
        settings = (config/f'eu/algites/tool/codegen/{subdir}'/
                    f'{generator}-{technology}.settings').read_text()
        assert f'classpath:{stem}-{technology}-name-conventions.yml' in settings
        assert f'classpath:{style}-{technology}-codegen-method-conventions.yml' in settings
        assert f'--generated-dataobject-method-naming-convention:{technology}=' in settings
        assert '--naming-conventions-file:standard=classpath:standard-conventions.yml' in settings

@pytest.mark.parametrize('style',('algites','standardprefix','standardpostfix'))
def test_native_artifact_is_build_time_settings_only(style):
    """Profile artifacts are not dependencies of the generated product."""
    meta=yaml.safe_load((TOOL/'profile'/style/'modustro-artifact.yml').read_text())
    assert set(meta['Artifact']['TechnologyKinds']) == {'java','python'}
    assert meta['Dependencies'][0]['Items'][0]['ArtifactId'] == f'pub.lib.General_naming.convention.profile.{style}'
    assert (TOOL/'profile'/style/'src/product/python/eu/algites/tool/codegen/profile'/style/'__init__.py').is_file()

@pytest.mark.parametrize('style', ('algites', 'standardprefix', 'standardpostfix'))
def test_defs_generator_outputs_both_languages_only_with_selected_profile(style, tmp_path):
    """The native generator respects the selected Java/Python profile without a built-in fallback."""
    import json
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import (
        AIcSchemaContractBindingsGenerator)

    stem = {'algites': 'algites', 'standardprefix': 'standard-prefix',
            'standardpostfix': 'standard-postfix'}[style]
    schemas = tmp_path/'intf/src/product/jsondefs/demo'
    schemas.mkdir(parents=True)
    (schemas/'customer_1.jsondef.schema.json').write_text(json.dumps({
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': 'urn:demo:customer:1', '$x-algites-schema-id': 'demo.customer',
        '$x-algites-schema-version': 1, 'type': 'object',
        'properties': {'Name': {'type': 'string'}}}))
    manifest = {
        'artifact': 'intf',
        'schema_inputs': [{'kind': 'jsondefs', 'directory': 'intf/src/product/jsondefs'}],
        'schema_input_naming_conventions': {'jsondefs': f'{stem}-jsondef-schema-versioned_1'},
        'technology_outputs': {lang: f'intf/src/product/{lang}.gen'
                               for lang in ('java', 'python')},
        'technology_output_naming_conventions': {
            lang: {'jsondefs': f'{stem}-{lang}-gen-json-intf-versioned_1'}
            for lang in ('java', 'python')},
        'naming_convention_files': [
            'resource:standard-conventions.yml',
            f'resource:{stem}-java-name-conventions.yml',
            f'resource:{stem}-python-name-conventions.yml',
            f'resource:{stem}-jsondef-name-conventions.yml'],
        'languages': ['java', 'python'],
    }
    generated = AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, manifest)
    assert len(generated) == 2
    assert {row['language'] for row in generated} == {'java', 'python'}
    assert {row['type'] for row in generated} == {
        {'algites': 'AIig_jCustomer_1', 'standardprefix': 'IGj_Customer_1',
         'standardpostfix': 'Customer_GenJsonIntf_1'}[style]}


@pytest.mark.parametrize('style', ('algites', 'standardprefix', 'standardpostfix'))
def test_sdo_generator_emits_native_types_under_selected_profile(style):
    """SDO role selection supports each independent native naming family without fixed AI prefixes."""
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import (
        AIcNameConventionCatalog)
    from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
    from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
    from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
    from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService

    stem = {'algites': 'algites', 'standardprefix': 'standard-prefix',
            'standardpostfix': 'standard-postfix'}[style]
    catalog = AIcNameConventionCatalog.load_many([
        LIB/'profile'/style/'src/product/config'/PATH/f'{stem}-python-name-conventions.yml',
        TOOL/'profile'/style/'src/product/config'/PATH/f'{style}-python-codegen-method-conventions.yml',
    ]).with_generated_method_profile(f'{stem}-python-codegen-standard_1')
    incoming = f'{stem}-python-gen-intf-versioned_1'
    mutable = f'{stem}-python-gen-data-intf-versioned_1'
    implementation = f'{stem}-python-gen-data-class-versioned_1'
    typename = catalog.format(incoming, 'main_container_name',
                              {'identifier': 'Customer', 'version': '1'}, 'upper_camel_case_1')
    read_contract = type(typename, (AIiDataObject,), {
        '__module__': 'demo.contracts.'+typename.lower(),
        '__data_object__': AIcdDataObject(schema_id='demo.customer', schema_version=1,
                                          naming_convention=incoming),
        '__data_object_fields__': (AIcdDataObjectField(field_name='Name', getter_name='getName'),),
        'getName': lambda self: None,
    })
    roles = ({'common': incoming}, {'common': mutable}, {'common': implementation}, catalog)
    result = AIcSdoCodegenService().generate(read_contract, naming=roles)
    expected_interface = catalog.format(mutable, 'main_container_name',
              {'identifier': 'Customer', 'version': '1'}, 'upper_camel_case_1')
    expected_class = catalog.format(implementation, 'main_container_name',
              {'identifier': 'Customer', 'version': '1'}, 'upper_camel_case_1')
    assert result.mutable_interface.type_name == expected_interface
    assert result.implementation.type_name == expected_class
    with pytest.raises(ValueError, match='Missing explicit SDO'):
        AIcSdoCodegenService().generate(read_contract)


def test_generators_reject_missing_explicit_output_profile(tmp_path):
    """An installed Algites package is not permission to choose its naming rules implicitly."""
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import (
        AIcSchemaContractBindingsGenerator)
    from eu.algites.tool.codegen.defs.impl.standard.aic_generation_names import AIcGenerationNames
    from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
    with pytest.raises(ValueError, match='No explicit output naming catalog'):
        AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, {
            'artifact': '.', 'languages': ['java', 'python']})
    with pytest.raises(ValueError, match='No output naming profile configured'):
        AIcGenerationNames().render('Customer', 1, object(), AInDefsNameRole.INTERFACE_TYPE)
