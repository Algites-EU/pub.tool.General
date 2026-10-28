#!/usr/bin/env python3
"""Publish verified Modustro Python wheels and sdists into a static PEP 503 file index.

The bootstrap is self-contained, requiring only the Python standard library.
Each package remains a standard wheel/sdist and can later be uploaded unchanged.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
from html import escape
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import quote
import zipfile


def root() -> Path:
    configured = os.environ.get('MODUSTRO_LOCAL_PYTHON_REPOSITORY')
    if configured:
        return Path(configured).expanduser().resolve()
    home = Path(os.environ.get('MODUSTRO_HOME') or Path.home() / '.modustro').expanduser()
    return (home / 'artifact-repos/python').resolve()


def normalize(name: str) -> str:
    return re.sub(r'[-_.]+', '-', name).lower()


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as source:
        for piece in iter(lambda: source.read(1024 * 1024), b''):
            result.update(piece)
    return result.hexdigest()


def coordinates(path: Path) -> tuple[str, str]:
    name = path.name
    if name.endswith('.whl'):
        pieces = name[:-4].split('-')
        if len(pieces) not in (5, 6) or not all(pieces):
            raise ValueError(f'Invalid wheel filename: {name}')
        with zipfile.ZipFile(path) as jar:
            metadata = [n for n in jar.namelist() if n.endswith('.dist-info/METADATA')]
            if len(metadata) != 1:
                raise ValueError(f'Wheel must contain one METADATA: {path}')
            text = jar.read(metadata[0]).decode('utf-8')
            actual_name = re.search(r'^Name: (.+)$', text, re.MULTILINE)
            actual_version = re.search(r'^Version: (.+)$', text, re.MULTILINE)
            if not actual_name or not actual_version or normalize(actual_name.group(1)) != normalize(pieces[0]) or actual_version.group(1) != pieces[1]:
                raise ValueError(f'Wheel metadata does not match filename: {path}')
        return normalize(pieces[0]), pieces[1]
    if name.endswith('.tar.gz'):
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)-([0-9][A-Za-z0-9_.+!]*)\.tar\.gz', name)
        if not match:
            raise ValueError(f'Invalid sdist filename: {name}')
        return normalize(match.group(1)), match.group(2)
    raise ValueError(f'Unsupported Python distribution: {name}')


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.modustro-', delete=False) as target:
        temporary = Path(target.name)
        target.write(text)
    os.replace(temporary, path)


def publish(manifest: Path, destination: Path) -> int:
    """Serializes writes with the same POSIX file lock used by the Java Builder adapter."""
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / '.modustro-local-index.lock').open('a+b') as lock_file:
        fcntl.lockf(lock_file, fcntl.LOCK_EX)
        try:
            return _publish_locked(manifest, destination)
        finally:
            fcntl.lockf(lock_file, fcntl.LOCK_UN)


def _publish_locked(manifest: Path, destination: Path) -> int:
    rows = [line.split('\t') for line in manifest.read_text(encoding='utf-8').splitlines() if line.strip()]
    batch: dict[str, tuple[Path, str, str]] = {}
    for row in rows:
        if len(row) != 2:
            raise ValueError(f'Expected WHEEL\\tSDIST row in {manifest}: {row}')
        wheel, sdist = (Path(field).expanduser().resolve() for field in row)
        if not wheel.is_file() or not sdist.is_file() or not wheel.stat().st_size or not sdist.stat().st_size:
            raise FileNotFoundError(f'Python wheel or sdist missing: {row}')
        if not wheel.name.endswith('.whl') or not sdist.name.endswith('.tar.gz'):
            raise ValueError(f'Expected wheel followed by sdist: {row}')
        if coordinates(wheel) != coordinates(sdist):
            raise ValueError(f'Wheel and sdist identify different projects/versions: {row}')
        for file in (wheel, sdist):
            if file.name in batch:
                raise ValueError(f'Duplicate Python distribution filename in manifest: {file.name}')
            batch[file.name] = (file, digest(file), coordinates(file)[0])
    if not rows:
        print('Promoted 0 Python publications (Maven-only bootstrap).', flush=True)
        return 0
    packages = destination / 'packages'
    simple = destination / 'simple'
    # Validate the entire batch and all existing collisions before touching the index.
    for name, (source, sha, _) in batch.items():
        target = packages / name
        if target.is_file() and digest(target) != sha:
            raise ValueError(f'Immutable Python distribution filename already has different content: {target}')
    packages.mkdir(parents=True, exist_ok=True)
    for name, (source, sha, _) in batch.items():
        target = packages / name
        if target.is_file():
            continue
        with tempfile.NamedTemporaryFile(dir=packages, prefix='.modustro-', delete=False) as out:
            temporary = Path(out.name)
        try:
            shutil.copyfile(source, temporary)
            if digest(temporary) != sha:
                raise ValueError(f'Python package copy checksum mismatch: {source}')
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    grouped: dict[str, list[Path]] = {}
    for entry in packages.iterdir():
        if not entry.is_file() or not (entry.name.endswith('.whl') or entry.name.endswith('.tar.gz')):
            continue
        name, _ = coordinates(entry)
        grouped.setdefault(name, []).append(entry)
    # Every project page links to the immutable package directory with a SHA256 fragment.
    for name, files in sorted(grouped.items()):
        links = '\n'.join(
            f'<a href="../../packages/{quote(file.name)}#sha256={digest(file)}">{escape(file.name)}</a><br>'
            for file in sorted(files)
        )
        write_atomic(simple / name / 'index.html', f'<!DOCTYPE html>\n<html><body>\n{links}\n</body></html>\n')
    index = '\n'.join(f'<a href="{quote(name)}/">{escape(name)}</a><br>' for name in sorted(grouped))
    write_atomic(simple / 'index.html', f'<!DOCTYPE html>\n<html><body>\n{index}\n</body></html>\n')
    print(f'Promoted {len(rows)} verified Python wheels and sdists to {destination}', flush=True)
    print(f'Local pip index: {simple.as_uri()}/', flush=True)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['publish', 'show-index-url'])
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--repository', type=Path, default=root())
    args = parser.parse_args()
    if args.action == 'show-index-url':
        print((args.repository / 'simple').resolve().as_uri() + '/')
    else:
        if args.manifest is None:
            parser.error('--manifest is required for publish')
        publish(args.manifest, args.repository)


if __name__ == '__main__':
    main()
