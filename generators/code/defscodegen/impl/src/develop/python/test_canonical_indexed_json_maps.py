"""JSONDEFS/YAMLDEFS indexed-map projections and universal CONST emission."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIngSourceInputKind_1 as Kind,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcdDefsCodegenSourceDocument as Document,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter as Emitter,
    AIcdDefsCodegenEmissionName as Names,
)
from test_canonical_source_emitter import _pipeline, _profile

ROOT = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
LIB = ROOT.parent / 'pub.lib.General'


def _schema():
    return {
        '$id': 'urn:map', 'title': 'Root', 'type': 'object',
        'properties': {
            'standardField': {'type': 'boolean'},
            'structureNaming': {
                'type': 'object',
                'x-algites-defscodegen-key': {
                    'id': 'UniqueStructureRoles', 'field-name': 'kind'},
                'propertyNames': {'$ref': '#/$defs/Kind'},
                'additionalProperties': {'type': 'string'},
            },
        },
        '$defs': {'Kind': {'type': 'string', 'enum': ['standard_getter', 'raw_getter']}},
    }


def _emit(schema, kind):
    result = _pipeline().process((Document(kind, 'urn:map', schema),))
    names = {node.identity: Names('AIigT' + str(i), 'AIigT' + str(i), 'aiig_t' + str(i))
             for i, node in enumerate(Emitter.declarations(result.types))}
    output = Emitter(_profile(), names, 'regression.output').render(result.types)
    return {entry.relative_path: entry.content for entry in output}


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
def test_keyed_json_map_uses_enum_list_and_constants_without_map_getter(kind, tmp_path):
    outputs = _emit(_schema(), kind)
    root_java = outputs['regression/output/AIigT0.java']
    item_java = outputs['regression/output/AIigT1.java']
    root_python = outputs['regression/output/aiig_t0.py']
    item_python = outputs['regression/output/aiig_t1.py']

    assert 'FIELD_NAME__STANDARD_FIELD = "standardField"' in root_java
    assert 'FIELD_NAME__STRUCTURE_NAMING = "structureNaming"' in root_java
    assert 'KEY_ID__UNIQUE_STRUCTURE_ROLES = "UniqueStructureRoles"' in root_java
    assert 'FIELD_NAME__KIND = "kind"' in root_java
    assert 'name = CONSTRoot.KEY_ID__UNIQUE_STRUCTURE_ROLES' in root_java
    assert 'fields = {CONSTRoot.FIELD_NAME__KIND}' in root_java
    assert 'AIiMultiMappedList<? extends AIigT1> getStructureNamingList()' in root_java
    assert 'Map<String, String> getStructureNaming()' not in root_java
    assert 'AIigT2 _getKey()' in item_java
    assert 'String _getValue()' in item_java
    assert '@AIaDataObjectField(fieldName = \"kind\"' not in item_java
    assert '@AIaDataObjectField(fieldName = \"value\"' not in item_java
    assert 'FIELD_NAME__KIND = "kind"' in item_java
    assert 'FIELD_NAME__VALUE = "value"' in item_java
    assert 'KEY_ID__UNIQUE_STRUCTURE_ROLES' in root_python
    assert 'FIELD_NAME__STANDARD_FIELD' in root_python
    assert 'AIiMultiMappedList[AIigT1]' in root_python
    assert 'def _getKey(self) -> AIigT2:' in item_python
    assert 'def _getValue(self) -> str:' in item_python

    java_dir = tmp_path / 'java'
    for rel, content in outputs.items():
        if rel.endswith('.java'):
            dest = java_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
        elif rel.endswith('.py'):
            compile(content, rel, 'exec')
    java_sources = list(java_dir.rglob('*.java'))
    lib_sources = ':'.join(str(path) for path in (
        LIB / 'data/dataobject/intf/src/product/java',
        LIB / 'common/util/src/product/java',
    ))
    compiled = subprocess.run(['javac', '-sourcepath', lib_sources, '-d', str(tmp_path / 'classes'),
                               *map(str, java_sources)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
def test_unindexed_map_keeps_old_form_and_all_field_constants(kind):
    schema = _schema()
    schema['properties']['structureNaming'].pop('x-algites-defscodegen-key')
    schema['properties']['structureNaming'].pop('propertyNames')
    outputs = _emit(schema, kind)
    root = outputs['regression/output/AIigT0.java']
    assert 'AIigT1 getStructureNaming()' in root
    assert 'AIiMultiMappedList' not in root
    assert 'FIELD_NAME__STANDARD_FIELD' in root
    assert 'KEY_ID__UNIQUE_STRUCTURE_ROLES' not in root


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
def test_keyed_map_rejects_lossy_constraints(kind):
    schema = _schema()
    schema['properties']['structureNaming']['patternProperties'] = {'^x': {'type': 'integer'}}
    with pytest.raises(ValueError, match='constraint'):
        _emit(schema, kind)


def test_key_field_name_must_resolve_to_string_property_name():
    schema = _schema()
    schema['$defs']['Kind'] = {'type': 'integer', 'enum': [1, 2]}
    with pytest.raises((ValueError, NotImplementedError), match='string|propertyNames'):
        _emit(schema, Kind.JSONDEFS)


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
def test_same_value_ref_for_explicit_properties_keeps_one_indexed_item(kind):
    """Repeated `$ref` constraints do not produce a different item per key."""
    schema = _schema()
    schema['$defs']['CompositionValue'] = {
        'type': 'object', 'properties': {'expression': {'type': 'string'}}}
    mapping = schema['properties']['structureNaming']
    value = {'$ref': '#/$defs/CompositionValue'}
    mapping['additionalProperties'] = value
    baseline = _emit(schema, kind)
    mapping['properties'] = {'standard_getter': value, 'raw_getter': value}
    actual = _emit(schema, kind)
    assert actual == baseline  # Equivalent JSON Schema constraints and API.
    assert 'AIiMultiMappedList<' in actual['regression/output/AIigT0.java']


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
def test_different_validation_facets_warn_without_dropping_indexed_storage(kind):
    """Per-key minLength is validation-only; the indexed map still stores values."""
    schema = _schema()
    mapping = schema['properties']['structureNaming']
    mapping['properties'] = {'standard_getter': {'type': 'string', 'minLength': 1}}
    with pytest.warns(UserWarning, match='Validation-only indexed map key constraints'):
        outputs = _emit(schema, kind)
    assert 'AIiMultiMappedList<' in outputs['regression/output/AIigT0.java']
    assert 'String _getValue()' in outputs['regression/output/AIigT1.java']


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
def test_external_property_names_ref_is_validation_only_and_keeps_string_key(kind):
    """External enum restrictions on JSON property names cannot block map storage."""
    schema = _schema()
    schema['properties']['structureNaming']['propertyNames'] = {
        '$ref': 'https://defs.dev.algites.eu/api/jsondefs/another/scheme_1.jsondef.schema.json'}
    with pytest.warns(UserWarning, match='external propertyNames'):
        outputs = _emit(schema, kind)
    item_java = outputs['regression/output/AIigT1.java']
    item_python = outputs['regression/output/aiig_t1.py']
    assert 'String _getKey()' in item_java
    assert 'def _getKey(self) -> str:' in item_python
    assert 'AIiMultiMappedList<' in outputs['regression/output/AIigT0.java']
