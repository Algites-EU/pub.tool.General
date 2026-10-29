"""Regressions for SDO Java bootstrap against source-built naming contracts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'devops/bootstrap/sdo-java.gradle'


def test_source_output_substitutes_own_published_jar_only():
    source = SCRIPT.read_text(encoding='utf-8')
    assert "MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE') == 'source'" in source
    assert "dependency.name.startsWith(String.valueOf(entry.artifactId) + '-')" in source
    assert "dependency.name.endsWith('.jar')" in source
    assert 'moduleProject.sourceSets.main.output' in source
    assert 'def toolFiles = toolClasspath.files.findAll { !ownPublishedJar(it) }' in source
    assert '.findAll { !ownPublishedJar(it) }' in source
    assert source.index('moduleProject.sourceSets.main.output,') < source.index('moduleFiles, toolFiles, classes')
    assert 'moduleProject.sourceSets.main.runtimeClasspath, classes)' not in source


def test_remaining_conflicting_standard_resources_fail_with_provenance():
    source = SCRIPT.read_text(encoding='utf-8')
    assert "standard-conventions.yml'" in source
    assert 'standardLoader.getResources(standardResource)' in source
    assert "java.security.MessageDigest.getInstance('SHA-256')" in source
    assert 'originsByHash.size() > 1' in source
    assert 'Incompatible naming standards on Java SDO classpath for ' in source


def test_source_jar_shadowing_is_a_real_semantic_difference():
    """Old grammar and new grammar disagree on the same identifier definition."""
    import tarfile
    old = ROOT / 'naming/convention/intf/src/product/config/eu/algites/lib/naming/convention/standard-conventions.yml'
    if not old.is_file():
        # The test applies equally to the tool repository, which does not own the grammar.
        return
    current = old.read_text(encoding='utf-8')
    assert 'all_lower_1:\n    ConversionStyle: lower_flat' in current
