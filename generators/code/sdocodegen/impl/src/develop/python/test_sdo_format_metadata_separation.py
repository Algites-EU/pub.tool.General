"""Regression tests for independent JSONDEFS/YAMLDEFS metadata."""
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from explicit_sdo_fixture import configured_service


class AIigIndependentFormatMetadata_1(AIiDataObject):
    """All three descriptors intentionally disagree on identity and URL."""
    __data_object__ = AIcdDataObject()
    __json_schema__ = AIaDataObjectJsonSchema(
        schema_id='modern-identity', schema_version=7,
        schema_url='https://example.org/modern-schema')
    __json_data_object__ = AIaJsonDataObject(
        schema_id='json-identity', schema_version=2,
        schema_url='https://example.org/json-schema')
    __yaml_data_object__ = AIaYamlDataObject(
        schema_id='yaml-identity', schema_version=5,
        schema_url='https://example.org/yaml-schema')
    __data_object_fields__ = ()


def test_json_and_yaml_metadata_never_conflict_or_override_modern_schema():
    """SDO emits the modern schema once; legacy projections stay independent."""
    read = AIigIndependentFormatMetadata_1
    read.__module__ = 'unit.example.aiig_independent_format_metadata_1'
    result = configured_service().generate(read)
    assert result.implementation.source_definition_id == 'modern-identity'
    assert result.implementation.source_definition_version == 7
    for emitted in (result.mutable_interface.source, result.implementation.source):
        assert emitted.count('__json_schema__ = AIaDataObjectJsonSchema(') == 1
        assert "schema_id='modern-identity', schema_version=7" in emitted
        assert "schema_id='json-identity', schema_version=2" in emitted
        assert "schema_id='yaml-identity', schema_version=5" in emitted
        assert 'https://example.org/json-schema' in emitted
        assert 'https://example.org/yaml-schema' in emitted


def test_bootstrap_does_not_label_codegen_validation_as_bootstrap():
    """Diagnostics are Codegen-owned even at the bootstrap invocation boundary."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[7]
    source = (root / 'devops/bootstrap/generate_sources.py').read_text(encoding='utf-8')
    assert "report_exception(failure, generator='Codegen')" in source
    assert 'Bootstrap Codegen' not in source
