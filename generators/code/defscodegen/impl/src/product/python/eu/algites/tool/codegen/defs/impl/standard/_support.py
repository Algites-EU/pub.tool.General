from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind

def _strip_extensions(name: str) -> str:
    """Remove recognized definition and serialization extensions from a resource name."""
    for suffix in (".yamldef.schema.json", ".jsondef.schema.json", ".schema.json", ".json", ".yaml", ".yml", ".xsd"):
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return Path(name).stem


def _value_kind(raw_type):
    """Map a schema value declaration to the normalized value kind."""
    return {
        "string": AInDataTypeKind.STRING,
        "integer": AInDataTypeKind.INTEGER,
        "number": AInDataTypeKind.NUMBER,
        "boolean": AInDataTypeKind.BOOLEAN,
        "array": AInDataTypeKind.ARRAY,
        "object": AInDataTypeKind.OBJECT,
    }.get(raw_type, AInDataTypeKind.ANY)


def _xsd_kind(value):
    """Map an XSD type declaration to the normalized value kind."""
    local = value.split(":")[-1]
    return {
        "string": AInDataTypeKind.STRING,
        "integer": AInDataTypeKind.INTEGER,
        "int": AInDataTypeKind.INTEGER,
        "decimal": AInDataTypeKind.NUMBER,
        "double": AInDataTypeKind.NUMBER,
        "boolean": AInDataTypeKind.BOOLEAN,
    }.get(local, AInDataTypeKind.REFERENCE)


def _java_quote(value):
    """Quote a value as a Java string literal."""
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + '"'


def _java_integer(value):
    """Render an optional integer as a Java literal."""
    return "null" if value is None else str(value)


def _java_type(prop, request, names):
    """Preserve exact scalar types and referenced collection item types."""
    from eu.algites.tool.codegen.defs.impl.standard.aic_scalar_generation import scalar_type
    array = prop.data_type.kind is AInDataTypeKind.ARRAY
    item = names.reference_type(prop.data_type.referenced_definition(), request.naming_profile) if prop.data_type.referenced_definition() else scalar_type(
        prop.data_type.element_type.kind if array else prop.data_type.kind, prop.data_type.element_type.constraints if array else prop.data_type.constraints, True)
    return f"java.util.List<{item}>" if array else item


def _java_scalar_type(kind):
    """Map a normalized scalar kind to its Java source type."""
    return {AInDataTypeKind.STRING: "String", AInDataTypeKind.INTEGER: "Long", AInDataTypeKind.NUMBER: "Double", AInDataTypeKind.BOOLEAN: "Boolean"}.get(kind, "Object")


def _python_type(prop, request, names):
    """Map a normalized property to its Python type annotation."""
    if prop.data_type.referenced_definition():
        return names.reference_type(prop.data_type.referenced_definition(), request.naming_profile)
    if prop.data_type.kind is AInDataTypeKind.ARRAY:
        return f"tuple[{_python_scalar_type(prop.data_type.element_type.kind)}, ...]"
    return {
        AInDataTypeKind.STRING: "str",
        AInDataTypeKind.INTEGER: "int",
        AInDataTypeKind.NUMBER: "float",
        AInDataTypeKind.BOOLEAN: "bool",
        AInDataTypeKind.OBJECT: "Mapping[str, Any]",
    }.get(prop.data_type.kind, "Any")


def _python_scalar_type(kind):
    """Map a normalized scalar kind to its Python type annotation."""
    return {AInDataTypeKind.STRING: "str", AInDataTypeKind.INTEGER: "int", AInDataTypeKind.NUMBER: "float", AInDataTypeKind.BOOLEAN: "bool"}.get(kind, "Any")
