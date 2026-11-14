"""Verify the active three-part Common / Defs / SDO profile architecture."""
from pathlib import Path
import yaml
import pytest

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
PROFILES = ('algites', 'standardprefix', 'standardpostfix')
LANGUAGES = ('java', 'python')


@pytest.mark.parametrize('profile', PROFILES)
@pytest.mark.parametrize('language', LANGUAGES)
def test_new_split_catalogs_are_selected_by_native_settings(profile, language):
    root = TOOL / 'generators/code/profile' / profile / 'src/product/config'
    catalog_root = root / 'eu/algites/lib/naming/convention/sourcecode'
    for generator, specialization, root_key, option in (
        ('defscodegen', 'defs', 'DefsCodegenNameConventions', 'codegen_defs'),
        ('sdocodegen', 'sdo', 'SdoCodegenNameConventions', 'codegen_sdo'),
    ):
        catalog = catalog_root / f'{profile}-{language}-{specialization}-codegen-conventions.yml'
        common = catalog_root / f'{profile}-{language}-common-codegen-conventions.yml'
        settings = root / f'eu/algites/tool/codegen/{specialization}/{generator}-{language}.settings'
        selected = settings.read_text(encoding='utf-8')
        assert f'--naming-conventions-file:codegen_common=classpath:{common.name}' in selected
        assert f'--naming-conventions-file:{option}=classpath:{catalog.name}' in selected
        assert f'--{specialization}-codegen-naming-convention:{language}=' in selected
        assert '--generated-dataobject-method-naming-convention:' not in selected
        document = yaml.safe_load(catalog.read_text(encoding='utf-8'))
        shared = yaml.safe_load(common.read_text(encoding='utf-8'))
        assert root_key in document
        assert 'CommonCodegenNameConventions' in shared
        assert len(document[root_key]['NameConventions']['NameConvention']) == 1
        assert len(shared['CommonCodegenNameConventions']['NameConventions']['NameConvention']) == 1


@pytest.mark.parametrize('profile', PROFILES)
@pytest.mark.parametrize('language', LANGUAGES)
def test_retired_parallel_catalogs_not_packaged(profile, language):
    root = (TOOL / 'generators/code/profile' / profile /
            'src/product/config/eu/algites/lib/naming/convention/sourcecode')
    for obsolete in ('dataobject', 'smartdataobject'):
        assert not (root / f'{profile}-{language}-{obsolete}-conventions.yml').exists()
    # The legacy method catalog is still needed by currently exercised
    # development utilities, but not selected by native Defs/SDO settings.
    assert (root / f'{profile}-{language}-codegen-method-conventions.yml').is_file()


@pytest.mark.parametrize('profile', PROFILES)
@pytest.mark.parametrize('language', LANGUAGES)
@pytest.mark.parametrize('generator, subpackage', [('defscodegen', 'defs'), ('sdocodegen', 'sdo')])
def test_public_profile_settings_alias_matches_native_overlay(profile, language, generator, subpackage):
    """The two distributed settings names are exact aliases, not competing profiles."""
    root = TOOL / 'generators/code/profile' / profile / 'src/product/config'
    directory = root / 'eu/algites/tool/codegen' / subpackage
    prefixed = directory / f'algites-{generator}-{language}.settings'
    selected = directory / f'{generator}-{language}.settings'
    assert prefixed.is_file() and selected.is_file()
    assert prefixed.read_bytes() == selected.read_bytes()
