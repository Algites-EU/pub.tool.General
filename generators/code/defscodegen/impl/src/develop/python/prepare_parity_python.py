"""Install declared external test dependencies into an isolated build directory."""
from __future__ import annotations

import argparse
import json
import textwrap
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib


def verify_imports(target: Path, modules: list[str]) -> None:
    """Check actual Python imports in the isolated installation before running tests."""
    if not modules:
        return
    checker = textwrap.dedent('''\
        import importlib
        import sys
        import traceback

        for name in sys.argv[1:]:
            try:
                imported = importlib.import_module(name)
            except Exception:
                print(f'Bootstrap Python dependency cannot be imported: {name}', file=sys.stderr)
                traceback.print_exc()
                raise SystemExit(1)
            print(f'Bootstrap Python import OK: {name} ({getattr(imported, "__file__", None)})')
    ''')
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(target.resolve())
    subprocess.run([sys.executable, '-c', checker, *modules], cwd=target,
                   env=environment, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, action='append', default=[])
    parser.add_argument('--endpoints-json', default='[]')
    parser.add_argument('--requirement', action='append', default=[])
    parser.add_argument('--verify-import', action='append', default=[])
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
    verify_imports(parsed.target, parsed.verify_import)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
