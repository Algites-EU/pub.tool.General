"""Regression checks for named indexed DataObject collections in generated SDOs.

The read-only contract is the sole input; neither generator nor runtime reads a
schema to determine the concrete collection implementation or its key indexes.
"""
import importlib.util
from pathlib import Path
import sys

from explicit_sdo_fixture import AItcConfiguredSdoGenerator
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_type_1 import AIigType_1
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_source_bindings_1 import AIigSourceBindings_1
from eu.algites.tool.codegen.defs.bootstrap.model.impl.aicgd__j_source_bindings_1 import AIcgd_jSourceBindings_1


def test_named_collection_is_generated_lazily_and_remains_attached(tmp_path, monkeypatch):
    """A nominal list getter must return the right SDO type, not a raw list."""
    generator = AIcSdoCodegenService()
    results = {contract: generator.generate(
        contract, naming=AItcConfiguredSdoGenerator._naming(contract))
        for contract in (AIigSourceBindings_1, AIigType_1)}
    source = results[AIigType_1].implementation.source
    assert "get_OrCreateNamedMappedCollectionField('SourceBindings'" in source
    assert 'def setSourceBindings(' not in source
    for result in results.values():
        for item in (result.mutable_interface, result.implementation):
            target = tmp_path / item.relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item.source, encoding='utf-8')
            compile(item.source, str(target), 'exec')
    monkeypatch.syspath_prepend(str(tmp_path))
    # Load only newly generated modules, never stale .extgen artifacts with
    # comparable names on Python's existing namespace package search path.
    loaded = {}
    for contract in (AIigSourceBindings_1, AIigType_1):
        for item in (results[contract].mutable_interface, results[contract].implementation):
            module_name = '.'.join(Path(item.relative_path).with_suffix('').parts)
            spec = importlib.util.spec_from_file_location(module_name, tmp_path / item.relative_path)
            module = importlib.util.module_from_spec(spec)
            monkeypatch.setitem(sys.modules, module_name, module)
            spec.loader.exec_module(module)
            loaded[module_name] = module
    result = results[AIigType_1]
    concrete = loaded['.'.join(Path(result.implementation.relative_path).with_suffix('').parts)]
    generated = getattr(concrete, result.implementation.type_name)
    parent = generated()
    collection = parent.getSourceBindings()
    assert isinstance(collection, AIigSourceBindings_1)
    assert type(collection).__name__ == results[AIigSourceBindings_1].implementation.type_name
    assert collection is parent.getSourceBindings()
    assert parent.isPresent_Field('SourceBindings')
    parent.unset_Field('SourceBindings')
    assert not parent.isPresent_Field('SourceBindings')
    assert parent.getSourceBindings() is not collection
