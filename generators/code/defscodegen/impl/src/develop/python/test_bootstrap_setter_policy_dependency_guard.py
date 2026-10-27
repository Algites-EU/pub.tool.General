"""Regression checks for the standalone Codegen DataObject dependency preflight.

These tests are intentionally independent of published SNAPSHOT repositories.
They check that the generated Gradle preflight includes the policy API and
examines annotation signatures, rather than accepting an outdated JAR solely
because earlier presence/XML classes exist.
"""

from pathlib import Path
import re


BOOTSTRAP = Path(__file__).resolve().parents[5] / 'bootstrap.sh'


def _verification_task() -> str:
    source = BOOTSTRAP.read_text(encoding='utf-8')
    return source.split("def verifyDataObjectDependency = tasks.register(", 1)[1].split(
        "project(':intf').tasks.named('compileJava')", 1
    )[0]


def test_preflight_checks_setter_policy_enum_and_both_annotations():
    task = _verification_task()
    for name in (
        'AInFieldSetterInheritancePolicy.class',
        'AIaDataObject.class',
        'AIaDataObjectField.class',
    ):
        assert name in task
    assert "getDeclaredMethod('setterInheritancePolicy')" in task
    assert 'member.returnType != policy' in task
    assert "member.defaultValue?.name() != 'DEFAULT'" in task
    for constant in (
        'DEFAULT',
        'INHERIT_AS_GENERIC_PARAMETER',
        'INHERIT_AS_FIXED_PARAMETER',
    ):
        assert constant in task


def test_preflight_is_dependency_of_java_compilation_and_explains_remote_mode():
    source = BOOTSTRAP.read_text(encoding='utf-8')
    assert "project(':intf').tasks.named('compileJava') { dependsOn verifyDataObjectDependency }" in source
    task = _verification_task()
    assert 'mode == \'remote\'' in task
    assert 'Publish the updated pub.lib.General' in task
    assert 'MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source' in task
    assert 'if (!problems.isEmpty())' in task


def test_preflight_remedy_uses_groovy_safe_branches_without_line_leading_concatenation():
    """The generated build.gradle must not split a Groovy ternary string over leading '+' lines.

    That shape failed Gradle 9.2.1 script compilation before any task could execute.
    Both dependency modes still need to produce actionable diagnostics.
    """
    task = _verification_task()
    remedy = task.split("def mode = System.getenv(", 1)[1].split('throw new GradleException(', 1)[0]
    assert 'def remedy\n' in remedy
    assert "if (mode == 'remote') {" in remedy
    assert '} else {' in remedy
    assert remedy.count("].join(' ')") == 2
    assert 'Publish the updated pub.lib.General' in remedy
    assert 'Build/publish the current pub.lib.General' in remedy
    assert not re.search(r'(?m)^\s*\+\s*[\"\']', remedy)


def test_source_mode_rejects_outdated_general_checkout():
    source = BOOTSTRAP.read_text(encoding='utf-8')
    required_sources = source.split('for locRequiredSource in \\', 1)[1].split('; do', 1)[0]
    assert 'AInFieldSetterInheritancePolicy.java' in required_sources


def test_naming_catalog_preflight_uses_test_runtime_classpath():
    """The naming profile is a testImplementation dependency, not a runtime one."""
    source = BOOTSTRAP.read_text(encoding='utf-8')
    assert "testImplementation project(':profile-algites')" in source
    task = source.split("def verifyNamingCatalog = tasks.register(", 1)[1].split(
        "project(':impl').tasks.withType(Test)", 1
    )[0]
    assert "project(':impl').configurations.testRuntimeClasspath" in task
    assert "project(':impl').configurations.runtimeClasspath" not in task
    assert "it.moduleVersion.id.group == 'eu.algites.lib.naming'" in task
    assert "it.moduleVersion.id.name == 'pub.lib.General_naming.convention.profile.algites'" in task
    for language in ('java', 'python'):
        assert f"algites-{language}-name-conventions.yml" in task
    assert "xml-element-intf" in task
    assert "Outdated pub.lib.General naming catalog" in task
    assert 'dependsOn prepareParityPython, verifyNamingCatalog' in source
