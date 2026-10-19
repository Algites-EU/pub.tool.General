from eu.algites.tool.codegen.defs.impl.standard._source_data_type import from_source_hints
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
"""Ensure cross-format verification never ignores recursively nested schema differences."""
from dataclasses import replace
import pytest

from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger


def _definition(source, data_type):
    property = AIcdPropertyDefinition('items', data_type, (AInFieldPresenceKind.REQUIRED if False else AInFieldPresenceKind.ALLOWED), False, None, None, None)
    return AIcdCanonicalDefinition('urn:example:recursive', 1, 'recursive',
        source, f'intf/src/product/{source.value}/example/recursive_1', None,
        AIcdDataType(AInDataTypeKind.OBJECT, properties=(property,)))


def test_nested_array_leaf_is_compared_and_rejected():
    integer = AIcdDataType(AInDataTypeKind.INTEGER)
    string = AIcdDataType(AInDataTypeKind.STRING)
    json = _definition(AInDefinitionSourceKind.JSONDEFS,
        AIcdDataType(AInDataTypeKind.ARRAY, element_type=AIcdDataType(AInDataTypeKind.ARRAY, element_type=integer)))
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS,
        AIcdDataType(AInDataTypeKind.ARRAY, element_type=AIcdDataType(AInDataTypeKind.ARRAY, element_type=string)))
    with pytest.raises(ValueError, match=r'items.*dataType.*items.*kind'):
        AIcCanonicalDefinitionMerger.validate((json, yaml))
    AIcCanonicalDefinitionMerger.validate((json, replace(yaml, data_type=json.data_type)))


def test_nested_oneof_anyof_are_never_interchangeable():
    leaf = AIcdDataType(AInDataTypeKind.STRING)
    choice = AIcdDataType.choice(AInDataTypeKind.ONE_OF, (leaf, leaf))
    anyof = AIcdDataType.choice(AInDataTypeKind.ANY_OF, (leaf, leaf))
    json = _definition(AInDefinitionSourceKind.JSONDEFS,
        AIcdDataType(AInDataTypeKind.ARRAY, element_type=choice))
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS,
        AIcdDataType(AInDataTypeKind.ARRAY, element_type=anyof))
    with pytest.raises(ValueError, match=r'items.*dataType.*items.*kind'):
        AIcCanonicalDefinitionMerger.validate((json, yaml))


def test_inline_object_property_presence_and_type_are_compared():
    left = AIcdPropertyDefinition('label', from_source_hints(AInDataTypeKind.STRING, None, None, AIcdValueConstraints(), AIcdValueConstraints()), (AInFieldPresenceKind.REQUIRED if False else AInFieldPresenceKind.ALLOWED), False, None, None, None)
    right = AIcdPropertyDefinition('label', from_source_hints(AInDataTypeKind.STRING, None, None, AIcdValueConstraints(), AIcdValueConstraints()), (AInFieldPresenceKind.REQUIRED if True else AInFieldPresenceKind.ALLOWED), False, None, None, None)
    json = _definition(AInDefinitionSourceKind.JSONDEFS,
        AIcdDataType(AInDataTypeKind.ARRAY, element_type=AIcdDataType(AInDataTypeKind.OBJECT, properties=(left,))))
    yaml = _definition(AInDefinitionSourceKind.YAMLDEFS,
        AIcdDataType(AInDataTypeKind.ARRAY, element_type=AIcdDataType(AInDataTypeKind.OBJECT, properties=(right,))))
    with pytest.raises(ValueError, match=r'properties\[label\].presence'):
        AIcCanonicalDefinitionMerger.validate((json, yaml))
