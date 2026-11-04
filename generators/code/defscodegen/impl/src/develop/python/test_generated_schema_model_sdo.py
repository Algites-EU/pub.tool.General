"""Schema-generated canonical model contracts work with the independent SDO generator."""
from __future__ import annotations

import sys
import json
from pathlib import Path

# SDO implementations here are generated test fixtures, not part of the Defs read-contract artifact.
_fixture_root = Path(__file__).resolve().parents[1] / "python.gen"
sys.path.insert(0, str(_fixture_root))

import pytest
from jsonschema import Draft202012Validator

from eu.algites.tool.codegen.defs.model.aiig_type_1 import AIigType_1
from eu.algites.tool.codegen.defs.model.aiig_scalar_1 import AIigScalar_1
from eu.algites.tool.codegen.defs.model.aiig_structure_selected_scalar_1 import AIigStructureSelectedScalar_1
from eu.algites.tool.codegen.defs.model.aiig_scalar_kind_1 import AIigScalarKind_1
from eu.algites.tool.codegen.defs.model.aiig_type_origin_1 import AIigTypeOrigin_1
from eu.algites.tool.codegen.defs.model.aiig_resolution_state_1 import AIigResolutionState_1
from eu.algites.tool.codegen.defs.model.impl.aicgd__j_canonical_model_1 import AIcgd_jCanonicalModel_1
from eu.algites.tool.codegen.defs.model.impl.aicgd__j_scalar_1 import AIcgd_jScalar_1
from eu.algites.tool.codegen.defs.model.impl.aicgd__j_structure_scalar_1 import AIcgd_jStructureScalar_1
from eu.algites.tool.codegen.defs.model.impl.aicgd__j_type_1 import AIcgd_jType_1
from eu.algites.tool.codegen.defs.model.impl.aicgd__j_source_binding_1 import AIcgd_jSourceBinding_1
from eu.algites.tool.codegen.defs.model.impl.aicgd__j_source_bindings_1 import AIcgd_jSourceBindings_1
from eu.algites.tool.codegen.defs.model.impl.aicgd__j_source_bindings_additional_properties_1 import (
    AIcgd_jSourceBindingsAdditionalProperties_1,
)


def _model():
    """Create a fully typed model without the handwritten canonical_model.py records."""
    scalar = AIcgd_jScalar_1()
    scalar.setScalarKind(AIigScalarKind_1.STRING)
    scalar.setFormat('')
    assert isinstance(scalar, AIigScalar_1)
    structure = AIcgd_jStructureScalar_1()
    structure.setScalar(scalar)

    source_binding = AIcgd_jSourceBinding_1()
    source_binding.setSourceResource('schema.json')
    source_binding.setSourcePointer('#/$defs/Node')
    source_binding.setRepresentationKind('object')
    source_bindings = AIcgd_jSourceBindings_1()
    source_bindings.append(AIcgd_jSourceBindingsAdditionalProperties_1(
        parent_property_key='JSONDEFS', parent_property_value=[source_binding]))

    node = AIcgd_jType_1()
    node.setIdentity('Node')
    node.setName('Node')
    node.setOrigin(AIigTypeOrigin_1.DECLARED)
    node.setResolutionState(AIigResolutionState_1.RESOLVED)
    node.setStructure(AIigStructureSelectedScalar_1(structure))
    node.setSourceBindings(source_bindings)
    assert isinstance(node, AIigType_1)
    result = AIcgd_jCanonicalModel_1()
    result.setTypes([node])
    return result


def test_generated_typed_canonical_model_round_trips_to_schema_payload():
    """The generated sealed choice and map entries preserve data in canonical JSON."""
    result = _model().to_mapping()
    tool = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
    schema = json.loads((tool / 'generators/code/defscodegen/intf/src/product/jsondefs/'
        'eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json').read_text())
    Draft202012Validator(schema).validate(result)
    assert result['types'][0]['structure']['Scalar']['scalar_kind'] == 'STRING'
    bindings = result['types'][0]['source_bindings']['JSONDEFS']
    assert bindings == [{'source_resource': 'schema.json',
                         'source_pointer': '#/$defs/Node', 'representation_kind': 'object'}]


def test_generated_property_map_rejects_duplicate_external_keys():
    """Repeated map keys cannot silently erase earlier provenance entries."""
    result = _model()
    collection = result.getTypes()[0].getSourceBindings()
    collection.append(AIcgd_jSourceBindingsAdditionalProperties_1(
        parent_property_key='JSONDEFS', parent_property_value=[]))
    with pytest.raises(ValueError, match='Duplicate or reserved mapped DataObject key'):
        result.to_mapping()
