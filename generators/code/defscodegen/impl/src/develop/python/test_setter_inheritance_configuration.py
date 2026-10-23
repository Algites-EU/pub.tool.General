"""Regression tests for layered, qualified Codegen settings and setter policy."""
from __future__ import annotations
import pytest

from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy as Policy
from eu.algites.tool.codegen.defs.impl.standard._setter_inheritance_policy_configuration import effective_default
from eu.algites.tool.codegen.defs.impl.cli.aic_defs_codegen_cli import AIcDefsCodegenCli


def test_direct_service_has_stable_generic_default(monkeypatch):
    monkeypatch.delenv('ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY', raising=False)
    assert effective_default() is Policy.INHERIT_AS_GENERIC_PARAMETER


def test_explicit_native_invocation_policy(monkeypatch):
    monkeypatch.setenv('ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY', 'INHERIT_AS_FIXED_PARAMETER')
    assert effective_default() is Policy.INHERIT_AS_FIXED_PARAMETER


def test_invalid_explicit_policy_is_rejected(monkeypatch):
    monkeypatch.setenv('ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY', 'DEFAULT')
    with pytest.raises(ValueError, match='Unresolved'):
        effective_default()


def test_qualified_defaults_and_explicit_settings_override(monkeypatch, tmp_path):
    monkeypatch.chdir(__import__('pathlib').Path(__file__).resolve().parents[7])
    explicit = tmp_path / 'custom.settings'
    explicit.write_text('--schema-input-dir:xmldefs=\n--schema-input-dir:jsondefs=\n--naming-conventions-file:xmldefs=\n--naming-conventions-file:custom=resource:algites-yamldef-name-conventions.yml\n--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER\n')
    result = AIcDefsCodegenCli._expand_settings([f'--settings-file={explicit}',
        '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER'])
    assert '--schema-input-dir=yamldefs:src/product/yamldefs' in result
    assert not any(option.startswith('--schema-input-dir=xmldefs:') for option in result)
    assert not any(option.startswith('--schema-input-dir=jsondefs:') for option in result)
    assert result.count('--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER') == 1
    assert not any(option.endswith('classpath:algites-xmldef-name-conventions.yml') for option in result)
    assert any(option.endswith('resource:algites-yamldef-name-conventions.yml') for option in result)


def test_legacy_arguments_still_normalize_to_qualified_values(monkeypatch):
    monkeypatch.chdir(__import__('pathlib').Path(__file__).resolve().parents[7])
    result = AIcDefsCodegenCli._expand_settings([
        '--schema-input-dir=yamldefs:other/yamldefs',
        '--output-interface-technology-naming-convention=python:yamldefs:defsintf=my-role'])
    assert '--schema-input-dir=yamldefs:other/yamldefs' in result
    assert '--schema-input-dir=yamldefs:src/product/yamldefs' not in result
    assert '--output-interface-technology-naming-convention=python:yamldefs:defsintf=my-role' in result


def test_classpath_settings_overlay_and_explicit_priority(monkeypatch, tmp_path):
    from pathlib import Path
    monkeypatch.chdir(Path(__file__).resolve().parents[7])
    resource = (tmp_path / 'eu/algites/tool/codegen/defs')
    resource.mkdir(parents=True)
    (resource / 'algites-defscodegen-python.settings').write_text(
        '--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER\n'
        '--schema-input-dir:xmldefs=\n')
    monkeypatch.syspath_prepend(str(tmp_path))
    merged = AIcDefsCodegenCli._expand_settings([])
    assert '--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER' in merged
    assert not any(option.startswith('--schema-input-dir=xmldefs:') for option in merged)
    explicit = AIcDefsCodegenCli._expand_settings([
        '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER'])
    assert '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER' in explicit


def test_all_sys_path_settings_are_merged_before_explicit_invocation(monkeypatch, tmp_path):
    """Every classpath settings file participates; CLI still has final priority."""
    from pathlib import Path
    import sys
    monkeypatch.chdir(Path(__file__).resolve().parents[7])
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    for directory in (first, second):
        (directory / 'eu/algites/tool/codegen/defs').mkdir(parents=True)
    name = 'algites-defscodegen-python.settings'
    (second / 'eu/algites/tool/codegen/defs/' / name).write_text(
        '--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER\n'
        '--naming-conventions-file:second=classpath:second-catalog.yml\n')
    (first / 'eu/algites/tool/codegen/defs/' / name).write_text(
        '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER\n'
        '--naming-conventions-file:first=classpath:first-catalog.yml\n')
    monkeypatch.setattr(sys, 'path', [str(first), str(second)] + sys.path)
    merged = AIcDefsCodegenCli._expand_settings([])
    assert '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER' in merged
    assert '--naming-conventions-file=classpath:second-catalog.yml' in merged
    assert '--naming-conventions-file=classpath:first-catalog.yml' in merged
    explicit = tmp_path / 'invocation.settings'
    explicit.write_text('--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER\n'
                        '--naming-conventions-file:second=\n')
    merged = AIcDefsCodegenCli._expand_settings([f'--settings-file={explicit}',
        '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER'])
    assert '--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER' in merged
    assert '--naming-conventions-file=classpath:second-catalog.yml' not in merged
    assert '--naming-conventions-file=classpath:first-catalog.yml' in merged


def test_packaged_and_direct_sys_path_settings_accumulate(monkeypatch, tmp_path):
    """importlib.resources and sys.path are layers, not mutually exclusive alternatives."""
    import sys
    from pathlib import Path
    from eu.algites.tool.codegen.defs.impl.cli import _layered_settings
    monkeypatch.chdir(Path(__file__).resolve().parents[7])
    packaged = tmp_path / 'packaged'
    packaged.mkdir()
    name = 'algites-defscodegen-python.settings'
    (packaged / name).write_text('--naming-conventions-file:packaged=classpath:package-only.yml\n')
    original = _layered_settings.importlib.resources.files

    def files(package):
        if package == 'eu.algites.tool.codegen.defs':
            return packaged
        return original(package)

    monkeypatch.setattr(_layered_settings.importlib.resources, 'files', files)
    direct = tmp_path / 'direct'
    direct.mkdir()
    (direct / name).write_text('--naming-conventions-file:direct=classpath:direct-only.yml\n')
    monkeypatch.setattr(sys, 'path', [str(direct)] + sys.path)
    values = AIcDefsCodegenCli._expand_settings([])
    assert '--naming-conventions-file=classpath:package-only.yml' in values
    assert '--naming-conventions-file=classpath:direct-only.yml' in values
