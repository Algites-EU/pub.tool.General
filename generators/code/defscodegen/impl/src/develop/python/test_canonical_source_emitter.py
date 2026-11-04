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
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIigSourceInputKind_1 as Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcDefsCodegenCanonicalPipeline, AIcdDefsCodegenSourceDocument)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter, AIcdDefsCodegenEmissionName)


def _profile():
    """Build a controlled profile with simulated resolved external getter compositions."""
    base = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/tool/codegen'
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
    assert 'java.util.List<AIigNode_1> getChildren()' in java
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
    schema = {'$id': 'urn:choices', 'oneOf': [{'type': 'string'}, {'type': 'integer'}]}
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
    assert 'sealed interface AIigT0 permits AIigT1, AIigT2' in java
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
    schema = {'$id': 'urn:choices', 'oneOf': [
        {'type': 'object', 'properties': {
            'name': {'type': 'string', 'description': 'Display name'},
            'age': {'type': 'integer'}}, 'required': ['name']},
        {'type': 'integer'}]}
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


def test_emitter_rejects_unrepresentable_choice_and_invalid_names():
    """Unsupported nested constraints still fail before returning any output."""
    schema = {'$id': 'urn:choices', 'oneOf': [
        {'type': 'object', 'properties': {'field': {
            'type': 'array', 'minItems': 2, 'items': {'type': 'string'}}}},
        {'type': 'integer'}]}
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'choices.json', schema),))
    types = AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)
    names = {item.identity: AIcdDefsCodegenEmissionName(f'AIigT{i}', f'AIigT{i}', f'aiig_t{i}')
             for i, item in enumerate(types)}
    with pytest.raises(NotImplementedError, match='Bounded LIST'):
        _emitter(result.types, names).render(result.types)
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
    assert 'class AIigChild(AIigBase)' in sources['python', child]
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


def test_lossless_emitter_rejects_bounded_arrays_and_imprecise_decimal_enums():
    """Unsupported numeric precision and occurrence restrictions never vanish."""
    cases = ({'$id': 'urn:bound', 'title': 'Bounded', 'type': 'object',
              'properties': {'items': {'type': 'array', 'minItems': 2,
                                       'items': {'type': 'string'}}}},
             {'$id': 'urn:enum', 'title': 'Status', 'type': 'number', 'enum': [1.25, 2.75]})
    for schema in cases:
        result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS,
                                                                    'test.json', schema),))
        names = {item.identity: AIcdDefsCodegenEmissionName('AIigSample', 'AIigSample', 'aiig_sample')
                 for item in result.types}
        with pytest.raises(NotImplementedError, match='Bounded LIST|decimal enum'):
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
    assert 'VALUE_1' in java and 'VALUE_1' in py
    source = tmp_path / 'AIigCodes.java'
    source.write_text(java)
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'), str(source)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    import types
    module = types.ModuleType('generated_enums')
    exec(compile(py, 'aiig_codes.py', 'exec'), module.__dict__)
    value = module.AIigCodes.VALUE_1.code()
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
    assert 'java.util.List<String> getLine()' in java
    assert 'void setLine(' not in java
    assert 'cardinality 0..-1' in java
    assert 'def getLine(self) -> list[str]' in python
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


def test_repeated_xml_particle_with_unenforced_bounds_fails_closed():
    """Emission must not drop nontrivial list cardinality constraints."""
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Order"><xs:sequence>
        <xs:element name="line" type="xs:string" minOccurs="1" maxOccurs="5"/>
      </xs:sequence></xs:complexType>
    </xs:schema>'''
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'order.xsd', schema),))
    names = {result.types[0].identity: AIcdDefsCodegenEmissionName(
        'AIigOrder', 'AIigOrder', 'aiig_order')}
    with pytest.raises(NotImplementedError, match='Bounded LIST'):
        _emitter(result.types, names).render(result.types)


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
            if (!AIigEscaped.VALUE_1.code().equals("a" + (char) 1 + "b"))
              throw new AssertionError("Control character modified");
            if (!AIigEscaped.VALUE_2.code().equals("literal" + (char) 92 + "u000a"))
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
