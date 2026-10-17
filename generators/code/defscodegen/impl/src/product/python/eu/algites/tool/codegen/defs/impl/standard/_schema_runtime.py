"""Standalone support embedded into generated Python modules; no generator runtime dependency."""
from dataclasses import dataclass
from decimal import Decimal
import base64
import calendar
import re
import struct

_AI_UNSET = object()


@dataclass(frozen=True, slots=True)
class _AIcSchemaTemporalValue:
    """An XML calendar value retaining arbitrary years, precision and optional timezone."""
    lexical: str
    data_type: str

    def __post_init__(self):
        patterns = {
            'date': r'(-?[0-9]{4,})-([0-9]{2})-([0-9]{2})',
            'dateTime': r'(-?[0-9]{4,})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2}(?:\.[0-9]+)?)',
            'dateTimeStamp': r'(-?[0-9]{4,})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2}(?:\.[0-9]+)?)',
            'time': r'([0-9]{2}):([0-9]{2}):([0-9]{2}(?:\.[0-9]+)?)',
            'gYearMonth': r'(-?[0-9]{4,})-([0-9]{2})', 'gYear': r'(-?[0-9]{4,})',
            'gMonthDay': r'--([0-9]{2})-([0-9]{2})', 'gDay': r'---([0-9]{2})', 'gMonth': r'--([0-9]{2})(?:--)?',
        }
        match = re.fullmatch(patterns[self.data_type]+r'(Z|[+-][0-9]{2}:[0-9]{2})?', self.lexical)
        if not match: raise ValueError(f'Invalid {self.data_type}: {self.lexical}')
        groups = list(match.groups()); timezone = groups.pop()
        if self.data_type == 'dateTimeStamp' and timezone is None: raise ValueError('dateTimeStamp requires a timezone')
        if timezone and timezone != 'Z':
            hours, minutes = map(int, timezone[1:].split(':'))
            if hours > 14 or minutes > 59 or (hours == 14 and minutes): raise ValueError('Invalid timezone offset')
        if self.data_type in ('date', 'dateTime', 'dateTimeStamp', 'gYearMonth', 'gYear'):
            year = int(groups[0])
            if year == 0: raise ValueError('XSD 1.0 has no year zero')
            if len(groups) >= 2 and not 1 <= int(groups[1]) <= 12: raise ValueError('Invalid month')
            if len(groups) >= 3 and not 1 <= int(groups[2]) <= calendar.monthrange(year, int(groups[1]))[1]: raise ValueError('Invalid calendar date')
        if self.data_type == 'gMonthDay':
            month, day = map(int, groups)
            if not 1 <= month <= 12 or not 1 <= day <= calendar.monthrange(2000, month)[1]: raise ValueError('Invalid month/day')
        if self.data_type == 'gDay' and not 1 <= int(groups[0]) <= 31: raise ValueError('Invalid day')
        if self.data_type == 'gMonth' and not 1 <= int(groups[0]) <= 12: raise ValueError('Invalid month')
        clock = groups[3:] if self.data_type in ('dateTime', 'dateTimeStamp') else groups if self.data_type == 'time' else None
        if clock:
            hour, minute, second = int(clock[0]), int(clock[1]), Decimal(clock[2])
            if not 0 <= hour <= 24 or not 0 <= minute < 60 or not 0 <= second < 60 or (hour == 24 and (minute or second)): raise ValueError('Invalid clock time')


@dataclass(frozen=True, slots=True)
class _AIcSchemaDuration:
    """A calendar duration preserving months and exact fractional seconds."""
    lexical: str

    def __post_init__(self):
        match = re.fullmatch(r'-?P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?', self.lexical)
        if not match or not any(value is not None for value in match.groups()) or self.lexical.endswith('T'): raise ValueError('Invalid XML duration')


# Public aliases are embedded into generated modules; implementations stay private.
AIcSchemaTemporalValue = _AIcSchemaTemporalValue
AIcSchemaDuration = _AIcSchemaDuration

def _ai_convert(value, data_type, kind):
    if value is None: return None
    if data_type in ('hexBinary', 'base64Binary'):
        if isinstance(value, bytes): return value
        if not isinstance(value, str): raise TypeError('Binary value must be bytes or encoded text')
        return bytes.fromhex(value) if data_type == 'hexBinary' else base64.b64decode(value, validate=True)
    if data_type in ('date', 'time', 'dateTime', 'dateTimeStamp', 'gYearMonth', 'gYear', 'gMonthDay', 'gDay', 'gMonth'):
        return value if isinstance(value, AIcSchemaTemporalValue) else AIcSchemaTemporalValue(str(value), data_type)
    if data_type in ('duration', 'yearMonthDuration', 'dayTimeDuration'):
        return value if isinstance(value, AIcSchemaDuration) else AIcSchemaDuration(str(value))
    if kind == 'INTEGER':
        if isinstance(value, bool): raise TypeError('Boolean is not an integer value')
        if isinstance(value, int): return value
        if isinstance(value, str) and re.fullmatch(r'[+-]?\d+', value): return int(value)
        raise TypeError('Expected an exact integer')
    if kind == 'NUMBER':
        if isinstance(value, bool): raise TypeError('Boolean is not a numeric value')
        if data_type == 'float': return struct.unpack('!f', struct.pack('!f', float(value)))[0]
        return float(value) if data_type == 'double' else Decimal(str(value))
    return value


def _ai_validate(value, kind, constraints, name):
    data_type, minimum, maximum, exclusive_min, exclusive_max, min_len, max_len, pattern, values = constraints
    if kind == 'INTEGER' and (not isinstance(value, int) or isinstance(value, bool)): raise TypeError(f'{name}: expected int')
    if kind == 'NUMBER' and not isinstance(value, float if data_type in ('float', 'double') else Decimal): raise TypeError(f'{name}: incorrect numeric representation')
    if kind == 'BOOLEAN' and not isinstance(value, bool): raise TypeError(f'{name}: expected bool')
    if kind == 'STRING':
        expected = bytes if data_type in ('hexBinary', 'base64Binary') else AIcSchemaTemporalValue if data_type in ('date', 'time', 'dateTime', 'dateTimeStamp', 'gYearMonth', 'gYear', 'gMonthDay', 'gDay', 'gMonth') else AIcSchemaDuration if data_type in ('duration', 'yearMonthDuration', 'dayTimeDuration') else str
        if not isinstance(value, expected): raise TypeError(f'{name}: incorrect scalar representation')
        if isinstance(value, AIcSchemaTemporalValue) and value.data_type != data_type: raise ValueError(f'{name}: incorrect temporal type')
    if kind == 'OBJECT' and not isinstance(value, dict):
        from collections.abc import Mapping
        if not isinstance(value, Mapping): raise TypeError(f'{name}: expected mapping')
    if data_type in ('anySimpleType', 'anyAtomicType') and isinstance(value, (dict, list, tuple)): raise TypeError(f'{name}: expected scalar')
    if minimum is not None or maximum is not None:
        numeric = Decimal(str(value))
        if minimum is not None and (numeric < Decimal(minimum) or (exclusive_min and numeric == Decimal(minimum))): raise ValueError(f'{name}: below minimum')
        if maximum is not None and (numeric > Decimal(maximum) or (exclusive_max and numeric == Decimal(maximum))): raise ValueError(f'{name}: above maximum')
    if min_len is not None and len(value) < min_len: raise ValueError(f'{name}: too short')
    if max_len is not None and len(value) > max_len: raise ValueError(f'{name}: too long')
    if pattern is not None and re.search(pattern, str(value)) is None: raise ValueError(f'{name}: pattern mismatch')
    if values and str(value) not in values: raise ValueError(f'{name}: invalid enum value')


def _ai_wire(value, data_type=None):
    if value is _AI_UNSET: return value
    if value is None: return None
    if isinstance(value, bytes): return value.hex().upper() if data_type == 'hexBinary' else base64.b64encode(value).decode('ascii')
    if isinstance(value, (AIcSchemaTemporalValue, AIcSchemaDuration)): return value.lexical
    if isinstance(value, (tuple, list)): return [_ai_wire(item, data_type) for item in value]
    if hasattr(value, 'to_mapping'): return value.to_mapping()
    from enum import Enum
    if isinstance(value, Enum): return value.value
    return value
