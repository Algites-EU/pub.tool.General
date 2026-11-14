"""Regressions for the boundary between archived SDO and the production bootstrap."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'devops/bootstrap/sdo-java.gradle'
PREPARE = ROOT / 'devops/bootstrap/prepare.py'
LEGACY = ROOT / 'generators/code/sdocodegen/legacy-archive'


def test_bootstrap_uses_only_current_java_sdo_cli():
    source = SCRIPT.read_text()
    assert "'eu.algites.tool.codegen.sdo.impl.cli.AIcSdoCodegenCli'" in source
    assert "'eu.algites.tool.codegen.sdo.impl.standard.AIcSdoCodegenService'" in source
    assert 'sdo.old' not in source
    assert '--sdo-input-paths:java=' in source
    assert '--sdo-dependency-paths:java=' in source
    assert '--dointf-classpath:java=' not in source
    assert '--technology-dointf-input-dir:java=' not in source


def test_legacy_sources_archived_not_packaged():
    for module in ('intf', 'impl', 'cli'):
        root = ROOT / 'generators/code/sdocodegen' / module
        assert not list((root / 'src/product').rglob('sdo/old/*.java'))
        assert not list((root / 'src/product').rglob('sdo/old/*.py'))
    assert (LEGACY / 'impl/src/product/java/eu/algites/tool/codegen/sdo/old/impl/standard/AIcSdoCodegenService.java').is_file()
    assert (LEGACY / 'cli/src/product/java/eu/algites/tool/codegen/sdo/old/impl/cli/AIcSdoCodegenCli.java').is_file()


def test_overlay_does_not_reintroduce_old_java_or_python_product():
    text = PREPARE.read_text()
    assert "java.exclude '**/eu/algites/tool/codegen/sdo/old/**'" in text
    assert "relative_parts[:6] == ('eu', 'algites', 'tool', 'codegen', 'sdo', 'old')" in text
