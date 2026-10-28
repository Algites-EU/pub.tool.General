"""Regressions for validating Python wheel and sdist product contents."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve().parents[1] / 'bootstrap' / 'prepare.py'


def _bootstrap():
    spec = importlib.util.spec_from_file_location('tool_native_bootstrap_python_verifier', SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def packages(tmp_path_factory):
    """Build real tool namespace packages with setuptools, without Cloudsmith."""
    module = _bootstrap()
    work = tmp_path_factory.mktemp('native-python-wheels')
    release = '1.1.dev20261028083823878247'
    records = module.module_records(ROOT, '1.1-SNAPSHOT', release)
    output = {}
    for path in ('generators/code/common', 'generators/code/defscodegen/intf'):
        record = next(item for item in records if item['path'] == path)
        project = module.stage_one_python(ROOT, work, record, release)
        dist = work / ('distributions-' + record['artifactId'])
        dist.mkdir()
        command = ('import setuptools.build_meta as b; '
                   f'd={str(dist)!r}; '
                   'print("SDIST:", b.build_sdist(d)); '
                   'print("WHEEL:", b.build_wheel(d))')
        result = subprocess.run([sys.executable, '-c', command], cwd=project,
                                text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr
        wheel, = dist.glob('*.whl')
        sdist, = dist.glob('*.tar.gz')
        output[path] = (module, record, release, project / 'src', wheel, sdist)
    return output


def _wheel_replace(source: Path, destination: Path, changes: dict[str, bytes | None]) -> None:
    with zipfile.ZipFile(source) as reader, zipfile.ZipFile(destination, 'w') as writer:
        for entry in reader.infolist():
            if entry.filename in changes:
                replacement = changes[entry.filename]
                if replacement is None:
                    continue
                writer.writestr(entry, replacement)
            else:
                writer.writestr(entry, reader.read(entry.filename))


def test_real_common_distribution_is_valid_and_contains_all_schemas(packages):
    module, record, release, source, wheel, sdist = packages['generators/code/common']
    module.verify_python_distribution(record, release, wheel, sdist, source)
    expected = module.expected_python_files(source)
    assert len(expected) == 13
    assert any(name.endswith('.xsd') for name in expected)
    assert any(name.endswith('.json') for name in expected)
    assert any(name.endswith('.yml') for name in expected)
    with zipfile.ZipFile(wheel) as archive:
        assert 'eu/algites/tool/codegen/common/__init__.py' in archive.namelist()
        assert all(archive.read(name) == path.read_bytes() for name, path in expected.items())


def test_generated_java_schema_metadata_and_properties_are_shipped(packages):
    module, record, release, source, wheel, sdist = packages['generators/code/defscodegen/intf']
    module.verify_python_distribution(record, release, wheel, sdist, source)
    expected = module.expected_python_files(source)
    properties = [name for name in expected if name.endswith('.properties')]
    # Two resource roots contain the same file, merged at one package path.
    assert len(properties) == 1
    with zipfile.ZipFile(wheel) as archive:
        assert all(archive.read(name) == expected[name].read_bytes() for name in properties)


def test_missing_wheel_product_file_is_rejected(packages, tmp_path):
    module, record, release, source, wheel, sdist = packages['generators/code/common']
    missing = next(name for name in module.expected_python_files(source) if name.endswith('.xsd'))
    broken = tmp_path / 'broken-missing.whl'
    _wheel_replace(wheel, broken, {missing: None})
    with pytest.raises(ValueError, match='Wheel is missing product file'):
        module.verify_python_distribution(record, release, broken, sdist, source)


def test_modified_wheel_product_file_is_rejected(packages, tmp_path):
    module, record, release, source, wheel, sdist = packages['generators/code/common']
    name = next(name for name in module.expected_python_files(source) if name.endswith('.xsd'))
    broken = tmp_path / 'broken-changed.whl'
    _wheel_replace(wheel, broken, {name: b'<schema>outdated</schema>'})
    with pytest.raises(ValueError, match='Wheel has modified product file'):
        module.verify_python_distribution(record, release, broken, sdist, source)


def test_missing_sdist_product_file_is_rejected(packages, tmp_path):
    module, record, release, source, wheel, sdist = packages['generators/code/common']
    missing = next(name for name in module.expected_python_files(source) if name.endswith('.xsd'))
    broken = tmp_path / 'broken-sdist.tar.gz'
    with tarfile.open(sdist, 'r:gz') as original, tarfile.open(broken, 'w:gz') as copy:
        for member in original.getmembers():
            if member.isfile() and member.name.endswith('/src/' + missing):
                continue
            copy.addfile(member, original.extractfile(member) if member.isfile() else None)
    with pytest.raises(ValueError, match='Source distribution is missing product file'):
        module.verify_python_distribution(record, release, wheel, broken, source)


def test_metadata_only_wheel_is_rejected(packages, tmp_path):
    module, record, release, source, wheel, sdist = packages['generators/code/common']
    broken = tmp_path / 'empty-product.whl'
    product_paths = module.expected_python_files(source)
    _wheel_replace(wheel, broken, {name: None for name in product_paths})
    with pytest.raises(ValueError, match='Wheel is missing product file'):
        module.verify_python_distribution(record, release, broken, sdist, source)


def test_empty_staged_source_is_rejected(packages, tmp_path):
    module, record, release, _, wheel, sdist = packages['generators/code/common']
    source = tmp_path / 'empty'
    source.mkdir()
    with pytest.raises(ValueError, match='Empty Python product'):
        module.verify_python_distribution(record, release, wheel, sdist, source)
