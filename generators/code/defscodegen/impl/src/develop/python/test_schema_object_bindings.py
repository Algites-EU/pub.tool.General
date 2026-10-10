"""Independent Python API and CLI tests; cross-JVM comparison runs through TestNG."""
import inspect
import json
from pathlib import Path
import subprocess
import sys

import pytest
from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.aic_schema_interface_generator import AIcSchemaInterfaceGenerator
from eu.algites.tool.codegen.defs.aic_schema_object_bindings_generator import AIcSchemaObjectBindingsGenerator
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from generator_implementation_parity import create_fixture, normalized_python, normalized_java


@pytest.mark.parametrize('target', list(AInCodeGenerationTarget))
@pytest.mark.parametrize('kind,suffix', [(AInDefinitionSourceKind.JSONDEFS,'jsondef.schema.json'),
    (AInDefinitionSourceKind.YAMLDEFS,'yamldef.schema.json'), (AInDefinitionSourceKind.XMLDEFS,'xsd')])
def test_native_contract_and_implementation_api(tmp_path, target, kind, suffix):
    profile = AIcAlgitesNamingProfiles.python_profile() if target is AInCodeGenerationTarget.PYTHON else AIcAlgitesNamingProfiles.java_profile()
    resource = Path(__file__).parents[1] / kind.value / f'parity-child_1.{suffix}'
    model = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(resource,kind,profile))
    output = AIcSchemaInterfaceGenerator().generate(AIcdCodeGenerationRequest(model,target,'example.contracts',profile))
    assert output.contract.type_name == 'AIigParityChild_1'
    assert output.implementation.type_name == 'AIcgdParityChild_1'
    assert 'SCHEMA_FIELD_NAME__NAME' in output.contract.source
    assert 'AIigParityLeaf_1' in output.contract.source
    assert 'AIcgdParityLeaf_1' not in output.contract.source
    assert ('(AIigParityChild_1)' if target is AInCodeGenerationTarget.PYTHON else 'implements AIigParityChild_1') in output.implementation.source


@pytest.mark.parametrize('target', list(AInCodeGenerationTarget))
def test_enums_have_only_shared_contract(target):
    profile = AIcAlgitesNamingProfiles.python_profile() if target is AInCodeGenerationTarget.PYTHON else AIcAlgitesNamingProfiles.java_profile()
    path = Path(__file__).parents[1] / 'jsondefs/parity-status_1.jsondef.schema.json'
    service = AIcDefaultDefsCodegenService()
    model = service.load(AIcdDefinitionLoadRequest(path,AInDefinitionSourceKind.JSONDEFS,profile))
    request = AIcdCodeGenerationRequest(model,target,'example.contracts',profile)
    result = AIcSchemaInterfaceGenerator().generate(request)
    assert result.contract == service.generate(request)
    assert result.implementation is None


def test_repository_cli_and_read_only_check(tmp_path):
    manifest = create_fixture(tmp_path)
    generator = AIcSchemaObjectBindingsGenerator()
    result = generator.generate_repository(tmp_path, manifest)
    assert result
    before = {p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert generator.generate_repository(tmp_path, manifest, True) == result
    process = subprocess.run([sys.executable,'-m','eu.algites.tool.codegen.defs.aic_schema_object_bindings_generator',
        str(tmp_path),str(manifest),'--check','--json'], capture_output=True,text=True,check=True)
    assert json.loads(process.stdout) == result
    assert before == {p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


def test_comparison_retains_semantic_differences():
    assert normalized_python("value = 'one'\n") == normalized_python('value="one"\n')
    assert normalized_python("value = 'one'\n") != normalized_python("value = 'two'\n")
    assert normalized_python('value = 1\n') != normalized_python('value = 2\n')
    assert normalized_java('class Example { String value = "one two"; }') == normalized_java('class\nExample{String value="one two";}')
    assert normalized_java('String value="one two";') != normalized_java('String value="onetwo";')
    assert normalized_java('/** Field documentation. */ class Example {}') != normalized_java('/** Lost documentation. */ class Example {}')


@pytest.mark.parametrize('kind,suffix',[(AInDefinitionSourceKind.JSONDEFS,'jsondef.schema.json'),
    (AInDefinitionSourceKind.YAMLDEFS,'yamldef.schema.json')])
def test_canonical_references_ignore_transient_build_copies(tmp_path,kind,suffix):
    (tmp_path / 'modustro-source-repository.yml').write_text('SourceRepository: {}\n')
    owner = tmp_path / 'devops/build/owner/src/product' / kind.value / 'example';owner.mkdir(parents=True)
    transient = tmp_path / 'build/run/owner/src/product' / kind.value / 'example';transient.mkdir(parents=True)
    (owner / ('leaf_1.'+suffix)).write_text('{"$id":"urn:tests:owned-leaf:1","type":"object","properties":{}}')
    (transient / ('leaf_1.'+suffix)).write_text('{broken transient JSON')
    consumer = tmp_path / 'consumer/src/product' / kind.value;consumer.mkdir(parents=True)
    schema = consumer / ('root_1.'+suffix)
    schema.write_text('{"type":"object","properties":{"leaf":{"$ref":"urn:tests:owned-leaf:1"}}}')
    model = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(schema,kind,AIcAlgitesNamingProfiles.python_profile()))
    assert model.properties[0].reference.logical_name == 'leaf'
