from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind

def _strip_extensions(name: str) -> str:
    """Remove recognized definition and serialization extensions from a resource name."""
    for suffix in (".yamldef.schema.json", ".jsondef.schema.json", ".schema.json", ".json", ".yaml", ".yml", ".xsd"):
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return Path(name).stem


def _value_kind(raw_type):
    """Map a schema value declaration to the normalized value kind."""
    return {
        "string": AInValueKind.STRING,
        "integer": AInValueKind.INTEGER,
        "number": AInValueKind.NUMBER,
        "boolean": AInValueKind.BOOLEAN,
        "array": AInValueKind.ARRAY,
        "object": AInValueKind.OBJECT,
    }.get(raw_type, AInValueKind.ANY)


def _xsd_kind(value):
    """Map an XSD type declaration to the normalized value kind."""
    local = value.split(":")[-1]
    return {
        "string": AInValueKind.STRING,
        "integer": AInValueKind.INTEGER,
        "int": AInValueKind.INTEGER,
        "decimal": AInValueKind.NUMBER,
        "double": AInValueKind.NUMBER,
        "boolean": AInValueKind.BOOLEAN,
    }.get(local, AInValueKind.REFERENCE)


def _java_quote(value):
    """Quote a value as a Java string literal."""
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + '"'


def _java_integer(value):
    """Render an optional integer as a Java literal."""
    return "null" if value is None else str(value)


def _java_type(prop, request, names):
    """Preserve exact scalar types and referenced collection item types."""
    from eu.algites.tool.codegen.defs.aic_scalar_generation import scalar_type
    array = prop.value_kind is AInValueKind.ARRAY
    item = names.reference_type(prop.reference, request.naming_profile) if prop.reference else scalar_type(
        prop.item_value_kind if array else prop.value_kind, prop.item_constraints if array else prop.constraints, True)
    return f"java.util.List<{item}>" if array else item


def _java_scalar_type(kind):
    """Map a normalized scalar kind to its Java source type."""
    return {AInValueKind.STRING: "String", AInValueKind.INTEGER: "Long", AInValueKind.NUMBER: "Double", AInValueKind.BOOLEAN: "Boolean"}.get(kind, "Object")


def _python_type(prop, request, names):
    """Map a normalized property to its Python type annotation."""
    if prop.reference:
        return names.reference_type(prop.reference, request.naming_profile)
    if prop.value_kind is AInValueKind.ARRAY:
        return f"tuple[{_python_scalar_type(prop.item_value_kind)}, ...]"
    return {
        AInValueKind.STRING: "str",
        AInValueKind.INTEGER: "int",
        AInValueKind.NUMBER: "float",
        AInValueKind.BOOLEAN: "bool",
        AInValueKind.OBJECT: "Mapping[str, Any]",
    }.get(prop.value_kind, "Any")


def _python_scalar_type(kind):
    """Map a normalized scalar kind to its Python type annotation."""
    return {AInValueKind.STRING: "str", AInValueKind.INTEGER: "int", AInValueKind.NUMBER: "float", AInValueKind.BOOLEAN: "bool"}.get(kind, "Any")
