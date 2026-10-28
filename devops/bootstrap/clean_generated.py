#!/usr/bin/env python3
"""Repository-scoped cleanup of native generated sources for all bootstraps.

Only `src/<source-branch>/{java,python}.gen` is managed by this interim
bootstrap. Other technology roots, including `config.gen`, are retained.
No repository-relative path or symlink may escape the selected source root.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil

TECHNOLOGIES = frozenset({'java.gen', 'python.gen'})
IGNORED = frozenset({'.git', 'build', '.gradle', '.venv', 'node_modules', '__pycache__', '.pytest_cache'})


def resolve_root(repository: Path, root: str) -> Path:
    repository = repository.resolve(strict=True)
    candidate = Path(root).expanduser()
    if not candidate.is_absolute():
        candidate = repository / candidate
    candidate = candidate.resolve(strict=True)
    if not candidate.is_dir() or not candidate.is_relative_to(repository):
        raise ValueError(f'Bootstrap root must be a directory in {repository}: {candidate}')
    if candidate != repository and not any(candidate.rglob('modustro-artifact.yml')):
        raise ValueError(f'No declared artifacts below bootstrap root: {candidate}')
    return candidate


def generated_directories(repository: Path, selected: Path) -> list[Path]:
    """Discover only source-branch generated roots; never traverse build output."""
    roots: list[Path] = []
    for current, directories, _ in os.walk(selected, followlinks=False):
        directory = Path(current)
        if directory.name == 'src':
            for branch in directory.iterdir():
                if not branch.is_dir() or branch.is_symlink():
                    continue
                for language in TECHNOLOGIES:
                    candidate = branch / language
                    if candidate.is_symlink():
                        raise ValueError(f'Refusing symlinked generated directory: {candidate}')
                    if candidate.is_dir():
                        if not candidate.resolve().is_relative_to(selected):
                            raise ValueError(f'Generated directory escapes bootstrap root: {candidate}')
                        roots.append(candidate)
        directories[:] = [name for name in directories
                          if name not in IGNORED and not (directory / name).is_symlink()]
    return sorted(set(roots))


def clean(repository: Path, selected: Path) -> None:
    for directory in generated_directories(repository, selected):
        for item in directory.iterdir():
            if item.is_dir() and not item.is_symlink():
                shutil.rmtree(item)
            else:
                item.unlink()
        print(f'Emptied {directory.relative_to(repository)}', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('validate', 'list', 'clean'))
    parser.add_argument('--repository', required=True, type=Path)
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    selected = resolve_root(repository, args.root)
    if args.operation == 'validate':
        print(selected)
    elif args.operation == 'list':
        for directory in generated_directories(repository, selected):
            print(directory.relative_to(repository))
    else:
        clean(repository, selected)


if __name__ == '__main__':
    main()
