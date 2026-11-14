"""Parallel-safe, per-artifact build workspaces and staged source publication.

Every invocation receives its own UUID work tree.  Publication acquires an
artifact/generator-scoped advisory lock before validating or touching outputs;
independent artifacts are never serialized.  Cleanup never deletes another
process's workspace (including on cancellation or process crash).

@author linhart1
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid
from typing import Iterator, Mapping


def artifact_root(repository: Path, output: Path) -> Path:
    """Find the nearest declared ancestor artifact; use repository for fixtures."""
    repository = repository.resolve(strict=True)
    path = output.resolve(strict=False)
    if not path.is_relative_to(repository):
        raise ValueError(f'Output outside repository: {output}')
    for candidate in [path, *path.parents]:
        if (candidate / 'modustro-artifact.yml').is_file():
            return candidate
        if candidate == repository:
            break
    return repository


def workspace_base(repository: Path, artifact: Path, generator: str) -> Path:
    """Return a private generator base under the repository's build tree."""
    if generator not in {'defscodegen', 'sdocodegen'}:
        raise ValueError(f'Unknown generator: {generator}')
    repository = repository.resolve(strict=True)
    artifact = artifact.resolve(strict=True)
    if not artifact.is_relative_to(repository):
        raise ValueError(f'Artifact outside repository: {artifact}')
    return repository / 'build' / artifact.relative_to(repository) / generator


@contextmanager
def invocation_workspace(repository: Path, artifact: Path, generator: str,
                         *, keep_on_error: bool = False) -> Iterator[Path]:
    """Allocate a unique work tree and release only the caller's own work tree.

    Args:
        repository: Checked-out repository containing the build directory.
        artifact: Selected artifact, never a different build's output.
        generator: ``defscodegen`` or ``sdocodegen``.
        keep_on_error: Retain diagnostic files after an exceptional exit.
    Yields:
        The unique work directory containing ``tmp`` and ``staging``.
    Raises:
        OSError: If creation or cleanup is unsuccessful.
    """
    base = workspace_base(repository, artifact, generator)
    base.mkdir(parents=True, exist_ok=True)
    run = base / str(uuid.uuid4())
    run.mkdir(mode=0o700)
    (run / 'tmp').mkdir()
    (run / 'staging').mkdir()
    with (run / '.run.lock').open('a+b') as handle:
        fcntl.lockf(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield run
        except BaseException:
            if not keep_on_error:
                shutil.rmtree(run)
            raise
        else:
            shutil.rmtree(run)
        finally:
            fcntl.lockf(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def publish_lock(repository: Path, artifact: Path, generator: str):
    """Guard one artifact's publication or clean against concurrent writers.

    Lock metadata is intentionally outside every UUID directory; it remains
    valid when a worker exits or crashes.  Readers/writers of other artifacts
    or different codegens use different locks.
    """
    base = workspace_base(repository, artifact, generator)
    base.mkdir(parents=True, exist_ok=True)
    with (base / '.publish.lock').open('a+b') as handle:
        fcntl.lockf(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.lockf(handle.fileno(), fcntl.LOCK_UN)


def publish_sources(repository: Path, artifact: Path, generator: str,
                    contents: Mapping[Path, str], run: Path,
                    *, check: bool = False, cleanup_output_folder_before_generation: bool = False) -> list[Path]:
    """Validate, stage and atomically replace a generator-owned source set.

    The ownership index lives beside the per-artifact workspaces.  The whole
    batch is protected by a publication lock and can be rolled back after a
    failed rename, including owned obsolete paths and its ownership index.
    By default only the requested output paths are replaced, including after
    unpacking an archive without its build/ ownership index. Other files are
    untouched. Explicit cleanup removes obsolete files recorded in this
    generator's index, never files owned by another generator sharing *.gen.
    The index is updated even in incremental mode; it is not required for --check.

    Args:
        repository: Root checkout directory.
        artifact: Owner of the generated sources.
        generator: Generating tool identity.
        contents: Absolute output-path to complete UTF-8 source mappings.
        run: Unique invocation workspace.
        check: Compare without changes.
        cleanup_output_folder_before_generation: Delete obsolete indexed outputs of this generator.
    Returns:
        Sorted list of expected destination paths.
    Raises:
        ValueError: On unsafe paths, collisions or changed owned sources.
        OSError: On filesystem failures, including incomplete rollback.
    """
    base = workspace_base(repository, artifact, generator)
    repository = repository.resolve(strict=True)
    artifact = artifact.resolve(strict=True)
    # Temporary self-hosting mode: bootstrap invocation ID scopes ownership
    # metadata. Never load a previous build's index after unpacking new sources.
    bootstrap_id = os.environ.get('MODUSTRO_BOOTSTRAP_RUN_ID', '') if (
        os.environ.get('MODUSTRO_BOOTSTRAP_FRESH_GENERATION') == '1') else ''
    if bootstrap_id:
        uuid.UUID(bootstrap_id)  # reject malformed IDs and path traversal
        state = base / 'bootstrap-invocations' / bootstrap_id / 'generated-files.json'
        state.parent.mkdir(parents=True, exist_ok=True)
    else:
        state = base / 'generated-files.json' 
    outputs = {}
    for path, content in contents.items():
        dst = path.absolute()
        if dst.resolve(strict=False) != dst or not dst.is_relative_to(artifact):
            raise ValueError(f'Unowned or symlinked generated path: {dst}')
        if not any(part.endswith('.gen') for part in dst.relative_to(artifact).parts):
            raise ValueError(f'Generated destination is not a *.gen tree: {dst}')
        key = dst.relative_to(repository).as_posix()
        if key in outputs and outputs[key] != content:
            raise ValueError(f'Conflicting generated content: {dst}')
        outputs[key] = content
    hashes = {key: hashlib.sha256(value.encode('utf-8')).hexdigest()
              for key, value in sorted(outputs.items())}
    with publish_lock(repository, artifact, generator):
        old = json.loads(state.read_text(encoding='utf-8')) if state.is_file() else {}
        if not isinstance(old, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                             for k, v in old.items()):
            raise ValueError(f'Invalid Codegen ownership index: {state}')
        for key in old:
            old_path = repository / key
            if (not old_path.is_relative_to(artifact) or old_path.resolve(strict=False) != old_path
                    or not any(part.endswith('.gen') for part in old_path.relative_to(artifact).parts)):
                raise ValueError(f'Invalid owned path in {state}: {key}')
        # A recorded file belongs to Codegen and may not be silently
        # overwritten after an external modification. A missing file is safe
        # to regenerate (for example after a clean), whereas an existing
        # file with a changed hash must be diagnosed before any publication.
        # Fresh archive extraction may have no ownership index, so unindexed
        # files remain eligible for replacement by an explicit generation.
        for key, expected_hash in old.items():
            dst = repository / key
            if dst.is_file() and hashlib.sha256(dst.read_bytes()).hexdigest() != expected_hash:
                raise ValueError(f'Generated source modified outside Codegen: {dst}; '
                                 'remove the stale generated file or restore the original')
        # Archive extraction does not restore build/ ownership indexes.
        # Only paths in the freshly requested output set may be overwritten.
        for key, content in outputs.items():
            dst = repository / key
            if dst.is_symlink() or (dst.exists() and not dst.is_file()):
                raise ValueError(f'Unsafe generated destination: {dst}')
            if check and (not dst.is_file() or dst.read_bytes() != content.encode('utf-8')):
                raise ValueError(f'Missing or outdated generated source: {dst}')
        if check:
            return [repository / key for key in sorted(outputs)]
        # Preserve mtime of byte-identical sources across repeated builds.
        replacements = {key for key, content in outputs.items()
                        if not (repository / key).is_file()
                        or (repository / key).read_bytes() != content.encode('utf-8')}
        if cleanup_output_folder_before_generation:
            # Shared .gen folders may contain outputs of other generators.
            next_hashes = hashes
            changed = sorted(replacements | (set(old) - set(outputs)))
        else:
            next_hashes = {**old, **hashes}
            changed = sorted(replacements)
        stages = run / 'staging'
        rollback = run / 'tmp' / 'rollback'
        rollback.mkdir(parents=True, exist_ok=True)
        for key, source in sorted(outputs.items()):
            dst = stages / key
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(source, encoding='utf-8')
        (stages / 'generated-files.json').write_text(
            json.dumps(next_hashes, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        # Make recoverable copies before modifying any old destination.
        for key in changed:
            dst = repository / key
            if dst.is_symlink():
                raise ValueError(f'Refusing symlinked generated source: {dst}')
            if dst.is_file():
                backup = rollback / key
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup)
        old_index = state.read_bytes() if state.is_file() else None
        committed = []
        try:
            for key in changed:
                dst = repository / key
                if key in outputs:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(stages / key, dst)
                else:
                    dst.unlink(missing_ok=True)
                committed.append(key)
            os.replace(stages / 'generated-files.json', state)
        except BaseException as error:
            failures = []
            for key in reversed(committed):
                dst = repository / key
                backup = rollback / key
                try:
                    if backup.is_file():
                        os.replace(backup, dst)
                    else:
                        dst.unlink(missing_ok=True)
                except OSError as exc:
                    failures.append(f'{dst}: {exc}')
            try:
                if old_index is None:
                    state.unlink(missing_ok=True)
                else:
                    state.write_bytes(old_index)
            except OSError as exc:
                failures.append(f'{state}: {exc}')
            if failures:
                raise RuntimeError('Codegen publish rollback incomplete: ' + '; '.join(failures)) from error
            raise
        return [repository / key for key in sorted(outputs)]


def cleanup_inactive_workspaces(repository: Path, artifact: Path,
                                generator: str) -> list[Path]:
    """Remove stale UUID workspaces without touching an active build.

    Args:
        repository: Root repository.
        artifact: Scope of cleanup; must be a declared ancestor of outputs.
        generator: Defs or SDO generator identity.
    Returns:
        Paths of workspaces cleaned during this call.
    Raises:
        OSError: On filesystem errors unrelated to a still-running worker.
    """
    base = workspace_base(repository, artifact, generator)
    if not base.is_dir():
        return []
    removed = []
    for child in base.iterdir():
        if child.is_symlink() or not child.is_dir():
            continue
        try:
            uuid.UUID(child.name)
        except ValueError:
            continue
        lock = child / '.run.lock'
        # Missing locks indicate a worker which crashed before lock creation.
        with lock.open('a+b') as handle:
            try:
                fcntl.lockf(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            try:
                shutil.rmtree(child)
                removed.append(child)
            finally:
                fcntl.lockf(handle.fileno(), fcntl.LOCK_UN)
    return removed
