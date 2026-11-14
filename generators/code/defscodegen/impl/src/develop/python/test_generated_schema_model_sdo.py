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
from eu.algites.tool.codegen.defs.model.aing_scalar_kind_1 import AIngScalarKind_1
from eu.algites.tool.codegen.defs.model.aing_type_origin_1 import AIngTypeOrigin_1
from eu.algites.tool.codegen.defs.model.aing_resolution_state_1 import AIngResolutionState_1
from eu.algites.tool.codegen.defs.model.aing_source_input_kind_1 import AIngSourceInputKind_1
from eu.algites.tool.codegen.defs.model.impl.aicgd_canonical_model_1 import AIcgdCanonicalModel_1
from eu.algites.tool.codegen.defs.model.impl.aicgd_scalar_1 import AIcgdScalar_1
from eu.algites.tool.codegen.defs.model.impl.aicgd_structure_scalar_1 import AIcgdStructureScalar_1
from eu.algites.tool.codegen.defs.model.impl.aicgd_type_1 import AIcgdType_1
from eu.algites.tool.codegen.defs.model.impl.aicgd_source_binding_1 import AIcgdSourceBinding_1
from eu.algites.tool.codegen.defs.model.impl.aicgd_source_bindings_1 import AIcgdSourceBindings_1
from eu.algites.tool.codegen.defs.model.impl.aicgd_source_binding_group_1 import (
    AIcgdSourceBindingGroup_1,
)


def _model():
    """Create a fully typed model without the handwritten canonical_model.py records."""
    scalar = AIcgdScalar_1()
    scalar.setScalarKind(AIngScalarKind_1.STRING)
    scalar.setFormat('')
    assert isinstance(scalar, AIigScalar_1)
    structure = AIcgdStructureScalar_1()
    structure.setScalar(scalar)

    source_binding = AIcgdSourceBinding_1()
    source_binding.setSourceResource('schema.json')
    source_binding.setSourcePointer('#/$defs/Node')
    source_binding.setRepresentationKind('object')
    source_bindings = AIcgdSourceBindings_1()
    group = AIcgdSourceBindingGroup_1()
    group.setInputKind(AIngSourceInputKind_1.JSONDEFS)
    group.getBinding().append(source_binding)
    source_bindings.getSourceBindingGroup().append(group)

    node = AIcgdType_1()
    node.setIdentity('Node')
    node.setName('Node')
    node.setOrigin(AIngTypeOrigin_1.DECLARED)
    node.setResolutionState(AIngResolutionState_1.RESOLVED)
    node.setStructure(AIigStructureSelectedScalar_1(structure))
    node.setSourceBindings(source_bindings)
    assert isinstance(node, AIigType_1)
    result = AIcgdCanonicalModel_1()
    result.getTypes().append(node)
    return result


def test_generated_typed_canonical_model_round_trips_to_schema_payload():
    """The generated sealed choice and map entries preserve data in canonical JSON."""
    result = _model().to_mapping()
    tool = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
    schema = json.loads((tool / 'generators/code/defscodegen/intf/src/product/jsondefs/'
        'eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json').read_text())
    Draft202012Validator(schema).validate(result)
    assert result['types'][0]['structure']['Scalar']['scalar_kind'] == 'STRING'
    groups = result['types'][0]['source_bindings']['SourceBindingGroup']
    assert len(groups) == 1
    assert groups[0]['InputKind'] == 'JSONDEFS'
    bindings = groups[0]['Binding']
    assert bindings == [{'source_resource': 'schema.json',
                         'source_pointer': '#/$defs/Node', 'representation_kind': 'object'}]


def test_canonical_mapping_rejects_duplicate_source_groups():
    """Repeated group kinds must not silently overwrite provenance."""
    from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import _bindings_mapping
    result = _model()
    collection = result.getTypes()[0].getSourceBindings()
    duplicate = AIcgdSourceBindingGroup_1()
    duplicate.setInputKind(AIngSourceInputKind_1.JSONDEFS)
    collection.getSourceBindingGroup().append(duplicate)
    with pytest.raises(ValueError, match='Repeated provenance kind'):
        _bindings_mapping(collection)
