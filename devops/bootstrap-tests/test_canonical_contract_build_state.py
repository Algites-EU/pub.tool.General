"""The optional canonical Defs helper delegates to the current public CLI.

It must not maintain its own generator state or modify promoted *.extgen.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / 'devops/bootstrap'


def _helper():
    sys.path.insert(0, str(BOOTSTRAP))
    spec = importlib.util.spec_from_file_location(
        'canonical_contracts_helper_test', BOOTSTRAP / 'generate-canonical-contracts.py')
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_helper_selects_all_source_schema_representations():
    """XML, JSON and YAML all contribute to the same canonical contracts."""
    helper = _helper()
    options = helper.canonical_arguments(ROOT, check=True)
    expected = ';'.join(item.as_posix() for item in helper.CANONICAL_SCHEMAS.values())
    assert set(helper.CANONICAL_SCHEMAS) == {'xmldefs', 'jsondefs', 'yamldefs'}
    assert '--defs-input-paths:java=' + expected in options
    assert '--defs-input-paths:python=' + expected in options
    assert '--check' in options
    assert not any('bootstrap.model' in value for value in options)


def test_helper_uses_native_cli_without_persistent_manifest(monkeypatch):
    """No private renderer or statefile can rewrite the generated contracts."""
    helper = _helper()
    called = []
    monkeypatch.setattr(helper, '_load_codegen',
                        lambda repository, output: lambda arguments: called.append(arguments) or 0)
    assert helper.main(['--check']) == 0
    assert len(called) == 1 and '--check' in called[0]
    assert not (ROOT / 'generators/code/defscodegen/intf/generated-canonical-contracts.json').exists()
