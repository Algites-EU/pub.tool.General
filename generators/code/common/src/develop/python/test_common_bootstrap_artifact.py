"""Regression tests for publication and discovery of shared naming resources."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tomllib

import pytest


_REPOSITORY = Path(__file__).resolve().parents[6]
_BOOTSTRAP = _REPOSITORY / 'generators/code/bootstrap-python-dist.py'


def _dist_module():
    """Import the standalone bootstrap distribution builder without a build installation."""
    spec = importlib.util.spec_from_file_location('codegen_bootstrap_dist', _BOOTSTRAP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_common_python_distribution_does_not_stage_method_profiles(tmp_path: Path):
    """The neutral Codegen common module must not activate an Algites profile."""
    module = _dist_module()
    name, stage = module.stage_artifact(
        _REPOSITORY, tmp_path, 'common', None, '1.1-SNAPSHOT', '1.1.dev20261024000000000')
    assert name == 'eu-algites-pub-tool-general-generators-code-common'
    assert not list((stage / 'src').rglob('*-codegen-method-conventions.yml'))
    for technology in ('java', 'python'):
        resource = (_REPOSITORY / 'generators/code/profile/algites/src/product/config'
                    / 'eu/algites/lib/naming/convention'
                    / f'algites-{technology}-codegen-method-conventions.yml')
        assert resource.is_file()
        assert 'GeneratedDataObjectMethodNameConventions:' in resource.read_text(encoding='utf-8')
    assert (stage / 'src/eu/algites/tool/codegen/common/__init__.py').is_file()


@pytest.mark.parametrize('generator', ['defscodegen', 'sdocodegen'])
def test_generator_impl_distribution_requires_same_release_common(tmp_path: Path, generator: str):
    """Native Python consumers must declare the newly published common distribution."""
    module = _dist_module()
    release = '1.1.dev20261024000000000'
    _, stage = module.stage_artifact(
        _REPOSITORY, tmp_path, generator, 'impl', '1.1-SNAPSHOT', release)
    metadata = tomllib.loads((stage / 'pyproject.toml').read_text(encoding='utf-8'))
    assert ('eu-algites-pub-tool-general-generators-code-common==' + release
            in metadata['project']['dependencies'])


def test_gradle_bootstrap_includes_common_in_both_java_builds():
    """Both standalone Java builds publish and consume the shared resource module."""
    contents = (_REPOSITORY / 'generators/code/bootstrap-selfhosted.sh').read_text(encoding='utf-8')
    assert contents.count("project(':common').projectDir") == 2
    assert contents.count("project(':common') {\n    sourceSets.main.resources.srcDirs") == 2
    assert contents.count("implementation project(':common')") >= 2
    assert "for locGenerator in common profile defscodegen sdocodegen; do" in contents
    assert contents.count("project(':profile-algites').projectDir") == 2
    assert contents.count("testImplementation project(':profile-algites')") >= 2
    assert "implementation project(':profile-algites')" not in contents.replace("testImplementation project(':profile-algites')", "")

@pytest.mark.parametrize('generator,part', [
    ('profile', 'algites'),
    ('profile', 'standardprefix'),
    ('profile', 'standardpostfix'),
    ('defscodegen', 'intf'),
    ('sdocodegen', 'intf'),
])
def test_bootstrap_wheel_verifies_neutral_settings_names(tmp_path: Path, generator: str, part: str):
    """Distribution checks must follow renamed settings, not historical Algites filenames."""
    import zipfile

    module = _dist_module()
    release = '1.1.dev20261026000000000'
    name = module.normalized_distribution(f'pub.tool.General_generators.code.{generator}.{part}')
    wheel = tmp_path / 'staged.whl'
    with zipfile.ZipFile(wheel, 'w') as archive:
        archive.writestr(f'{name.replace("-", "_")}-{release}.dist-info/METADATA',
                         f'Metadata-Version: 2.1\nName: {name}\nVersion: {release}\n')
        archive.writestr('eu/algites/tool/codegen/marker.py', '')
        if generator == 'profile':
            for technology in ('java', 'python'):
                archive.writestr(
                    f'eu/algites/lib/naming/convention/{part}-{technology}-codegen-method-conventions.yml', '')
                for family, basename in (('defs', 'defscodegen'), ('sdo', 'sdocodegen')):
                    archive.writestr(
                        f'eu/algites/tool/codegen/{family}/{basename}-{technology}.settings', '')
        else:
            family = 'defs' if generator == 'defscodegen' else 'sdo'
            archive.writestr(
                f'eu/algites/tool/codegen/{family}/{generator}-python-default.settings', '')
    module.verify_wheel(wheel, name, generator, part, release)
