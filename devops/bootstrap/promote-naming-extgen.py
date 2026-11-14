#!/usr/bin/env python3
"""Manage the temporary, repository-local naming SDO bootstrap source snapshot.

This does not generate classes. Initially the checked-in naming seed contains
read-only Defs classes and minimal Java SDO *ABI stubs* (intentionally abstract,
without setters or implementation logic), alongside complete existing Python
Defs/SDO files. It is used only to compile the independent generators.
After a successful bootstrap, promote only real Defs + SDO output from the
existing independent CLIs. Bootstrap stubs are NEVER the final SDO output.
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
import shutil
import sys
import uuid

REPOSITORY = Path(__file__).resolve().parents[2]
PRODUCT = REPOSITORY / 'naming/convention/intf/src/product'
SUFFIXES = {'java': '.java', 'python': '.py'}


def snapshot(root: Path, suffix: str) -> dict[str, Path]:
    """Collect source files, refusing unsafe symlinks and duplicate paths."""
    if root.is_symlink():
        raise ValueError(f'Symlinked naming source root: {root}')
    if not root.is_dir():
        raise ValueError(f'Missing naming source root: {root}')
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Symlinked naming source: {path}')
        if path.is_file() and path.suffix == suffix:
            key = path.relative_to(root).as_posix()
            if key in result:
                raise ValueError(f'Duplicate naming source: {key}')
            result[key] = path
    return result


def roles(sources: dict[str, Path], language: str) -> dict[str, int]:
    """Require real Defs interfaces and both SDO interface/implementation kinds."""
    names = list(sources)
    if language == 'java':
        counts = {
            'read': sum(Path(n).name.startswith('AIig') and not Path(n).name.startswith('AIigd') for n in names),
            'interface': sum('/impl/intf/AIigd' in '/' + n for n in names),
            'implementation': sum('/impl/AIcgd' in '/' + n for n in names),
        }
    else:
        counts = {
            'read': sum(Path(n).name.startswith('aiig') and not Path(n).name.startswith('aiigd') for n in names),
            'interface': sum('/impl/intf/aiigd' in '/' + n for n in names),
            'implementation': sum('/impl/aicgd' in '/' + n for n in names),
        }
    if any(value == 0 for value in counts.values()):
        raise ValueError(f'Incomplete {language} naming Defs/SDO snapshot: {counts}')
    return counts


def required_naming_sdo(files: dict[str, Path], language: str) -> None:
    """Reject incomplete unified naming contracts after genuine generation.

    A format-specific x/j/y naming interface may be present in an *older*
    compiler-ABI seed, but current Defs/SDO output must use one common read
    and writable contract per schema type. Never REQUIRE old prefixed types
    to promote newly generated code.
    """
    path_prefix = 'eu/algites/lib/naming/convention/'
    for role, prefix, directory in (
        ('interface', 'AIigd', 'impl/intf/'),
        ('implementation', 'AIcgd', 'impl/'),
    ):
        for name in ('IdentifierConventions', 'NameCompositions',
                     'NameFragments', 'VersionConventions',
                     'CommonNamingConventions', 'StandardConventions'):
            symbol = f'{prefix}{name}_1'
            if language == 'python':
                symbol = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', symbol).lower()
            expected = path_prefix + directory + symbol + ('.py' if language == 'python' else '.java')
            if expected not in files:
                raise ValueError(f'Missing generated {language} naming {role}: {expected}')


def reject_format_projections(sources: dict[str, Path], language: str) -> None:
    """Reject obsolete per-technology naming interfaces in modern snapshots.

    The bootstrap seed must represent the unified read-only/writable API.  A
    historical x/j/y projection cannot satisfy that API, even if its name is
    present alongside the proper unified interface.
    """
    pattern = (r'^(?:AIigd|AIig|AIcgd)_[xjy](?:[A-Z_]|$)'
               if language == 'java'
               else r'^(?:aiigd|aiig|aicgd)_{1,2}[xjy]_(?:[a-z]|$)')
    obsolete = [key for key in sources if re.match(pattern, Path(key).name)]
    if obsolete:
        raise ValueError(f'Obsolete technology-specific {language} naming contracts: '
                         + ', '.join(sorted(obsolete)))


def check() -> None:
    """Validate the actual compiler ABI snapshots, without persistent metadata.

    The snapshots are complete generated source trees. Their contents, not a
    checked-in list of hashes, determine whether first-stage compilation can
    proceed. This works before Defs/SDO have produced fresh ``*.gen`` roots.
    """
    counts = {}
    for language, suffix in SUFFIXES.items():
        actual = snapshot(PRODUCT / (language + '.extgen'), suffix)
        counts[language] = roles(actual, language)
        required_naming_sdo(actual, language)
        reject_format_projections(actual, language)
    print(f'Naming extgen source snapshots validated (Java/Python): {counts}')


def refresh() -> None:
    """Atomically replace both seeds from complete *.gen output.

    Generated *.gen files remain intact until the owning bootstrap has finished:
    removing them during code generation can invalidate compiler and Python
    imports. Gradle source selection is a separate integration concern.
    """
    new = {}
    counts = {}
    for language, suffix in SUFFIXES.items():
        files = snapshot(PRODUCT / (language + '.gen'), suffix)
        counts[language] = roles(files, language)
        # Require complete unified Defs+SDO output before replacing the ABI seed.
        required_naming_sdo(files, language)
        reject_format_projections(files, language)
        new[language] = files
    token = uuid.uuid4().hex
    staged = []
    completed = []
    succeeded = False
    try:
        for language in SUFFIXES:
            destination = PRODUCT / (language + '.extgen')
            if destination.is_symlink():
                raise ValueError(f'Symlinked seed destination: {destination}')
            stage = destination.with_name(destination.name + '.stage-' + token)
            backup = destination.with_name(destination.name + '.backup-' + token)
            stage.mkdir(parents=True)
            staged.append((destination, stage, backup))
            for key, source in new[language].items():
                target = stage / key
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        for destination, stage, backup in staged:
            existed = destination.exists()
            if existed:
                os.replace(destination, backup)
            try:
                os.replace(stage, destination)
            except BaseException:
                if existed:
                    os.replace(backup, destination)
                raise
            completed.append((destination, backup, existed))
        succeeded = True
    except BaseException:
        for destination, backup, existed in reversed(completed):
            if destination.exists():
                shutil.rmtree(destination)
            if existed:
                os.replace(backup, destination)
        raise
    finally:
        for _, stage, backup in staged:
            if stage.exists():
                shutil.rmtree(stage)
            if succeeded and backup.exists():
                shutil.rmtree(backup)
    # One-time cleanup of the retired persistent sidecar from older builds.
    legacy = PRODUCT.parents[1] / 'naming-bootstrap-extgen.json'
    if legacy.is_file() or legacy.is_symlink():
        legacy.unlink()
    print(f'Refreshed naming extgen: {counts}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--check', action='store_true')
    choice.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    if args.check:
        check()
    else:
        refresh()


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        sys.exit(f'Naming extgen: {exc}')
