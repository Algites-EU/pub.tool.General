"""Cross-format contracts plus independent checks of generated runtime behavior."""
from dataclasses import replace
from decimal import Decimal
import importlib
import os
from pathlib import Path
import subprocess
import sys
import typing
import pytest

from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind

STEMS = ('parity-root', 'parity-child', 'parity-leaf', 'parity-status', 'parity-builtins')
FORMATS = ((AInDefinitionSourceKind.YAMLDEFS, 'yamldefs', 'yamldef.schema.json'),
           (AInDefinitionSourceKind.JSONDEFS, 'jsondefs', 'jsondef.schema.json'),
           (AInDefinitionSourceKind.XMLDEFS, 'xmldefs', 'xsd'))


def load(stem, kind, folder, suffix):
    return AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(
        Path(__file__).parents[1] / folder / f'{stem}_1.{suffix}', kind,
        AIcAlgitesNamingProfiles.python_profile()))


def normalize(model):
    # Only provenance differs legitimately; keep every comment and constraint.
    return replace(model, identity=f'urn:parity:{model.logical_name}:1',
                   source_kind=AInDefinitionSourceKind.JSONDEFS,
                   source_resource=f'{model.logical_name}_1.schema')


@pytest.mark.parametrize('stem', STEMS)
def test_equivalent_models_and_complete_outputs(stem):
    models = [load(stem, *fmt) for fmt in FORMATS]
    merged = AIcCanonicalDefinitionMerger.merge(models)
    assert all(model.identity in merged.description for model in models)
    for target in AInCodeGenerationTarget:
        profile = AIcAlgitesNamingProfiles.java_profile() if target is AInCodeGenerationTarget.JAVA else AIcAlgitesNamingProfiles.python_profile()
        outputs = [AIcDefaultDefsCodegenService().generate(AIcdCodeGenerationRequest(
            normalize(model), target, 'parity_generated', profile)) for model in models]
        assert outputs[0] == outputs[1] == outputs[2]
    root = models[0]
    if stem == 'parity-root':
        props = {p.source_name: p for p in root.properties}
        assert len(props) == 28 and 'inner' not in props
        assert props['children'].value_kind is AInValueKind.ARRAY
        assert props['children'].reference.logical_name == 'parity-child'
        assert props['statuses'].reference.logical_name == 'parity-status'
        assert props['nullableText'].required and props['nullableText'].nullable
        assert props['boundedInteger'].constraints.minimum == '-4'
        assert props['boundedDecimal'].constraints.exclusive_maximum
    if stem == 'parity-builtins':
        props = {p.source_name: p for p in root.properties}
        assert len(props) == 46
        assert props['unsignedLong'].constraints.maximum == '18446744073709551615'
        assert props['byte'].constraints.minimum == '-128'
        assert props['decimal'].constraints.data_type == 'decimal'
        assert props['float'].constraints.data_type == 'float'
        assert props['double'].constraints.data_type == 'double'


def test_schema_field_name_constants_across_all_definition_kinds():
    """Verify documented canonical field-name constants for YAML, JSON and XML inputs."""
    service = AIcDefaultDefsCodegenService()
    for fmt in FORMATS:
        model = load('parity-root', *fmt)
        java_source = service.generate(AIcdCodeGenerationRequest(
            model, AInCodeGenerationTarget.JAVA, 'parity_generated', AIcAlgitesNamingProfiles.java_profile())).source
        assert 'public static final String SCHEMA_FIELD_NAME__OPTIONAL_TEXT = "optionalText";' in java_source
        assert '<strong>Field Name:</strong> {@code optionalText}<br/>' in java_source
        assert '<strong>Field Description:</strong> Optional text value.' in java_source

        python_source = service.generate(AIcdCodeGenerationRequest(
            model, AInCodeGenerationTarget.PYTHON, 'parity_generated', AIcAlgitesNamingProfiles.python_profile())).source
        assert "SCHEMA_FIELD_NAME__OPTIONAL_TEXT = 'optionalText'" in python_source
        assert '**Field Name:** ``optionalText``' in python_source
        assert '**Field Description:** Optional text value.' in python_source


def generate_package(tmp_path, target):
    service = AIcDefaultDefsCodegenService()
    profile = AIcAlgitesNamingProfiles.java_profile() if target is AInCodeGenerationTarget.JAVA else AIcAlgitesNamingProfiles.python_profile()
    paths = []
    for stem in STEMS:
        output = service.generate(AIcdCodeGenerationRequest(load(stem, *FORMATS[2]), target, 'parity_generated', profile))
        path = tmp_path / output.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output.source)
        paths.append(path)
    return paths


def test_generated_java_compiles(tmp_path):
    paths = generate_package(tmp_path, AInCodeGenerationTarget.JAVA)
    javac = Path(os.environ.get('JAVA_HOME', '/usr')) / 'bin/javac'
    subprocess.run([str(javac) if javac.is_file() else 'javac', '-d', str(tmp_path / 'classes'), *map(str, paths)], check=True)
    source = '\n'.join(path.read_text() for path in paths)
    assert 'java.math.BigInteger' in source and 'java.math.BigDecimal' in source
    assert 'javax.xml.datatype.XMLGregorianCalendar' in source and 'byte[]' in source


def valid_payload():
    return dict(text='hello', count=10**80, amount=Decimal('12345678901234567890.1234567890123456789'), enabled=True,
        nullableText=None, child={'name':'child', 'detail':{'label':'leaf', 'quantity':10**90}},
        children=[{'name':'second','detail':{'label':'nested','quantity':2}}], status='pending', statuses=['pending','complete'],
        texts=['a','b'], counts=[10**80], amounts=[Decimal('0.123456789012345678901')], flags=[True,False],
        freeObject={'a':1}, inlineObject={'inner':'value'}, anything={'value':[1,2]}, inlineState='first',
        dateValue='12345-02-28+14:00', timeValue='23:59:59.1234567890123456789Z',
        timestamp='2024-02-29T23:59:59.1234567890123456789Z', durationValue='P1Y2M3DT4H5M6.123456789S',
        binaryHex='01FF', binaryBase64='Af8=', boundedText='ABC', boundedInteger=8, boundedDecimal=Decimal('2.499999999999999999'))


def test_generated_python_exact_types_and_invalid_values(tmp_path):
    paths = generate_package(tmp_path, AInCodeGenerationTarget.PYTHON)
    (tmp_path / 'parity_generated/__init__.py').touch()
    sys.path.insert(0, str(tmp_path))
    try:
        root_path = next(path for path in paths if 'parity_root' in path.name)
        module = importlib.import_module('parity_generated.' + root_path.stem)
        cls = next(value for value in vars(module).values() if isinstance(value, type) and getattr(value, '__canonical_source_id__', '').endswith(':parity-root:1'))
        assert typing.get_type_hints(cls)
        payload = valid_payload()
        value = cls.from_mapping(payload)
        assert value.to_mapping() == payload
        assert value.count == 10**80 and value.amount == payload['amount']
        assert value.binary_hex == b'\x01\xff'
        assert value.child.detail.quantity == 10**90
        assert 'optionalText' not in value.to_mapping()
        for key, invalid in [('count', True), ('optionalText', None), ('boundedInteger',9), ('boundedDecimal',Decimal('2.5')),
            ('boundedText','a'), ('boundedText','TOOLONG'), ('inlineState','wrong'), ('status','wrong'),
            ('dateValue','2023-02-29'), ('timeValue','25:00:00'), ('binaryHex','xx'), ('binaryBase64','***')]:
            with pytest.raises((ValueError, TypeError)):
                cls.from_mapping(dict(payload, **{key:invalid}))
        with pytest.raises(KeyError): cls.from_mapping({key:value for key,value in payload.items() if key != 'text'})
    finally:
        sys.path.remove(str(tmp_path))
        for name in tuple(sys.modules):
            if name == 'parity_generated' or name.startswith('parity_generated.'):
                del sys.modules[name]


@pytest.mark.parametrize('kind,suffix', [(AInDefinitionSourceKind.JSONDEFS,'jsondef.schema.json'),(AInDefinitionSourceKind.YAMLDEFS,'yamldef.schema.json'),(AInDefinitionSourceKind.YAMLDEFS,'yamldef.yaml')])
def test_schema_decimal_facets_remain_exact(tmp_path, kind, suffix):
    path = tmp_path / f'exact_1.{suffix}'
    boundary = '0.12345678901234567890123456789'
    path.write_text('{"type":"object","properties":{"value":{"type":"number","minimum":'+boundary+'}}}')
    model = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(path,kind,AIcAlgitesNamingProfiles.python_profile()))
    assert model.properties[0].constraints.minimum == boundary


def test_float_width_and_calendar_values():
    from eu.algites.tool.codegen.defs._schema_runtime import _ai_convert, AIcSchemaTemporalValue, AIcSchemaDuration
    assert _ai_convert('16777217', 'float', 'NUMBER') == 16777216.0
    assert _ai_convert('16777217', 'double', 'NUMBER') == 16777217.0
    for dtype, value in [('date','12345-02-28+14:00'),('time','24:00:00Z'),('dateTime','2024-02-29T12:34:56.1234567890123456789'),
        ('gYear','-12345Z'),('gYearMonth','2024-02'),('gMonthDay','--02-29'),('gMonth','--12'),('gDay','---31')]:
        assert AIcSchemaTemporalValue(value,dtype).lexical == value
    assert AIcSchemaDuration('P1Y2M3DT4H5M6.1234567890123456789S').lexical.endswith('1234567890123456789S')
    with pytest.raises(ValueError): AIcSchemaTemporalValue('2024-02-29T00:00:00','dateTimeStamp')


def test_urn_subschema_and_anchor_resolution(tmp_path):
    definitions = tmp_path / 'yamldefs'; definitions.mkdir()
    (definitions / 'leaf_1.yamldef.schema.json').write_text('{"$id":"urn:tests:leaf:1","$defs":{"value":{"$anchor":"Content","type":"integer","minimum":1}},"type":"object","properties":{}}')
    path = definitions / 'root_1.yamldef.schema.json'
    path.write_text('{"type":"object","properties":{"inline":{"$ref":"urn:tests:leaf:1#Content"},"leaf":{"$ref":"urn:tests:leaf:1"}}}')
    model = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(path,AInDefinitionSourceKind.YAMLDEFS,AIcAlgitesNamingProfiles.python_profile()))
    assert model.properties[0].value_kind is AInValueKind.INTEGER
    assert model.properties[0].constraints.minimum == '1'
    assert model.properties[1].reference.logical_name == 'leaf'


def test_scalar_root_preserves_type_and_facets(tmp_path):
    for kind, folder, suffix in FORMATS:
        path = tmp_path / f'scalar_1.{suffix}'
        path.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:simpleType name="Value"><xs:restriction base="xs:decimal"><xs:minInclusive value="0.1234567890123456789"/></xs:restriction></xs:simpleType></xs:schema>' if kind is AInDefinitionSourceKind.XMLDEFS else '{"type":"number","minimum":0.1234567890123456789}')
        model = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(path,kind,AIcAlgitesNamingProfiles.python_profile()))
        assert model.properties[0].value_kind is AInValueKind.NUMBER
        assert model.properties[0].constraints.minimum == '0.1234567890123456789'
