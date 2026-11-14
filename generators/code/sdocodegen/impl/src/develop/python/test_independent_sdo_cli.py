"""Standalone independent SDO CLI regressions using only current contracts.

No archived Defs/SDO implementation is imported. Naming roles are the same
format-neutral input, mutable interface and implementation roles in Java/Python.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main
from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException


TOOL = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == 'pub.tool.General')
LIB = TOOL.parent / 'pub.lib.General'


def _fixture(tmp_path: Path, *, shared_package: bool = False) -> Path:
    """Create handwritten DO inputs and explicit current Algites profile settings."""
    root = tmp_path / 'repository'
    source = root / 'intf/src/product/python/exampleinvoice'
    source.mkdir(parents=True)
    (source / '__init__.py').touch()
    (source / 'invoice_models.py').write_text('''
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField

class AIigInvoice_1(AIiDataObject):
    __data_object__ = AIcdDataObject()
    @AIaDataObjectField(dataFieldName='invoice_code')
    def getCode(self) -> str:
        raise NotImplementedError
''', encoding='utf-8')
    (source / 'other_models.py').write_text('''
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField

class AIigOther_1(AIiDataObject):
    __data_object__ = AIcdDataObject()
    @AIaDataObjectField(dataFieldName='other_value')
    def getValue(self) -> str:
        raise NotImplementedError
''', encoding='utf-8')
    naming = LIB / ('naming/convention/profile/algites/src/product/config/'
                    'eu/algites/lib/naming/convention/sourcecode')
    codegen = TOOL / ('generators/code/profile/algites/src/product/config/'
                      'eu/algites/lib/naming/convention/sourcecode')
    args = [
        f'--repository-root={root}',
        '--sdo-input-paths:python=intf/src/product/python',
        '--technology-sdointf-output-dir:python=intf/src/product/python.gen',
        '--technology-sdoimpl-output-dir:python=intf/src/product/python.gen',
        '--dointf-naming-convention:python=algites-python-gen-intf-versioned_1',
        '--sdointf-naming-convention:python=algites-python-gen-data-intf-versioned_1',
        '--sdoimpl-naming-convention:python=algites-python-gen-data-class-versioned_1',
        f'--naming-conventions-file:python={naming / "algites-python-name-conventions.yml"}',
        f'--naming-conventions-file:codegen_common={codegen / "algites-python-common-codegen-conventions.yml"}',
        f'--naming-conventions-file:codegen_sdo={codegen / "algites-python-sdo-codegen-conventions.yml"}',
        '--common-codegen-naming-convention:python=algites-python-codegen-common_1',
        '--sdo-codegen-naming-convention:python=algites-python-sdocodegen-standard_1',
    ]
    if not shared_package:
        args += ['--sdointf-subpackage=impl.intf', '--sdoclass-subpackage=impl']
    settings = tmp_path / 'current-sdo.settings'
    settings.write_text('\n'.join(args) + '\n', encoding='utf-8')
    return settings


def _generated(tmp_path: Path) -> list[Path]:
    return sorted((tmp_path / 'repository/intf/src/product/python.gen').rglob('*.py'))


def test_handwritten_interface_produces_writable_interface_and_implementation(tmp_path):
    """An independently handwritten contract generates both SDO roles."""
    settings = _fixture(tmp_path)
    assert main([f'--settings-file={settings}']) == 0
    generated = _generated(tmp_path)
    assert len(generated) == 4
    assert any('class AIigdInvoice_1(' in p.read_text() for p in generated)
    assert any('class AIcgdInvoice_1(' in p.read_text() for p in generated)
    # Canonical wire names stay on the authoritative read-only getter.
    assert any('def getCode(self)' in p.read_text() for p in generated)


def test_same_package_for_writable_and_concrete(tmp_path):
    """Current naming roles can coexist in one package without filename collisions."""
    settings = _fixture(tmp_path, shared_package=True)
    assert main([f'--settings-file={settings}']) == 0
    assert len(_generated(tmp_path)) == 4


def test_explicit_handwritten_class_selector(tmp_path):
    """Explicit class selection filters independent handwritten DO inputs."""
    settings = _fixture(tmp_path)
    assert main([f'--settings-file={settings}',
                 '--dointf-input-classes:python=exampleinvoice.invoice_models:AIigInvoice_1']) == 0
    assert len(_generated(tmp_path)) == 2


def test_unresolved_handwritten_class_is_not_silently_ignored(tmp_path):
    """A nonexistent selected interface must yield a validation error."""
    settings = _fixture(tmp_path)
    with pytest.raises((ValueError, AIxCodegenValidationException, ImportError)):
        main([f'--settings-file={settings}',
              '--dointf-input-classes:python=exampleinvoice.invoice_models:AIigMissing_1'])


@pytest.mark.parametrize('argument', [
    '--schema-input=x.xsd',
    '--defs-input-artifacts:python=some-package==1.1.dev',
    '--canonical-schema=x.json',
    '--schema-input-dir:python=./schemas',
    '--mutable-sdo-python=manifest.json',
])
def test_sdo_cli_does_not_accept_defs_schema_or_canonical_options(argument):
    """The standalone SDO CLI must reject Defs schema and canonical-model options."""
    algites = (TOOL / 'generators/code/profile/algites/src/product/config'
               / 'eu/algites/tool/codegen/sdo/sdocodegen-python.settings')
    assert algites.is_file()
    with pytest.raises(ValueError, match='Unknown|unqualified|Invalid'):
        main([f'--settings-file={algites}', argument])
