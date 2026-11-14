"""Public reference resolution must ignore developer fixtures, not real conflicts."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE = (Path(__file__).resolve().parents[2] / 'product/python/eu/algites/tool/codegen'
          '/defs/impl/standard/schema_reference_resolver.py')
spec = importlib.util.spec_from_file_location('schema_reference_resolver_standalone', MODULE)
import sys
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

URI = 'https://defs.dev.algites.eu/api/jsondefs/example/schema_1.jsondef.schema.json'


def _write(root: Path, relative: str, *, name: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'$id': URI, 'title': name}), encoding='utf-8')
    return path


def test_development_example_does_not_shadow_published_schema(tmp_path):
    example = _write(tmp_path, 'generators/code/defs/src/develop/examples/jsondefs/example_1.jsondef.schema.json', name='example')
    published = _write(tmp_path, 'builder/common/src/product/jsondefs/example/schema_1.jsondef.schema.json', name='product')
    result = module.SchemaReferenceResolver((tmp_path,), tmp_path / 'cache').resolve(URI)
    assert result.origin == str(published)
    assert str(example) != result.origin


def test_conflicting_published_schema_ids_include_both_paths(tmp_path):
    first = _write(tmp_path, 'alpha/src/product/jsondefs/schema_1.jsondef.schema.json', name='alpha')
    second = _write(tmp_path, 'beta/src/product/jsondefs/schema_1.jsondef.schema.json', name='beta')
    with pytest.raises(ValueError, match='Conflicting published local schema') as error:
        module.SchemaReferenceResolver((tmp_path,), tmp_path / 'cache').resolve(URI)
    assert str(first) in str(error.value)
    assert str(second) in str(error.value)


def test_identical_published_schema_ids_are_allowed(tmp_path):
    _write(tmp_path, 'alpha/src/product/jsondefs/schema_1.jsondef.schema.json', name='same')
    _write(tmp_path, 'beta/src/product/jsondefs/schema_1.jsondef.schema.json', name='same')
    assert module.SchemaReferenceResolver((tmp_path,), tmp_path / 'cache').resolve(URI).uri == URI
