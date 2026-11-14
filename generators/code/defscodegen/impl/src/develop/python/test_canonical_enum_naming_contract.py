"""Generated canonical types are resolved from schema provenance, not prefixes."""
from __future__ import annotations

import importlib
from pathlib import Path

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_symbols import (
    _index, generated_type,
)


def test_generated_canonical_symbols_use_declared_source_id_not_prefix(tmp_path, monkeypatch):
    """An alternate naming profile must not break enum/SDO lookup."""
    root = tmp_path / 'semantic_generated_model'
    (root / 'impl').mkdir(parents=True)
    (root / '__init__.py').write_text('', encoding='utf-8')
    (root / 'impl/__init__.py').write_text('', encoding='utf-8')
    (root / 'some_arbitrary_filename.py').write_text('''from enum import Enum
def descriptor(**kw):
    return kw

class CompletelyCustomStatus(str, Enum):
    """Generated from canonical definition demo.canonical#/$defs/Status/1. Source: local schema."""
    ENABLED = "enabled"

class CompletelyCustomVariant:
    __json_schema__ = descriptor(schema_id="demo.canonical#/$defs/Structure#/oneOf/0")

from dataclasses import dataclass
@dataclass(frozen=True)
class ArbitrarySelectedRecord:
    value: CompletelyCustomVariant
''', encoding='utf-8')
    (root / 'impl/random_impl_module.py').write_text('''class ImplementationWithNonAlgitesName:
    __json_schema__ = descriptor(schema_id="demo.canonical#/$defs/Node")
''', encoding='utf-8')
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    _index.cache_clear()
    result = generated_type('semantic_generated_model', role='enum',
                            schema_id='demo.canonical#/$defs/Status')
    assert result.__name__ == 'CompletelyCustomStatus'
    symbols, selections = _index('semantic_generated_model')
    assert symbols['implementation', 'demo.canonical#/$defs/Node'].typename == 'ImplementationWithNonAlgitesName'
    assert selections['CompletelyCustomVariant'].typename == 'ArbitrarySelectedRecord'


def test_generated_model_loader_does_not_invent_prefixes():
    """The loader must resolve symbols by schema ID, never by prefix templates."""
    source = (Path(__file__).resolve().parents[2] /
              'product/python/eu/algites/tool/codegen/defs/impl/standard/canonical_generated_model.py')
    text = source.read_text(encoding='utf-8')
    assert "_ROOT}.aing_" not in text
    assert "_ROOT}.aiig_" not in text
    assert "_IMPL}.aicgd_" not in text


def test_external_contract_index_uses_annotations_not_generated_prefixes(tmp_path):
    """External inheritance recognizes generated contracts from any profile."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import (
        _existing_contracts,
    )
    java = tmp_path / 'src/product/java.gen/demo'
    python = tmp_path / 'src/product/python.gen/demo'
    java.mkdir(parents=True)
    python.mkdir(parents=True)
    (java / 'SomeCustomContract.java').write_text('''package demo;
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(
    schemaId = "demo.naming", schemaUrl = "https://example.org/demo.schema.json")
public interface SomeCustomContract {}
''', encoding='utf-8')
    (python / 'unconventional_module.py').write_text('''class CustomNamedReadContract:
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='demo.naming',
        schema_url='https://example.org/demo.schema.json')
''', encoding='utf-8')
    assert _existing_contracts((tmp_path,)) == {
        'https://example.org/demo.schema.json': {
            'java': 'demo.SomeCustomContract',
            'python_module': 'demo.unconventional_module',
            'python_type': 'CustomNamedReadContract',
        },
    }
