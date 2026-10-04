from decimal import Decimal
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind


def decimal_text(value):
    """Normalize exact decimal boundaries without using floating-point arithmetic."""
    text = format(Decimal(str(value)), 'f')
    return text.rstrip('0').rstrip('.') if '.' in text else text


def defaults(data_type):
    """Retain integer subtype bounds without narrowing arbitrary-precision values."""
    minimum = maximum = None
    widths = {'byte': 8, 'short': 16, 'int': 32, 'long': 64,
              'unsignedByte': 8, 'unsignedShort': 16, 'unsignedInt': 32, 'unsignedLong': 64}
    if data_type in widths:
        bits = widths[data_type]; unsigned = data_type.startswith('unsigned')
        minimum = '0' if unsigned else str(-(1 << (bits - 1)))
        maximum = str((1 << (bits if unsigned else bits - 1)) - 1)
    elif data_type == 'nonNegativeInteger': minimum = '0'
    elif data_type == 'positiveInteger': minimum = '1'
    elif data_type == 'nonPositiveInteger': maximum = '0'
    elif data_type == 'negativeInteger': maximum = '-1'
    return AIcdValueConstraints(data_type=data_type, minimum=minimum, maximum=maximum)


def from_json(node, kind):
    """Use JSON Schema keywords, with explicit Modustro hints for types lacking native equivalents."""
    data_type = node.get('x-modustro-datatype')
    if not data_type:
        encoding, format_name = node.get('contentEncoding'), node.get('format')
        if encoding in ('base64', 'base16'): data_type = 'base64Binary' if encoding == 'base64' else 'hexBinary'
        elif format_name in ('date', 'time', 'date-time', 'duration'): data_type = 'dateTime' if format_name == 'date-time' else format_name
        else: data_type = {AInValueKind.STRING: 'string', AInValueKind.INTEGER: 'integer', AInValueKind.NUMBER: 'decimal', AInValueKind.BOOLEAN: 'boolean'}.get(kind)
    if data_type == "anyType": data_type = None
    base = defaults(data_type)
    return AIcdValueConstraints(data_type,
        decimal_text(node.get('exclusiveMinimum', node.get('minimum'))) if 'exclusiveMinimum' in node or 'minimum' in node else base.minimum,
        decimal_text(node.get('exclusiveMaximum', node.get('maximum'))) if 'exclusiveMaximum' in node or 'maximum' in node else base.maximum,
        'exclusiveMinimum' in node, 'exclusiveMaximum' in node,
        node.get('minLength'), node.get('maxLength'), node.get('pattern'), tuple(str(v) for v in node.get('enum', ())))
