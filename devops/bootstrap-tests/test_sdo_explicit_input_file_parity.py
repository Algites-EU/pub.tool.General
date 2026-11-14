"""Explicit input files must not select adjacent DataObject contracts."""
from contextlib import contextmanager
from pathlib import Path
import pytest

TOOL = Path(__file__).resolve().parents[2]
LIB = TOOL.parent / 'pub.lib.General'


def _python_cli(monkeypatch):
    paths = (
        LIB / 'common/util/src/product/python',
        LIB / 'factory/cpdiscovery/intf/src/product/python',
        LIB / 'factory/cpdiscovery/impl/src/product/python',
        LIB / 'data/dataobject/intf/src/product/python',
        LIB / 'data/smartdataobject/intf/src/product/python',
        LIB / 'data/smartdataobject/impl/common/src/product/python',
        LIB / 'naming/convention/impl/src/product/python',
        LIB / 'naming/convention/intf/src/product/python',
        TOOL / 'generators/code/common/src/product/python',
        TOOL / 'generators/code/sdocodegen/intf/src/product/python',
        TOOL / 'generators/code/sdocodegen/impl/src/product/python',
        TOOL / 'generators/code/sdocodegen/cli/src/product/python',
    )
    for item in paths:
        monkeypatch.syspath_prepend(str(item))
    from eu.algites.tool.codegen.sdo.impl.cli import aic_sdo_codegen_cli
    return aic_sdo_codegen_cli


@pytest.mark.parametrize('single_file', (True, False))
def test_python_cli_single_file_is_not_parent_directory(monkeypatch, tmp_path, single_file):
    cli = _python_cli(monkeypatch)
    source = tmp_path / 'module/src/product/python/demo'
    source.mkdir(parents=True)
    (source / 'selected.py').write_text('class Selected:\n    __data_object__ = object()\n')
    (source / 'sibling.py').write_text('class Sibling:\n    __data_object__ = object()\n')
    (tmp_path / 'module/modustro-artifact.yml').write_text('Artifact: {}\n')
    seen = []
    class FakeCatalog:
        @staticmethod
        def load_many(_paths):
            return FakeCatalog()
        def with_codegen_naming_profiles(self, *_args):
            return self
        def profile(self, _name):
            return None
    @contextmanager
    def fake_catalog(_paths):
        yield [Path('fake.yml')]
    class FakeService:
        def generate_from_sources(self, root, selection, **_kwargs):
            seen.extend((root, tuple(selection.items())))
            return {}
    monkeypatch.setattr(cli, 'AIcNameConventionCatalog', FakeCatalog)
    monkeypatch.setattr(cli, 'expand_naming_catalogs', fake_catalog)
    monkeypatch.setattr(cli, 'AIcSdoCodegenService', FakeService)
    chosen = source / 'selected.py' if single_file else source.parent
    options = [
        f'--repository-root={tmp_path}',
        '--technology-sdointf-output-dir:python=module/src/product/python.gen',
        '--technology-sdoimpl-output-dir:python=module/src/product/python.gen',
        '--naming-conventions-file:codegen_common=classpath:fake-common.yml',
        '--naming-conventions-file:codegen_sdo=classpath:fake-sdo.yml',
        '--common-codegen-naming-convention:python=common',
        '--sdo-codegen-naming-convention:python=sdo',
        '--dointf-naming-convention:python=input',
        '--sdointf-naming-convention:python=mutable',
        '--sdoimpl-naming-convention:python=concrete',
        f'--sdo-input-paths:python={chosen}',
    ]
    with pytest.raises(Exception, match='No eligible DataObject'):
        cli._main(options)
    names = {name for selection in seen[1::2] for _rel, name in selection}
    assert names == ({'Selected'} if single_file else {'Selected', 'Sibling'})


def test_java_cli_source_selection_and_unknown_args_regression():
    source = (TOOL / 'generators/code/sdocodegen/cli/src/product/java'
              '/eu/algites/tool/codegen/sdo/impl/cli/AIcSdoCodegenCli.java').read_text()
    assert 'locSelectedSourceFiles.computeIfAbsent(locParent' in source
    assert '!locSelectedSourceFiles.get(locSourceRoot).contains(locSource)' in source
    assert 'locUnrestrictedSourceRoots.add(selected)' in source
    assert 'Set.of("technology-sdointf-output-dir"' in source
    assert 'default -> throw new AIxCodegenValidationException("Unknown SDO CLI argument: "' in source
    assert 'locQualified[1].equals("python")) continue;' not in source


def test_python_cli_rejects_unused_old_input_dir(monkeypatch):
    cli = _python_cli(monkeypatch)
    with pytest.raises(Exception, match='Unknown or unqualified Python SDO option'):
        cli._main(['--technology-dointf-input-dir:python=src/product/python.gen'])


def test_python_cli_rejects_malformed_other_language_qualifier(monkeypatch):
    """The peer-language bypass is valid only for one exact qualifier."""
    cli = _python_cli(monkeypatch)
    with pytest.raises(Exception, match='Unknown or unqualified Python SDO option'):
        cli._main(['--sdo-input-paths:java:unexpected=somewhere'])
