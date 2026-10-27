"""Check contract signatures for multiple array nesting levels in both languages."""
import json
import pytest

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from explicit_legacy_naming import configured_generation as AIcdCodeGenerationRequest
from explicit_legacy_naming import configured_load as AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator


def _request(tmp_path, item):
    path = tmp_path / 'matrix_1.jsondef.schema.json'
    path.write_text(json.dumps({'type': 'object', 'properties': {'grid': {
        'type': 'array', 'items': {'type': 'array', 'items': item}}}}))
    profile = AIcAlgitesNamingProfiles.python_profile()
    model = AIcJsonDefsFrontend().load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, profile))
    return model


def test_nested_array_is_preserved_in_python_and_java_contracts(tmp_path):
    model = _request(tmp_path, {'type': 'integer'})
    generator = AIcSchemaContractInterfaceGenerator()
    java = generator.generate(AIcdCodeGenerationRequest(model, AInCodeGenerationTarget.JAVA,
        'example.matrix', AIcAlgitesNamingProfiles.java_profile())).source
    python = generator.generate(AIcdCodeGenerationRequest(model, AInCodeGenerationTarget.PYTHON,
        'example.matrix', AIcAlgitesNamingProfiles.python_profile())).source
    assert 'java.util.List<? extends java.util.List<? extends java.math.BigInteger>>' in java
    assert 'tuple[tuple[int, ...], ...]' in python


def test_nested_choice_has_a_named_type_in_both_contracts(tmp_path):
    model = _request(tmp_path, {'oneOf': [{'type': 'integer'}, {'type': 'string'}]})
    generator = AIcSchemaContractInterfaceGenerator()
    java = generator.generate(AIcdCodeGenerationRequest(model, AInCodeGenerationTarget.JAVA,
        'example.matrix', AIcAlgitesNamingProfiles.java_profile())).source
    python = generator.generate(AIcdCodeGenerationRequest(model, AInCodeGenerationTarget.PYTHON,
        'example.matrix', AIcAlgitesNamingProfiles.python_profile())).source
    assert 'java.util.List<? extends java.util.List<? extends AIigMatrixGridItemsItems_1>>' in java
    assert 'tuple[tuple[AIigMatrixGridItemsItems_1, ...], ...]' in python


def test_nested_array_contract_feeds_python_sdo(tmp_path, monkeypatch):
    """Ensure stage two can import a contract with its full nested tuple signature."""
    import importlib
    from explicit_sdo_fixture import configured_service

    model = _request(tmp_path, {'type': 'string'})
    catalog = AIcAlgitesNamingProfiles.python_profile()
    source = AIcSchemaContractInterfaceGenerator().generate(AIcdCodeGenerationRequest(
        model, AInCodeGenerationTarget.PYTHON, 'example.nested_arrays', catalog))
    root = tmp_path / 'python.gen'
    file = root / source.relative_path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(source.source)
    monkeypatch.syspath_prepend(str(root))
    contract = getattr(importlib.import_module('example.nested_arrays.aiig_matrix_1'), source.type_name)
    emitted = configured_service().generate(contract)
    for part in (emitted.mutable_interface, emitted.implementation):
        target = root / part.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(part.source)
    implementation = importlib.import_module('example.nested_arrays.aicgd_matrix_1')
    assert hasattr(implementation, 'AIcgdMatrix_1')


def test_nested_inline_object_uses_named_contract(tmp_path):
    model = _request(tmp_path, {'type': 'object', 'properties': {'value': {'type': 'integer'}}})
    generator = AIcSchemaContractInterfaceGenerator()
    for target, profile in ((AInCodeGenerationTarget.PYTHON, AIcAlgitesNamingProfiles.python_profile()),
                            (AInCodeGenerationTarget.JAVA, AIcAlgitesNamingProfiles.java_profile())):
        generated = generator.generate(AIcdCodeGenerationRequest(model, target, 'example.matrix', profile))
        assert 'AIigMatrixGridItemsItems_1' in generated.source



def test_batch_emits_recursive_objects_choices_and_importable_sdo(tmp_path, monkeypatch):
    """Batch discovery and field typing must agree on every inline node name."""
    import importlib
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
    from explicit_naming_fixture import explicit_legacy_generic_manifest
    from explicit_sdo_fixture import configured_service

    folder = tmp_path / 'intf/src/product/jsondefs/example/recursive_contract'
    folder.mkdir(parents=True)
    source = {'type': 'object', 'properties': {'lines': {'type': 'array', 'items':
        {'type': 'array', 'items': {'type': 'object', 'properties': {
            'code': {'type': 'string'},
            'selection': {'oneOf': [{'type': 'string'}, {'type': 'integer'}]}
        }}}}}}
    (folder / 'invoice_1.jsondef.schema.json').write_text(json.dumps(source))
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({'artifact': 'intf', 'languages': ['java', 'python']})))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    java = tmp_path / 'intf/src/product/java.gen/example/recursive_contract'
    python = tmp_path / 'intf/src/product/python.gen/example/recursive_contract'
    assert 'java.util.List<? extends java.util.List<? extends AIigInvoiceLinesItemsItems_1>> getLines()' in (
        java / 'AIigInvoice_1.java').read_text()
    assert 'AIigInvoiceLinesItemsItemsSelection_1 getSelection()' in (
        java / 'AIigInvoiceLinesItemsItems_1.java').read_text()
    choice = (java / 'AIigInvoiceLinesItemsItemsSelection_1.java').read_text()
    assert 'sealed interface' in choice and 'permits' in choice
    assert len(list(java.glob('AIigInvoiceLinesItemsItemsSelectionAlternative*.java'))) == 2
    pyroot = tmp_path / 'intf/src/product/python.gen'
    monkeypatch.syspath_prepend(str(pyroot))
    package = 'example.recursive_contract'
    for file in sorted(python.glob('*.py')):
        importlib.import_module(package + '.' + file.stem)
    catalog = AIcAlgitesNamingProfiles.python_profile()
    for stem, typename in [('aiig_invoice_lines_items_items_1', 'AIigInvoiceLinesItemsItems_1'),
                           ('aiig_invoice_1', 'AIigInvoice_1')]:
        contract = getattr(importlib.import_module(package + '.' + stem), typename)
        sources = configured_service().generate(contract)
        for part in (sources.mutable_interface, sources.implementation):
            output = pyroot / part.relative_path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(part.source)
    importlib.import_module(package + '.aicgd_invoice_1')
    importlib.import_module(package + '.aicgd_invoice_lines_items_items_1')


def test_array_references_to_defs_use_identical_nominal_types(tmp_path, monkeypatch):
    """The direct and two-dimensional $defs reference must target one named contract."""
    import importlib
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
    from explicit_naming_fixture import explicit_legacy_generic_manifest
    folder = tmp_path / 'intf/src/product/jsondefs/example/reference_arrays'
    folder.mkdir(parents=True)
    (folder / 'example_1.jsondef.schema.json').write_text(json.dumps({
        'type': 'object', '$defs': {'account': {'type': 'object', 'properties': {
            'id': {'type': 'string'}}}},
        'properties': {'account': {'$ref': '#/$defs/account'},
                       'accounts': {'type': 'array', 'items': {'type': 'array',
                                    'items': {'$ref': '#/$defs/account'}}}}}))
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({'artifact': 'intf', 'languages': ['java', 'python']})))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    java = (tmp_path / 'intf/src/product/java.gen/example/reference_arrays/AIigExample_1.java').read_text()
    assert 'AIigExampleDefinitionAccount_1 getAccount()' in java
    assert 'java.util.List<? extends java.util.List<? extends AIigExampleDefinitionAccount_1>> getAccounts()' in java
    pyroot = tmp_path / 'intf/src/product/python.gen'
    monkeypatch.syspath_prepend(str(pyroot))
    module = importlib.import_module('example.reference_arrays.aiig_example_1')
    assert module.AIigExample_1.__annotations__['account'] == 'AIigExampleDefinitionAccount_1'
    assert 'AIigExampleDefinitionAccount_1' in module.AIigExample_1.__annotations__['accounts']
