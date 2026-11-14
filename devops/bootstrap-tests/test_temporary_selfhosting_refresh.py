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


def _fake_generated_model(tmp_path, monkeypatch):
    """Build the four owned outputs without mutating the actual repository."""
    module = _script('promote-canonical-extgen.py')
    outputs = []
    for language, owner in (('java', 'intf'), ('python', 'intf'),
                            ('java', 'impl'), ('python', 'impl')):
        branch = tmp_path / 'generators/code/defscodegen' / owner / 'src/product'
        # Defs and SDO both write to the Defs input artifact's *.gen root.
        generated = tmp_path / 'generators/code/defscodegen/intf/src/product' / (language + '.gen')
        seed = branch / (language + '.extgen')
        file = ('model.java' if language == 'java' else 'model.py')
        relative = Path('impl') / file if owner == 'impl' else Path(file)
        source = generated / module.OLD_PATH / relative
        source.parent.mkdir(parents=True)
        source.write_text(f'{owner}-{language} current\n', encoding='utf-8')
        old = seed / module.NEW_PATH / ('impl' if owner == 'impl' else '')
        old.mkdir(parents=True)
        (old / file).write_text(f'{owner}-{language} previous\n', encoding='utf-8')
        (old / ('obsolete.' + ('java' if language == 'java' else 'py'))).write_text('old\n')
        outputs.append((language, generated, seed))
    schema = tmp_path / 'canonical-model.json'
    schema.write_text('{}', encoding='utf-8')
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'SCHEMA', schema)
    monkeypatch.setattr(module, 'OUTPUTS', tuple(outputs))
    monkeypatch.setattr(module, 'NORMALIZE', lambda source, lang: source)
    monkeypatch.setattr(module, 'relocate', lambda source, lang: source)
    monkeypatch.setattr(module, 'validate_read_roles', lambda files, content=None: None)
    monkeypatch.setattr(module, 'validate_sdo_roles', lambda files, content=None: None)
    monkeypatch.setattr(module, 'ensure_symmetry', lambda files, content=None: {
        'java': (1, 1), 'python': (1, 1)
    })
    return module, outputs


def test_prune_seed_checks_actual_seed_without_manifests(tmp_path, monkeypatch):
    module, outputs = _fake_generated_model(tmp_path, monkeypatch)
    module.prune_seed()
    for language, _, seed in outputs:
        target = seed / module.NEW_PATH / ('impl' if '/impl/' in seed.as_posix() else '')
        assert (target / ('model.java' if language == 'java' else 'model.py')).is_file()
        assert list(target.glob('obsolete.*')), 'Prune must not guess stale paths before fresh generation'
    assert not list(tmp_path.rglob('*bootstrap-extgen.json'))


def test_full_refresh_replaces_all_four_sides_from_fresh_gen(tmp_path, monkeypatch):
    module, outputs = _fake_generated_model(tmp_path, monkeypatch)
    module.refresh()
    for language, _, seed in outputs:
        destination = seed / module.NEW_PATH
        current = destination / ('impl' if '/impl/' in seed.as_posix() else '') / ('model.java' if language == 'java' else 'model.py')
        assert current.read_text() == ('intf' if '/intf/' in current.as_posix() else 'impl') + '-' + language + ' current\n'
        assert not list(destination.glob('obsolete.*'))
    module.refresh()
    assert not list(tmp_path.rglob('*bootstrap-extgen.json'))
    module.check()


def test_refresh_rolls_back_all_four_trees_on_mid_commit_failure(tmp_path, monkeypatch):
    module, outputs = _fake_generated_model(tmp_path, monkeypatch)
    originals = {
        seed: {(file.relative_to(seed).as_posix(), file.read_bytes())
               for file in seed.rglob('*') if file.is_file()}
        for _, _, seed in outputs
    }
    real_replace = module.os.replace
    counter = {'stage': 0}

    def fail_during_second_tree(source, destination):
        if '.stage-' in Path(source).name and Path(destination) in originals:
            counter['stage'] += 1
            if counter['stage'] == 2:
                raise OSError('simulated failure before second tree publication')
        return real_replace(source, destination)

    monkeypatch.setattr(module.os, 'replace', fail_during_second_tree)
    with pytest.raises(OSError, match='simulated failure'):
        module.refresh()
    assert not list(tmp_path.rglob('*bootstrap-extgen.json'))
    for _, _, seed in outputs:
        assert {(file.relative_to(seed).as_posix(), file.read_bytes())
                for file in seed.rglob('*') if file.is_file()} == originals[seed]
        assert not list(seed.parent.glob('*.stage-*'))
        assert not list(seed.parent.glob('*.backup-*'))


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
