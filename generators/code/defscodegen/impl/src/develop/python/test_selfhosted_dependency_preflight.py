"""Regression tests for the canonical Codegen dependency preflight.

The former self-hosted Gradle build was removed because it could invoke the
obsolete Defs contract generator. These checks now verify the universal route.
"""
from pathlib import Path
import subprocess

REPOSITORY = Path(__file__).resolve().parents[7]
LAUNCHER = REPOSITORY / 'generators/code/bootstrap-selfhosted.sh'
UNIVERSAL = REPOSITORY / 'devops/bootstrap/bootstrap.sh'
SOURCE_DEPENDENCIES = REPOSITORY / 'devops/bootstrap/source-dependencies.py'


def test_preflight_checks_setter_policy_enum_and_both_annotations():
    """The shared build uses current source libraries, not old annotation JARs."""
    source = SOURCE_DEPENDENCIES.read_text(encoding='utf-8')
    assert 'NAMING_ABI_SEED' in source
    assert 'build_prerequisite' in source
    assert 'MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE' in UNIVERSAL.read_text(encoding='utf-8')


def test_preflight_is_dependency_of_java_compilation_and_explains_remote_mode():
    source = UNIVERSAL.read_text(encoding='utf-8')
    assert 'source-dependencies.py' in source
    assert 'locSourceAction=prepare' in source
    assert 'locSourceAction=plan' in source
    assert '--root "$locRoot"' in source


def test_preflight_remedy_uses_universal_bootstrap_only():
    source = LAUNCHER.read_text(encoding='utf-8')
    assert 'exec bash "$locRepository/devops/bootstrap/bootstrap.sh"' in source
    assert 'mktemp -d' not in source
    assert 'gradle' not in source.lower()
    assert 'AIcSchemaContractBindingsGenerator' not in source


def test_source_mode_rejects_outdated_general_checkout():
    source = SOURCE_DEPENDENCIES.read_text(encoding='utf-8')
    assert 'pub.lib.General' in source
    assert 'build_prerequisite' in source


def test_naming_catalog_preflight_uses_test_runtime_classpath():
    """Artifact dependency wiring is owned by universal Gradle adapter."""
    source = (REPOSITORY / 'devops/bootstrap/sdo-java.gradle').read_text(encoding='utf-8')
    assert 'classpath' in source.lower()
    assert 'sdocodegen' in source.lower()


def test_compatibility_launcher_plan_only():
    result = subprocess.run(['bash', str(LAUNCHER), '--help'],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert '--cleanup-output-folder-before-generation' in result.stdout
