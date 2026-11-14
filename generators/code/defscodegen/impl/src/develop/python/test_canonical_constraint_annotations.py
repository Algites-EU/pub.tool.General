"""End-to-end tests for canonical scalar, collection and object field facets.

These intentionally inspect the emitted Java and Python *source*, not just the
frontend's in-memory model, to prevent a silently discarded restriction.
"""
from pathlib import Path
import subprocess

from test_canonical_source_emitter import _pipeline, _emitter, LIB
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIngSourceInputKind_1 as Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import AIcdDefsCodegenSourceDocument
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import AIcdDefsCodegenEmissionName, AIcDefsCodegenCanonicalSourceEmitter


def _render(source, kind, suffix, tmp_path):
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(kind, 'schema.' + suffix, source),))
    names = {item.identity: AIcdDefsCodegenEmissionName('AIig' + item.name, 'AIig' + item.name, 'aiig_' + item.name.lower())
             for item in AIcDefsCodegenCanonicalSourceEmitter.declarations(result.types)}
    files = _emitter(result.types, names).render(result.types)
    sources = {}
    for file in files:
        output = tmp_path / file.language / file.relative_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(file.content)
        sources[(file.language, output.stem)] = file.content
        if file.language == 'python':
            compile(file.content, str(output), 'exec')
    java = list((tmp_path / 'java').rglob('*.java'))
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'),
                               '-d', str(tmp_path / 'classes'), *map(str, java)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    return sources



def _assert_pipeline_diagnostic(document, diagnostic, *, original_error=ValueError):
    """Assert the public source-located error and its original frontend cause.

    The canonical pipeline intentionally wraps unsupported frontend structures
    in ValueError, retaining the original exception with Python chaining.  Test
    callers must check the public diagnostic contract, not bypass that wrapper.
    """
    from pytest import raises
    with raises(ValueError, match=diagnostic) as caught:
        _pipeline().process((document,))
    assert str(caught.value).startswith(document.resource + ': ')
    assert isinstance(caught.value.__cause__, original_error), caught.value


def _assert_constraints(java, python):
    for token in ('@eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 2, maxLength = 12, pattern = "[A-Z]+", format = "uuid")',
                  '@eu.algites.lib.data.dataobject.AIaDataObjectFieldNumericConstraints(minimum = "1.5", maximum = "10", exclusiveMaximum = true, format = "decimal")',
                  '@eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints(minItems = 2, maxItems = 4, uniqueItems = true)',
                  '@eu.algites.lib.data.dataobject.AIaDataObjectFieldObjectConstraints(minProperties = 1, maxProperties = 3)'):
        assert token in java, token
    for token in ('@AIaDataObjectFieldStringConstraints(min_length=2, max_length=12, pattern=\'[A-Z]+\', format=\'uuid\')',
                  "@AIaDataObjectFieldNumericConstraints(minimum='1.5', maximum='10', exclusive_maximum=True, format='decimal')",
                  '@AIaDataObjectFieldListConstraints(min_items=2, max_items=4, unique_items=True)',
                  '@AIaDataObjectFieldObjectConstraints(min_properties=1, max_properties=3)'):
        assert token in python, token


def _json_schema():
    return {'$id': 'urn:facets', 'type': 'object', 'properties': {
        'artifact': {'type': 'string', 'minLength': 2, 'maxLength': 12, 'pattern': '[A-Z]+', 'format': 'uuid'},
        'amount': {'type': 'number', 'minimum': 1.5, 'exclusiveMaximum': 10, 'format': 'decimal'},
        'items': {'type': 'array', 'minItems': 2, 'maxItems': 4, 'uniqueItems': True,
                  'items': {'type': 'string'}},
        'info': {'type': 'object', 'minProperties': 1, 'maxProperties': 3,
                 'properties': {'x': {'type': 'string'}}}}}


def test_json_schema_constraints_are_emitted_and_java_compiles(tmp_path):
    files = _render(_json_schema(), Kind.JSONDEFS, 'json', tmp_path)
    _assert_constraints(next(content for (language, _), content in files.items() if language == 'java' and 'getArtifact' in content), next(content for (language, _), content in files.items() if language == 'python' and 'getArtifact' in content))


def test_yamldefs_constraints_are_emitted_and_java_compiles(tmp_path):
    files = _render(_json_schema(), Kind.YAMLDEFS, 'yaml', tmp_path)
    _assert_constraints(next(content for (language, _), content in files.items() if language == 'java' and 'getArtifact' in content), next(content for (language, _), content in files.items() if language == 'python' and 'getArtifact' in content))


def test_xsd_referenced_simple_type_facets_are_emitted(tmp_path):
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:t="urn:facets" targetNamespace="urn:facets">
    <xs:complexType name="Document"><xs:sequence>
      <xs:element name="artifact"><xs:simpleType><xs:restriction base="xs:string">
        <xs:minLength value="2"/><xs:maxLength value="12"/><xs:pattern value="[A-Z]+"/>
      </xs:restriction></xs:simpleType></xs:element>
      <xs:element name="quantity"><xs:simpleType><xs:restriction base="xs:decimal">
        <xs:minInclusive value="1.5"/><xs:maxExclusive value="10"/>
      </xs:restriction></xs:simpleType></xs:element>
      <xs:element name="items" type="xs:string" minOccurs="2" maxOccurs="4"/>
    </xs:sequence></xs:complexType></xs:schema>'''
    files = _render(schema, Kind.XMLDEFS, 'xsd', tmp_path)
    java = files['java', 'AIigDocument']
    python = files['python', 'aiig_document']
    assert '@eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 2, maxLength = 12, pattern = "[A-Z]+")' in java
    assert '@AIaDataObjectFieldStringConstraints(min_length=2, max_length=12, pattern=\'[A-Z]+\')' in python
    assert '@eu.algites.lib.data.dataobject.AIaDataObjectFieldNumericConstraints(minimum = "1.5", maximum = "10", exclusiveMaximum = true)' in java
    assert '@AIaDataObjectFieldNumericConstraints(minimum=\'1.5\', maximum=\'10\', exclusive_maximum=True)' in python
    assert '@eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints(minItems = 2, maxItems = 4)' in java
    assert '@AIaDataObjectFieldListConstraints(min_items=2, max_items=4)' in python


def test_xsd_sequence_and_attribute_facets_are_direct_getters(tmp_path):
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:complexType name="Entry"><xs:sequence>
      <xs:element name="name" nillable="false"><xs:simpleType><xs:restriction base="xs:string">
        <xs:minLength value="1"/><xs:maxLength value="64"/>
      </xs:restriction></xs:simpleType></xs:element>
    </xs:sequence>
    <xs:attribute name="code" use="required"><xs:simpleType><xs:restriction base="xs:string">
      <xs:minLength value="3"/><xs:pattern value="[A-Z]+"/>
    </xs:restriction></xs:simpleType></xs:attribute></xs:complexType></xs:schema>'''
    files = _render(schema, Kind.XMLDEFS, 'xsd', tmp_path)
    java = files['java', 'AIigEntry']
    python = files['python', 'aiig_entry']
    assert 'String getName()' in java and 'String getCode()' in java
    assert '@eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1, maxLength = 64)' in java
    assert '@eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 3, pattern = "[A-Z]+")' in java
    assert '@AIaDataObjectFieldStringConstraints(min_length=1, max_length=64)' in python
    assert '@AIaDataObjectFieldStringConstraints(min_length=3, pattern=\'[A-Z]+\')' in python
    assert 'valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ATTRIBUTE' in java


def test_conjunctive_numeric_bounds_keep_stricter_exclusive_limit(tmp_path):
    source = {'type': 'object', 'properties': {'price': {
        'type': 'number', 'minimum': 1.5, 'exclusiveMinimum': 2.5,
        'maximum': 100, 'exclusiveMaximum': 10}}}
    files = _render(source, Kind.JSONDEFS, 'json', tmp_path)
    java = next(content for (language, _), content in files.items()
                if language == 'java' and 'getPrice' in content)
    python = next(content for (language, _), content in files.items()
                  if language == 'python' and 'getPrice' in content)
    assert 'AIaDataObjectFieldNumericConstraints(minimum = "2.5", maximum = "10", exclusiveMinimum = true, exclusiveMaximum = true)' in java
    assert "AIaDataObjectFieldNumericConstraints(minimum='2.5', maximum='10', exclusive_minimum=True, exclusive_maximum=True)" in python


def test_invalid_facets_fail_instead_of_being_silently_dropped():
    from pytest import raises
    from test_canonical_source_emitter import _pipeline
    for field, error in (({'type': 'array', 'items': {'type': 'string'}, 'maxItems': -1}, 'maxItems'),
                         ({'type': 'string', 'minLength': 4, 'maxLength': 3}, 'minLength'),
                         ({'type': 'number', 'minimum': 1, 'exclusiveMaximum': 1}, 'numeric bounds'),
                         ({'type': 'number', 'minimum': '1'}, 'must be numeric')):
        schema = {'type': 'object', 'properties': {'value': field}}
        with raises(ValueError, match=error):
            _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'invalid.json', schema),))


def test_sibling_facets_never_disappear_before_canonical_linking():
    """Unsupported intersections must be diagnosed instead of silently erased."""
    from pytest import raises
    probes = (
        ({'$ref': '#/$defs/Name', 'minLength': 2}, 'Ref sibling constraints'),
        ({'$ref': '#/$defs/Name', 'format': 'uri'}, 'Ref sibling constraints'),
        ({'type': 'string', 'const': 'a', 'minLength': 2}, 'Enum/const literal violates length constraint'),
        ({'type': 'object', 'properties': {'x': {'type': 'string'}},
          'minLength': 2}, 'Conditional string constraints'),
        ({'type': 'array', 'items': {'type': 'string'},
          'minimum': 3}, 'Conditional number constraints'),
        ({'minLength': 2}, 'Conditional string constraints'),
    )
    for field, message in probes:
        schema = {'type': 'object', 'properties': {'value': field}}
        # A contradictory literal is invalid schema content, not an unsupported
        # feature; other still-unrepresentable intersections fail explicitly.
        expected = ValueError if 'Enum/const literal' in message else NotImplementedError
        for source_kind, source_file in ((Kind.JSONDEFS, 'schema.json'),
                                         (Kind.YAMLDEFS, 'schema.yaml')):
            _assert_pipeline_diagnostic(
                AIcdDefsCodegenSourceDocument(source_kind, source_file, schema),
                message, original_error=expected)


def test_valid_enum_const_intersections_are_projected_losslessly(tmp_path):
    """A restricted finite set is equivalent to the finite set alone."""
    source = {'type': 'object', 'properties': {
        'shortCode': {'type': 'string', 'const': 'ABC', 'minLength': 2,
                      'maxLength': 5, 'pattern': '[A-Z]+'},
        'level': {'type': 'integer', 'enum': [2, 4, 6],
                  'minimum': 2, 'maximum': 6, 'multipleOf': 2}}}
    for source_kind, suffix in ((Kind.JSONDEFS, 'json'), (Kind.YAMLDEFS, 'yaml')):
        files = _render(source, source_kind, suffix, tmp_path / suffix)
        emitted = '\n'.join(files.values())
        assert 'ABC' in emitted and ('getShortCode' in emitted or 'get_short_code' in emitted)
        assert 'getLevel' in emitted or 'get_level' in emitted


def test_xsd_named_simple_type_references_preserve_string_and_numeric_facets(tmp_path):
    """A local named simpleType must not hide its restrictions from the field."""
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
          xmlns:t="urn:facet-links" targetNamespace="urn:facet-links">
       <xs:simpleType name="Code"><xs:restriction base="xs:string">
          <xs:minLength value="2"/><xs:maxLength value="8"/><xs:pattern value="[A-Z]+"/>
       </xs:restriction></xs:simpleType>
       <xs:simpleType name="Quantity"><xs:restriction base="xs:decimal">
          <xs:minExclusive value="1.5"/><xs:maxInclusive value="100"/>
       </xs:restriction></xs:simpleType>
       <xs:complexType name="Document"><xs:sequence>
          <xs:element name="artifact" type="t:Code"/>
          <xs:element name="quantity" type="t:Quantity"/>
       </xs:sequence><xs:attribute name="code" type="t:Code"/></xs:complexType>
    </xs:schema>'''
    files = _render(schema, Kind.XMLDEFS, 'xsd', tmp_path)
    java = files['java', 'AIigDocument']
    python = files['python', 'aiig_document']
    assert java.count('AIaDataObjectFieldStringConstraints(minLength = 2, maxLength = 8, pattern = "[A-Z]+")') == 2
    assert 'AIaDataObjectFieldNumericConstraints(minimum = "1.5", maximum = "100", exclusiveMinimum = true)' in java
    assert python.count("AIaDataObjectFieldStringConstraints(min_length=2, max_length=8, pattern='[A-Z]+')") == 2
    assert "AIaDataObjectFieldNumericConstraints(minimum='1.5', maximum='100', exclusive_minimum=True)" in python


def test_xsd_named_enum_remains_nominal_while_scalar_facets_are_inlined(tmp_path):
    """Named enums remain generated types; scalar aliases supply annotations."""
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:t="urn:records" targetNamespace="urn:records">
      <xs:simpleType name="Code"><xs:restriction base="xs:string">
        <xs:minLength value="2"/></xs:restriction></xs:simpleType>
      <xs:simpleType name="Status"><xs:restriction base="xs:string">
        <xs:enumeration value="OPEN"/><xs:enumeration value="CLOSED"/>
      </xs:restriction></xs:simpleType>
      <xs:complexType name="Record"><xs:sequence>
        <xs:element name="code" type="t:Code"/>
        <xs:element name="status" type="t:Status"/>
      </xs:sequence></xs:complexType></xs:schema>'''
    files = _render(xsd, Kind.XMLDEFS, 'xsd', tmp_path)
    java = files['java', 'AIigRecord']
    assert 'AIaDataObjectFieldStringConstraints(minLength = 2)' in java
    assert 'AIigStatus getStatus()' in java
    assert ('java', 'AIigStatus') in files


def test_xsd_multilevel_named_scalar_restrictions_merge_and_emit(tmp_path):
    """An intermediate alias must not erase inherited facet values."""
    schema = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:m="urn:chain" targetNamespace="urn:chain">
      <xs:simpleType name="BaseCode"><xs:restriction base="xs:string">
        <xs:minLength value="2"/><xs:maxLength value="20"/><xs:pattern value="[A-Z]+"/>
      </xs:restriction></xs:simpleType>
      <xs:simpleType name="MidCode"><xs:restriction base="m:BaseCode">
        <xs:minLength value="3"/>
      </xs:restriction></xs:simpleType>
      <xs:simpleType name="FinalCode"><xs:restriction base="m:MidCode">
        <xs:maxLength value="8"/>
      </xs:restriction></xs:simpleType>
      <xs:simpleType name="BaseAmount"><xs:restriction base="xs:decimal">
        <xs:minInclusive value="1.5"/><xs:maxInclusive value="100"/>
      </xs:restriction></xs:simpleType>
      <xs:simpleType name="FinalAmount"><xs:restriction base="m:BaseAmount">
        <xs:minExclusive value="2"/><xs:maxInclusive value="10"/>
      </xs:restriction></xs:simpleType>
      <xs:complexType name="Invoice"><xs:sequence>
        <xs:element name="code" type="m:FinalCode"/>
        <xs:element name="amount" type="m:FinalAmount"/>
      </xs:sequence><xs:attribute name="alias" type="m:MidCode"/></xs:complexType>
    </xs:schema>'''
    files = _render(schema, Kind.XMLDEFS, 'xsd', tmp_path)
    java = files['java', 'AIigInvoice']
    python = files['python', 'aiig_invoice']
    assert 'AIaDataObjectFieldStringConstraints(minLength = 3, maxLength = 8, pattern = "[A-Z]+")' in java
    assert 'AIaDataObjectFieldStringConstraints(minLength = 3, maxLength = 20, pattern = "[A-Z]+")' in java
    assert 'AIaDataObjectFieldNumericConstraints(minimum = "2", maximum = "10", exclusiveMinimum = true)' in java
    assert "AIaDataObjectFieldStringConstraints(min_length=3, max_length=8, pattern='[A-Z]+')" in python
    assert "AIaDataObjectFieldStringConstraints(min_length=3, max_length=20, pattern='[A-Z]+')" in python
    assert "AIaDataObjectFieldNumericConstraints(minimum='2', maximum='10', exclusive_minimum=True)" in python


def test_xsd_named_scalar_restrictions_reject_cycle_and_unrepresentable_patterns():
    """Cycle diagnostics and impossible intersections cannot disappear."""
    from pytest import raises
    cases = (
      ('''<xs:simpleType name="A"><xs:restriction base="t:B"/></xs:simpleType>
          <xs:simpleType name="B"><xs:restriction base="t:A"/></xs:simpleType>''',
       ValueError, 'Cyclic XSD simpleType restriction'),
      ('''<xs:simpleType name="A"><xs:restriction base="xs:string"><xs:minLength value="3"/>
          <xs:maxLength value="5"/></xs:restriction></xs:simpleType>
          <xs:simpleType name="B"><xs:restriction base="t:A"><xs:minLength value="6"/>
          </xs:restriction></xs:simpleType>''',
       ValueError, 'Unsatisfiable inherited XSD length bounds'),
      ('''<xs:simpleType name="A"><xs:restriction base="xs:string"><xs:pattern value="[A-Z]+"/>
          </xs:restriction></xs:simpleType>
          <xs:simpleType name="B"><xs:restriction base="t:A"><xs:pattern value="A+"/>
          </xs:restriction></xs:simpleType>''',
       NotImplementedError, 'Multiple inherited XSD patterns'),
    )
    for declarations, error, diagnostic in cases:
        xsd = ('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:t="urn:loop"
                   targetNamespace="urn:loop">''' + declarations + '</xs:schema>')
        _assert_pipeline_diagnostic(
            AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'bad.xsd', xsd),
            diagnostic, original_error=error)


def test_json_yaml_inline_scalar_allof_intersects_representable_facets(tmp_path):
    """Inline scalar conjunctions must emit their effective restrictions."""
    source = {'type': 'object', 'properties': {
        'code': {'type': 'string', 'minLength': 2, 'allOf': [
            {'minLength': 3}, {'maxLength': 8}, {'pattern': '[A-Z]+'}]},
        'score': {'type': 'integer', 'minimum': 0, 'allOf': [
            {'type': 'number', 'minimum': 5}, {'exclusiveMinimum': 5},
            {'maximum': 10}]}}}
    for kind, suffix in ((Kind.JSONDEFS, 'json'), (Kind.YAMLDEFS, 'yaml')):
        files = _render(source, kind, suffix, tmp_path / suffix)
        java = next(content for (language, _), content in files.items()
                    if language == 'java' and 'getCode' in content)
        python = next(content for (language, _), content in files.items()
                      if language == 'python' and 'getCode' in content)
        assert 'AIaDataObjectFieldStringConstraints(minLength = 3, maxLength = 8, pattern = "[A-Z]+")' in java
        assert "AIaDataObjectFieldStringConstraints(min_length=3, max_length=8, pattern='[A-Z]+')" in python
        assert 'AIaDataObjectFieldNumericConstraints(minimum = "5", maximum = "10", exclusiveMinimum = true)' in java
        assert "AIaDataObjectFieldNumericConstraints(minimum='5', maximum='10', exclusive_minimum=True)" in python


def test_inline_scalar_allof_rejects_unrepresentable_intersections():
    """Do not erase compound patterns, object constraints or contradictory ranges."""
    from pytest import raises
    samples = (
        ({'type': 'string', 'allOf': [{'pattern': 'A+'}, {'pattern': 'B+'}]},
         NotImplementedError, 'Multiple inherited XSD patterns'),
        ({'type': 'string', 'allOf': [{'minLength': 5}, {'maxLength': 4}]},
         ValueError, 'Unsatisfiable inherited XSD length bounds'),
        ({'type': 'object', 'allOf': [{'properties': {'x': {'type': 'string'}}}]},
         NotImplementedError, 'Inline non-scalar allOf'),
    )
    for data, error, message in samples:
        document = {'type': 'object', 'properties': {'field': data}}
        _assert_pipeline_diagnostic(
            AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'invalid.json', document),
            message, original_error=error)


def test_json_yaml_scalar_allof_exact_multiple_of_lcm(tmp_path):
    """Independent multipleOf constraints reduce to the exact decimal LCM."""
    document = {'type': 'object', 'properties': {'lot': {
        'type': 'number', 'allOf': [
            {'multipleOf': 0.2}, {'multipleOf': 0.3}]}}}
    for kind, suffix in ((Kind.JSONDEFS, 'json'), (Kind.YAMLDEFS, 'yaml')):
        files = _render(document, kind, suffix, tmp_path / suffix)
        java = next(content for (language, _), content in files.items()
                    if language == 'java' and 'getLot' in content)
        python = next(content for (language, _), content in files.items()
                      if language == 'python' and 'getLot' in content)
        assert 'AIaDataObjectFieldNumericConstraints(multipleOf = "0.6")' in java
        assert "AIaDataObjectFieldNumericConstraints(multiple_of='0.6')" in python


def test_scalar_intersection_preserves_large_decimal_precision():
    """The effective multipleOf must never round at Decimal context precision."""
    from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
        AIcgdScalar_1 as Scalar, AIngScalarKind_1 as ScalarKind)
    from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
        AIcDefsCodegenCanonicalSchemaFrontend as Frontend)
    # Long exact terminating decimals must behave like Java BigDecimal's LCM.
    first = '123456789012345678901234567890.1'
    combined = Frontend._intersect_scalar_facets(
        Scalar(ScalarKind.NUMBER, multiple_of=first),
        Scalar(ScalarKind.NUMBER, multiple_of='0.2'), '#/price')
    assert combined.multiple_of == '246913578024691357802469135780.2'
    # Even a 50-digit fractional component must remain exact.
    tiny = '0.' + '0' * 49 + '2'
    result = Frontend._intersect_scalar_facets(
        Scalar(ScalarKind.NUMBER, multiple_of='0.1'),
        Scalar(ScalarKind.NUMBER, multiple_of=tiny), '#/quantity')
    assert result.multiple_of == '0.1'


def test_scalar_allof_does_not_attach_format_to_boolean_or_null():
    """Compound scalar handling must enforce the same type rules as plain schemas."""
    from pytest import raises
    for source_kind, suffix in ((Kind.JSONDEFS, 'json'), (Kind.YAMLDEFS, 'yaml')):
        for kind in ('boolean', 'null'):
            document = {'type': 'object', 'properties': {'field': {
                'type': kind, 'allOf': [{'format': 'date-time'}]}}}
            _assert_pipeline_diagnostic(
                AIcdDefsCodegenSourceDocument(source_kind, 'invalid.' + suffix, document),
                'format on an untyped or non-scalar', original_error=NotImplementedError)
