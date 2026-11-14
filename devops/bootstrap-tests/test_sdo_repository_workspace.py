"""Regression tests for checkout-scoped Java SDO bootstrap workspaces.

The selected artifact owns generated source files only. All temporary SDO
invocation data must be rooted in the checkout-wide build directory.

@author linhart1
"""
from pathlib import Path
import subprocess

import pytest

REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY / 'devops/bootstrap/sdo-java.gradle'


def test_java_sdo_uses_checkout_not_artifact_as_repository_root():
    """Ensure CLI workspace ownership cannot regress to the artifact."""
    script = SCRIPT.read_text(encoding='utf-8')
    assert "System.getenv('MODUSTRO_BOOTSTRAP_REPOSITORY')" in script
    assert "'--repository-root=' + sourceRepository.absolutePath" in script
    assert '.directory(sourceRepository)' in script
    assert "'--repository-root=' + moduleProject.projectDir" not in script
    assert '.directory(moduleProject.projectDir)' not in script
    assert "moduleProject.projectDir.canonicalFile.toPath().startsWith(sourceRepository.toPath())" in script
    assert 'modustro-source-repository.yml' in script


def test_bootstrap_entrypoints_export_the_checkout_root():
    """CLI/Gradle must receive the actual checkout when invoked from below it."""
    bootstrap = (REPOSITORY / 'devops/bootstrap/bootstrap.sh').read_text(encoding='utf-8')
    build = (REPOSITORY / 'devops/bootstrap/build.sh').read_text(encoding='utf-8')
    assert 'locRepository="$(cd -- "$locBootstrapDirectory/../.." && pwd -P)"' in bootstrap
    assert 'export MODUSTRO_BOOTSTRAP_REPOSITORY="$locRepository"' in bootstrap
    assert 'locRepo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"' in build
    assert 'export MODUSTRO_BOOTSTRAP_REPOSITORY="$locRepo"' in build


@pytest.mark.parametrize('entrypoint', ('bootstrap.sh',))
def test_bootstrap_help_runs_when_called_from_nested_artifact(entrypoint):
    """Its entrypoint must not depend on the shell's current directory."""
    nested = REPOSITORY / 'devops/bootstrap-tests'
    runner = REPOSITORY / 'devops/bootstrap' / entrypoint
    result = subprocess.run(['bash', str(runner), '--help'], cwd=nested,
                            check=True, capture_output=True, text=True)
    assert 'Usage:' in result.stdout
