from eu.algites.tool.codegen.defs.impl.standard._source_data_type import from_source_hints
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
"""Different serialization-specific $schema URLs may merge, but real field differences may not."""
from dataclasses import replace
import pytest

from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger


def definition(kind, uri, field_kind=AInDataTypeKind.STRING):
    fmt = kind.value
    suffix = 'jsondef' if fmt == 'jsondefs' else 'yamldef'
    path = f'artifact/src/product/{fmt}/example/customer_1.{suffix}.schema.json'
    return AIcdCanonicalDefinition('urn:customer', 1, 'customer', kind, path, None,
        AIcdDataType(AInDataTypeKind.OBJECT, properties=(
            AIcdPropertyDefinition('$schema', from_source_hints(AInDataTypeKind.STRING, None, None, AIcdValueConstraints(
                data_type='string', enum_values=(uri,)), AIcdValueConstraints()), (AInFieldPresenceKind.REQUIRED if False else AInFieldPresenceKind.ALLOWED), False, None, None, None),
            AIcdPropertyDefinition('Name', from_source_hints(field_kind, None, None, AIcdValueConstraints(), AIcdValueConstraints()), (AInFieldPresenceKind.REQUIRED if True else AInFieldPresenceKind.ALLOWED), False, None, None, None))))


def test_format_specific_self_published_urls_merge():
    j = definition(AInDefinitionSourceKind.JSONDEFS,
        'https://defs.dev.algites.eu/api/jsondefs/example/customer_1.jsondef.schema.json')
    y = definition(AInDefinitionSourceKind.YAMLDEFS,
        'https://defs.dev.algites.eu/api/yamldefs/example/customer_1.yamldef.schema.json')
    merged = AIcCanonicalDefinitionMerger.merge((j, y))
    assert merged.data_type.properties[0].data_type.constraints.enum_values == ()
    assert merged.data_type.properties[1].data_type.kind is AInDataTypeKind.STRING
    # Builder's artifact-local source paths start directly at src/product/.
    root_json = replace(j, source_resource=j.source_resource.removeprefix('artifact/'))
    root_yaml = replace(y, source_resource=y.source_resource.removeprefix('artifact/'))
    assert AIcCanonicalDefinitionMerger.merge((root_json, root_yaml)).data_type.properties[0].data_type.constraints.enum_values == ()


def test_other_constant_and_real_field_incompatibility():
    j = definition(AInDefinitionSourceKind.JSONDEFS,
        'https://defs.dev.algites.eu/api/jsondefs/example/customer_1.jsondef.schema.json')
    y = definition(AInDefinitionSourceKind.YAMLDEFS,
        'https://defs.dev.algites.eu/api/yamldefs/example/customer_1.yamldef.schema.json')
    with pytest.raises(ValueError, match='Incompatible'):
        AIcCanonicalDefinitionMerger.merge((j, replace(y, data_type=y.data_type.with_properties((replace(y.data_type.properties[0],
            data_type=replace(y.data_type.properties[0].data_type, constraints=AIcdValueConstraints(enum_values=('urn:foreign',)))),
                        y.data_type.properties[1])) )))
    with pytest.raises(ValueError, match='Incompatible'):
        AIcCanonicalDefinitionMerger.merge((j, replace(y, data_type=y.data_type.with_properties((y.data_type.properties[0],
        replace(y.data_type.properties[1], data_type=AIcdDataType(AInDataTypeKind.INTEGER)))))))
