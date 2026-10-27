"""Regression tests for SDO classpath and invocation settings precedence."""
from __future__ import annotations
from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import _settings


def test_defaults_are_keyed_and_split_into_named_sdo_roles(monkeypatch):
    from pathlib import Path
    monkeypatch.chdir(Path(__file__).resolve().parents[7])
    result = _settings([])
    assert '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER' in result
    assert '--output-technology-naming-convention=python:yamldefs:sdointf=algites-python-gen-data-yaml-intf-versioned_1' in result
    assert '--output-technology-naming-convention=python:yamldefs:sdoclass=algites-python-gen-data-yaml-class-versioned_1' in result


def test_explicit_sdo_settings_and_boolean_removal(monkeypatch, tmp_path):
    from pathlib import Path
    monkeypatch.chdir(Path(__file__).resolve().parents[7])
    settings = tmp_path / 'custom.settings'
    settings.write_text('--naming-conventions-file:jsondefs=\n'
                        '--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER\n'
                        '--check=true\n')
    result = _settings([f'--settings-file={settings}', '--check=false'])
    assert '--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER' in result
    assert not any(value.endswith('classpath:algites-jsondef-name-conventions.yml') for value in result)
    assert '--check' not in result


def test_missing_input_source_root_is_informational(tmp_path, capsys, monkeypatch):
    from pathlib import Path
    from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main
    monkeypatch.chdir(Path(__file__).resolve().parents[7])
    assert main([f'--repository-root={tmp_path}']) == 0
    assert 'skipping configured input directory (not found)' in capsys.readouterr().err


def test_all_sys_path_settings_are_merged_before_explicit_invocation(monkeypatch, tmp_path):
    """Every classpath settings file participates; CLI still has final priority."""
    from pathlib import Path
    import sys
    monkeypatch.chdir(Path(__file__).resolve().parents[7])
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    for directory in (first, second):
        (directory / 'eu/algites/tool/codegen/sdo').mkdir(parents=True)
    name = 'sdocodegen-python.settings'
    (second / 'eu/algites/tool/codegen/sdo/' / name).write_text(
        '--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER\n'
        '--naming-conventions-file:second=classpath:second-catalog.yml\n')
    (first / 'eu/algites/tool/codegen/sdo/' / name).write_text(
        '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER\n'
        '--naming-conventions-file:first=classpath:first-catalog.yml\n')
    monkeypatch.setattr(sys, 'path', [str(first), str(second)] + sys.path)
    merged = _settings([])
    assert '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER' in merged
    assert '--naming-conventions-file=classpath:second-catalog.yml' in merged
    assert '--naming-conventions-file=classpath:first-catalog.yml' in merged
    explicit = tmp_path / 'invocation.settings'
    explicit.write_text('--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER\n'
                        '--naming-conventions-file:second=\n')
    merged = _settings([f'--settings-file={explicit}',
        '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER'])
    assert '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER' in merged
    assert '--naming-conventions-file=classpath:second-catalog.yml' not in merged
    assert '--naming-conventions-file=classpath:first-catalog.yml' in merged


def test_packaged_and_direct_sys_path_settings_accumulate(monkeypatch, tmp_path):
    """importlib.resources and sys.path are layers, not mutually exclusive alternatives."""
    import sys
    from pathlib import Path
    from eu.algites.tool.codegen.sdo.impl.cli import _layered_settings
    monkeypatch.chdir(Path(__file__).resolve().parents[7])
    packaged = tmp_path / 'packaged'
    packaged.mkdir()
    name = 'sdocodegen-python.settings'
    (packaged / name).write_text('--naming-conventions-file:packaged=classpath:package-only.yml\n')
    original = _layered_settings.importlib.resources.files

    def files(package):
        if package == 'eu.algites.tool.codegen.sdo':
            return packaged
        return original(package)

    monkeypatch.setattr(_layered_settings.importlib.resources, 'files', files)
    direct = tmp_path / 'direct'
    direct.mkdir()
    (direct / name).write_text('--naming-conventions-file:direct=classpath:direct-only.yml\n')
    monkeypatch.setattr(sys, 'path', [str(direct)] + sys.path)
    values = _settings([])
    assert '--naming-conventions-file=classpath:package-only.yml' in values
    assert '--naming-conventions-file=classpath:direct-only.yml' in values


def test_packaged_defaults_resolve_from_python_source_classpath_outside_checkout(monkeypatch, tmp_path):
    """Gradle's temporary working directory must not hide packaged native defaults."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[7]
    config = root / 'generators/code/sdocodegen/intf/src/product/config'
    assert (config / 'eu/algites/tool/codegen/sdo/sdocodegen-python-default.settings').is_file()
    monkeypatch.syspath_prepend(str(config))
    monkeypatch.chdir(tmp_path)
    assert '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER' in _settings([])
