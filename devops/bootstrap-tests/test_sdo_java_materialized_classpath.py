"""Guard against Gradle passing unmaterialized classpath entries to Java SDO."""

from pathlib import Path


BOOTSTRAP_ROOT = Path(__file__).resolve().parents[1] / 'bootstrap'
GRADLE_SCRIPT = BOOTSTRAP_ROOT / "sdo-java.gradle"
JAVA_CLI = (
    BOOTSTRAP_ROOT.parent.parent
    / "generators/code/sdocodegen/cli/src/product/java"
    / "eu/algites/tool/codegen/sdo/impl/cli/AIcSdoCodegenCli.java"
)


def test_sdo_java_uses_the_same_materialized_classpath_for_process_and_sources():
    """Only existing entries may reach Java's in-memory source compiler."""
    source = GRADLE_SCRIPT.read_text(encoding="utf-8")
    assert "def existingDependencyFiles = binaryClasspath.files.findAll { it.exists() }" in source
    assert "def classpath = files(existingDependencyFiles).asPath" in source
    assert "existingDependencyFiles.collect { it.absolutePath }.join(';')" in source
    assert "Missing required Java SDO dependency archives" in source
    assert "--sdo-dependency-paths:java=' + binaryClasspath.files.collect" not in source


def test_sdo_java_cli_checks_shared_classpath_once_before_source_batch():
    """One absent dependency must not be repeated for every read-only DO."""
    # The universal bootstrap also lives in repositories that do not own
    # the SDO generator implementation. In those repos test its launcher
    # alone; the CLI contract is tested in the owning tool repository.
    if not JAVA_CLI.is_file():
        return
    source = JAVA_CLI.read_text(encoding="utf-8")
    before_batch = source.index("List<Path> locSourceRoots = new ArrayList<>()")
    assert "for (Path locDependency : locDependencies)" in source[:before_batch]
    assert "Missing Java SDO dependency classpath entry" in source[:before_batch]
