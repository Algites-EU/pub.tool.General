"""Business-level cross-language parity of *native canonical Defs output*.

This checks the shared DataObject contract semantics, rather than the spelling
of target-language syntax. It complements (but does not replace) the separate
TestNG check that compares independently executed JVM/Python generators.
"""
from __future__ import annotations

import re

import pytest

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIigSourceInputKind_1 as SourceKind,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcdDefsCodegenSourceDocument,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter,
    AIcdDefsCodegenEmissionName,
)
from test_canonical_source_emitter import _pipeline, _profile


def _sources(schema, source_kind=SourceKind.JSONDEFS):
    """Produce and index actual Java and Python sources from one typed graph."""
    payload = schema if source_kind is not SourceKind.XMLDEFS else schema
    types = _pipeline().process((AIcdDefsCodegenSourceDocument(source_kind, 'contract.schema', payload),)).types
    declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(types)
    names = {item.identity: AIcdDefsCodegenEmissionName(
        f'AIigT{index}', f'AIigT{index}', f'aiig_t{index}')
        for index, item in enumerate(declarations)}
    output = AIcDefsCodegenCanonicalSourceEmitter(
        _profile(), names, 'equivalence.contract').render(types)
    result = {}
    for entry in output:
        result[entry.language, entry.relative_path.split('/')[-1]] = entry.content
    return result


def _java_getters(source):
    """Read the public parameterless getter surface from an interface."""
    return set(re.findall(r'\b(get[A-Z]\w*)\s*\(\s*\)\s*;', source))


def _python_getters(source):
    """Read generated abstract getter declarations from the matching interface."""
    return set(re.findall(r'\bdef\s+(get[A-Z]\w*)\s*\(self\)', source))


class TestReadOnlyContractParity:
    """One schema must produce structurally matching Java and Python DO APIs."""

    @pytest.mark.parametrize('schema', (
        {'$id': 'urn:basic', 'type': 'object', 'properties': {
            'name': {'type': 'string'}, 'enabled': {'type': 'boolean'},
            'count': {'type': 'integer'}}, 'required': ['name']},
        {'$id': 'urn:array', 'type': 'object', 'properties': {
            'children': {'type': 'array', 'items': {'type': 'string'}},
            'meta': {'type': 'object', 'properties': {'flag': {'type': 'boolean'}}}}},
    ))
    @pytest.mark.parametrize('source_kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
    def test_field_getters_and_dataobject_annotations(self, schema, source_kind):
        """Java and Python must expose exactly the same named getter roles."""
        sources = _sources(schema, source_kind)
        for (_, file), java in sources.items():
            if not file.endswith('.java') or 'interface ' not in java:
                continue
            stem = file.removesuffix('.java').lower()
            python_file = 'aiig_' + stem.removeprefix('aiig') + '.py'
            # Names in the fixture use AIigT0 / aiig_t0, with package-independent lookup.
            index = re.search(r'(\d+)$', stem)
            if index:
                python_file = f'aiig_t{index.group(1)}.py'
            python = sources['python', python_file]
            assert _java_getters(java) == _python_getters(python)
            assert '@eu.algites.lib.data.dataobject.AIaDataObject(' in java
            assert 'AIcdDataObject(' in python
            for getter in _java_getters(java):
                assert 'AIaDataObjectField' in java
                assert '@AIaDataObjectField' in python
            assert 'void set' not in java
            assert 'def set' not in python

    @pytest.mark.parametrize('values,expected_type', (
        (['ready', 'blocked'], 'String'),
        ([True, False], 'Boolean'),
        ([100000000000000000000000000000, -4], 'java.math.BigInteger'),
    ))
    def test_enum_wire_code_and_member_count(self, values, expected_type):
        """Enums retain value order/type and identical stable member ordinals."""
        type_name = ('string' if isinstance(values[0], str) else
                     'boolean' if isinstance(values[0], bool) else 'integer')
        sources = _sources({'$id': 'urn:enum', 'type': type_name, 'enum': values})
        java = sources['java', 'AIigT0.java']
        python = sources['python', 'aiig_t0.py']
        assert f'{expected_type} code()' in java
        assert 'def code(self)' in python
        assert [int(n) for n in re.findall(r'\bVALUE_(\d+)\s*\(', java)] == [1, 2]
        assert [int(n) for n in re.findall(r'\bVALUE_(\d+)\s*=', python)] == [1, 2]
