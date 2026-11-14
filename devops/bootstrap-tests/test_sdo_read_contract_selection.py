"""Regression for rejecting mutable SDO markers before invoking the Java CLI.

The bootstrap must remain compatible with an older SDO CLI downloaded from a
local repository while a new version of pub.tool.General is being bootstrapped.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
GRADLE = ROOT / 'devops/bootstrap/sdo-java.gradle'


def test_selection_uses_compiled_types_not_naming_or_filename_guesses():
    source = GRADLE.read_text(encoding='utf-8')
    assert "Class.forName(className, false, binaryLoader)" in source
    assert 'readMarker.isAssignableFrom(candidate)' in source
    assert "mutableMarker.isAssignableFrom(candidate)" in source
    assert "AIiSmartDataObject'" in source
    assert 'eligible.add(className)' in source


def test_cli_receives_selected_classes_not_an_unfiltered_binary_directory():
    source = GRADLE.read_text(encoding='utf-8')
    assert "arguments << '--dointf-input-classes:java=' + eligible.join(';')" in source
    assert "arguments << '--sdo-input-paths:java=' + generatedRoot.absolutePath" in source
    assert "arguments << '--sdo-input-paths:java=' + classes.collect" not in source
    assert "arguments << '--sdo-dependency-paths:java=' + binaryClasspath.files" in source
    assert "--dointf-input-artifact=" not in source
    assert "if (eligible.isEmpty())" in source
    assert "skipping generator" in source
    assert source.index('if (eligible.isEmpty())') < source.index('def arguments = [')


def test_bootstrap_class_loader_uses_forked_cli_classpath_and_is_closed():
    source = GRADLE.read_text(encoding='utf-8')
    assert 'binaryUrls = binaryClasspath.files' in source
    assert 'ClassLoader.getPlatformClassLoader()' in source
    assert 'binaryLoader.close()' in source
    assert 'classes.each { directory ->' in source


def test_abi_seed_is_never_implicitly_used_as_an_sdo_input():
    """Only current Defs sources or explicitly authored contracts may enter SDO."""
    source = GRADLE.read_text(encoding='utf-8')
    assert "new File(moduleProject.projectDir, 'src/product/java.gen')" in source
    assert "new File(moduleProject.projectDir, 'src/product/java')" in source
    assert 'if (!manualInputNames.contains(className)) return' in source
    assert 'if (generatedContracts)' in source
    assert "source.getText('UTF-8')" in source
    assert "new File(moduleProject.projectDir, 'src/product/java.extgen')" not in source
    assert "arguments << '--sdo-input-paths:java=' + classes" not in source


def test_unified_naming_contracts_exist_without_per_format_read_interfaces():
    """Actual Defs generated inputs, not extgen ABI classes, back SDO source mode."""
    repository = ROOT if (ROOT / 'naming/convention/intf').is_dir() else ROOT.parent / 'pub.lib.General'
    generated = repository / 'naming/convention/intf/src/product/java.gen/eu/algites/lib/naming/convention'
    unified = generated / 'AIigNameCompositions_1.java'
    assert unified.is_file()
    assert '@eu.algites.lib.data.dataobject.AIaDataObject(' in unified.read_text(encoding='utf-8')
    assert not (generated / 'AIigNameCompositions_1.java').exists()
    assert not (generated / 'AIigNameCompositions_1.java').exists()
    assert not (generated / 'AIigNameCompositions_1.java').exists()
