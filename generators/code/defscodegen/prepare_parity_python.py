"""Install declared external test dependencies into an isolated build directory."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, action='append', default=[])
    parser.add_argument('--endpoints-json', default='[]')
    parser.add_argument('--requirement', action='append', default=[])
    parsed = parser.parse_args()
    projects = [tomllib.loads(path.read_text(encoding='utf-8'))['project'] for path in parsed.metadata]
    def name(requirement):
        return re.sub(r'[-_.]+', '-', re.match(r'[A-Za-z0-9_.-]+', requirement).group()).lower()
    local_names = {name(project['name']) for project in projects}
    requirements = list(dict.fromkeys([dependency for project in projects for dependency in project.get('dependencies', ())
        if name(dependency) not in local_names] + parsed.requirement))
    if not requirements:
        raise ValueError('No external Python dependencies were declared for generator parity tests')
    endpoints = []
    for endpoint in json.loads(parsed.endpoints_json):
        identity, uri, profile, profile_type = endpoint.split('\t')
        if profile:
            raise ValueError(f'Generator parity dependency installation requires a configured public index: {identity}')
        if uri not in endpoints:
            endpoints.append(uri)
    parsed.target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='parity-python-', dir=parsed.target.parent) as directory:
        command = [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--pre', '--target', directory]
        if endpoints:
            command.extend(['--index-url',endpoints[0]])
            for endpoint in endpoints[1:]:
                command.extend(['--extra-index-url',endpoint])
        subprocess.run(command + requirements, check=True)
        if parsed.target.exists():
            shutil.rmtree(parsed.target)
        shutil.copytree(directory, parsed.target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
