"""Independent SDO Codegen inputs are DataObject interfaces, never Defs schemas.

The same manually authored interfaces must work under the promoted implementation
without requiring either Defs Codegen or its canonical schema representation.
"""
from __future__ import annotations

import pytest

from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main
import test_handwritten_naming_cli as original


def test_handwritten_interface_produces_writable_interface_and_implementation(tmp_path, monkeypatch):
    """An annotated hand-written Python class is a complete SDO input."""
    monkeypatch.setattr(original, 'main', main)
    original.test_handwritten_contract_uses_annotated_convention_not_filename(tmp_path)
    files = list((tmp_path / 'generated').rglob('*.py'))
    assert len(files) == 2
    assert any('class AIi' in p.read_text() or 'class AIig' in p.read_text() for p in files)
    assert any('class AIc' in p.read_text() for p in files)


def test_same_package_for_writable_and_concrete(tmp_path, monkeypatch):
    """Writable and implementation outputs can coexist without extra schema input."""
    monkeypatch.setattr(original, 'main', main)
    original.test_shared_package_is_allowed_for_distinct_names(tmp_path)


def test_explicit_handwritten_class_selector(tmp_path, monkeypatch):
    """Explicit class selectors can target names unrelated to Defs naming rules."""
    monkeypatch.setattr(original, 'main', main)
    original.test_explicit_python_input_class(tmp_path)


def test_unresolved_handwritten_class_is_not_silently_ignored(tmp_path, monkeypatch):
    """Missing explicit interface input must fail before publication."""
    monkeypatch.setattr(original, 'main', main)
    original.test_missing_explicit_python_input_class_fails(tmp_path)


@pytest.mark.parametrize('argument', [
    '--schema-input=x.xsd',
    '--defs-input-artifacts:python=some-package==1.1.dev',
    '--canonical-schema=x.json',
    '--schema-input-dir:python=./schemas',
    '--mutable-sdo-python=manifest.json',
])
def test_sdo_cli_does_not_accept_defs_schema_or_canonical_options(argument):
    """The independent SDO CLI has no schema-reading or canonical-model options."""
    with pytest.raises(ValueError, match='Unknown|unqualified|Invalid'):
        main([argument])
