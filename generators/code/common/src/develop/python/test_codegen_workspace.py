"""Regressions for independent Codegen workspaces and published sources.

@author linhart1
"""
from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path
import uuid

import pytest

from eu.algites.tool.codegen.common.workspace import (
    artifact_root, cleanup_inactive_workspaces, invocation_workspace,
    publish_sources, workspace_base,
)


def _artifact(repository: Path, name: str) -> Path:
    root = repository / name / 'intf'
    root.mkdir(parents=True)
    (root / 'modustro-artifact.yml').write_text('identifier: test\n', encoding='utf-8')
    return root


def _hold_run(repository: str, artifact: str, ready, release):
    """Hold a workspace in another process, exercising actual kernel file locks."""
    with invocation_workspace(Path(repository), Path(artifact), 'defscodegen') as work:
        ready.put(str(work))
        release.get(timeout=15)


def test_private_workspace_and_cleanup_skips_live_process(tmp_path):
    artifact = _artifact(tmp_path, 'a')
    context = get_context('spawn')
    ready = context.Queue()
    release = context.Queue()
    process = context.Process(target=_hold_run, args=(str(tmp_path), str(artifact), ready, release))
    process.start()
    active = Path(ready.get(timeout=15))
    try:
        assert uuid.UUID(active.name)
        assert active.parent == workspace_base(tmp_path, artifact, 'defscodegen')
        stale = active.parent / str(uuid.uuid4())
        stale.mkdir()
        assert cleanup_inactive_workspaces(tmp_path, artifact, 'defscodegen') == [stale]
        assert active.is_dir()
        with invocation_workspace(tmp_path, artifact, 'sdocodegen') as sdo_work:
            assert sdo_work.parent != active.parent
            assert sdo_work.is_dir()
    finally:
        release.put(None)
        process.join(timeout=15)
        if process.is_alive():
            process.terminate()
            process.join()
    assert process.exitcode == 0
    assert not active.exists()


def test_independent_artifacts_publishing_and_ownership(tmp_path):
    first, second = (_artifact(tmp_path, part) for part in ('a', 'b'))
    a = first / 'src/product/python.gen/a.py'
    b = second / 'src/product/python.gen/b.py'
    for artifact, target, source in ((first, a, 'first\n'), (second, b, 'second\n')):
        with invocation_workspace(tmp_path, artifact, 'defscodegen') as run:
            publish_sources(tmp_path, artifact, 'defscodegen', {target: source}, run)
            publish_sources(tmp_path, artifact, 'defscodegen', {target: source}, run, check=True)
    assert a.read_text() == 'first\n'
    assert b.read_text() == 'second\n'
    assert artifact_root(tmp_path, a) == first
    assert artifact_root(tmp_path, b) == second
    with invocation_workspace(tmp_path, first, 'defscodegen') as run:
        publish_sources(tmp_path, first, 'defscodegen', {}, run)
    assert a.exists()
    with invocation_workspace(tmp_path, first, 'defscodegen') as run:
        publish_sources(tmp_path, first, 'defscodegen', {}, run,
                        cleanup_output_folder_before_generation=True)
    assert not a.exists()
    assert b.read_text() == 'second\n'


@pytest.mark.parametrize('generator', ['defscodegen', 'sdocodegen'])
def test_default_overwrites_expected_paths_without_manifest_and_preserves_others(tmp_path, generator):
    """Unpacked archives have generated sources but no transient ownership index."""
    artifact = _artifact(tmp_path, 'a')
    output = artifact / 'src/product/python.gen/a.py'
    foreign = artifact / 'src/product/python.gen/manual.py'
    output.parent.mkdir(parents=True)
    output.write_text('stale generated\n')
    foreign.write_text('keep independent source\n')
    with invocation_workspace(tmp_path, artifact, generator) as run:
        publish_sources(tmp_path, artifact, generator, {output: 'new generated\n'}, run)
    assert output.read_text() == 'new generated\n'
    assert foreign.read_text() == 'keep independent source\n'
    output.write_text('locally changed\n')
    with invocation_workspace(tmp_path, artifact, generator) as run:
        with pytest.raises(ValueError, match='Generated source modified outside Codegen'):
            publish_sources(tmp_path, artifact, generator, {output: 'new generated\n'},
                            run, check=True)
        with pytest.raises(ValueError, match='Generated source modified outside Codegen'):
            publish_sources(tmp_path, artifact, generator, {output: 'newer generated\n'}, run)
    # Ordinary publication must preserve the local-change guard. Revert the
    # unauthorized edit before testing legitimate regeneration in a new run.
    assert output.read_text() == 'locally changed\n'
    output.write_text('new generated\n')
    with invocation_workspace(tmp_path, artifact, generator) as run:
        publish_sources(tmp_path, artifact, generator, {output: 'newer generated\n'}, run)
    assert output.read_text() == 'newer generated\n'
    assert foreign.read_text() == 'keep independent source\n'
    # --check has no dependency on the transitory build/ index.
    (workspace_base(tmp_path, artifact, generator) / 'generated-files.json').unlink()
    with invocation_workspace(tmp_path, artifact, generator) as run:
        publish_sources(tmp_path, artifact, generator,
                        {output: 'newer generated\n'}, run, check=True)


@pytest.mark.parametrize('generator', ['defscodegen', 'sdocodegen'])
def test_explicit_cleanup_only_removes_obsolete_outputs_of_same_generator(tmp_path, generator):
    artifact = _artifact(tmp_path, 'a')
    generated = artifact / 'src/product/python.gen/old.py'
    current = artifact / 'src/product/python.gen/new.py'
    other = artifact / 'src/product/python.gen/foreign.py'
    with invocation_workspace(tmp_path, artifact, generator) as run:
        publish_sources(tmp_path, artifact, generator,
                        {generated: 'old\n'}, run)
    other.write_text('another producer\n')
    with invocation_workspace(tmp_path, artifact, generator) as run:
        publish_sources(tmp_path, artifact, generator,
                        {current: 'current\n'}, run,
                        cleanup_output_folder_before_generation=True)
    assert not generated.exists()
    assert current.read_text() == 'current\n'
    assert other.read_text() == 'another producer\n'


def test_failed_publication_restores_all_owned_files_and_index(tmp_path, monkeypatch):
    """Recover a partially renamed batch rather than exposing half-written output."""
    from eu.algites.tool.codegen.common import workspace
    artifact = _artifact(tmp_path, 'a')
    first = artifact / 'src/product/python.gen/first.py'
    second = artifact / 'src/product/python.gen/second.py'
    original = {first: 'before first\n', second: 'before second\n'}
    with invocation_workspace(tmp_path, artifact, 'defscodegen') as run:
        publish_sources(tmp_path, artifact, 'defscodegen', original, run)
    state = workspace_base(tmp_path, artifact, 'defscodegen') / 'generated-files.json'
    previous_index = state.read_bytes()
    initial = {path: path.read_bytes() for path in original}
    replace = workspace.os.replace
    failed = False

    def fail_second(src, dst):
        nonlocal failed
        if not failed and Path(dst) == second:
            failed = True
            raise OSError('injected publication failure')
        return replace(src, dst)

    monkeypatch.setattr(workspace.os, 'replace', fail_second)
    with invocation_workspace(tmp_path, artifact, 'defscodegen') as run:
        with pytest.raises(OSError, match='injected publication failure'):
            publish_sources(tmp_path, artifact, 'defscodegen',
                            {first: 'after first\n', second: 'after second\n'}, run)
    assert failed
    assert state.read_bytes() == previous_index
    assert {path: path.read_bytes() for path in original} == initial


@pytest.mark.parametrize('generator', ['defscodegen', 'sdocodegen'])
def test_publish_refuses_symlinked_destination_and_parent(tmp_path, generator):
    """Never overwrite through generated-output symlinks, even with cleanup disabled."""
    artifact = _artifact(tmp_path, 'a')
    outside = tmp_path / 'outside'
    outside.mkdir()
    victim = outside / 'keep.py'
    victim.write_text('unchanged\n')
    generated = artifact / 'src/product/python.gen'
    generated.mkdir(parents=True)
    target = generated / 'keep.py'
    target.symlink_to(victim)
    with invocation_workspace(tmp_path, artifact, generator) as run:
        with pytest.raises(ValueError, match='symlink'):
            publish_sources(tmp_path, artifact, generator, {target: 'replacement\n'}, run)
    assert victim.read_text() == 'unchanged\n'
    target.unlink()
    nested = generated / 'nested'
    nested.symlink_to(outside, target_is_directory=True)
    with invocation_workspace(tmp_path, artifact, generator) as run:
        with pytest.raises(ValueError, match='symlink'):
            publish_sources(tmp_path, artifact, generator,
                            {nested / 'keep.py': 'replacement\n'}, run)
    assert victim.read_text() == 'unchanged\n'


def test_repeating_identical_publication_preserves_mtime(tmp_path):
    """Default incremental mode avoids needlessly modifying generated files."""
    artifact = _artifact(tmp_path, 'a')
    generated = artifact / 'src/product/python.gen/file.py'
    with invocation_workspace(tmp_path, artifact, 'defscodegen') as run:
        publish_sources(tmp_path, artifact, 'defscodegen', {generated: 'same\n'}, run)
    original_ns = generated.stat().st_mtime_ns
    with invocation_workspace(tmp_path, artifact, 'defscodegen') as run:
        publish_sources(tmp_path, artifact, 'defscodegen', {generated: 'same\n'}, run)
    assert generated.stat().st_mtime_ns == original_ns
