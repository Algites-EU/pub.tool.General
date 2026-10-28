"""Verify one authenticated Cloudsmith session, without network or credentials."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
UPLOAD = ROOT / 'devops/bootstrap/upload-cloudsmith.sh'


def test_upload_wrapper_one_session_and_both_ecosystems(tmp_path: Path) -> None:
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    log = tmp_path / 'calls.txt'
    wrapper = bin_dir / 'algites-cloudsmith'
    wrapper.write_text('''#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == --session ]]; then
    [[ "$2" == -- ]] || exit 4
    echo session >> "$TEST_CALLS"
    shift 2
    export ALGITES_CLOUDSMITH_SESSION=1
    exec "$@"
fi
[[ "$ALGITES_CLOUDSMITH_SESSION" == 1 ]] || exit 5
printf '%s\\n' "$*" >> "$TEST_CALLS"
''')
    wrapper.chmod(0o755)
    files = []
    for name in ('artifact.jar', 'artifact.pom', 'artifact.module', 'artifact-sources.jar',
                 'artifact.whl', 'artifact.tar.gz'):
        p = tmp_path / name
        p.write_bytes(b'publication')
        files.append(p)
    maven = tmp_path / 'maven.tsv'
    python = tmp_path / 'python.tsv'
    maven.write_text('\t'.join(str(p) for p in files[:4]) + '\n')
    python.write_text('\t'.join(str(p) for p in files[4:]) + '\n')
    env = dict(os.environ, TEST_CALLS=str(log), PATH=f'{bin_dir}:{os.environ["PATH"]}')
    result = subprocess.run(['algites-cloudsmith', '--session', '--', 'bash', str(UPLOAD),
                             'owner/maven-repo', str(maven), 'owner/python-repo', str(python)],
                            env=env, text=True, capture_output=True)
    assert result.returncode == 0, (result.stdout, result.stderr)
    calls = log.read_text().splitlines()
    assert calls[0] == 'session'
    assert len(calls) == 4
    assert calls[1].startswith('push maven owner/maven-repo ')
    assert calls[2].startswith('push python owner/python-repo ')
    assert calls[3].startswith('push python owner/python-repo ')


def test_upload_rejects_missing_authenticated_session(tmp_path: Path):
    result = subprocess.run(['bash', str(UPLOAD), 'owner/maven', 'nonexistent',
                             'owner/python', 'nonexistent'], env={**os.environ,
                             'ALGITES_CLOUDSMITH_SESSION': ''}, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'session' in result.stderr
