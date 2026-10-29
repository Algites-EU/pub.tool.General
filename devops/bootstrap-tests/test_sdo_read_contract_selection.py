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
    assert "getMethod('isReadContract', Class.class)" in source
    assert "mutableMarker.isAssignableFrom(candidate)" in source
    assert "AIiSmartDataObject'" in source
    assert 'eligible.add(className)' in source


def test_cli_receives_selected_classes_not_an_unfiltered_binary_directory():
    source = GRADLE.read_text(encoding='utf-8')
    assert "eligible.each { arguments << '--dointf-input-class=' + it }" in source
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
