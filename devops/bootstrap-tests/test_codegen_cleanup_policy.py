"""Verify the temporary tool bootstrap's fresh-generation cleanup policy.

@author linhart1
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess


def test_tool_bootstrap_help_advertises_default_enabled_cleanup():
    repository = Path(__file__).resolve().parents[2]
    result = subprocess.run(['bash', str(repository / 'devops/bootstrap/bootstrap.sh'), '--help'],
                            cwd=repository, capture_output=True, text=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, check=True)
    assert '--cleanup-output-folder-before-generation=true|false' in result.stdout
    assert 'defaults to repository bootstrap policy' in result.stdout
    from importlib.util import module_from_spec, spec_from_file_location
    source = repository / 'devops/bootstrap/selfhosting.py'
    spec = spec_from_file_location('bootstrap_cleanup_policy', source)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.policies(repository)['CleanGeneratedDefault'] is True


def test_selected_cleanup_rejects_invalid_boolean():
    repository = Path(__file__).resolve().parents[2]
    result = subprocess.run(['bash', str(repository / 'devops/bootstrap/bootstrap.sh'),
                             '--cleanup-output-folder-before-generation=maybe', '--plan-only'],
                            cwd=repository, capture_output=True, text=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    assert result.returncode == 2
    assert 'true or false' in result.stderr
