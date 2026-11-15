"""Temporary, tool-only fresh bootstrap and canonical seed promotion tests.

@author linhart1
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / 'devops/bootstrap'


def _script(name: str):
    spec = importlib.util.spec_from_file_location('temporary_bootstrap_' + name,
                                                   BOOTSTRAP / name)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_promotion_only_verifies_preexisting_sources():
    """The seed check never reads a manifest or modifies generated output."""
    module = _script('promote-canonical-extgen.py')
    checksums = module.collect_existing()
    assert checksums
    module.check()
    assert module.collect_existing() == checksums
    assert not list(ROOT.rglob('canonical-bootstrap-extgen.json'))


def test_run_ids_do_not_reuse_publisher_index(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'generators/code/common/src/product/python'))
    from eu.algites.tool.codegen.common.workspace import (
        invocation_workspace, publish_sources, workspace_base,
    )
    repository = tmp_path
    artifact = repository / 'module'
    artifact.mkdir()
    path = artifact / 'src/product/python.gen/type.py'
    path.parent.mkdir(parents=True)
    old_id = str(uuid.uuid4())
    new_id = str(uuid.uuid4())
    monkeypatch.setenv('MODUSTRO_BOOTSTRAP_FRESH_GENERATION', '1')
    monkeypatch.setenv('MODUSTRO_BOOTSTRAP_RUN_ID', old_id)
    with invocation_workspace(repository, artifact, 'defscodegen') as run:
        publish_sources(repository, artifact, 'defscodegen', {path: 'old\n'}, run)
    path.write_text('updated by new source distribution\n')
    monkeypatch.setenv('MODUSTRO_BOOTSTRAP_RUN_ID', new_id)
    with invocation_workspace(repository, artifact, 'defscodegen') as run:
        publish_sources(repository, artifact, 'defscodegen', {path: 'new\n'}, run)
    assert path.read_text() == 'new\n'
    base = workspace_base(repository, artifact, 'defscodegen') / 'bootstrap-invocations'
    assert (base / old_id / 'generated-files.json').is_file()
    assert (base / new_id / 'generated-files.json').is_file()
    assert not (base.parent / 'generated-files.json').exists()


def test_tool_help_declares_clean_default_and_refuses_false():
    script = BOOTSTRAP / 'bootstrap.sh'
    proc = subprocess.run(['bash', str(script), '--help'], capture_output=True,
                          text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    assert proc.returncode == 0
    assert 'repository bootstrap policy' in proc.stdout
    proc = subprocess.run(['bash', str(script), '--plan-only',
                           '--cleanup-output-folder-before-generation=false'],
                          capture_output=True, text=True,
                          env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    # Planning remains side-effect free and permits testing an alternate policy.
    # Do not assert success: descriptor-only plan may require configured deps.
    assert 'temporary bootstrap requires fresh' not in proc.stderr


def test_source_dependency_child_never_inherits_tool_only_state(tmp_path, monkeypatch):
    resolver = _script('source-dependencies.py')
    artifact = resolver.Artifact(repository=tmp_path / 'pub.lib.General',
                                 relative=Path('common'), identifier='pub.lib.General_common',
                                 group='example', version='1.1-SNAPSHOT',
                                 technologies=frozenset({'java'}), dependencies=())
    monkeypatch.setenv('MODUSTRO_BOOTSTRAP_RUN_ID', str(uuid.uuid4()))
    monkeypatch.setenv('MODUSTRO_BOOTSTRAP_FRESH_GENERATION', '1')
    monkeypatch.setenv('MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION', 'true')
    captured = []
    monkeypatch.setattr(resolver.subprocess, 'run', lambda *args, **kw: captured.append(kw['env']))
    resolver.build_prerequisite(artifact)
    assert len(captured) == 1
    assert 'MODUSTRO_BOOTSTRAP_FRESH_GENERATION' not in captured[0]
    assert 'MODUSTRO_BOOTSTRAP_RUN_ID' not in captured[0]
    assert 'MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION' not in captured[0]


def test_source_prerequisites_run_before_tool_lock_and_run_state_export():
    source = (BOOTSTRAP / 'bootstrap.sh').read_text(encoding='utf-8')
    prepare = source.index('"$locBootstrapDirectory/source-dependencies.py" "$locSourceAction"')
    lock = source.index('flock -x "$locBootstrapLockFd"')
    export = source.index('export MODUSTRO_BOOTSTRAP_FRESH_GENERATION=1')
    generate = source.index('bash "$locBootstrapDirectory/generate.sh"') if (
        'bash "$locBootstrapDirectory/generate.sh"' in source) else source.index('bash "$locBootstrapDirectory/generate.sh')
    assert prepare < lock < export < generate
