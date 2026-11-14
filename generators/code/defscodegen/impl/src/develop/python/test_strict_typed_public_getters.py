"""Regression: canonical getters must never use Object/Any as a fallback.

The canonical graph can record unresolved schema information temporarily, but
neither public Defs emitter may turn that into an untyped DataObject getter.

@author linhart1
"""
from pathlib import Path
import re

import pytest

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdScalar_1 as Scalar,
    AIngScalarKind_1 as ScalarKind,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter as Emitter,
)


@pytest.mark.parametrize('language', ('java', 'python'))
def test_unresolved_any_never_emits_an_untyped_public_getter(language):
    location = 'sample.jsondef.schema.json#/$defs/Thing/properties/value'
    with pytest.raises(ValueError, match=r'Object/Any is forbidden') as failure:
        Emitter.__new__(Emitter)._typed(Scalar(ScalarKind.ANY), language, {}, location)
    assert location in str(failure.value)
    assert language in str(failure.value)


@pytest.mark.parametrize('language,expected', (
    ('java', 'String'), ('python', 'str'),
))
def test_known_scalars_remain_precisely_typed(language, expected):
    assert Emitter.__new__(Emitter)._typed(
        Scalar(ScalarKind.STRING), language, {}, 'typed-property') == expected


def test_native_java_emitter_rejects_any_instead_of_generating_object():
    root = next(parent for parent in Path(__file__).resolve().parents
                if parent.name == 'pub.tool.General')
    java = (root / 'generators/code/defscodegen/impl/src/product/java/eu/algites/'
            'tool/codegen/defs/impl/standard/AIcDefsCodegenCanonicalSourceEmitter.java')
    source = java.read_text(encoding='utf-8')
    assert re.search(r'case ANY\s*->\s*throw new IllegalArgumentException\(', source)
    assert not re.search(r'case ANY\s*->\s*(?:javaTarget\s*\?|["\']Object)', source)
    assert 'Object/Any is forbidden' in source

@pytest.mark.parametrize('kind', ('missing', 'incompatible'))
def test_common_merger_does_not_silently_lose_business_getter(kind):
    """Real schema source kinds must never disappear through field intersection."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _merge_common_contract
    from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
        AIcgdType_1 as Type,
        AIcgdElementList_1 as Group,
        AIcgdElement_1 as Element,
        AIngComposition_1 as Composition,
        AIngSourceInputKind_1 as SourceKind,
    )

    class StubEmitter:
        def __init__(self, field_type):
            self.field_type = field_type

        def _fields(self, _node, _types, _language):
            return ([('IdentifierConventions', 'getIdentifierConventions',
                      'setIdentifierConventions', self.field_type, 0, 1, '')]
                    if self.field_type is not None else [])

    contexts = []
    for source, field_type in (
        (SourceKind.XMLDEFS, 'AIigIdentifierConventions_1'),
        (SourceKind.JSONDEFS, None if kind == 'missing'
         else 'AIiMultiMappedList<? extends AIigIdentifierConvention_1>'),
    ):
        node = Type('schema.identity', 'CommonNamingConventions', source,
                    structure=Group(Composition.SEQUENCE, (
                        Element('IdentifierConventions', Scalar(ScalarKind.STRING)),)))
        contexts.append((node, {'schema.identity': node}, StubEmitter(field_type),
                         (), 'java', source.name))
    with pytest.raises(ValueError, match='IdentifierConventions') as failure:
        _merge_common_contract('naming/convention/AIigCommonNamingConventions_1.java', contexts)
    assert ('absent' if kind == 'missing' else 'incompatible types') in str(failure.value)
    assert 'naming/convention' in str(failure.value)
