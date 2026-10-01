from pathlib import Path

from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind


def test_json_enum_and_yamldefs_object_generation():
    """Verify enum and object generation across jsondefs and yamldefs."""
    examples = Path(__file__).parents[1] / "examples"
    service = AIcDefaultDefsCodegenService()
    profile = AIcAlgitesNamingProfiles.python_profile()
    enum_def = service.load(AIcdDefinitionLoadRequest(examples / "resource-endpoint-action_1.jsondef.schema.json", AInDefinitionSourceKind.JSONDEFS, profile))
    assert enum_def.kind is AInDefinitionKind.ENUM
    assert enum_def.logical_name == "resource-endpoint-action"
    assert enum_def.version == 1
    enum_src = service.generate(AIcdCodeGenerationRequest(enum_def, AInCodeGenerationTarget.PYTHON, "example.generated", profile))
    assert enum_src.type_name == "AIngResourceEndpointAction_1"
    assert enum_src.relative_path.endswith("aing_resource_endpoint_action_1.py")
    assert "Example canonical enum definition for a resource-endpoint action." in enum_src.source

    obj_def = service.load(AIcdDefinitionLoadRequest(examples / "resource-endpoint_1.yamldef.schema.json", AInDefinitionSourceKind.YAMLDEFS, profile))
    assert obj_def.properties[1].reference.target_kind is AInDefinitionKind.ENUM
    obj_src = service.generate(AIcdCodeGenerationRequest(obj_def, AInCodeGenerationTarget.PYTHON, "example.generated", profile))
    assert obj_src.type_name == "AIcgdResourceEndpoint_1"
    assert "action: AIngResourceEndpointAction_1" in obj_src.source
    assert "Example canonical object definition for a resource endpoint." in obj_src.source
    assert "id: Stable example resource-endpoint identifier." in obj_src.source
    assert "action: Action performed through the resource endpoint." in obj_src.source

    java_profile = AIcAlgitesNamingProfiles.java_profile()
    java_src = service.generate(AIcdCodeGenerationRequest(obj_def, AInCodeGenerationTarget.JAVA, "example.generated", java_profile))
    assert "Example canonical object definition for a resource endpoint." in java_src.source
    assert "@param id Stable example resource-endpoint identifier." in java_src.source
    assert "@param action Action performed through the resource endpoint." in java_src.source

    xsd_def = service.load(AIcdDefinitionLoadRequest(examples / "resource-endpoint-action_1.xsd", AInDefinitionSourceKind.XMLDEFS, profile))
    assert xsd_def.description == "Defines one resource endpoint action value set."
