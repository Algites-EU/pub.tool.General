"""Regression coverage for standalone Codegen cleanup (never incremental upgrade)."""
from pathlib import Path
import importlib.util
import shutil
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parent / 'regenerate_sources.py'


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    repository = tmp_path / 'pub.tool.General'
    source = repository / 'generators/code/defscodegen/intf/src/product'
    (repository / 'generators/code/defscodegen/intf').mkdir(parents=True)
    (repository / 'generators/code/defscodegen/intf/modustro-artifact.yml').write_text('Artifact: {}\n')
    for name in ('java.gen', 'python.gen', 'java', 'config.gen'):
        target = source / name
        target.mkdir(parents=True)
        (target / 'stale').write_text('stale')
    decoy = repository / 'build/output/src/product/java.gen'
    decoy.mkdir(parents=True)
    (decoy / 'stale').write_text('must survive')
    return repository


def test_cleanup_clears_native_generated_content_but_not_handwritten_or_build(checkout):
    result = subprocess.run([sys.executable, str(SCRIPT), 'clean',
        '--repository', str(checkout)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    source = checkout / 'generators/code/defscodegen/intf/src/product'
    assert list((source / 'java.gen').iterdir()) == []
    assert list((source / 'python.gen').iterdir()) == []
    assert (source / 'java/stale').is_file()
    assert (source / 'config.gen/stale').is_file()
    assert (checkout / 'build/output/src/product/java.gen/stale').is_file()


def test_cleanup_does_not_follow_external_generated_symlinks(checkout, tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'important').write_text('unchanged')
    target = checkout / 'generators/code/defscodegen/intf/src/product/java.gen'
    shutil.rmtree(target)
    target.symlink_to(outside, target_is_directory=True)
    result = subprocess.run([sys.executable, str(SCRIPT), 'clean',
        '--repository', str(checkout)], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Refusing symlinked generated directory' in result.stderr
    assert (outside / 'important').read_text() == 'unchanged'


def test_codegen_manifest_has_both_languages_and_all_source_formats(checkout):
    spec = importlib.util.spec_from_file_location('regenerate_sources', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    artifact = checkout / 'generators/code/defscodegen/intf'
    for kind in ('jsondefs', 'yamldefs', 'xmldefs'):
        (artifact / 'src/product' / kind).mkdir(parents=True)
    result = module.manifest(checkout, artifact, ['java', 'python'])
    assert {entry['kind'] for entry in result['schema_inputs']} == {
        'jsondefs', 'yamldefs', 'xmldefs'}
    assert set(result['technology_outputs']) == {'java', 'python'}
    assert all(output.endswith('.gen') for output in result['technology_outputs'].values())


def test_scoped_clean_preserves_other_artifacts(checkout):
    from pathlib import Path
    other = checkout / 'generators/code/sdocodegen/intf/src/product/java.gen'
    other.mkdir(parents=True)
    (other / 'stale').write_text('keep')
    result = subprocess.run([
        sys.executable, str(SCRIPT), 'clean', '--repository', str(checkout),
        '--root', 'generators/code/defscodegen/intf',
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (other / 'stale').read_text() == 'keep'
    own = checkout / 'generators/code/defscodegen/intf/src/product/java.gen'
    assert not list(own.iterdir())


def test_root_escape_is_rejected_before_cleanup(checkout, tmp_path):
    other = tmp_path / 'external'
    other.mkdir()
    result = subprocess.run([
        sys.executable, str(SCRIPT), 'clean', '--repository', str(checkout),
        '--root', str(other),
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert (checkout / 'generators/code/defscodegen/intf/src/product/java.gen/stale').is_file()
