from dataclasses import replace
from pathlib import Path
import pytest
import sys
import types

from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind


def test_common_metadata_representations():
    """Retain both definitions' documentation while rejecting an incompatible wire type."""
    root = Path(__file__).parents[1]
    service = AIcDefaultDefsCodegenService()
    profile = AIcAlgitesNamingProfiles.python_profile()
    yaml = service.load(AIcdDefinitionLoadRequest(root / "yamldefs/document-common-metadata_1.yamldef.schema.json", AInDefinitionSourceKind.YAMLDEFS, profile))
    json = service.load(AIcdDefinitionLoadRequest(root / "jsondefs/document-common-metadata_1.jsondef.schema.json", AInDefinitionSourceKind.JSONDEFS, profile))
    assert yaml.properties == json.properties
    merged = AIcCanonicalDefinitionMerger.merge((yaml, json))
    for target in AInCodeGenerationTarget:
        profile = AIcAlgitesNamingProfiles.java_profile() if target is AInCodeGenerationTarget.JAVA else AIcAlgitesNamingProfiles.python_profile()
        source = service.generate(AIcdCodeGenerationRequest(merged, target, "example.generated", profile)).source
        assert yaml.identity in source and json.identity in source
        assert yaml.description in source and json.description in source
        if target is AInCodeGenerationTarget.PYTHON:
            module = types.ModuleType("defs_regression_generated")
            sys.modules[module.__name__] = module
            try:
                exec(compile(source, "generated.py", "exec"), module.__dict__)
                generated = next(value for value in module.__dict__.values() if isinstance(value, type) and hasattr(value, "from_mapping"))
                wire = {"$schema": "https://example.test/schema"}
                assert generated.from_mapping(wire).to_mapping() == wire
            finally:
                del sys.modules[module.__name__]
    with pytest.raises(ValueError, match="Incompatible"):
        AIcCanonicalDefinitionMerger.merge((yaml, replace(json, properties=(replace(json.properties[0], value_kind=AInValueKind.INTEGER),))))


def test_local_pointer_and_anchor(tmp_path):
    """Resolve chained local pointers and anchors without versioned-file parsing."""
    path = tmp_path / "local_1.jsondef.schema.json"
    path.write_text('{"type":"object","$defs":{"text":{"type":"string","description":"Inline text"},"list":{"$anchor":"Items","type":"array","items":{"type":"integer"}},"alias":{"$ref":"#/$defs/text"}},"properties":{"text":{"$ref":"#/$defs/alias"},"items":{"$ref":"#Items"}}}')
    definition = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles.python_profile()))
    assert definition.properties[0].value_kind is AInValueKind.STRING
    assert definition.properties[0].description == "Inline text"
    assert definition.properties[1].value_kind is AInValueKind.ARRAY
    assert definition.properties[1].item_value_kind is AInValueKind.INTEGER
    path.write_text('{"type":"object","properties":{"bad":{"$ref":"#/$defs/missing"}}}')
    with pytest.raises(ValueError, match="Undefined"):
        AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles.python_profile()))


def test_composition_and_xml_identity(tmp_path):
    """Retain composed fields and distinguish canonical files with generic XSD type names."""
    service = AIcDefaultDefsCodegenService()
    profile = AIcAlgitesNamingProfiles.python_profile()
    path = tmp_path / "composed_1.jsondef.schema.json"
    path.write_text('{"$defs":{"content":{"type":"object","properties":{"Name":{"type":"string"}},"required":["Name"]}},"allOf":[{"$ref":"#/$defs/content"}]}')
    definition = service.load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, profile))
    assert len(definition.properties) == 1 and definition.properties[0].required
    path = tmp_path / "xml-contract_1.xsd"
    path.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:complexType name="Configuration"><xs:sequence><xs:element name="Item" type="xs:string" minOccurs="0" maxOccurs="unbounded"/></xs:sequence></xs:complexType></xs:schema>')
    definition = service.load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS, profile))
    assert definition.logical_name == "xml-contract"
    assert definition.properties[0].value_kind is AInValueKind.ARRAY
    assert definition.properties[0].item_value_kind is AInValueKind.STRING
