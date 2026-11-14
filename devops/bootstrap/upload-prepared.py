#!/usr/bin/env python3
"""Select verified local Maven snapshots and latest Python distributions for upload.

No generation, compilation, metadata rewriting or package creation is done.
Selection uses the existing Modustro artifact descriptors and --root boundary.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re
import sys
import os
import xml.etree.ElementTree as ET


def module(filename: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, filename)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def latest_python(repo, distribution: str, java_version: str, verify, override: str | None = None) -> tuple[Path, Path]:
    """Select the latest *built* wheel/sdist version, rejecting incomplete latest."""
    folder = repo / 'packages'
    expected_prefix = java_version.removesuffix('-SNAPSHOT')
    expected_name = verify.normalize(distribution)
    candidates: dict[str, dict[str, list[Path]]] = {}
    for file in sorted(folder.iterdir()) if folder.is_dir() else ():
        if file.is_symlink() or not file.is_file() or not file.name.endswith(('.whl', '.tar.gz')):
            continue
        try:
            name, version = verify.coordinates(file)
        except (ValueError, OSError):
            # Another package may be present in the repository.  Its format
            # cannot influence the selection of this specific distribution.
            continue
        if name != expected_name or (override is not None and version != override):
            continue
        if java_version.endswith('-SNAPSHOT'):
            match = re.fullmatch(re.escape(expected_prefix) + r'\.dev(\d+)', version)
            if not match:
                continue
        elif version != java_version:
            continue
        kind = 'wheel' if file.suffix == '.whl' else 'sdist'
        candidates.setdefault(version, {}).setdefault(kind, []).append(file)
    if not candidates:
        raise ValueError(f'No built Python wheel/sdist for {distribution} at {repo} '
                         f'(Java {java_version}; requested Python version {override or "latest"})')
    def version_key(version: str):
        if '.dev' in version:
            release, dev = version.split('.dev', 1)
            return tuple(int(v) for v in release.split('.')), int(dev)
        return tuple(int(v) for v in version.split('.')), 0
    version = max(candidates, key=version_key)
    files = candidates[version]
    if len(files.get('wheel', ())) != 1 or len(files.get('sdist', ())) != 1:
        raise ValueError(f'Latest Python build is incomplete or ambiguous: {distribution} {version}: {files}')
    wheel, sdist = files['wheel'][0], files['sdist'][0]
    if verify.coordinates(wheel) != verify.coordinates(sdist):
        raise ValueError(f'Python distributions disagree: {wheel} and {sdist}')
    return wheel.resolve(), sdist.resolve()


def prepare(repository: Path, root: Path, output: Path, version: str,
            python_version: str | None = None) -> tuple[Path, Path]:
    adapter = repository / 'devops/bootstrap'
    definitions = module(adapter / 'prepare.py', 'modustro_upload_prepare')
    maven = module(adapter / 'bootstrap-maven-stage.py', 'modustro_upload_maven')
    python = module(adapter / 'modustro-local-python-repo.py', 'modustro_upload_python')
    if not root.is_relative_to(repository):
        raise ValueError(f'Invalid root: {root}')
    records = definitions.module_records(repository, version, '0')
    selected = [record for record in records if (repository / record['path']).is_relative_to(root)]
    if not selected:
        raise ValueError(f'No publishable Modustro artifacts selected under {root}')
    java_repo = maven.modustro_local_maven()
    python_repo = python.root()
    java_rows = []
    python_rows = []
    for record in selected:
        if record['java']:
            directory = (java_repo / record['groupId'].replace('.', '/') /
                         record['artifactId'] / version)
            paths = maven.artifact_files(directory, record['artifactId'], version)
            if len(paths) != 4 or any(p is None or not p.is_file() or not p.stat().st_size for p in paths):
                raise ValueError(f'Incomplete local Maven publication for {record["artifactId"]}: {paths}')
            found = maven.xml_fields(paths[1])
            if found != {'groupId': record['groupId'], 'artifactId': record['artifactId'],
                          'version': version}:
                raise ValueError(f'Unexpected POM coordinates for {record["artifactId"]}: {found}')
            java_rows.append('\t'.join(str(p.resolve()) for p in paths))
        if record['python']:
            wheel, sdist = latest_python(python_repo, record['pythonName'], version,
                                          python, override=python_version)
            python_rows.append(f'{wheel}\t{sdist}')
    if not java_rows and not python_rows:
        raise ValueError('No local Maven or Python publications selected; no upload started')
    output.mkdir(parents=True, exist_ok=True)
    java_manifest = output / 'packages.tsv'
    python_manifest = output / 'python-packages.tsv'
    java_manifest.write_text('\n'.join(java_rows) + '\n', encoding='utf-8')
    python_manifest.write_text('\n'.join(python_rows) + '\n', encoding='utf-8')
    print(f'Upload-prepared: verified {len(java_rows)} Maven publications and '
          f'{len(python_rows)} latest wheel/sdist pairs. No build or generation.', flush=True)
    print(f'Maven manifest: {java_manifest}\nPython manifest: {python_manifest}', flush=True)
    return java_manifest, python_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--python-version')
    args = parser.parse_args()
    prepare(args.repository.resolve(strict=True), args.root.resolve(strict=True),
            args.output.resolve(), args.version, args.python_version)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, ET.ParseError) as error:
        print(f'Upload-prepared selection failed before upload: {error}', file=sys.stderr)
        raise SystemExit(2) from error
