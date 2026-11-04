"""Defs generates only read-only contracts; SDO must process interfaces separately."""
from __future__ import annotations

import json

import pytest
from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import prepare


def test_defs_rejects_direct_mutable_sdo_generation(tmp_path):
    """An SDO output target may not be derived directly from XMLDEFS input."""
    manifest = tmp_path / 'config.json'
    manifest.write_text(json.dumps({
        'mutable_sdo_python': {'output_dir': 'impl/src/product/python.gen'},
        'repository_root': '.',
    }), encoding='utf-8')
    with pytest.raises(ValueError, match='SDO Codegen separately'):
        prepare(manifest)


def test_defs_rejects_sdo_naming_profile(tmp_path):
    """SDO naming settings belong to the SDO interface-to-implementation phase."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _profile
    with pytest.raises(ValueError, match='independent SDO Codegen'):
        _profile(tmp_path / 'manifest.json', {
            'common_file': 'anything', 'defs_file': 'anything',
            'sdo_file': 'anything', 'sdo_id': 'anything',
        })
