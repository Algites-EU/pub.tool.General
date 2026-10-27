from explicit_legacy_naming import catalog, source_convention, output_convention, rendering_catalog
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
from dataclasses import replace
from pathlib import Path
import pytest
import sys
import types

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.impl.standard.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger
from explicit_legacy_naming import configured_load as AIcdDefinitionLoadRequest
from explicit_legacy_naming import configured_generation as AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind


def test_common_metadata_representations():
    """Retain both definitions' documentation while rejecting an incompatible wire type."""
    root = Path(__file__).parents[1]
    service = AIcDefaultDefsCodegenService()
    profile = catalog('python')
    yaml = service.load(AIcdDefinitionLoadRequest(root / "yamldefs/document-common-metadata_1.yamldef.schema.json", AInDefinitionSourceKind.YAMLDEFS, profile, "algites-yamldef-schema-versioned_1"))
    json = service.load(AIcdDefinitionLoadRequest(root / "jsondefs/document-common-metadata_1.jsondef.schema.json", AInDefinitionSourceKind.JSONDEFS, profile, "algites-jsondef-schema-versioned_1"))
    assert yaml.data_type.properties == json.data_type.properties
    merged = AIcCanonicalDefinitionMerger.merge((yaml, json))
    for target in AInCodeGenerationTarget:
        profile = catalog('java') if target is AInCodeGenerationTarget.JAVA else catalog('python')
        source = service.generate(AIcdCodeGenerationRequest(merged, target, "example.generated", rendering_catalog(profile, "java" if target is AInCodeGenerationTarget.JAVA else "python"), None,
            output_convention("java" if target is AInCodeGenerationTarget.JAVA else "python"), "common")).source
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
        AIcCanonicalDefinitionMerger.merge((yaml, replace(json, data_type=json.data_type.with_properties((replace(json.data_type.properties[0], data_type=AIcdDataType(AInDataTypeKind.INTEGER)),)))))


def test_local_pointer_and_anchor(tmp_path):
    """Resolve chained local pointers and anchors without versioned-file parsing."""
    path = tmp_path / "local_1.jsondef.schema.json"
    path.write_text('{"type":"object","$defs":{"text":{"type":"string","description":"Inline text"},"list":{"$anchor":"Items","type":"array","items":{"type":"integer"}},"alias":{"$ref":"#/$defs/text"}},"properties":{"text":{"$ref":"#/$defs/alias"},"items":{"$ref":"#Items"}}}')
    definition = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, catalog('python'), "algites-jsondef-schema-versioned_1"))
    assert definition.data_type.properties[0].data_type.kind is AInDataTypeKind.STRING
    assert definition.data_type.properties[0].description == "Inline text"
    assert definition.data_type.properties[1].data_type.kind is AInDataTypeKind.ARRAY
    assert definition.data_type.properties[1].data_type.element_type.kind is AInDataTypeKind.INTEGER
    path.write_text('{"type":"object","properties":{"bad":{"$ref":"#/$defs/missing"}}}')
    with pytest.raises(ValueError, match="Undefined"):
        AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, catalog('python'), "algites-jsondef-schema-versioned_1"))


def test_composition_and_xml_identity(tmp_path):
    """Retain composed fields and distinguish canonical files with generic XSD type names."""
    service = AIcDefaultDefsCodegenService()
    profile = catalog('python')
    path = tmp_path / "composed_1.jsondef.schema.json"
    path.write_text('{"$defs":{"content":{"type":"object","properties":{"Name":{"type":"string"}},"required":["Name"]}},"allOf":[{"$ref":"#/$defs/content"}]}')
    definition = service.load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, profile, "algites-jsondef-schema-versioned_1"))
    assert len(definition.data_type.properties) == 1 and (definition.data_type.properties[0].presence is AInFieldPresenceKind.REQUIRED)
    path = tmp_path / "xml-contract_1.xsd"
    path.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:complexType name="Configuration"><xs:sequence><xs:element name="Item" type="xs:string" minOccurs="0" maxOccurs="unbounded"/></xs:sequence></xs:complexType></xs:schema>')
    definition = service.load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS, profile, "algites-xmldef-schema-versioned_1"))
    assert definition.logical_name == "xml-contract"
    assert definition.data_type.properties[0].data_type.kind is AInDataTypeKind.ARRAY
    assert definition.data_type.properties[0].data_type.element_type.kind is AInDataTypeKind.STRING
