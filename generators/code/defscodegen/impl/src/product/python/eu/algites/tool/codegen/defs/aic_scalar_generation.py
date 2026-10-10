from pathlib import Path
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.lib.naming.convention.ain_output_name_kind import AInOutputNameKind

TEMPORAL = {'date', 'time', 'dateTime', 'dateTimeStamp', 'gYearMonth', 'gYear', 'gMonthDay', 'gDay', 'gMonth'}
DURATION = {'duration', 'yearMonthDuration', 'dayTimeDuration'}
BINARY = {'hexBinary', 'base64Binary'}


def scalar_type(kind, constraints, java=False):
    dtype = constraints.data_type
    if dtype in BINARY: return 'byte[]' if java else 'bytes'
    if dtype in TEMPORAL: return 'javax.xml.datatype.XMLGregorianCalendar' if java else 'AIcSchemaTemporalValue'
    if dtype in DURATION: return 'javax.xml.datatype.Duration' if java else 'AIcSchemaDuration'
    if kind is AInValueKind.INTEGER: return 'java.math.BigInteger' if java else 'int'
    if kind is AInValueKind.NUMBER:
        if dtype in ('float', 'double'): return ('Float' if dtype == 'float' else 'Double') if java else 'float'
        return 'java.math.BigDecimal' if java else 'Decimal'
    return {AInValueKind.STRING: 'String' if java else 'str', AInValueKind.BOOLEAN: 'Boolean' if java else 'bool',
            AInValueKind.OBJECT: 'java.util.Map<String, Object>' if java else 'Mapping[str, Any]'}.get(kind, 'Object' if java else 'Any')


def constraint_tuple(constraints):
    return (constraints.data_type, constraints.minimum, constraints.maximum, constraints.exclusive_minimum,
            constraints.exclusive_maximum, constraints.min_length, constraints.max_length, constraints.pattern, constraints.enum_values)


def python_data_source(request, names, type_name, docstring):
    import keyword, re
    imports, fields, docs, arguments, validations, wire_entries, schema_field_constants = set(), [], [], [], [], [], []
    used = set()
    props = sorted(request.definition.properties, key=lambda p: not p.required)
    for prop in props:
        name = re.sub(r'[^a-zA-Z0-9_]', '_', names.property_name(prop.source_name, request.naming_profile))
        if not name or name[0].isdigit(): name = '_'+name
        if keyword.iskeyword(name): name += '_'
        if name in used: raise ValueError(f'Duplicate Python property name {name}')
        used.add(name)
        ref = None
        if prop.reference:
            enum = prop.reference.target_kind is AInDefinitionKind.ENUM
            ref = names.render(prop.reference.logical_name, prop.reference.version, request.naming_profile, AInOutputNameKind.ENUM_TYPE if enum else AInOutputNameKind.DATA_TYPE)
            file = names.render(prop.reference.logical_name, prop.reference.version, request.naming_profile, AInOutputNameKind.ENUM_TYPE_FILE_STEM if enum else AInOutputNameKind.DATA_TYPE_FILE_STEM)
            imports.add(f'from .{file} import {ref}')
        array = prop.value_kind is AInValueKind.ARRAY
        kind = (prop.item_value_kind or AInValueKind.ANY) if array else prop.value_kind
        constraints = prop.item_constraints if array else prop.constraints
        typ = ref or scalar_type(kind, constraints)
        if array: typ = f'tuple[{typ}, ...]'
        if prop.nullable: typ += ' | None'
        fields.append(f'    {name}: {typ}'+('' if prop.required else ' = _AI_UNSET'))
        docs.append(f'{name}: '+(' '.join((prop.description or f'Value of canonical property {prop.source_name}.').split())))
        schema_field_constants.append(_python_schema_field_constant(prop, request, names))
        raw = f'value[{prop.source_name!r}]' if prop.required else f'value.get({prop.source_name!r}, _AI_UNSET)'
        def convert(expr):
            if ref:
                return f'({expr} if isinstance({expr}, {ref}) else {ref}({expr}))' if prop.reference.target_kind is AInDefinitionKind.ENUM else f'({expr} if isinstance({expr}, {ref}) else {ref}.from_mapping({expr}))'
            return f'_ai_convert({expr}, {constraints.data_type!r}, {kind.name!r})'
        converted = f'tuple({convert("item")} for item in {raw})' if array else convert(raw)
        arguments.append(f'{name}=({raw} if {raw} is _AI_UNSET or {raw} is None else {converted})')
        validations.append(f'        if self.{name} is not _AI_UNSET:')
        validations.append(f'            if self.{name} is None:')
        validations.append('                '+('pass' if prop.nullable else f'raise ValueError({prop.source_name!r} + ": null is not permitted")'))
        validations.append('            else:')
        if array:
            validations.append(f'                if not isinstance(self.{name}, (tuple, list)): raise TypeError({prop.source_name!r} + ": expected collection")')
            validations.append(f'                for item in self.{name}:')
            value, indent = 'item', '                    '
        else: value, indent = f'self.{name}', '                '
        if ref: validations.append(f'{indent}if not isinstance({value}, {ref}): raise TypeError({prop.source_name!r} + ": incorrect referenced type")')
        else: validations.append(f'{indent}_ai_validate({value}, {kind.name!r}, {constraint_tuple(constraints)!r}, {prop.source_name!r})')
        if prop.required: validations.append(f'        else: raise ValueError({prop.source_name!r} + ": value is required")')
        dtype = constraints.data_type
        wire_entries.append(f'            {prop.source_name!r}: _ai_wire(self.{name}, {dtype!r}),')
    runtime = Path(__file__).with_name('_schema_runtime.py').read_text()
    return ('from __future__ import annotations\n\nfrom typing import Any, Mapping\n'+runtime+'\n'+ '\n'.join(sorted(imports))+'\n\n'
        '@dataclass(frozen=True, slots=True)\n'+f'class {type_name}:\n'+docstring(request.definition, docs)+
        f'    __canonical_source_id__ = {request.definition.identity!r}\n    __canonical_source_version__ = {request.definition.version!r}\n    __canonical_source_resource__ = {request.definition.source_resource!r}\n\n'+
        '\n'.join(schema_field_constants) + ('\n\n' if schema_field_constants else '') +
        '\n'.join(fields or ['    pass'])+'\n\n    def __post_init__(self):\n'+ '\n'.join(validations or ['        pass'])+
        '\n\n    @classmethod\n    def from_mapping(cls, value: Mapping[str, object]):\n'+f'        return cls({", ".join(arguments)})\n'+
        '\n    def to_mapping(self) -> Mapping[str, object]:\n        return {key: value for key, value in {\n'+ '\n'.join(wire_entries)+'\n        }.items() if value is not _AI_UNSET}\n')


def _python_schema_field_constant(prop, request, names):
    """Render one documented class constant for a canonical schema field name."""
    constant = names.schema_field_name_constant(prop.source_name, request.naming_profile)
    field_name = prop.source_name.replace('\\', '\\\\').replace('"""', r'\"\"\"')
    rows = [f'    {constant} = {prop.source_name!r}', f'    """**Field Name:** ``{field_name}``']
    if prop.description:
        description = ' '.join(prop.description.split()).replace('\\', '\\\\').replace('"""', r'\"\"\"')
        rows.extend(['', f'    **Field Description:** {description}'])
    rows[-1] += '"""'
    return '\n'.join(rows)


def java_validation(prop, name):
    from eu.algites.tool.codegen.defs._support import _java_quote
    rows = []
    if prop.required and not prop.nullable: rows.append(f'        java.util.Objects.requireNonNull({name}, {_java_quote(prop.source_name)});')
    rows.append(f'        if ({name} != null) {{')
    array = prop.value_kind is AInValueKind.ARRAY
    if array:
        rows.extend([f'            for (var locItem : {name}) {{', '                java.util.Objects.requireNonNull(locItem, "Array item");'])
    value, indent = ('locItem', '                ') if array else (name, '            ')
    c = prop.item_constraints if array else prop.constraints
    def check(condition): rows.append(indent+f'if ({condition}) throw new IllegalArgumentException("Schema value violates its constraints.");')
    if c.data_type in TEMPORAL:
        expected = 'dateTime' if c.data_type == 'dateTimeStamp' else c.data_type
        check(f'!{value}.isValid() || !{_java_quote(expected)}.equals({value}.getXMLSchemaType().getLocalPart())')
        if c.data_type == 'dateTimeStamp': check(f'{value}.getTimezone() == javax.xml.datatype.DatatypeConstants.FIELD_UNDEFINED')
    if c.minimum is not None: check(f'new java.math.BigDecimal({value}.toString()).compareTo(new java.math.BigDecimal({_java_quote(c.minimum)})) {"<=" if c.exclusive_minimum else "<"} 0')
    if c.maximum is not None: check(f'new java.math.BigDecimal({value}.toString()).compareTo(new java.math.BigDecimal({_java_quote(c.maximum)})) {">=" if c.exclusive_maximum else ">"} 0')
    length = value+'.length' if c.data_type in BINARY else f'{value}.codePointCount(0, {value}.length())'
    if c.min_length is not None: check(f'{length} < {c.min_length}')
    if c.max_length is not None: check(f'{length} > {c.max_length}')
    if c.pattern is not None: check(f'!java.util.regex.Pattern.compile({_java_quote(c.pattern)}).matcher({value}.toString()).find()')
    if c.enum_values: check(f'!java.util.List.of({", ".join(_java_quote(v) for v in c.enum_values)}).contains({value}.toString())')
    if array: rows.append('            }')
    rows.append('        }')
    return '\n'.join(rows)+'\n'


_JAVA_RESERVED = frozenset("abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for goto if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while true false null _ record yield var sealed permits non-sealed clone finalize getClass hashCode notify notifyAll toString wait".split())

def java_identifier(name):
    return name + '_' if name in _JAVA_RESERVED else name
