"""Temporary tool bootstrap CLI regression tests with an isolated fake repository."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'bootstrap'


@pytest.fixture
def repository(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / 'repository'
    target = root / 'devops/bootstrap'
    target.mkdir(parents=True)
    for filename in ('bootstrap.sh', 'clean_generated.py', 'bootstrap-config.py', 'modustro-bootstrap.yml',
                     'selfhosting.py', 'schema-locations.py', 'source-dependencies.py'):
        shutil.copy2(SOURCE / filename, target / filename)
    (root / 'modustro-source-repository.yml').write_text('''SourceRepository:
  Id: fake.repository
GroupId: eu.algites.fake
Version:
  ReleaseLineVersion: '1'
  Revision: 1
  QualifierKind: snapshot
''', encoding='utf-8')
    (target / 'bootstrap-specializations.yml').write_text('''CleanGeneratedDefault: true
RequireFreshGenerated: true
Snapshots:
  - ArtifactPath: a/leaf
    Program: promote-canonical-extgen.py
    AfterBootstrap: --refresh
    RequireWholeRepository: true
''', encoding='utf-8')
    (target / 'promote-canonical-extgen.py').write_text('pass\n', encoding='utf-8')
    (target / 'build.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
echo "build:$MODUSTRO_BOOTSTRAP_ROOT_RELATIVE:${1-}" >> "$TEST_LOG"
''')
    (target / 'generate.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
echo "generate:$MODUSTRO_BOOTSTRAP_ROOT_RELATIVE" >> "$TEST_LOG"
''')
    for branch in ('a', 'b'):
        artifact = root / branch / 'leaf'
        artifact.mkdir(parents=True)
        (artifact / 'modustro-artifact.yml').write_text('Artifact:\n  TechnologyKinds: [java, python]\n')
        src = artifact / 'src/product'
        for name in ('java.gen', 'python.gen', 'config.gen'):
            d = src / name
            d.mkdir(parents=True)
            (d / 'old').write_text(name)
        (src / 'java').mkdir()
        (src / 'java/Handwritten.java').write_text('retained')
    # Build trees MUST be excluded even if they imitate real source roots.
    decoy = root / 'build/output/src/product/java.gen'
    decoy.mkdir(parents=True)
    (decoy / 'old').write_text('untouched')
    log = root / 'invocations.log'
    env = dict(os.environ, TEST_LOG=str(log), ALGITES_PYTHON_EXECUTABLE='python3')
    return root, env


def invoke(repository, *params: str):
    root, env = repository
    result = subprocess.run(['bash', str(root / 'devops/bootstrap/bootstrap.sh'), *params],
                            cwd=root, env=env, capture_output=True, text=True, timeout=45)
    log = root / 'invocations.log'
    return result, log.read_text() if log.exists() else ''


def test_default_root_cleans_existing_generated_sources(repository):
    root, _ = repository
    result, log = invoke(repository, '--prepare-only')
    assert result.returncode == 0, result.stderr
    assert 'generate:.' in log and 'build:.:--prepare-only' in log
    for branch in ('a', 'b'):
        product = root / branch / 'leaf/src/product'
        for name in ('java.gen', 'python.gen'):
            assert not (product / name / 'old').exists()
        assert (product / 'config.gen/old').is_file()
        assert (product / 'java/Handwritten.java').is_file()
    assert (root / 'build/output/src/product/java.gen/old').is_file()


def test_explicit_cleanup_cleans_selected_generated_roots(repository):
    root, _ = repository
    result, log = invoke(repository, '--prepare-only',
                         '--cleanup-output-folder-before-generation=true')
    assert result.returncode == 0, result.stderr
    assert 'generate:.' in log
    for branch in ('a', 'b'):
        product = root / branch / 'leaf/src/product'
        for name in ('java.gen', 'python.gen'):
            assert not list((product / name).iterdir())
        assert (product / 'config.gen/old').is_file()


def test_scoped_root_only_touches_selected_branch(repository):
    root, _ = repository
    result, log = invoke(repository, '--root', 'a', '--prepare-only',
                         '--cleanup-output-folder-before-generation=true')
    assert result.returncode == 0, result.stderr
    assert 'generate:a' in log and 'build:a:--prepare-only' in log
    assert not list((root / 'a/leaf/src/product/java.gen').iterdir())
    assert (root / 'b/leaf/src/product/java.gen/old').is_file()


def test_plan_only_does_not_clean_or_generate(repository):
    root, _ = repository
    result, log = invoke(repository, '--plan-only', '--root=b')
    assert result.returncode == 0, result.stderr
    assert log == 'build:b:--plan-only\n'
    assert (root / 'b/leaf/src/product/java.gen/old').is_file()


def test_failed_generator_prevents_build(repository):
    root, _ = repository
    (root / 'devops/bootstrap/generate.sh').write_text('#!/usr/bin/env bash\nexit 13\n')
    result, log = invoke(repository, '--root=a', '--prepare-only')
    assert result.returncode == 13
    assert 'build:' not in log
    assert not (root / 'a/leaf/src/product/java.gen/old').exists()
    assert (root / 'b/leaf/src/product/java.gen/old').is_file()


def test_root_outside_repository_rejected(repository, tmp_path):
    root, _ = repository
    other = tmp_path / 'other'
    other.mkdir()
    result, log = invoke(repository, '--root', str(other))
    assert result.returncode != 0
    assert log == ''
    assert (root / 'a/leaf/src/product/java.gen/old').is_file()


def test_nonartifact_or_missing_root_rejected(repository):
    root, _ = repository
    for path in ('missing', 'a/leaf/src/product/java'):
        result, log = invoke(repository, '--root', path)
        assert result.returncode != 0, (path, result.stderr)
        assert not log
    assert (root / 'a/leaf/src/product/java.gen/old').is_file()


def test_symlinked_generated_root_rejected(repository, tmp_path):
    root, _ = repository
    target = root / 'a/leaf/src/product/java.gen'
    shutil.rmtree(target)
    target.symlink_to(root / 'b/leaf/src/product/java.gen', target_is_directory=True)
    result, log = invoke(repository, '--root', 'a')
    assert result.returncode != 0, result.stdout
    assert log == ''
    assert (root / 'b/leaf/src/product/java.gen/old').is_file()


def test_default_action_is_upload(repository):
    result, log = invoke(repository)
    assert result.returncode == 0, result.stderr
    assert 'build:.:--upload' in log


def test_duplicate_action_rejected_before_cleanup(repository):
    root, _ = repository
    result, log = invoke(repository, '--upload', '--plan-only')
    assert result.returncode != 0
    assert not log
    assert (root / 'a/leaf/src/product/java.gen/old').is_file()


def test_full_bootstrap_refreshes_seed_only_after_success(repository):
    """Full tool builds promote the self-hosting seed; scoped/failed builds do not."""
    root, _ = repository
    bootstrap = root / 'devops/bootstrap'
    (bootstrap / 'promote-canonical-extgen.py').write_text(
        'import os, sys\n'
        'with open(os.environ["TEST_LOG"], "a", encoding="utf-8") as handle:\n'
        '    handle.write("seed:" + sys.argv[1] + "\\n")\n',
        encoding='utf-8',
    )
    result, log = invoke(repository, '--root', 'a', '--prepare-only')
    assert result.returncode == 0, result.stderr
    assert 'seed:' not in log

    (root / 'invocations.log').unlink()
    result, log = invoke(repository, '--prepare-only')
    assert result.returncode == 0, result.stderr
    assert log.splitlines() == ['generate:.', 'build:.:--prepare-only', 'seed:--refresh']

    (root / 'invocations.log').unlink()
    (bootstrap / 'build.sh').write_text('#!/usr/bin/env bash\nexit 17\n', encoding='utf-8')
    result, log = invoke(repository, '--prepare-only')
    assert result.returncode == 17, result.stderr
    assert log == 'generate:.\n'
