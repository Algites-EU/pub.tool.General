"""Nonexistent default schema roots are informational, not configuration failures."""
from __future__ import annotations

from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


def test_all_missing_schema_input_directories_are_safe_noop(tmp_path, capsys):
    from pathlib import Path
    state = tmp_path / 'build/run/schema-contract-bindings/generated-files.json'
    state.parent.mkdir(parents=True)
    state.write_text('[]')
    manifest = {
        'artifact': '.',
        'schema_inputs': [{'kind': 'yamldefs', 'directory': 'src/product/yamldefs'},
                          {'kind': 'jsondefs', 'directory': 'src/product/jsondefs'}],
        'technology_outputs': {'python': 'src/product/python.gen'},
        'technology_output_naming_conventions': {},
        'schema_input_naming_conventions': {},
        'naming_convention_files': ['resource:standard-conventions.yml'],
        'languages': ['python'],
    }
    assert AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, manifest) == []
    diagnostic = capsys.readouterr().err
    assert 'skipping configured yamldefs input directory (not found)' in diagnostic
    assert 'skipping configured jsondefs input directory (not found)' in diagnostic
    assert 'nothing to generate' in diagnostic
    assert state.read_text() == '[]'
