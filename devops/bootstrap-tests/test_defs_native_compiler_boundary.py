"""Guard all Defs bootstrap entry points against accidental legacy execution.

@author linhart1
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / 'devops/bootstrap'


def test_normal_bootstrap_uses_current_defs_cli_and_not_legacy_renderer():
    """Both entry scripts must retain the independent current Defs CLI path."""
    generate = (BOOTSTRAP / 'generate.sh').read_text(encoding='utf-8')
    sources = (BOOTSTRAP / 'generate_sources.py').read_text(encoding='utf-8')
    assert 'generate_sources.py' in generate
    assert 'canonical_defs_codegen_cli import' in sources
    assert 'AIcSchemaContractBindingsGenerator' not in generate + sources
    assert 'generate-canonical-contracts.py' not in generate + sources


def test_canonical_first_stage_delegates_to_native_public_cli():
    """Even an explicitly requested canonical refresh must not invoke defs.old."""
    helper = (BOOTSTRAP / 'generate-canonical-contracts.py').read_text(encoding='utf-8')
    assert 'from generate_sources import' in helper
    assert '_qualified_defs_arguments(' in helper
    assert '_load_codegen(' in helper
    assert 'AIcSchemaContractBindingsGenerator' not in helper
    assert 'defs.old' not in helper.replace('``defs.old``', '')
