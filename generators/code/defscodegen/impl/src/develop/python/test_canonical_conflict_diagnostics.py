from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
"""Diagnostic regression for all pairs, source lines and changed documentation."""
from dataclasses import replace
from pathlib import Path
import pytest

from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger
from eu.algites.tool.codegen.defs.impl.standard.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_yaml_defs_frontend import AIcYamlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest

ROOT = Path(__file__).parents[4] / 'intf/src/product'
FORMATS = (
    ('yamldefs', 'yamldef.schema.json', AIcYamlDefsFrontend, AInDefinitionSourceKind.YAMLDEFS),
    ('jsondefs', 'jsondef.schema.json', AIcJsonDefsFrontend, AInDefinitionSourceKind.JSONDEFS),
    ('xmldefs', 'xsd', AIcXmlDefsFrontend, AInDefinitionSourceKind.XMLDEFS),
)


@pytest.mark.parametrize('stem', ('input-profile', 'schema-field-bindings'))
def test_published_formats_compatible_and_documentation_edits_detected(stem):
    models = []
    for directory, extension, frontend, kind in FORMATS:
        source = ROOT / directory / 'eu/algites/tool/codegen/defs' / f'{stem}_1.{extension}'
        models.append(frontend().load(AIcdDefinitionLoadRequest(source, kind, None)))
    AIcCanonicalDefinitionMerger.merge_strict(models)
    original = models[1]
    first = original.data_type.properties[0]
    amended = replace(first, description=(first.description or '') + '!')
    changed = replace(original, data_type=original.data_type.with_properties((amended, *original.data_type.properties[1:])))
    with pytest.raises(ValueError, match='Incompatible canonical definitions') as error:
        AIcCanonicalDefinitionMerger.merge_strict((models[0], changed, models[2]))
    message = str(error.value)
    assert 'description' in message and 'INCONSISTENT' in message and 'CONSISTENT' in message
    assert all(str(Path(model.source_resource).resolve()) in message for model in models)
    assert 'Pairwise comparison' in message and ':' in message
    changed_type = replace(first, data_type=AIcdDataType(AInDataTypeKind.INTEGER))
    with pytest.raises(ValueError, match='kind'):
        AIcCanonicalDefinitionMerger.merge_strict((models[0], replace(original, data_type=original.data_type.with_properties((changed_type, *original.data_type.properties[1:]))), models[2]))
