"""Regression: source SDO profile takes precedence over a stale published JAR.

All tests invoke the new settings loaders directly, without a Gradle build or
network access. Old/legacy generator implementations are intentionally untouched.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
JAVA = ROOT / 'generators/code/sdocodegen/cli/src/product/java/eu/algites/tool/codegen/sdo/impl/cli/AIcLayeredCodegenSettings.java'
COMMON_JAVA = ROOT / 'generators/code/common/src/product/java/eu/algites/tool/codegen/common/AIxCodegenValidationException.java'
PYTHON = ROOT / 'generators/code/sdocodegen/cli/src/product/python/eu/algites/tool/codegen/sdo/impl/cli/_layered_settings.py'
COMMON_PYTHON = ROOT / 'generators/code/common/src/product/python'
RESOURCE = Path('eu/algites/tool/codegen/sdo')
COMMON_ID = '--common-codegen-naming-convention:java=algites-java-codegen-common_1'
SDO_ID = '--sdo-codegen-naming-convention:java=algites-java-sdocodegen-standard_1'
SOURCE_DO = '--dointf-naming-convention:java=algites-java-gen-intf-versioned_1'
OLD_DO = '--dointf-naming-convention:java=algites-java-old-intf-versioned_1'


def _settings(*options: str) -> str:
    return '\n'.join(options) + '\n'


def _resource(where: Path, name: str, contents: str) -> None:
    dest = where / RESOURCE / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(contents, encoding='utf-8')


@pytest.fixture
def sample(tmp_path: Path):
    """Current checkout resource before stale JAR, with deliberately divergent DO ID."""
    source, packaged = tmp_path / 'source', tmp_path / 'packaged'
    _resource(source, 'sdocodegen-java-default.settings', '--check=false\n')
    _resource(source, 'sdocodegen-python-default.settings', '--check=false\n')
    for language in ('java', 'python'):
        old = _settings(COMMON_ID.replace(':java=', f':{language}='),
                        SDO_ID.replace(':java=', f':{language}='),
                        OLD_DO.replace(':java=', f':{language}='),
                        '--naming-conventions-file:codegen_sdo=classpath:obsolete.yml')
        new = _settings(COMMON_ID.replace(':java=', f':{language}='),
                        SDO_ID.replace(':java=', f':{language}='),
                        SOURCE_DO.replace(':java=', f':{language}='),
                        '--naming-conventions-file:codegen_sdo=classpath:current.yml')
        _resource(source, f'sdocodegen-{language}.settings', new)
        _resource(packaged, f'sdocodegen-{language}.settings', old)
    jar = tmp_path / 'published.jar'
    with zipfile.ZipFile(jar, 'w') as archive:
        for resource in packaged.rglob('*.settings'):
            archive.write(resource, resource.relative_to(packaged).as_posix())
    return source, packaged, jar


@pytest.fixture
def java_loader(tmp_path: Path):
    """Compile exactly the current SDO loader and shared diagnostics."""
    target = tmp_path / 'classes'
    target.mkdir()
    runner = tmp_path / 'Probe.java'
    runner.write_text('''
public class Probe {
    public static void main(String[] args) throws Exception {
        String[] values = eu.algites.tool.codegen.sdo.impl.cli.AIcLayeredCodegenSettings
            .expand(args, "sdocodegen", "java", "sdo");
        for (String value : values) System.out.println(value);
    }
}
''', encoding='utf-8')
    subprocess.run(['javac', '-d', str(target), str(COMMON_JAVA), str(JAVA), str(runner)],
                   check=True, capture_output=True, text=True)
    return target


def _java_run(java_loader: Path, cp: list[Path], cwd: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(['java', '-cp', ':'.join(map(str, [java_loader] + cp)), 'Probe'] + args,
                          cwd=cwd, capture_output=True, text=True)


def test_java_current_source_profile_overrides_published_copy(sample, java_loader, tmp_path):
    source, _, jar = sample
    result = _java_run(java_loader, [source, jar], tmp_path, [COMMON_ID, SDO_ID, SOURCE_DO])
    assert result.returncode == 0, result.stderr
    assert SOURCE_DO in result.stdout
    assert 'classpath:current.yml' in result.stdout
    assert OLD_DO not in result.stdout
    assert 'classpath:obsolete.yml' not in result.stdout


def test_java_independent_families_still_conflict(sample, java_loader, tmp_path):
    source, _, _ = sample
    other = tmp_path / 'other'
    _resource(other, 'sdocodegen-java.settings', _settings(
        '--common-codegen-naming-convention:java=standardprefix-java-codegen-common_1',
        '--sdo-codegen-naming-convention:java=standardprefix-java-sdocodegen-standard_1'))
    # With no explicit family the two different profiles must remain ambiguous.
    result = _java_run(java_loader, [source, other], tmp_path, [])
    assert result.returncode != 0
    assert 'Ambiguous Codegen naming profile overlays' in result.stderr


def test_python_current_source_profile_overrides_packaged_copy(sample, tmp_path, monkeypatch):
    source, packaged, _ = sample
    monkeypatch.chdir(tmp_path)
    # Resource order follows sys.path: source first, stale installed copy later.
    monkeypatch.syspath_prepend(str(packaged))
    monkeypatch.syspath_prepend(str(source))
    monkeypatch.syspath_prepend(str(COMMON_PYTHON))
    spec = importlib.util.spec_from_file_location('sdo_settings_priority_test', PYTHON)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    requested = [COMMON_ID.replace(':java=', ':python='),
                 SDO_ID.replace(':java=', ':python='),
                 SOURCE_DO.replace(':java=', ':python=')]
    actual = module.expand(requested, 'sdocodegen', 'python', 'sdo')
    assert SOURCE_DO.replace(':java=', ':python=') in actual
    assert '--naming-conventions-file:codegen_sdo=classpath:current.yml' in actual
    assert all('obsolete.yml' not in x and 'old-intf' not in x for x in actual)


def test_python_different_families_remain_ambiguous(sample, tmp_path, monkeypatch):
    source, _, _ = sample
    other = tmp_path / 'other'
    _resource(other, 'sdocodegen-python.settings', _settings(
        '--common-codegen-naming-convention:python=standardprefix-python-codegen-common_1',
        '--sdo-codegen-naming-convention:python=standardprefix-python-sdocodegen-standard_1'))
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(other))
    monkeypatch.syspath_prepend(str(source))
    monkeypatch.syspath_prepend(str(COMMON_PYTHON))
    spec = importlib.util.spec_from_file_location('sdo_settings_ambiguity_test', PYTHON)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match='Ambiguous Codegen naming profile overlays'):
        module.expand([], 'sdocodegen', 'python', 'sdo')
