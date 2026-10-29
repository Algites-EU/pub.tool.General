#!/usr/bin/env python3
"""Read the portable bootstrap's infrastructure endpoints.

Only publication targets and remote package registries are configured here.
Build defaults and naming conventions come from the bootstrap and the native
repository/artifact descriptors, never from repository-specific settings.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

import yaml

FIELDS = (
    ('Publication', 'Maven'), ('Publication', 'Python'),
    ('DependencyResolution', 'RemoteMavenUrl'),
    ('DependencyResolution', 'RemotePythonIndexUrl'),
)


def settings(repository: Path) -> dict[str, str]:
    repository = repository.resolve(strict=True)
    config = repository / 'devops/bootstrap/modustro-bootstrap.yml'
    if not config.is_file():
        raise ValueError(f'Missing bootstrap configuration: {config}')
    descriptor = yaml.safe_load(config.read_text(encoding='utf-8'))
    if not isinstance(descriptor, dict):
        raise ValueError(f'Invalid bootstrap configuration: {config}')
    expected_sections = {key for key, _ in FIELDS}
    if set(descriptor) != expected_sections:
        raise ValueError(f'Unexpected bootstrap configuration sections in {config}: '
                         f'{set(descriptor) ^ expected_sections}')
    result: dict[str, str] = {}
    for section, name in FIELDS:
        data = descriptor.get(section)
        if not isinstance(data, dict) or set(data) != {n for s, n in FIELDS if s == section}:
            raise ValueError(f'Unexpected or missing keys in {section}: {config}')
        value = data.get(name)
        if not isinstance(value, str) or not value.strip() or '\x00' in value or '\n' in value:
            raise ValueError(f'Missing or invalid {section}.{name} in {config}')
        result[section + '.' + name] = value
    for field in ('Publication.Maven', 'Publication.Python'):
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+', result[field]):
            raise ValueError(f'Invalid Cloudsmith target in {field}: {result[field]}')
    for field in ('DependencyResolution.RemoteMavenUrl',
                  'DependencyResolution.RemotePythonIndexUrl'):
        url = urlparse(result[field])
        if url.scheme not in ('https', 'file') or (url.scheme == 'https' and not url.netloc):
            raise ValueError(f'{field} must be an HTTPS or file URL')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--nul', action='store_true')
    args = parser.parse_args()
    values = settings(args.repository)
    if args.nul:
        sys.stdout.buffer.write('\x00'.join(values[k] for k in
                           (s + '.' + n for s, n in FIELDS)).encode('utf-8') + b'\x00')
    else:
        for key, value in values.items():
            print(f'{key}: {value}')


if __name__ == '__main__':
    main()
