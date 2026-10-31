from explicit_legacy_naming import catalog, source_convention, output_convention, rendering_catalog
from pathlib import Path

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.impl.standard.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from explicit_legacy_naming import configured_generation as AIcdCodeGenerationRequest
from explicit_legacy_naming import configured_load as AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind


def test_json_enum_and_yamldefs_object_generation():
    """Verify enum and object generation across jsondefs and yamldefs."""
    examples = Path(__file__).parents[1] / "examples"
    service = AIcDefaultDefsCodegenService()
    profile = catalog('python')
    enum_def = service.load(AIcdDefinitionLoadRequest(examples / "resource-endpoint-action_1.jsondef.schema.json", AInDefinitionSourceKind.JSONDEFS, profile, "algites-jsondef-schema-versioned_1"))
    assert enum_def.data_type.kind is AInDataTypeKind.ENUM
    assert enum_def.logical_name == "resource-endpoint-action"
    assert enum_def.version == 1
    assert enum_def.enum_values[0].value == "download"
    assert enum_def.enum_values[0].description == "Reads resources from the example endpoint."
    enum_src = service.generate(AIcdCodeGenerationRequest(enum_def, AInCodeGenerationTarget.PYTHON, "example.generated", rendering_catalog(profile, "python"),
            None, output_convention("python", "enum"), "common"))
    assert enum_src.type_name == "AIngResourceEndpointAction_1"
    assert enum_src.relative_path.endswith("aing_resource_endpoint_action_1.py")
    assert "Example canonical enum definition for a resource-endpoint action." in enum_src.source
    assert "DOWNLOAD: Reads resources from the example endpoint." in enum_src.source

    obj_def = service.load(AIcdDefinitionLoadRequest(examples / "resource-endpoint_1.yamldef.schema.json", AInDefinitionSourceKind.YAMLDEFS, profile, "algites-yamldef-schema-versioned_1"))
    assert obj_def.data_type.properties[1].data_type.referenced_definition().targets_enum
    obj_src = service.generate(AIcdCodeGenerationRequest(obj_def, AInCodeGenerationTarget.PYTHON, "example.generated", rendering_catalog(profile, "python"),
            None, output_convention("python"), "common"))
    assert obj_src.type_name == "AIcgdResourceEndpoint_1"
    assert "action: AIngResourceEndpointAction_1" in obj_src.source
    assert "Example canonical object definition for a resource endpoint." in obj_src.source
    assert "id: Stable example resource-endpoint identifier." in obj_src.source
    assert "action: Action performed through the resource endpoint." in obj_src.source
    assert "def from_mapping(cls, value: Mapping[str, object]):" in obj_src.source
    assert "def to_mapping(self) -> Mapping[str, object]:" in obj_src.source

    java_profile = catalog('java')
    java_src = service.generate(AIcdCodeGenerationRequest(obj_def, AInCodeGenerationTarget.JAVA, "example.generated", rendering_catalog(java_profile, "java"),
            None, output_convention("java"), "common"))
    assert "Example canonical object definition for a resource endpoint." in java_src.source
    assert "@param id Stable example resource-endpoint identifier." in java_src.source
    assert "@param action Action performed through the resource endpoint." in java_src.source

    yaml_enum_def = service.load(AIcdDefinitionLoadRequest(examples / "resource-endpoint-action_1.yamldef.schema.json", AInDefinitionSourceKind.YAMLDEFS, profile, "algites-yamldef-schema-versioned_1"))
    assert yaml_enum_def.enum_values[0].description == "Reads resources from the example YAML-defined endpoint."

    xsd_def = service.load(AIcdDefinitionLoadRequest(examples / "resource-endpoint-action_1.xsd", AInDefinitionSourceKind.XMLDEFS, profile, "algites-xmldef-schema-versioned_1"))
    assert xsd_def.description == "Defines one resource endpoint action value set."
    assert xsd_def.enum_values[0].value == "download"
    assert xsd_def.enum_values[0].description == "Reads resources from the example XML-defined endpoint."

    xsd_java_src = service.generate(AIcdCodeGenerationRequest(xsd_def, AInCodeGenerationTarget.JAVA, "example.generated", rendering_catalog(java_profile, "java"),
            None, output_convention("java", "enum"), "common"))
    assert "Reads resources from the example XML-defined endpoint." in xsd_java_src.source
    assert "implements eu.algites.lib.common.enums.AIiEnumItem" in xsd_java_src.source
    assert "DOWNLOAD(CONST.FIELD_NAME__DOWNLOAD)" in xsd_java_src.source
    assert 'String FIELD_NAME__DOWNLOAD = "download";' in xsd_java_src.source
    assert 'public String code()' in xsd_java_src.source
    assert 'wireValue' not in xsd_java_src.source
    assert 'wireValue' not in enum_src.source
    assert 'def code(self) -> str:' in enum_src.source
    assert 'FIELD_NAME__DOWNLOAD' in enum_src.source
    assert "def wireValue" not in enum_src.source
    from eu.algites.lib.common.enums.aii_enum_item import AIiEnumItem
    namespace = {'__name__': 'generated_test_enum'}
    exec(compile(enum_src.source, '<generated-python-enum>', 'exec'), namespace)
    generated_enum = namespace[enum_src.type_name]
    item = generated_enum.DOWNLOAD
    assert isinstance(item, AIiEnumItem)
    assert item.code() == 'download'
    assert item.value == 'download'
    assert generated_enum.CONST.FIELD_NAME__DOWNLOAD == 'download'
    assert item.name == 'DOWNLOAD'
    assert not hasattr(item, 'wireValue')


def test_generated_java_enum_compiles_with_enum_item_contract(tmp_path):
    """Compile the actual generated Java enum against the canonical core API."""
    import shutil
    import subprocess
    import pytest

    if shutil.which('javac') is None:
        pytest.skip('javac is not installed')
    examples = Path(__file__).parents[1] / 'examples'
    service = AIcDefaultDefsCodegenService()
    profile = catalog('java')
    definition = service.load(AIcdDefinitionLoadRequest(
        examples / 'resource-endpoint-action_1.xsd', AInDefinitionSourceKind.XMLDEFS,
        profile, 'algites-xmldef-schema-versioned_1'))
    output = service.generate(AIcdCodeGenerationRequest(
        definition, AInCodeGenerationTarget.JAVA, 'example.generated',
        rendering_catalog(profile, 'java'), None, output_convention('java', 'enum'), 'common'))
    enum_source = tmp_path / output.relative_path
    enum_source.parent.mkdir(parents=True)
    enum_source.write_text(output.source)
    current = Path(__file__).resolve()
    for ancestor in current.parents:
        candidate = ancestor / 'pub.lib.General/common/util/src/product/java/eu/algites/lib/common/enums/AIiEnumItem.java'
        if candidate.is_file():
            lib_source = candidate
            break
    else:
        pytest.fail('Unable to locate the Java AIiEnumItem canonical API source')
    verifier = tmp_path / 'VerifyEnum.java'
    verifier.write_text(f'''public class VerifyEnum {{
        public static void main(String[] args) {{
            example.generated.{output.type_name} item = example.generated.{output.type_name}.DOWNLOAD;
            eu.algites.lib.common.enums.AIiEnumItem contract = item;
            if (!"download".equals(contract.code())) throw new AssertionError(contract.code());
            if (!example.generated.{output.type_name}.CONST.FIELD_NAME__DOWNLOAD.equals(contract.code())) throw new AssertionError();
        }}
    }}''')
    subprocess.run(['javac', '--release', '17', '-d', str(tmp_path),
                    str(lib_source), str(enum_source), str(verifier)], check=True)
    subprocess.run(['java', '-cp', str(tmp_path), 'VerifyEnum'], check=True)
