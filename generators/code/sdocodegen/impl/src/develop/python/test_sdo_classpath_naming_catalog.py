"""Test classpath naming lookup with explicit sys.path filesystem precedence."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
from eu.algites.tool.codegen.sdo.impl.cli._catalog_sources import resolve_naming_catalog


def test_importlib_resource_is_used_without_direct_sys_path_override(monkeypatch, tmp_path):
    """A packaged naming catalog remains supported without a filesystem override."""
    from eu.algites.tool.codegen.sdo.impl.cli import _catalog_sources

    packaged = tmp_path / 'packaged'
    packaged.mkdir()
    (packaged / 'demo.yml').write_text('NameFragments: {packaged: []}\n', encoding='utf-8')
    real_files = _catalog_sources.importlib.resources.files

    def files(package):
        if package == 'eu.algites.lib.naming.convention':
            return packaged
        return real_files(package)

    monkeypatch.setattr(_catalog_sources.importlib.resources, 'files', files)
    monkeypatch.setattr(sys, 'path', [str(tmp_path / 'empty')])
    assert resolve_naming_catalog('classpath:demo.yml') == 'resource:demo.yml'
    assert resolve_naming_catalog('resource:demo.yml') == 'resource:demo.yml'


def test_direct_sys_path_overrides_importlib_and_reads_sibling(monkeypatch, tmp_path):
    """A directly listed sys.path root overrides a valid packaged catalog."""
    from eu.algites.tool.codegen.sdo.impl.cli import _catalog_sources

    packaged = tmp_path / 'packaged'
    packaged.mkdir()
    (packaged / 'demo.yml').write_text('NameFragments: {packaged: []}\n', encoding='utf-8')
    real_files = _catalog_sources.importlib.resources.files

    def files(package):
        if package == 'eu.algites.lib.naming.convention':
            return packaged
        return real_files(package)

    monkeypatch.setattr(_catalog_sources.importlib.resources, 'files', files)
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    (first / 'demo.yml').write_text(
        'StandardConventionsFile: standard-conventions.yml\n'
        'NameFragments: {selected: []}\n', encoding='utf-8')
    (first / 'standard-conventions.yml').write_text(
        'IdentifierConventions: {custom: "[a-z]+"}\n', encoding='utf-8')
    (second / 'demo.yml').write_text('NameFragments: {wrong: []}\n', encoding='utf-8')
    monkeypatch.setattr(sys, 'path', [str(first), str(second)])
    resolved = resolve_naming_catalog('classpath:demo.yml')
    assert resolved == str((first / 'demo.yml').resolve())
    assert resolve_naming_catalog('resource:demo.yml') == resolved
    catalog = AIcNameConventionCatalog.load_many([resolved])
    assert 'selected' in catalog._config['NameFragments']
    assert 'wrong' not in catalog._config['NameFragments']
    assert 'custom' in catalog._config['IdentifierConventions']


def test_missing_or_unsafe_classpath_catalog(monkeypatch, tmp_path):
    """Unsupported resource names fail rather than escaping a search root."""
    monkeypatch.setattr(sys, 'path', [str(tmp_path)])
    with pytest.raises(ValueError, match='Invalid classpath'):
        resolve_naming_catalog('classpath:../untrusted.yml')
    with pytest.raises(FileNotFoundError, match='not found'):
        resolve_naming_catalog('classpath:no-such-codegen-catalog-9931.yml')


def test_all_matching_catalogs_are_combined(monkeypatch, tmp_path):
    """A classpath catalog name loads every provider and sys.path copy."""
    from eu.algites.tool.codegen.sdo.impl.cli import _catalog_sources
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
    packaged = tmp_path / 'packaged'
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    for folder in (packaged, first, second):
        folder.mkdir()
    (packaged / 'multiple.yml').write_text('NameFragments: {packagedOnly: []}\n')
    (first / 'multiple.yml').write_text('NameFragments: {firstOnly: []}\n')
    (second / 'multiple.yml').write_text('NameFragments: {secondOnly: []}\n')
    original = _catalog_sources.importlib.resources.files

    def files(package):
        if package == 'eu.algites.lib.naming.convention':
            return packaged
        return original(package)

    monkeypatch.setattr(_catalog_sources.importlib.resources, 'files', files)
    monkeypatch.setattr(sys, 'path', [str(first), str(second)])
    with _catalog_sources.expand_naming_catalogs(['classpath:multiple.yml']) as sources:
        assert len(sources) == 3
        catalog = AIcNameConventionCatalog.load_many(sources)
        assert set(catalog._config['NameFragments']) == {
            'packagedOnly', 'firstOnly', 'secondOnly'}


def test_conflicting_classpath_catalog_definitions_fail(monkeypatch, tmp_path):
    """Combining sources must not silently replace incompatible naming IDs."""
    from eu.algites.tool.codegen.sdo.impl.cli import _catalog_sources
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    (first / 'overlap.yml').write_text('NameFragments: {same: [{Kind: constant_string, Value: first}]}\n')
    (second / 'overlap.yml').write_text('NameFragments: {same: [{Kind: constant_string, Value: second}]}\n')
    monkeypatch.setattr(sys, 'path', [str(first), str(second)])
    with _catalog_sources.expand_naming_catalogs(['classpath:overlap.yml']) as sources:
        with pytest.raises(ValueError, match='Conflicting naming definition'):
            AIcNameConventionCatalog.load_many(sources)


def test_moved_sourcecode_profile_and_shared_standard_in_separate_roots(monkeypatch, tmp_path):
    """Bootstrap resolves relocated sourcecode profiles without duplicating standards."""
    from eu.algites.tool.codegen.sdo.impl.cli import _catalog_sources
    base = tmp_path / 'config-profile'
    shared = tmp_path / 'config-intf'
    profile_root = base / 'eu/algites/lib/naming/convention/sourcecode'
    shared_root = shared / 'eu/algites/lib/naming/convention'
    profile_root.mkdir(parents=True)
    shared_root.mkdir(parents=True)
    (profile_root / 'moved-profile.yml').write_text(
        'StandardConventionsFile: standard-conventions.yml\n'
        'NameFragments: {moved_1: {Segments: [{Kind: constant_string, Value: moved}]}}\n',
        encoding='utf-8')
    (shared_root / 'standard-conventions.yml').write_text(
        'IdentifierConventions: {}\nVersionConventions: {}\n', encoding='utf-8')
    monkeypatch.setattr(sys, 'path', [str(base), str(shared)])
    assert _catalog_sources.resolve_naming_catalog('resource:moved-profile.yml') == str(
        (profile_root / 'moved-profile.yml').resolve())
    with _catalog_sources.expand_naming_catalogs(['resource:moved-profile.yml']) as files:
        catalog = AIcNameConventionCatalog.load_many(files)
        assert 'moved_1' in catalog._config['NameFragments']


def test_shared_intf_standard_is_resolved_from_base_namespace(monkeypatch, tmp_path):
    """Shared naming grammar stays at convention/, not convention/sourcecode/."""
    from eu.algites.tool.codegen.sdo.impl.cli import _catalog_sources
    root = tmp_path / 'library-root'
    shared = root / 'eu/algites/lib/naming/convention'
    shared.mkdir(parents=True)
    (shared / 'standard-conventions.yml').write_text(
        'IdentifierConventions: {}\n', encoding='utf-8')
    monkeypatch.setattr(sys, 'path', [str(root)])
    with _catalog_sources.expand_naming_catalogs(['resource:standard-conventions.yml']) as sources:
        assert len(sources) == 1
        assert Path(sources[0]).read_text().startswith('IdentifierConventions:')
