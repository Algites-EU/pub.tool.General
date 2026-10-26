"""Regression coverage for all native code generation profiles and their catalogs."""
from __future__ import annotations
from pathlib import Path
import yaml
import pytest

from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1

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
    catalog = AIcNameConventionCatalog_1.load(
        LIB/style/'src/product/config'/PATH/f'{stem}-{technology}-name-conventions.yml')
    profile = f'{stem}-{technology}-gen-data-yaml-intf-versioned_1'
    assert catalog.format(profile, 'main_container_name',
                          {'identifier':'Customer','version':'1'}, 'upper_camel_case_1') == result
    assert catalog.matches(profile, 'main_container_name', result)

@pytest.mark.parametrize('technology', ('java','python'))
def test_arbitrary_user_name_remains_part_of_the_entity(technology):
    """Postfix role suffix must not discard a legitimate *Impl entity name."""
    catalog = AIcNameConventionCatalog_1.load(
        LIB/'standardpostfix'/'src/product/config'/PATH/
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
                    f'algites-{generator}-{technology}.settings').read_text()
        assert f'classpath:{stem}-{technology}-name-conventions.yml' in settings
        assert f'classpath:{style}-{technology}-codegen-method-conventions.yml' in settings
        assert f'--generated-dataobject-method-naming-convention:{technology}=' in settings
        assert '--naming-conventions-file:standard=classpath:standard-conventions.yml' in settings

@pytest.mark.parametrize('style',('algites','standardprefix','standardpostfix'))
def test_native_artifact_is_build_time_settings_only(style):
    """Profile artifacts are not dependencies of the generated product."""
    meta=yaml.safe_load((TOOL/'profile'/style/'modustro-artifact.yml').read_text())
    assert set(meta['Artifact']['TechnologyKinds']) == {'java','python'}
    assert meta['Dependencies'][0]['Items'][0]['ArtifactId'] == f'pub.lib.General_naming.convention.{style}'
    assert (TOOL/'profile'/style/'src/product/python/eu/algites/tool/codegen/profile'/style/'__init__.py').is_file()
