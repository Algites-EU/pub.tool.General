"""Cross-language canonical enum wire values must be semantically unique."""
import sys
from pathlib import Path
import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
for relative in ('generators/code/defscodegen/intf/src/product/python',
                 'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(ROOT / relative))
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdEnum_1, AIcgdEnumValue_1, AIngScalarKind_1,
)


@pytest.mark.parametrize(('kind', 'values'), [
    (AIngScalarKind_1.STRING, ('ready', 'ready')),
    (AIngScalarKind_1.INTEGER, ('1', '01')),
    (AIngScalarKind_1.INTEGER, ('+1', '1')),
    (AIngScalarKind_1.NUMBER, ('1.0', '1.00')),
    (AIngScalarKind_1.NUMBER, ('10e-1', '1')),
    (AIngScalarKind_1.BOOLEAN, ('true', '1')),
])
def test_duplicate_semantic_wire_values_rejected(kind, values):
    with pytest.raises(ValueError, match='Duplicate ENUM'):
        AIcgdEnum_1(kind, tuple(AIcgdEnumValue_1(item) for item in values))


def test_distinct_enum_values_keep_source_spelling_and_order():
    values = ('001', '2', '3')
    enum = AIcgdEnum_1(AIngScalarKind_1.INTEGER,
            tuple(AIcgdEnumValue_1(item) for item in values))
    assert tuple(item.wire_value for item in enum.values) == values
