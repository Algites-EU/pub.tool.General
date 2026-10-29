"""Portable bootstrap infrastructure settings and descriptor-driven defaults."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
BOOT = ROOT / 'devops/bootstrap'


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), BOOT / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shared_configuration_has_exactly_four_endpoints():
    data = yaml.safe_load((BOOT / 'modustro-bootstrap.yml').read_text())
    assert set(data) == {'Publication', 'DependencyResolution'}
    assert set(data['Publication']) == {'Maven', 'Python'}
    assert set(data['DependencyResolution']) == {'RemoteMavenUrl', 'RemotePythonIndexUrl'}
    result = load('bootstrap-config.py').settings(ROOT)
    assert len(result) == 4
    assert result['DependencyResolution.RemotePythonIndexUrl'].endswith('/python/simple/')
    assert not (ROOT / 'modustro-bootstrap.yml').exists()


def test_python_prefix_from_repository_group_id():
    module = load('prepare.py')
    assert module.python_prefix(ROOT) == 'eu-algites'
    assert module.python_name('pub.lib.General_naming.convention.intf', module.python_prefix(ROOT)) == \
           'eu-algites-pub-lib-general-naming-convention-intf'


@pytest.mark.parametrize('requirement,expected', [
    ({'Exact': '2.18.3'}, '2.18.3'),
    ({'Minimum': '>=2.0.0', 'Maximum': '<3.0.0', 'MaximumStrict': True}, '[2.0.0,3.0.0)'),
    ({'Minimum': '>=7.0.0', 'Maximum': '<8.0.0', 'MaximumStrict': True}, '[7.0.0,8.0.0)'),
])
def test_gradle_uses_descriptor_versions(requirement, expected):
    assert load('prepare.py').java_version('com.example:lib', requirement) == expected


def test_config_loader_exports_four_fields():
    done = subprocess.run([sys.executable, str(BOOT / 'bootstrap-config.py'),
                           '--repository', str(ROOT), '--nul'],
                          capture_output=True, check=True)
    assert len([x for x in done.stdout.split(b'\0') if x]) == 4
