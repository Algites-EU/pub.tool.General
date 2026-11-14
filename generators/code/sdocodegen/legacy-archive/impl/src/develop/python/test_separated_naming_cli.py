"""Real CLI coverage for independent Common/SDO profiles and compatibility entry points."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main as current_main
from eu.algites.tool.codegen.sdo.old.impl.cli.aic_sdo_codegen_cli import main as historical_main
import test_handwritten_naming_cli as handwritten


@pytest.mark.parametrize('invoke', (current_main, historical_main))
def test_sdo_cli_renders_selected_common_and_specific_roles(tmp_path: Path, invoke):
    """A selected SDO composition changes the *generated* runtime accessor."""
    handwritten.test_handwritten_contract_uses_annotated_convention_not_filename(tmp_path)
    settings = tmp_path / 'custom.settings'
    profile_root = (Path(__file__).resolve().parents[5] / 'profile/algites/src/product/config'
                    / 'eu/algites/lib/naming/convention/sourcecode')
    sdo = yaml.safe_load((profile_root/'algites-python-sdo-codegen-conventions.yml').read_text())
    sdo['NameCompositions']['algites-python-raw_getter_1']['Segments'][0][
        'NameFragmentsSegmentValue']['Value'] = '_selectedRaw_'
    profile = tmp_path/'selected-sdo.yml'
    profile.write_text(yaml.safe_dump(sdo), encoding='utf-8')
    settings.write_text(settings.read_text(encoding='utf-8') + '\n'.join((
        f'--naming-conventions-file:codegen_common={profile_root / "algites-python-common-codegen-conventions.yml"}',
        f'--naming-conventions-file:codegen_sdo={profile}',
        '--common-codegen-naming-convention:python=algites-python-codegen-common_1',
        '--sdo-codegen-naming-convention:python=algites-python-sdocodegen-standard_1',
    )) + '\n', encoding='utf-8')
    assert invoke([f'--settings-file={settings}']) == 0
    contents = '\n'.join(file.read_text() for file in (tmp_path/'generated').rglob('*.py'))
    assert 'def _selectedRaw_Code(self)' in contents
    assert 'def _getRaw_Code(self)' not in contents
    assert 'def _isPresent_Code(self)' in contents
    assert 'def _unset_Code(self)' in contents


@pytest.mark.parametrize('invoke', (current_main, historical_main))
def test_sdo_cli_rejects_missing_specialization_and_cross_domain_mix(tmp_path: Path, invoke):
    """A selected common ID is insufficient, and Defs naming cannot configure SDO."""
    handwritten.test_handwritten_contract_uses_annotated_convention_not_filename(tmp_path)
    settings = tmp_path/'custom.settings'
    profile_root = (Path(__file__).resolve().parents[5]
                    / 'profile/algites/src/product/config'
                    / 'eu/algites/lib/naming/convention/sourcecode')
    settings.write_text(settings.read_text(encoding='utf-8') +
        f'--naming-conventions-file:codegen_common={profile_root / "algites-python-common-codegen-conventions.yml"}\n'
        '--common-codegen-naming-convention:python=algites-python-codegen-common_1\n'
        '--sdo-codegen-naming-convention:python=\n'
        '--naming-conventions-file:codegen_sdo=\n',
        encoding='utf-8')
    with pytest.raises(ValueError, match='both Common and SDO|needs Common and SDO'):
        invoke([f'--settings-file={settings}'])
    settings.write_text(settings.read_text(encoding='utf-8') +
        f'--naming-conventions-file:codegen_sdo={profile_root / "algites-python-defs-codegen-conventions.yml"}\n'
        '--sdo-codegen-naming-convention:python=algites-python-defscodegen-standard_1\n',
        encoding='utf-8')
    with pytest.raises(ValueError, match='Unknown Common/sdo|Missing .* naming profile|Conflicting naming profile selection'):
        invoke([f'--settings-file={settings}'])
