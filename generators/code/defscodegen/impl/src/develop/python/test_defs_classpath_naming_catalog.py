"""Test classpath naming lookup with explicit sys.path filesystem precedence."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
from eu.algites.tool.codegen.defs.impl.standard._catalog_sources import resolve_naming_catalog


def test_importlib_resource_is_used_without_direct_sys_path_override(monkeypatch, tmp_path):
    """A packaged naming catalog remains supported without a filesystem override."""
    from eu.algites.tool.codegen.defs.impl.standard import _catalog_sources

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
    from eu.algites.tool.codegen.defs.impl.standard import _catalog_sources

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
    catalog = AIcNameConventionCatalog_1.load_many([resolved])
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
    from eu.algites.tool.codegen.defs.impl.standard import _catalog_sources
    from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
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
        catalog = AIcNameConventionCatalog_1.load_many(sources)
        assert set(catalog._config['NameFragments']) == {
            'packagedOnly', 'firstOnly', 'secondOnly'}


def test_conflicting_classpath_catalog_definitions_fail(monkeypatch, tmp_path):
    """Combining sources must not silently replace incompatible naming IDs."""
    from eu.algites.tool.codegen.defs.impl.standard import _catalog_sources
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    (first / 'overlap.yml').write_text('NameFragments: {same: [{Kind: constant_string, Value: first}]}\n')
    (second / 'overlap.yml').write_text('NameFragments: {same: [{Kind: constant_string, Value: second}]}\n')
    monkeypatch.setattr(sys, 'path', [str(first), str(second)])
    with _catalog_sources.expand_naming_catalogs(['classpath:overlap.yml']) as sources:
        with pytest.raises(ValueError, match='Conflicting naming definition'):
            AIcNameConventionCatalog_1.load_many(sources)
