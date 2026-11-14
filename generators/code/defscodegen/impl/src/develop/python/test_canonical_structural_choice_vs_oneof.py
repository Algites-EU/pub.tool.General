"""Keep Algites structural CHOICE strictly independent from JSON Schema validation."""
import json
from pathlib import Path
import pytest
from test_canonical_schema_frontend import frontend
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIngComposition_1 as Composition, AIngSourceInputKind_1 as Source,
    AIcgdType_1 as NamedType,
)


@pytest.mark.parametrize('kind', (Source.JSONDEFS, Source.YAMLDEFS))
def test_oneof_never_synthesizes_choice_or_loses_object_properties(kind):
    source = {
        'title': 'Person', 'type': 'object',
        'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}},
        'oneOf': [{'required': ['name']}, {'required': ['age']}],
    }
    with pytest.warns(UserWarning, match=r'oneOf.*#'):
        result = frontend().load_json_or_yaml(source, 'person.schema.json', kind)
    assert result.structure.composition == Composition.SEQUENCE
    assert [field.name for field in result.structure.children] == ['name', 'age']
    assert all(field.structure.kind.name == 'SCALAR' for field in result.structure.children)


@pytest.mark.parametrize('kind', (Source.JSONDEFS, Source.YAMLDEFS))
def test_explicit_choice_creates_closed_structural_variants(kind):
    schema = {
        'title': 'Selected', 'type': 'object',
        'x-algites-defscodegen-choice': True,
        'properties': {'text': {'type': 'string'}, 'number': {'type': 'integer'}},
        'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False,
    }
    result = frontend().load_json_or_yaml(schema, 'selected.schema.json', kind)
    assert result.structure.composition == Composition.CHOICE
    assert [field.name for field in result.structure.children] == ['text', 'number']
    assert all(isinstance(field.structure, NamedType) for field in result.structure.children)
    assert [field.structure.structure.scalar_kind.name for field in result.structure.children] == ['STRING', 'INTEGER']


@pytest.mark.parametrize('kind', (Source.JSONDEFS, Source.YAMLDEFS))
def test_explicit_choice_with_named_ref_keeps_typed_variant(kind):
    schema = {
        'title': 'Root', '$defs': {'Named': {'type': 'object', 'properties': {'id': {'type': 'string'}}}},
        'type': 'object', 'x-algites-defscodegen-choice': True,
        'properties': {'named': {'$ref': '#/$defs/Named'}, 'number': {'type': 'integer'}},
        'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False,
    }
    result = frontend().load_json_or_yaml(schema, 'selected.schema.json', kind)
    assert result.structure.composition == Composition.CHOICE
    named_variant = result.structure.children[0].structure
    assert named_variant.structure.composition == Composition.SEQUENCE
    assert named_variant.structure.children[0].structure.identity == '#/$defs/Named'


@pytest.mark.parametrize('kind', (Source.JSONDEFS, Source.YAMLDEFS))
def test_canonical_model_type_content_is_explicit_structural_choice(kind):
    tool = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
    extension = 'jsondef' if kind is Source.JSONDEFS else 'yamldef'
    directory = 'jsondefs' if kind is Source.JSONDEFS else 'yamldefs'
    path = tool / f'generators/code/defscodegen/intf/src/product/{directory}/eu/algites/tool/codegen/defs/model/canonical-model_1.{extension}.schema.json'
    schema = json.loads(path.read_text())
    nodes = frontend().load_json_or_yaml_types(schema, str(path), kind)
    by_name = {node.name: node for node in nodes}
    assert by_name['Structure'].structure.composition == Composition.CHOICE
    assert by_name['ElementListChild'].structure.composition == Composition.CHOICE
    assert by_name['Type'].structure.composition == Composition.SEQUENCE
    assert {field.name for field in by_name['Type'].structure.children} >= {'content'}
    assert 'structure' not in {field.name for field in by_name['Type'].structure.children}
    assert 'target_identity' not in {field.name for field in by_name['Type'].structure.children}
    assert by_name['TypeContent'].structure.composition == Composition.CHOICE
    assert {field.name for field in by_name['TypeContent'].structure.children} == {
        'structure', 'target_identity'}



_TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
_PRODUCT_SCHEMAS = sorted(
    (path, kind)
    for repository in ('pub.lib.General', 'pub.tool.General')
    for extension, kind in (('jsondef', Source.JSONDEFS), ('yamldef', Source.YAMLDEFS))
    for path in (_TOOL.parent / repository).rglob('*.' + extension + '.schema.json')
    if '/src/product/' in path.as_posix()
)


def test_product_schema_preflight_scope_has_all_current_schemas():
    assert len(_PRODUCT_SCHEMAS) == 42


@pytest.mark.parametrize('path,kind', _PRODUCT_SCHEMAS,
    ids=[p.parent.name + '/' + p.name for p, _ in _PRODUCT_SCHEMAS])
def test_current_product_schema_preserves_storage_shape(path, kind):
    """Every product definition remains structurally readable despite deferred validation."""
    import warnings
    with warnings.catch_warnings(record=True):
        warnings.simplefilter('always', UserWarning)
        nodes = frontend().load_json_or_yaml_types(json.loads(path.read_text()),
                                                    str(path), kind)
    assert nodes


@pytest.mark.parametrize('keyword', ('oneOf', 'anyOf', 'allOf', 'then', 'not'))
def test_structural_choice_cannot_be_hidden_in_validation_only_branch(keyword):
    marker = {'type': 'object', 'x-algites-defscodegen-choice': True,
              'properties': {'a': {'type': 'string'}, 'b': {'type': 'integer'}},
              'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False}
    schema = {'type': 'object', keyword: [marker] if keyword in ('oneOf','anyOf','allOf') else marker}
    with pytest.raises(ValueError, match='Structural choice inside validation-only branch'):
        frontend().load_json_or_yaml(schema, 'invalid.schema.json', Source.JSONDEFS)


def test_referenced_structural_choice_emits_typed_java_and_python(tmp_path):
    """Named choice wrappers use actual refs without treating any oneOf as structure."""
    import subprocess
    from test_canonical_source_emitter import _pipeline, _emitter
    from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
        AIcDefsCodegenCanonicalSourceEmitter, AIcdDefsCodegenEmissionName)
    from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import AIcdDefsCodegenSourceDocument
    schema = {'$id': 'urn:choice-with-ref', '$defs': {
        'Named': {'type': 'object', 'properties': {'id': {'type': 'string'}}},
        'Selected': {'type': 'object', 'x-algites-defscodegen-choice': True,
            'properties': {'named': {'$ref': '#/$defs/Named'}, 'number': {'type': 'integer'}},
            'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False}}}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Source.JSONDEFS, 'choice.json', schema),))
    types = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    names = {node.identity: AIcdDefsCodegenEmissionName(
        f'AIigChoice{i}', f'AIigChoice{i}', f'aiig_choice{i}') for i, node in enumerate(types)}
    rendered = _emitter(result.types, names).render(result.types)
    assert rendered
    for item in rendered:
        path = tmp_path / item.language / item.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item.content)
    tool = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
    lib = tool.parent / 'pub.lib.General'
    java_files = list((tmp_path / 'java').rglob('*.java'))
    compiled = subprocess.run(['javac', '-sourcepath', str(lib / 'data/dataobject/intf/src/product/java'),
        '-d', str(tmp_path / 'classes'), *map(str, java_files)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    for path in (tmp_path / 'python').rglob('*.py'):
        compile(path.read_text(), str(path), 'exec')
