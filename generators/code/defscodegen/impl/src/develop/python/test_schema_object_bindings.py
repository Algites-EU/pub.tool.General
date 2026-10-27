"""First-stage contracts and repository check-mode regression tests."""
import json
from pathlib import Path
import subprocess
import sys
import pytest

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.impl.standard.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
from explicit_legacy_naming import configured_generation as AIcdCodeGenerationRequest
from explicit_legacy_naming import configured_load as AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from generator_implementation_parity import create_fixture


@pytest.mark.parametrize('target', list(AInCodeGenerationTarget))
@pytest.mark.parametrize('kind,suffix', [(AInDefinitionSourceKind.JSONDEFS,'jsondef.schema.json'),
    (AInDefinitionSourceKind.YAMLDEFS,'yamldef.schema.json'), (AInDefinitionSourceKind.XMLDEFS,'xsd')])
def test_native_read_contract_without_dto(target, kind, suffix):
    profile = (AIcAlgitesNamingProfiles.python_profile() if target is AInCodeGenerationTarget.PYTHON
        else AIcAlgitesNamingProfiles.java_profile())
    source = Path(__file__).parents[1] / kind.value / f'parity-child_1.{suffix}'
    model = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(source, kind, profile))
    output = AIcSchemaContractInterfaceGenerator().generate(
        AIcdCodeGenerationRequest(model, target, 'example.contracts', profile))
    assert output.type_name == 'AIigParityChild_1'
    assert 'SCHEMA_FIELD_NAME__NAME' in output.source
    assert 'AIigParityLeaf_1' in output.source
    assert 'AIcgdParityLeaf_1' not in output.source
    assert output.primary_type.type_name == output.type_name
    assert 'AIcgd' not in output.relative_path
    assert 'class AIig' in output.source if target is AInCodeGenerationTarget.PYTHON else 'interface AIig' in output.source


@pytest.mark.parametrize('target', list(AInCodeGenerationTarget))
def test_enums_share_a_single_native_source(target):
    profile = (AIcAlgitesNamingProfiles.python_profile() if target is AInCodeGenerationTarget.PYTHON
        else AIcAlgitesNamingProfiles.java_profile())
    source = Path(__file__).parents[1] / 'jsondefs/parity-status_1.jsondef.schema.json'
    request = AIcdCodeGenerationRequest(AIcDefaultDefsCodegenService().load(
        AIcdDefinitionLoadRequest(source, AInDefinitionSourceKind.JSONDEFS, profile)),
        target, 'example.contracts', profile)
    result = AIcSchemaContractInterfaceGenerator().generate(request)
    assert result == AIcDefaultDefsCodegenService().generate(request)


def test_first_stage_repository_cli_and_check(tmp_path):
    manifest = create_fixture(tmp_path)
    generator = AIcSchemaContractBindingsGenerator()
    result = generator.generate_repository(tmp_path, manifest)
    assert result
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert generator.generate_repository(tmp_path, manifest, True) == result
    command = [sys.executable, '-m',
        'eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator',
        str(tmp_path), str(manifest), '--check', '--json']
    proc = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(proc.stdout) == result
    assert before == {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert not any('/impl/' in item['path'] for item in result)


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
    assert model.data_type.properties[0].data_type.referenced_definition().logical_name == 'leaf'
