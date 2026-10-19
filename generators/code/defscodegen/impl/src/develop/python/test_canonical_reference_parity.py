from eu.algites.tool.codegen.defs.impl.standard._source_data_type import from_source_hints
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
"""Reference parity compares canonical targets, not source serialization suffixes."""
from dataclasses import replace
import pytest

from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_definition_reference import AIcdDefinitionReference
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger


def _definition(source_kind):
    suffix = 'jsondef.schema.json' if source_kind is AInDefinitionSourceKind.JSONDEFS else 'yamldef.schema.json'
    properties = tuple(
        AIcdPropertyDefinition(name, from_source_hints(AInDataTypeKind.REFERENCE if singular else AInDataTypeKind.ARRAY, None if singular else AInDataTypeKind.REFERENCE, AIcdDefinitionReference(f'../values/{target}_1.{suffix}', 1, target, AIcdDataType(kind)), AIcdValueConstraints(), AIcdValueConstraints()), (AInFieldPresenceKind.REQUIRED if False else AInFieldPresenceKind.ALLOWED), False, None, None, None)
        for name, target, kind, singular in (
            ('Child', 'child', AInDataTypeKind.OBJECT, True),
            ('Children', 'child', AInDataTypeKind.OBJECT, False),
            ('State', 'state', AInDataTypeKind.ENUM, True),
            ('States', 'state', AInDataTypeKind.ENUM, False)))
    return AIcdCanonicalDefinition('urn:example:root', 1, 'root', source_kind,
        f'intf/src/product/{source_kind.value}/example/contracts/root_1.{suffix}', None,
        AIcdDataType(AInDataTypeKind.OBJECT, properties=properties))


def test_json_yaml_reference_suffixes_are_not_semantic_differences():
    json = _definition(AInDefinitionSourceKind.JSONDEFS)
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS)
    AIcCanonicalDefinitionMerger.validate((json, yaml))
    merged = AIcCanonicalDefinitionMerger.merge_strict((json, yaml))
    assert merged.data_type.properties == json.data_type.properties
    assert all(a.data_type.referenced_definition().identity != b.data_type.referenced_definition().identity
        for a, b in zip(json.data_type.properties, yaml.data_type.properties))


@pytest.mark.parametrize('member,updated', (
    ('logical_name', 'another-child'),
    ('version', 2),
    ('target_data_type', AIcdDataType(AInDataTypeKind.ENUM)),
))
def test_reference_target_mismatch_is_reported(member, updated):
    json = _definition(AInDefinitionSourceKind.JSONDEFS)
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS)
    changed = replace(yaml.data_type.properties[0], data_type=replace(yaml.data_type.properties[0].data_type,
        reference=replace(yaml.data_type.properties[0].data_type.reference, **{member: updated})))
    yaml = replace(yaml, data_type=yaml.data_type.with_properties((changed, *yaml.data_type.properties[1:])))
    with pytest.raises(ValueError, match="field 'Child'.reference") as error:
        AIcCanonicalDefinitionMerger.merge_strict((json, yaml))
    message = str(error.value)
    assert 'JSONDEFS vs [2] YAMLDEFS: INCONSISTENT' in message
    assert 'jsondef.schema.json' in message and 'yamldef.schema.json' in message
    assert "field 'Children'.reference" not in message
