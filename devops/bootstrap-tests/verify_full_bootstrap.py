#!/usr/bin/env python3
"""Isolated full source-bootstrap smoke test for both Algites repositories.

Copies the *actual* checked-out sources into adjacent temporary repositories,
then runs the public bootstrap CLI; never rewrites the source checkouts.  All
per-run logs and diagnostics remain in the specified build report directory.

Example:
    PYTHONDONTWRITEBYTECODE=1 python3 devops/bootstrap-tests/verify_full_bootstrap.py \
        --output build/run/bootstrap/full-verification --timeout-seconds 900

The script returns nonzero if either full bootstrap fails or times out.  A
successful --plan-only check is not misreported as a successful full bootstrap.

@author linhart1
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main(argv=None):
    """Run Lib then Tool bootstrap and save exact exit status and diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='Directory for a temporary workspace, logs and report')
    parser.add_argument('--timeout-seconds', type=int, default=900)
    parser.add_argument('--dependency-mode', choices=('source', 'remote'), default='source')
    parser.add_argument('--plan-only', action='store_true',
                        help='Check discovery only (does not count as full bootstrap)')
    args = parser.parse_args(argv)
    if args.timeout_seconds < 1:
        parser.error('--timeout-seconds must be positive')
    tool = Path(__file__).resolve().parents[2]
    lib = tool.parent / 'pub.lib.General'
    if not lib.is_dir():
        parser.error(f'Expected adjacent library repository: {lib}')
    destination = args.output.resolve()
    if tool == destination or tool in destination.parents:
        # Build directory under source checkout is intended and safe.
        pass
    destination.mkdir(parents=True, exist_ok=True)
    work = destination / 'workspace'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    ignore = shutil.ignore_patterns('build', '.git', '__pycache__', '*.pyc', '.pytest_cache')
    for source in (lib, tool):
        shutil.copytree(source, work / source.name, symlinks=True,
                        copy_function=shutil.copy2, ignore=ignore)
    report = {'mode': 'plan-only' if args.plan_only else 'full-prepare-only',
              'dependency_mode': args.dependency_mode, 'results': []}
    for name in ('pub.lib.General', 'pub.tool.General'):
        cmd = ['bash', 'devops/bootstrap/bootstrap.sh',
               '--plan-only' if args.plan_only else '--prepare-only',
               '--cleanup-output-folder-before-generation=false']
        start = time.monotonic()
        environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                       'MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE': args.dependency_mode}
        entry = {'repository': name, 'command': cmd, 'status': None}
        log = destination / (name + '.log')
        try:
            result = subprocess.run(cmd, cwd=work / name, env=environment,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, errors='replace',
                                    timeout=args.timeout_seconds)
            log.write_text(result.stdout, encoding='utf8')
            entry['status'] = 'passed' if result.returncode == 0 else 'failed'
            entry['exit_code'] = result.returncode
        except subprocess.TimeoutExpired as err:
            partial = err.stdout or b''
            if isinstance(partial, bytes):
                partial = partial.decode('utf8', errors='replace')
            log.write_text(partial + '\nTIMEOUT\n', encoding='utf8')
            entry['status'] = 'timeout'
        entry['elapsed_seconds'] = round(time.monotonic() - start, 2)
        entry['log'] = str(log)
        report['results'].append(entry)
        print(f"{name}: {entry['status']} ({entry['elapsed_seconds']} s) -> {log}", flush=True)
    destination.joinpath('summary.json').write_text(json.dumps(report, indent=2) + '\n')
    return int(any(r['status'] != 'passed' for r in report['results']))


if __name__ == '__main__':
    sys.exit(main())
