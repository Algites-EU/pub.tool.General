"""Regression tests for scope-specific offline schema maps and build-free uploads."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
from zipfile import ZipFile

import pytest

TOOL = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
BOOTSTRAP = TOOL / 'devops/bootstrap'


def _load(filename: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, filename)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def test_source_map_includes_current_transitive_naming_schema(tmp_path):
    mapping_module = _load(BOOTSTRAP / 'schema-locations.py', 'schema_map_regression')
    scope = TOOL / 'generators/code/sdocodegen/intf'
    target = tmp_path / 'schema-locations.properties'
    count = mapping_module.save(TOOL, scope, target)
    assert count > 0
    mapping = dict(line.split('=', 1) for line in target.read_text().splitlines()
                   if line and not line.startswith('#'))
    url = ('https://defs.dev.algites.eu/api/jsondefs/eu/algites/lib/'
           'naming/convention/common-naming-conventions_1.jsondef.schema.json')
    current = Path(mapping[url])
    assert current.is_file()
    assert current.read_text().find('"$id"') >= 0
    assert 'pub.lib.General/naming/convention/intf/src/product/jsondefs/' in str(current)
    assert any('/yamldefs/' in value for value in mapping.values())
    assert any('/xmldefs/' in value for value in mapping.values())
    assert not any('/src/develop/' in value for value in mapping.values())
    assert all('/build/' not in value for value in mapping.values())


def test_resolver_map_is_strict_and_never_calls_web(tmp_path):
    resolver_path = (TOOL / 'generators/code/defscodegen/impl/src/product/python/eu/'
                     'algites/tool/codegen/defs/impl/standard/schema_reference_resolver.py')
    mod = _load(resolver_path, 'schema_reference_resolver_map_regression')
    url = 'https://defs.dev.algites.eu/api/jsondefs/example_1.jsondef.schema.json'
    source = tmp_path / 'schema.jsondef.schema.json'
    source.write_text(json.dumps({'$id': url, 'type': 'object'}))
    config = tmp_path / 'locations.properties'
    config.write_text(f'{url}={source}\n')
    calls = []
    resolver = mod.SchemaReferenceResolver((), tmp_path / 'cache',
                    locations_file=config, fetch=lambda *args: calls.append(args))
    assert resolver.resolve(url + '#/$defs/Person').origin == str(source)
    with pytest.raises(FileNotFoundError, match='absent from --schema-locations'):
        resolver.resolve('https://defs.dev.algites.eu/api/jsondefs/missing_1.jsondef.schema.json')
    assert calls == []
    assert not (tmp_path / 'cache').exists()
    config.write_text(f'{url}={source}\n{url}={source}\n')
    with pytest.raises(ValueError, match='duplicate schema URL'):
        mod.SchemaReferenceResolver((), locations_file=config)
    config.write_text(f'{url}={source}\n')
    source.write_text(json.dumps({'$id': 'https://wrong.invalid/a', 'type': 'object'}))
    with pytest.raises(ValueError, match='mismatch'):
        mod.SchemaReferenceResolver((), locations_file=config).resolve(url)


def _write_wheel(target: Path, distribution: str, version: str):
    name = distribution.replace('-', '_')
    filename = target / f'{name}-{version}-py3-none-any.whl'
    with ZipFile(filename, 'w') as wheel:
        wheel.writestr(f'{name}-{version}.dist-info/METADATA',
                       f'Metadata-Version: 2.1\nName: {distribution}\nVersion: {version}\n')
    return filename


def _make_repository(tmp_path, monkeypatch, version='1.1-SNAPSHOT'):
    prepared = _load(BOOTSTRAP / 'prepare.py', 'prepare_upload_regression')
    records = prepared.module_records(TOOL, version, '0')
    record = next(item for item in records if item['path'] == 'generators/code/sdocodegen/intf')
    java_root = tmp_path / 'java'
    python_root = tmp_path / 'python'
    dest = java_root / record['groupId'].replace('.', '/') / record['artifactId'] / version
    dest.mkdir(parents=True)
    stem = record['artifactId'] + '-' + version
    for ext in ('.jar', '.pom', '.module', '-sources.jar'):
        target = dest / (stem + ext)
        if ext == '.pom':
            target.write_text('<project><groupId>' + record['groupId'] + '</groupId><artifactId>' +
                              record['artifactId'] + '</artifactId><version>' + version + '</version></project>')
        else:
            target.write_bytes(b'not-empty-publication')
    (python_root / 'packages').mkdir(parents=True)
    monkeypatch.setenv('MODUSTRO_LOCAL_MAVEN_REPOSITORY', str(java_root))
    monkeypatch.setenv('MODUSTRO_LOCAL_PYTHON_REPOSITORY', str(python_root))
    return record, dest, python_root / 'packages'


def test_upload_chooses_latest_complete_python_build(tmp_path, monkeypatch):
    record, _, packages = _make_repository(tmp_path, monkeypatch)
    for version in ('1.1.dev20261113080000', '1.1.dev20261113120000'):
        _write_wheel(packages, record['pythonName'], version)
        (packages / (record['pythonName'] + '-' + version + '.tar.gz')).write_bytes(b'distribution')
    upload = _load(BOOTSTRAP / 'upload-prepared.py', 'upload_prepared_regression')
    java_manifest, python_manifest = upload.prepare(
        TOOL, TOOL / record['path'], tmp_path / 'output', '1.1-SNAPSHOT')
    assert len(java_manifest.read_text().splitlines()) == 1
    lines = python_manifest.read_text().splitlines()
    assert len(lines) == 1
    assert '1.1.dev20261113120000' in lines[0]


def test_incomplete_latest_python_build_fails_before_any_manifest(tmp_path, monkeypatch):
    record, _, packages = _make_repository(tmp_path, monkeypatch)
    _write_wheel(packages, record['pythonName'], '1.1.dev20261113120000')
    upload = _load(BOOTSTRAP / 'upload-prepared.py', 'upload_prepared_incomplete_regression')
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='incomplete'):
        upload.prepare(TOOL, TOOL / record['path'], output, '1.1-SNAPSHOT')
    assert not (output / 'packages.tsv').exists()
    assert not (output / 'python-packages.tsv').exists()
