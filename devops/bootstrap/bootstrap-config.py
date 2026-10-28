#!/usr/bin/env python3
"""Read source repository bootstrap settings without any repository-specific defaults.

All paths are relative to the descriptor's repository root. The common scripts
never depend on a repository identifier or on naming-profile implementation.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import yaml

FIELDS = (
    ('Build', 'WorkDirectory'), ('Build', 'JavaRelease'),
    ('Build', 'PythonRequires'),
    ('Publication', 'Maven'), ('Publication', 'Python'),
    ('DependencyResolution', 'RemoteMavenUrl'),
    ('DependencyResolution', 'RemoteGroupRegex'),
)


def settings(repository: Path) -> dict[str, str]:
    repository = repository.resolve(strict=True)
    config = repository / 'modustro-bootstrap.yml'
    if not config.is_file():
        raise ValueError(f'Missing bootstrap configuration: {config}')
    descriptor = yaml.safe_load(config.read_text(encoding='utf-8'))
    if not isinstance(descriptor, dict):
        raise ValueError(f'Invalid bootstrap configuration: {config}')
    result: dict[str, str] = {}
    for section, name in FIELDS:
        data = descriptor.get(section)
        value = data.get(name) if isinstance(data, dict) else None
        if value is None or not str(value).strip() or '\x00' in str(value) or '\n' in str(value):
            raise ValueError(f'Missing or invalid {section}.{name} in {config}')
        result[section + '.' + name] = str(value)
    for field in ('Build.WorkDirectory',):
        path = Path(result[field])
        if path.is_absolute() or '..' in path.parts or path == Path('.'):
            raise ValueError(f'{field} must be a repository-relative path: {path}')
        resolved = (repository / path).resolve()
        if not resolved.is_relative_to(repository):
            raise ValueError(f'{field} leaves repository: {path}')
    # build.sh recursively empties WorkDirectory on every invocation. Never
    # allow configuration mistakes to delete the checkout or a source subtree.
    work = Path(result['Build.WorkDirectory'])
    if len(work.parts) < 2 or work.parts[0] != 'build':
        raise ValueError('Build.WorkDirectory must be a dedicated directory beneath build/')
    if not result['Build.JavaRelease'].isdigit():
        raise ValueError('Build.JavaRelease must be an integer')
    for field in ('Publication.Maven', 'Publication.Python'):
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+', result[field]):
            raise ValueError(f'Invalid Cloudsmith target in {field}: {result[field]}')
    if not result['DependencyResolution.RemoteMavenUrl'].startswith(('https://', 'file:')):
        raise ValueError('DependencyResolution.RemoteMavenUrl must use HTTPS or file:')
    re.compile(result['DependencyResolution.RemoteGroupRegex'])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--nul', action='store_true')
    args = parser.parse_args()
    values = settings(args.repository)
    if args.nul:
        sys.stdout.buffer.write('\x00'.join(values[k] for k in (s+'.'+n for s, n in FIELDS)).encode('utf-8') + b'\x00')
    else:
        for key, value in values.items():
            print(f'{key}: {value}')


if __name__ == '__main__':
    main()
