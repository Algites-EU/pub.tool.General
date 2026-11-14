"""Native canonical Defs emitter contract tests, independent of legacy backends."""
import json
import subprocess
import sys
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import replace
from pathlib import Path

import pytest
import yaml

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
LIB = TOOL.parent / 'pub.lib.General'
for name in ('generators/code/common/src/product/python',
             'generators/code/defscodegen/intf/src/product/python',
             'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(TOOL / name))

from eu.algites.tool.codegen.common.naming_profiles import resolve_codegen_naming_profiles
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIngSourceInputKind_1 as Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcDefsCodegenCanonicalPipeline, AIcdDefsCodegenSourceDocument)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter, AIcdDefsCodegenEmissionName)


def _profile():
    """Build a controlled profile with simulated resolved external getter compositions."""
    base = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
    common = yaml.safe_load((base / 'algites-java-common-codegen-conventions.yml').read_text())
    defs = yaml.safe_load((base / 'algites-java-defs-codegen-conventions.yml').read_text())
    name = resolve_codegen_naming_profiles(common, 'algites-java-codegen-common_1',
                                           defs, 'algites-java-defscodegen-standard_1')
    segments = lambda prefix: {'Segments': [
        {'NameFragmentsSegmentValue': {'Kind': 'constant_string', 'Value': prefix}},
        {'NameFragmentsSegmentValue': {'Kind': 'identifier', 'Convention': 'upper_camel_case_1'}}]}
    return replace(name, common_roles={**name.common_roles, 'standard_getter': 'test-get',
                                     'standard_setter': 'test-set'},
                   name_compositions={**name.name_compositions,
                                      'test-get': segments('get'), 'test-set': segments('set')})


def _pipeline():
    """Validate against the real generated canonical schema before source emission."""
    schema = TOOL / ('generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/'
                     'tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')
    return AIcDefsCodegenCanonicalPipeline(_profile(), json.loads(schema.read_text()))


def _source_schema():
    """Provide three mutually referential types with an exact-code enum."""
    return {'$id': 'urn:test', '$defs': {
        'Node': {'type': 'object', 'description': 'Self-referential node',
                 'properties': {'value': {'type': 'string'}, 'next': {'$ref': '#/$defs/Node'},
                                'children': {'type': 'array', 'items': {'$ref': '#/$defs/Node'}}},
                 'required': ['value']},
        'Status': {'type': 'string', 'enum': ['ready', 'on-hold']}}}


def _emitter(types, names):
    """Create a catalog-explicit source emitter without implicit class name inference."""
    return AIcDefsCodegenCanonicalSourceEmitter(_profile(), names, 'test.output')


def test_end_to_end_canonical_sources_compile_java_and_python(tmp_path):
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'test.json', _source_schema()),))
    identities = {item.name: item.identity for item in result.types}
    names = {identities['Node']: AIcdDefsCodegenEmissionName('AIigNode_1', 'AIigNode_1', 'aiig_node_1'),
             identities['Status']: AIcdDefsCodegenEmissionName('AIigStatus_1', 'AIigStatus_1', 'aiig_status_1')}
    output = _emitter(result.types, names).render(result.types)
    assert len(output) == 4
    for entry in output:
        path = tmp_path / entry.language / entry.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(entry.content)
    java = (tmp_path / 'java/test/output/AIigNode_1.java').read_text()
    python = (tmp_path / 'python/test/output/aiig_node_1.py').read_text()
    assert 'AIigNode_1 getNext()' in java
    assert 'java.util.List<? extends AIigNode_1> getChildrenList()' in java
    assert 'void setNext(' not in java
    assert 'def getNext(self) -> AIigNode_1' in python
    assert 'def setNext(' not in python
    assert '__xml_repeated_fields__' not in python  # JSONDEFS has no XML-specific runtime metadata
    assert 'required; cardinality 1..1' in java
    assert '"on-hold"' in (tmp_path / 'java/test/output/AIigStatus_1.java').read_text()
    assert "'on-hold'" in (tmp_path / 'python/test/output/aiig_status_1.py').read_text()
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                                *[str(p) for p in (tmp_path / 'java').rglob('*.java')]],
                               text=True, capture_output=True)
    assert compiled.returncode == 0, compiled.stderr
    for file in (tmp_path / 'python').rglob('*.py'):
        compile(file.read_text(), str(file), 'exec')


def test_emitter_does_not_guess_missing_catalog_names_or_unresolved_type():
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'test.json', _source_schema()),))
    with pytest.raises(ValueError, match='missing='):
        _emitter(result.types, {}).render(result.types)
    wrong = {item.identity: AIcdDefsCodegenEmissionName('AIigSame', 'AIigSame', 'aiig_same')
             for item in result.types}
    with pytest.raises(ValueError, match='collision'):
        _emitter(result.types, wrong).render(result.types)


def test_sealed_choice_records_compile_and_retain_typed_variants(tmp_path):
    schema = {'$id': 'urn:choices', 'type': 'object',
              'x-algites-defscodegen-choice': True,
              'properties': {'text': {'type': 'string'}, 'number': {'type': 'integer'}},
              'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'choices.json', schema),))
    types = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    names = {item.identity: AIcdDefsCodegenEmissionName(f'AIigT{i}', f'AIigT{i}', f'aiig_t{i}')
             for i, item in enumerate(types)}
    outputs = _emitter(result.types, names).render(result.types)
    assert len(outputs) == 6
    for entry in outputs:
        path = tmp_path / entry.language / entry.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(entry.content)
    java = (tmp_path / 'java/test/output/AIigT0.java').read_text()
    assert ('sealed interface AIigT0 extends eu.algites.lib.data.dataobject.AIiDataObject '
            'permits AIigT1, AIigT2') in java
    assert 'record AIigT1(String value) implements AIigT0' in (tmp_path / 'java/test/output/AIigT1.java').read_text()
    assert 'record AIigT2(Long value) implements AIigT0' in (tmp_path / 'java/test/output/AIigT2.java').read_text()
    result = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                             *map(str, (tmp_path / 'java').rglob('*.java'))],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for file in (tmp_path / 'python').rglob('*.py'):
        compile(file.read_text(), str(file), 'exec')


def test_structured_choice_records_compile_and_preserve_fields(tmp_path, monkeypatch):
    """Both targets emit nominal alternatives with exact, named getter contracts."""
    schema = {'$id': 'urn:choices', 'type': 'object',
        'x-algites-defscodegen-choice': True,
        'properties': {'person': {'type': 'object', 'properties': {
            'name': {'type': 'string', 'description': 'Display name'},
            'age': {'type': 'integer'}}, 'required': ['name']},
        'number': {'type': 'integer'}}, 'minProperties': 1,
        'maxProperties': 1, 'additionalProperties': False}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'choices.json', schema),))
    types = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    names = {item.identity: AIcdDefsCodegenEmissionName(f'AIigT{i}', f'AIigT{i}', f'aiig_t{i}')
             for i, item in enumerate(types)}
    outputs = AIcDefsCodegenCanonicalSourceEmitter(_profile(), names, 'choice.generated').render(result.types)
    assert len(outputs) == 6
    for entry in outputs:
        path = tmp_path / entry.language / entry.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(entry.content)
    java = (tmp_path / 'java/choice/generated/AIigT1.java').read_text()
    assert 'record AIigT1(String field1, Long field2) implements AIigT0' in java
    assert 'String getName() { return field1; }' in java
    assert 'Long getAge() { return field2; }' in java
    assert 'requireNonNull(field1' in java
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                               *map(str, (tmp_path / 'java').rglob('*.java'))],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    monkeypatch.syspath_prepend(str(tmp_path / 'python'))
    import importlib
    cls = importlib.import_module('choice.generated.aiig_t1').AIigT1
    base = importlib.import_module('choice.generated.aiig_t0').AIigT0
    instance = cls('Ada', None)
    assert isinstance(instance, base)
    assert instance.getName() == 'Ada' and instance.getAge() is None
    with pytest.raises(ValueError, match='name is required'):
        cls(None, 12)
    with pytest.raises(Exception):
        instance.field1 = 'changed'


def test_emitter_preserves_choice_variant_constraint_annotations_and_invalid_names(tmp_path):
    """Scalar and nested object CHOICE getters retain facets in Java and Python."""
    schema = {'$id': 'urn:choices', 'type': 'object',
        'x-algites-defscodegen-choice': True,
        'properties': {'record': {'type': 'object', 'properties': {
            'field': {'type': 'array', 'minItems': 2, 'maxItems': 5,
                      'items': {'type': 'string'}},
            'label': {'type': 'string', 'minLength': 3}}},
        'text': {'type': 'string', 'minLength': 2, 'maxLength': 10}},
        'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'choices.json', schema),))
    types = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    names = {item.identity: AIcdDefsCodegenEmissionName(f'AIigT{i}', f'AIigT{i}', f'aiig_t{i}')
             for i, item in enumerate(types)}
    emitted = _emitter(result.types, names).render(result.types)
    java = '\n'.join(entry.content for entry in emitted if entry.language == 'java')
    python = '\n'.join(entry.content for entry in emitted if entry.language == 'python')
    assert 'AIaDataObjectFieldListConstraints(minItems = 2, maxItems = 5)' in java
    assert 'AIaDataObjectFieldStringConstraints(minLength = 3)' in java
    assert 'AIaDataObjectFieldStringConstraints(minLength = 2, maxLength = 10)' in java
    assert 'AIaDataObjectFieldListConstraints(min_items=2, max_items=5)' in python
    assert 'AIaDataObjectFieldStringConstraints(min_length=3)' in python
    assert 'AIaDataObjectFieldStringConstraints(min_length=2, max_length=10)' in python
    for entry in emitted:
        out = tmp_path / entry.language / entry.relative_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(entry.content)
        if entry.language == 'python':
            compile(entry.content, str(out), 'exec')
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'),
                               '-d', str(tmp_path / 'classes'),
                               *map(str, (tmp_path / 'java').rglob('*.java'))],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    typed = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'test.json', _source_schema()),)).types
    wrong = {item.identity: AIcdDefsCodegenEmissionName('class', 'Foo', 'foo') for item in typed}
    with pytest.raises(ValueError, match='identifier'):
        _emitter(typed, wrong).render(typed)


def test_emitter_preserves_named_inheritance_and_dependency_references(tmp_path):
    schema = {'$id': 'urn:types', '$defs': {
        'Base': {'type': 'object', 'properties': {'id': {'type': 'integer'}}},
        'Child': {'type': 'object', 'allOf': [{'$ref': '#/$defs/Base'}],
                  'properties': {'label': {'type': 'string'}}}}}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'inherit.json', schema),))
    names = {node.identity: AIcdDefsCodegenEmissionName('AIig'+node.name, 'AIig'+node.name,
                'aiig_'+node.name.lower()) for node in result.types}
    entries = _emitter(result.types, names).render(result.types)
    sources = {(entry.language, entry.type_identity): entry.content for entry in entries}
    child = result.types[1].identity
    assert 'extends AIigBase' in sources['java', child]
    assert 'class AIigChild(AIigBase, AIiJsonDataObject)' in sources['python', child]
    assert 'getLabel' in sources['java', child]
    for entry in entries:
        if entry.language == 'java':
            path = tmp_path / entry.relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(entry.content)
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                                *[str(path) for path in tmp_path.rglob('*.java')]],
                               capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr


def test_real_common_getter_and_type_name_compositions_are_resolved():
    """The actual Algites source catalog supplies methods and versioned names."""
    from eu.algites.tool.codegen.common.naming_profiles import with_external_sourcecode_conventions
    source = TOOL.parent / ('pub.lib.General/naming/convention/profile/algites/src/product/config/'
                            'eu/algites/lib/naming/convention/sourcecode/algites-java-name-conventions.yml')
    profile = with_external_sourcecode_conventions(_profile(), yaml.safe_load(source.read_text()))
    assert profile.composed_name('algites-java-gen-intf-versioned_1', 'sample_name', version='7') == 'AIigSampleName_7'
    assert profile.composed_name('algites-java-gen-intf-versioned-file_1', 'sample_name', version='7') == 'AIigSampleName_7'
    invalid = {'NameCompositions': {'test-get': {'Segments': [
        {'NameFragmentsSegmentValue': {'Kind': 'constant_string', 'Value': 'wrong'}}]}}}
    with pytest.raises(ValueError, match='Conflicting'):
        with_external_sourcecode_conventions(_profile(), invalid)


def test_bounded_arrays_emit_constraints_but_decimal_enums_still_fail():
    """Supported list facets are emitted; exact decimal enums fail closed."""
    array = {'$id': 'urn:bound', 'title': 'Bounded', 'type': 'object',
             'properties': {'items': {'type': 'array', 'minItems': 2,
                                      'items': {'type': 'string'}}}}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS,
                                                                 'bound.json', array),))
    names = {item.identity: AIcdDefsCodegenEmissionName('AIigSample', 'AIigSample', 'aiig_sample')
             for item in result.types}
    outputs = _emitter(result.types, names).render(result.types)
    assert any('AIaDataObjectFieldListConstraints(minItems = 2)' in entry.content
               for entry in outputs if entry.language == 'java')
    assert any('AIaDataObjectFieldListConstraints(min_items=2)' in entry.content
               for entry in outputs if entry.language == 'python')
    decimal_enum = {'$id': 'urn:enum', 'title': 'Status', 'type': 'number',
                    'enum': [1.25, 2.75]}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS,
                                                                 'enum.json', decimal_enum),))
    names = {item.identity: AIcdDefsCodegenEmissionName('AIigSample', 'AIigSample', 'aiig_sample')
             for item in result.types}
    with pytest.raises(NotImplementedError, match='decimal enum'):
        _emitter(result.types, names).render(result.types)


@pytest.mark.parametrize(('schema', 'expected', 'target_type'), [
    ({'$id': 'urn:integer-enum', 'title': 'Codes', 'type': 'integer',
      'enum': [123456789012345678901234567890, -22]}, 123456789012345678901234567890, 'java.math.BigInteger'),
    ({'$id': 'urn:boolean-enum', 'title': 'Flags', 'type': 'boolean',
      'enum': [True, False]}, True, 'Boolean'),
])
def test_exact_numeric_enums_compile_and_keep_python_wire_types(tmp_path, schema, expected, target_type):
    """Integer wire values are unbounded, while boolean enums are boolean-valued."""
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS,
                                                                 'enum.json', schema),))
    names = {item.identity: AIcdDefsCodegenEmissionName('AIigCodes', 'AIigCodes', 'aiig_codes')
             for item in result.types}
    outputs = _emitter(result.types, names).render(result.types)
    java = next(item.content for item in outputs if item.language == 'java')
    py = next(item.content for item in outputs if item.language == 'python')
    assert f'public {target_type} code()' in java
    # Enum names now follow the selected naming conventions rather than
    # synthetic ordinal placeholders. The original numeric/bool wire codes
    # must nevertheless retain their exact Java and Python types.
    member = ('ValueTrue' if type(expected) is bool else
              'Value123456789012345678901234567890')
    assert member in java and member in py
    source = tmp_path / 'AIigCodes.java'
    source.write_text(java)
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'), str(source)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    import types
    module = types.ModuleType('generated_enums')
    exec(compile(py, 'aiig_codes.py', 'exec'), module.__dict__)
    value = getattr(module.AIigCodes, member).code()
    assert value == expected and type(value) is type(expected)


def test_repeated_xml_particle_emits_direct_typed_list_in_both_languages(tmp_path):
    """A repeated XSD particle has a direct LIST child, not an ELEMENT wrapper."""
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Order">
        <xs:sequence>
          <xs:element name="line" type="xs:string"
                      minOccurs="0" maxOccurs="unbounded"/>
        </xs:sequence>
      </xs:complexType>
    </xs:schema>'''
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'order.xsd', schema),))
    assert len(result.types) == 1
    names = {result.types[0].identity: AIcdDefsCodegenEmissionName(
        'AIigOrder', 'AIigOrder', 'aiig_order')}
    output = _emitter(result.types, names).render(result.types)
    java = next(entry.content for entry in output if entry.language == 'java')
    python = next(entry.content for entry in output if entry.language == 'python')
    assert 'java.util.List<? extends String> getLineList()' in java
    assert 'void setLine(' not in java
    assert 'cardinality 0..-1' in java
    assert 'def getLineList(self) -> list[str]' in python
    assert 'def setLine(' not in python
    for entry in output:
        file = tmp_path / entry.language / entry.relative_path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(entry.content)
    compile_result = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                                    *map(str, (tmp_path / 'java').rglob('*.java')),
                                    *(str(LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs' / name)
                                      for name in ('AIaXmlDataObjectField.java', 'AInXmlValueKind.java'))],
                                   capture_output=True, text=True)
    assert compile_result.returncode == 0, compile_result.stderr
    for file in (tmp_path / 'python').rglob('*.py'):
        compile(file.read_text(), str(file), 'exec')


def test_repeated_xml_particle_emits_list_cardinality_constraints():
    """Nontrivial XSD occurrence bounds survive in both generated contracts."""
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Order"><xs:sequence>
        <xs:element name="line" type="xs:string" minOccurs="1" maxOccurs="5"/>
      </xs:sequence></xs:complexType>
    </xs:schema>'''
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'order.xsd', schema),))
    names = {result.types[0].identity: AIcdDefsCodegenEmissionName(
        'AIigOrder', 'AIigOrder', 'aiig_order')}
    output = _emitter(result.types, names).render(result.types)
    java = next(entry.content for entry in output if entry.language == 'java')
    python = next(entry.content for entry in output if entry.language == 'python')
    assert 'AIaDataObjectFieldListConstraints(minItems = 1, maxItems = 5)' in java
    assert 'AIaDataObjectFieldListConstraints(min_items=1, max_items=5)' in python
    assert 'minItemCount = 1, maxItemCount = 5' in java
    assert 'min_item_count=1, max_item_count=5' in python


def test_json_array_item_bounds_use_schema_neutral_field_annotation():
    """JSON minItems/maxItems have the same field metadata as XSD occurs bounds."""
    schema = {'$id': 'urn:json-bounds', 'title': 'Bounded', 'type': 'object',
              'properties': {'items': {'type': 'array', 'minItems': 2,
                                       'maxItems': 4, 'items': {'type': 'string'}}}}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(
        Kind.JSONDEFS, 'bounds.json', schema),))
    names = {result.types[0].identity: AIcdDefsCodegenEmissionName(
        'AIigBounded', 'AIigBounded', 'aiig_bounded')}
    output = _emitter(result.types, names).render(result.types)
    java = next(item.content for item in output if item.language == 'java')
    python = next(item.content for item in output if item.language == 'python')
    assert 'minItemCount = 2, maxItemCount = 4' in java
    assert 'min_item_count=2, max_item_count=4' in python
    # The array's item limits do not make the object property mandatory.
    assert 'presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED' in java
    assert 'presence=AInFieldPresenceKind.ALLOWED' in python
    assert 'AIaDataObjectFieldListConstraints(minItems = 2, maxItems = 4)' in java
    assert 'AIaDataObjectFieldListConstraints(min_items=2, max_items=4)' in python


def test_string_enum_control_characters_emit_compilable_java_and_python(tmp_path):
    """Java escapes nonprinting codes as octal, never as early Unicode escapes."""
    schema = {'$id': 'urn:escaped-enum', 'title': 'Escaped', 'type': 'string',
              'enum': ['a\x01b', 'literal\\u000a', 'line\nbreak']}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(
        Kind.JSONDEFS, 'escaped.json', schema),))
    names = {result.types[0].identity: AIcdDefsCodegenEmissionName(
        'AIigEscaped', 'AIigEscaped', 'aiig_escaped')}
    output = _emitter(result.types, names).render(result.types)
    java = next(entry.content for entry in output if entry.language == 'java')
    assert r'"a\001b"' in java
    assert r'\u0001' not in java
    assert '[U+0001]' in java  # printable source documentation
    assert 'literal' in java
    for entry in output:
        path = tmp_path / entry.language / entry.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(entry.content)
    runtime = tmp_path / 'EnumProbe.java'
    runtime.write_text('''import test.output.AIigEscaped;
        public class EnumProbe {
          public static void main(String[] args) {
            if (!AIigEscaped.A_B.code().equals("a" + (char) 1 + "b"))
              throw new AssertionError("Control character modified");
            if (!AIigEscaped.LITERAL_U000A.code().equals("literal" + (char) 92 + "u000a"))
              throw new AssertionError("Literal backslash-u modified");
          }
        }
    ''')
    build = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                            *map(str, (tmp_path / 'java').rglob('*.java')), str(runtime)],
                           capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    check = subprocess.run(['java', '-cp', str(tmp_path / 'classes'), 'EnumProbe'],
                           capture_output=True, text=True)
    assert check.returncode == 0, check.stderr
    for path in (tmp_path / 'python').rglob('*.py'):
        compile(path.read_text(), str(path), 'exec')


def test_const_property_emits_named_singleton_enum_in_both_languages(tmp_path):
    """A fixed business field is emitted, not silently widened to unrestricted text."""
    schema = {'$id': 'urn:constant-holder', 'title': 'ConstantHolder', 'type': 'object',
              'properties': {'fixed': {'type': 'string', 'const': 'urn:fixed-schema'}}}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'fixed.json', schema),))
    declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    names = {item.identity: AIcdDefsCodegenEmissionName(
        f'FixedType{index}', f'FixedType{index}', f'fixed_type_{index}')
        for index, item in enumerate(declarations)}
    outputs = _emitter(result.types, names).render(result.types)
    assert len(outputs) == 4
    for entry in outputs:
        path = tmp_path / entry.language / entry.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(entry.content)
    java_sources = '\n'.join(item.content for item in outputs if item.language == 'java')
    py_sources = '\n'.join(item.content for item in outputs if item.language == 'python')
    assert '"urn:fixed-schema"' in java_sources
    assert "'urn:fixed-schema'" in py_sources
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'),
                               '-d', str(tmp_path / 'classes'),
                               *map(str, (tmp_path / 'java').rglob('*.java'))],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    for file in (tmp_path / 'python').rglob('*.py'):
        compile(file.read_text(), str(file), 'exec')


def test_open_json_object_ignores_untyped_wildcards_with_diagnostics(tmp_path):
    """Open values without a schema must not leak Object/Any getter types.

    Missing arbitrary JSON values may be lost on a DataObject roundtrip; an
    explicit warning with a concrete typed-schema hint is required.
    """
    schema = {'$id': 'urn:open-map', '$defs': {
        'Document': {'type': 'object', 'properties': {
            'extra': {'type': 'object', 'additionalProperties': True}},
            'additionalProperties': False}}}
    with pytest.warns(UserWarning, match=r'open-map.json.*additionalProperties.*Hint:'):
        result = _pipeline().process((AIcdDefsCodegenSourceDocument(
            Kind.JSONDEFS, 'open-map.json', schema),))
    declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    names = {item.identity: AIcdDefsCodegenEmissionName(
        f'AIigOpen{index}', f'AIigOpen{index}', f'aiig_open_{index}')
        for index, item in enumerate(declarations)}
    outputs = _emitter(result.types, names).render(result.types)
    java = '\n'.join(output.content for output in outputs if output.language == 'java')
    python = '\n'.join(output.content for output in outputs if output.language == 'python')
    assert 'java.util.Map<String, Object>' not in java
    assert 'dict[str, Any]' not in python
    assert 'getAdditionalProperties' not in java
    assert 'getAdditionalProperties' not in python
    for entry in outputs:
        path = tmp_path / entry.language / entry.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(entry.content)
    compiler = subprocess.run([
        'javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'),
        '-d', str(tmp_path / 'classes'),
        *map(str, (tmp_path / 'java').rglob('*.java'))],
        text=True, capture_output=True)
    assert compiler.returncode == 0, compiler.stderr
    for source in (tmp_path / 'python').rglob('*.py'):
        compile(source.read_text(), str(source), 'exec')


def test_xsd_named_choice_branches_emit_typed_java_python_records(tmp_path):
    """The structural XSD choice generates named variants without losing XML QNames."""
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                 xmlns:tns="urn:structural-choice" targetNamespace="urn:structural-choice">
      <xs:complexType name="Select"><xs:choice>
        <xs:element name="first" type="xs:string"/>
        <xs:element name="second" type="xs:integer"/>
      </xs:choice></xs:complexType>
    </xs:schema>'''
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(
        Kind.XMLDEFS, 'selection.xsd', schema),))
    types = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    assert len(types) == 3
    names = {node.identity: AIcdDefsCodegenEmissionName(
        f'AIigChoice{i}', f'AIigChoice{i}', f'aiig_choice{i}')
        for i, node in enumerate(types)}
    produced = _emitter(result.types, names).render(result.types)
    java = '\n'.join(item.content for item in produced if item.language == 'java')
    assert ('sealed interface AIigChoice0 extends eu.algites.lib.data.dataobject.AIiDataObject '
            'permits AIigChoice1, AIigChoice2') in java
    assert 'getFirst()' in java and 'getSecond()' in java
    assert 'namespaceLocalName = "first"' in java and 'namespaceLocalName = "second"' in java
    assert any('__xml_data_object_fields__' in item.content for item in produced if item.language == 'python')
    for item in produced:
        destination = tmp_path / item.language / item.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(item.content)
        if item.language == 'python':
            compile(item.content, str(destination), 'exec')
    compile_result = subprocess.run([
        'javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'),
        '-d', str(tmp_path / 'classes'),
        *map(str, (tmp_path / 'java').rglob('*.java')),
    ], capture_output=True, text=True)
    assert compile_result.returncode == 0, compile_result.stderr


def test_xsd_anonymous_enum_is_nominal_type_in_both_targets(tmp_path):
    """Anonymous XSD enumeration fields need a synthetic enum, not an inline ENUM."""
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Wire"><xs:sequence>
        <xs:element name="state"><xs:simpleType><xs:restriction base="xs:string">
          <xs:enumeration value="active"/><xs:enumeration value="pending"/>
        </xs:restriction></xs:simpleType></xs:element>
      </xs:sequence></xs:complexType>
    </xs:schema>'''
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(
        Kind.XMLDEFS, 'wire.xsd', schema),))
    types = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    assert len(types) == 2
    enum_type = next(node for node in types if node.structure.kind.value == 'ENUM')
    assert enum_type.name == 'WireState'
    assert result.types[0].structure.children[0].structure.identity == enum_type.identity
    names = {node.identity: AIcdDefsCodegenEmissionName(
        f'AIigAnon{i}', f'AIigAnon{i}', f'aiig_anon{i}') for i, node in enumerate(types)}
    outputs = _emitter(result.types, names).render(result.types)
    assert any('enum AIigAnon' in item.content and '"pending"' in item.content
               for item in outputs if item.language == 'java')
    assert any('getState()' in item.content for item in outputs if item.language == 'java')
    for item in outputs:
        dest = tmp_path / item.language / item.relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(item.content)
        if item.language == 'python':
            compile(item.content, str(dest), 'exec')
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'),
        '-d', str(tmp_path / 'classes'), *map(str, (tmp_path / 'java').rglob('*.java'))],
        capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr


def test_xsd_inline_enum_attribute_and_named_enum_reuse():
    """Inline enum is owner+field; named enum preserves nominal QName."""
    xml = """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="urn:t" targetNamespace="urn:t">
      <xs:simpleType name="Status"><xs:restriction base="xs:string"><xs:enumeration value="ready"/></xs:restriction></xs:simpleType>
      <xs:complexType name="Item"><xs:sequence><xs:element name="State" type="tns:Status"/></xs:sequence>
      <xs:attribute name="Phase"><xs:simpleType><xs:restriction base="xs:string"><xs:enumeration value="new"/></xs:restriction></xs:simpleType></xs:attribute>
      </xs:complexType></xs:schema>"""
    result=_pipeline().process((AIcdDefsCodegenSourceDocument(Kind.XMLDEFS,'enums.xsd',xml),))
    nodes=AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    assert {n.name for n in nodes} == {'Status','Item','ItemPhase'}
    item=next(n for n in nodes if n.name=='Item')
    assert item.structure.children[0].structure.target_identity==next(n for n in nodes if n.name=='Status').identity
    assert item.structure.children[1].structure.name=='ItemPhase'


@pytest.mark.parametrize('kind', (Kind.JSONDEFS, Kind.YAMLDEFS))
def test_json_yaml_inline_property_enum_emits_nominal_java_python_types(tmp_path, kind):
    """Inline JSON/YAML enum uses the same named nominal TYPE as inline XSD."""
    schema = {'$id': 'urn:person', 'title': 'Person', 'type': 'object',
              'properties': {'Status': {'type': 'string', 'enum': ['active', 'inactive']}}}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(kind, 'person.json', schema),))
    declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    assert len(declarations) == 2
    enum_type = next(node for node in declarations if node.structure.kind.value == 'ENUM')
    assert enum_type.name == 'PersonStatus'
    assert enum_type.origin.value == 'SYNTHETIC'
    assert result.types[0].structure.children[0].structure.identity == enum_type.identity
    names = {node.identity: AIcdDefsCodegenEmissionName(
        f'AIigPerson{i}', f'AIigPerson{i}', f'aiig_person{i}')
        for i, node in enumerate(declarations)}
    outputs = _emitter(result.types, names).render(result.types)
    assert len(outputs) == 4
    assert any('enum AIigPerson' in entry.content and '"inactive"' in entry.content
               for entry in outputs if entry.language == 'java')
    assert any('getStatus()' in entry.content and 'AIigPerson' in entry.content
               for entry in outputs if entry.language == 'java')
    for entry in outputs:
        dest = tmp_path / entry.language / entry.relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(entry.content)
        if entry.language == 'python':
            compile(entry.content, str(dest), 'exec')
    compiled = subprocess.run(['javac',
        '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'),
        '-d', str(tmp_path / 'classes'),
        *map(str, (tmp_path / 'java').rglob('*.java'))],
        capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr


def test_xml_choice_variant_prefixes_are_emitted_for_nested_sequences():
    """Both languages dispatch nested CHOICE by real wire QNames, not type names."""
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:choice" xmlns:tns="urn:choice"
        elementFormDefault="qualified">
      <xs:complexType name="Decision"><xs:sequence>
        <xs:element name="Kind" type="xs:string"/>
        <xs:choice>
          <xs:element name="Value" type="xs:string"/>
          <xs:sequence>
            <xs:element name="Name" type="xs:string"/>
            <xs:element name="Regexp" type="xs:string"/>
          </xs:sequence>
        </xs:choice>
      </xs:sequence></xs:complexType>
    </xs:schema>'''
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(
        Kind.XMLDEFS, 'decision.xsd', schema),))
    declared = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    names = {node.identity: AIcdDefsCodegenEmissionName(
        f'AIigDecision{i}', f'AIigDecision{i}', f'aiig_decision{i}')
        for i, node in enumerate(declared)}
    outputs = _emitter(result.types, names).render(result.types)
    java = '\n'.join(item.content for item in outputs if item.language == 'java')
    python = '\n'.join(item.content for item in outputs if item.language == 'python')
    assert 'xmlFirstQNames()' in java
    assert '__xml_choice_first_qnames__' in python
    for qname in ('{urn:choice}Value', '{urn:choice}Name'):
        assert qname in java
        assert qname in python
    assert '{urn:choice}Regexp' not in ''.join(
        line for line in python.splitlines() if '__xml_choice_first_qnames__' in line)


def test_named_indexed_map_is_field_collection_not_data_object_supertype():
    """A $defs map is referenced by its getter, not emitted as a list interface."""
    source = {'$id': 'https://example.org/test_1.json', 'type': 'object',
              'properties': {'Entries': {'$ref': '#/$defs/Entries'}},
              '$defs': {'Entries': {'type': 'object',
                       'additionalProperties': {'type': 'string'},
                       'x-algites-defscodegen-key': {'id': 'ByName', 'field-name': 'name'}}}}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'test.json', source),))
    declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    names = {item.identity: AIcdDefsCodegenEmissionName(
        'AIigT' + str(i), 'AIigT' + str(i), 'aiig_t' + str(i))
        for i, item in enumerate(declarations)}
    outputs = _emitter(result.types, names).render(result.types)
    alias = next(item for item in declarations if item.name == 'Entries')
    assert all(out.type_identity != alias.identity for out in outputs)
    java = next(out.content for out in outputs if out.language == 'java'
                and out.type_identity == result.types[0].identity)
    python = next(out.content for out in outputs if out.language == 'python'
                  and out.type_identity == result.types[0].identity)
    assert 'AIiMultiMappedList<? extends AIigT' in java and 'getEntries()' in java
    assert 'AIiMultiMappedList[AIigT' in python and 'def getEntries(' in python
    assert 'from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList' in python
    assert not any('extends eu.algites.lib.common.list.AIiMultiMappedList' in out.content
                   for out in outputs if out.language == 'java')
