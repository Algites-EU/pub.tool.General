"""Cross-language regressions for the schema-defined SourceBindingGroup model.

These tests run against the persistent first-stage bootstrap inputs, not the
build-local *.gen files.  They must pass after a clean source archive extract.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT.parent / 'pub.lib.General'
READ = ROOT / 'generators/code/defscodegen/intf/src/product'
SDO = ROOT / 'generators/code/defscodegen/impl/src/product'
PKG = 'eu/algites/tool/codegen/defs/bootstrap/model'




def test_group_sdo_contracts_extend_matching_json_and_neutral_parents():
    """Mutable Java/Python group contracts inherit the correct read/SDO types."""
    java = (SDO / 'java.extgen' / PKG / 'impl/intf/AIigdSourceBindingGroup_1.java').read_text()
    py = (SDO / 'python.extgen' / PKG / 'impl/intf/aiigd_source_binding_group_1.py').read_text()
    assert 'AIigSourceBindingGroup_1' in java
    assert 'AIigdSourceBindingGroup_1' in java
    assert 'AIigSourceBindingGroup_1' in py
    assert 'AIigdSourceBindingGroup_1' in py
    assert (SDO / 'java.extgen' / PKG / 'impl/AIcgdSourceBindingGroup_1.java').is_file()
    assert (SDO / 'python.extgen' / PKG / 'impl/aicgd_source_binding_group_1.py').is_file()
    for tech, filename in [('java', 'AIcgdSourceBindingsAdditionalProperties_1.java'),
                           ('python', 'aicgd_source_bindings_additional_properties_1.py')]:
        assert not list((SDO / f'{tech}.extgen').rglob(filename)), 'Obsolete map entry leaked into bootstrap'






def test_source_binding_group_has_only_one_shared_read_contract():
    """Schema technologies share a canonical read contract, not shadow types."""
    java = READ / 'java.extgen' / PKG / 'AIigSourceBindingGroup_1.java'
    python = READ / 'python.extgen' / PKG / 'aiig_source_binding_group_1.py'
    assert java.is_file() and python.is_file()
    assert 'AIiJsonDataObject' not in java.read_text()
    assert 'AIiJsonDataObject' not in python.read_text()
    assert len(list((READ / 'java.extgen').rglob('AIigSourceBindingGroup_1.java'))) == 1
    assert len(list((READ / 'python.extgen').rglob('aiig_source_binding_group_1.py'))) == 1
