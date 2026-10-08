"""JSON Schema null semantics shared by the native Python definition frontend."""
from collections.abc import Mapping
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind


def _accepts_null(schema):
    """Evaluate supported JSON Schema assertions on the actual JSON null value."""
    if isinstance(schema, bool):
        return schema
    if not isinstance(schema, Mapping):
        return False
    types = schema.get("type")
    if types is not None and ("null" not in types if isinstance(types, list) else types != "null"):
        return False
    if "enum" in schema and None not in schema["enum"]:
        return False
    if "const" in schema and schema["const"] is not None:
        return False
    if any(not _accepts_null(branch) for branch in schema.get("allOf", ())):
        return False
    if "anyOf" in schema and not any(_accepts_null(branch) for branch in schema["anyOf"]):
        return False
    if "oneOf" in schema and sum(_accepts_null(branch) for branch in schema["oneOf"]) != 1:
        return False
    if "not" in schema and _accepts_null(schema["not"]):
        return False
    if "if" in schema:
        branch = "then" if _accepts_null(schema["if"]) else "else"
        if branch in schema and not _accepts_null(schema[branch]):
            return False
    return True


def _non_null_kind(schema):
    """Infer the primitive value kind of an untyped enum/const without treating null as text."""
    non_null = next((value for value in schema.get("enum", ()) if value is not None), schema.get("const"))
    if isinstance(non_null, bool):
        return AInValueKind.BOOLEAN
    if isinstance(non_null, int):
        return AInValueKind.INTEGER
    if isinstance(non_null, float):
        return AInValueKind.NUMBER
    if isinstance(non_null, str):
        return AInValueKind.STRING
    return AInValueKind.ANY
