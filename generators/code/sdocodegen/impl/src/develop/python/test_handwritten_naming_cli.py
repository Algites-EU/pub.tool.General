"""Verify that SDO CLI can select handwritten contracts independent of filenames."""
from __future__ import annotations

from pathlib import Path

import yaml
from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main


def test_handwritten_contract_uses_annotated_convention_not_filename(tmp_path: Path):
    """The contract's actual class and metadata must outrank source-file heuristics."""
    config = tmp_path / 'config'
    config.mkdir()
    # Resolve the resource through its installed package rather than relying on a checkout.
    from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
    packaged = AIcNameConventionCatalog_1.load_resource('algites-python-name-conventions.yml')
    profile = dict(packaged._config['NameConventions']['algites-python-gen-intf-versioned_1'])
    profile['StructureNaming'] = dict(profile['StructureNaming'])
    profile['StructureNaming']['main_container_name'] = 'handwritten-container_1'
    custom = {'IdentifierConventions': dict(packaged._config['IdentifierConventions']),
              'VersionConventions': dict(packaged._config['VersionConventions']),
              'NameFragments': dict(packaged._config['NameFragments']),
              'NameCompositions': {**packaged._config['NameCompositions'], 'handwritten-container_1': {'Segments': [
        {'Kind': 'constant_string', 'Value': 'Contract'},
        {'Kind': 'identifier', 'Convention': 'upper_camel_case_1'},
        {'Kind': 'constant_string', 'Value': '_'},
        {'Kind': 'version', 'Convention': 'positive_integer_1'},
    ]}}, 'NameConventions': {'handwritten-python-intf_1': profile}}
    # The custom catalog does not override any default naming ID.
    (config / 'handwritten.yml').write_text(yaml.safe_dump(custom), encoding='utf-8')
    root = tmp_path / 'source'
    folder = root / 'exampleinvoice'
    folder.mkdir(parents=True)
    (folder / 'invoice_models.py').write_text('''
from eu.algites.lib.data.dataobject.yamldefs.aii_yaml_data_object import AIiYamlDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField

class ContractInvoice_1(AIiYamlDataObject):
    __data_object__ = AIcdDataObject(schema_id='example.invoice', schema_version=1,
                                    naming_convention='handwritten-python-intf_1')
    __data_object_fields__ = (AIcdDataObjectField(field_name='Code', getter_name='getCode'),)
    def getCode(self) -> str:
        raise NotImplementedError
''', encoding='utf-8')
    settings = tmp_path / 'custom.settings'
    settings.write_text('\n'.join([
        f'--repository-root={tmp_path}',
        '--technology-dointf-input-dir=python:source',
        '--technology-sdointf-output-dir=python:generated',
        '--technology-sdoimpl-output-dir=python:generated',
        '--sdointf-subpackage=impl.intf',
        '--sdoclass-subpackage=impl',
        '--input-technology-naming-convention=python:yamldefs:defsintf=handwritten-python-intf_1',
        '--output-technology-naming-convention=python:yamldefs:sdointf=algites-python-gen-data-yaml-intf-versioned_1,sdoclass=algites-python-gen-data-yaml-class-versioned_1',
        '--naming-conventions-file=resource:standard-conventions.yml',
        '--naming-conventions-file=resource:algites-python-name-conventions.yml',
        f'--naming-conventions-file={config / "handwritten.yml"}',
    ]) + '\n', encoding='utf-8')
    assert main([f'--settings-file={settings}']) == 0
    files = sorted((tmp_path / 'generated').rglob('*.py'))
    assert len(files) == 2
    assert any('naming_convention=\'algites-python-gen-data-yaml-intf-versioned_1\'' in p.read_text()
               for p in files)
    assert any('naming_convention=\'algites-python-gen-data-yaml-class-versioned_1\'' in p.read_text()
               for p in files)
    assert all('invoice_models.py' not in str(p) for p in files)


def test_shared_package_is_allowed_for_distinct_names(tmp_path: Path):
    """Separate SDO roles may share a package if the generated names do not collide."""
    test_handwritten_contract_uses_annotated_convention_not_filename(tmp_path)
    settings = tmp_path / 'custom.settings'
    lines = [line for line in settings.read_text().splitlines()
             if not line.startswith('--sdointf-subpackage=')
             and not line.startswith('--sdoclass-subpackage=')]
    settings.write_text('\n'.join(lines + ['--sdointf-subpackage=', '--sdoclass-subpackage=']) + '\n', encoding='utf-8')
    assert main([f'--settings-file={settings}']) == 0
    sources = sorted((tmp_path / 'generated' / 'exampleinvoice').glob('*.py'))
    assert len(sources) == 2
    assert all('naming_convention=' in file.read_text(encoding='utf-8') for file in sources)
