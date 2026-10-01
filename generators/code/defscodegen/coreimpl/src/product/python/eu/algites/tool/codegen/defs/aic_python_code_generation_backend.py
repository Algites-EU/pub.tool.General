from __future__ import annotations

from eu.algites.lib.naming.convention.ain_output_name_kind import AInOutputNameKind
from eu.algites.tool.codegen.defs._support import _python_type
from eu.algites.tool.codegen.defs.aic_generation_names import AIcGenerationNames
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind


class AIcPythonCodeGenerationBackend:
    """Generates Python dataclasses and enums from normalized canonical definitions."""

    target = AInCodeGenerationTarget.PYTHON

    def __init__(self) -> None:
        """Create the backend with the default generation-name service."""
        self.names = AIcGenerationNames()

    def generate(self, request) -> AIcdGeneratedSource:
        """Generate one Python module from a canonical definition."""
        is_enum = request.definition.kind is AInDefinitionKind.ENUM
        type_kind = AInOutputNameKind.ENUM_TYPE if is_enum else AInOutputNameKind.DATA_TYPE
        file_kind = AInOutputNameKind.ENUM_TYPE_FILE_STEM if is_enum else AInOutputNameKind.DATA_TYPE_FILE_STEM
        type_name = self.names.type_name(request.definition, request.naming_profile, type_kind)
        file_stem = self.names.file_stem(request.definition, request.naming_profile, file_kind)
        if is_enum:
            fields = "\n".join(
                f"    {self.names.enum_constant(value.value, request.naming_profile)} = {value.value!r}"
                for value in request.definition.enum_values
            )
            values = tuple(
                f"{self.names.enum_constant(value.value, request.naming_profile)}: {self._doc(value.description, f'Canonical enum value {value.value}.')}"
                for value in request.definition.enum_values
            )
            source = (
                "from enum import Enum\n\n\n"
                f"class {type_name}(str, Enum):\n"
                f"{self._type_docstring(request.definition, values=values)}"
                f"    __canonical_source_id__ = {request.definition.identity!r}\n"
                f"    __canonical_source_version__ = {request.definition.version!r}\n"
                f"    __canonical_source_resource__ = {request.definition.source_resource!r}\n"
                f"{fields}\n"
            )
        else:
            imports = set()
            fields = []
            attributes = []
            mappings = []
            ordered_properties = tuple(prop for prop in request.definition.properties if prop.required) + tuple(
                prop for prop in request.definition.properties if not prop.required
            )
            for prop in ordered_properties:
                ptype = _python_type(prop, request, self.names)
                if prop.reference:
                    ref_type_kind = AInOutputNameKind.ENUM_TYPE if prop.reference.target_kind is AInDefinitionKind.ENUM else AInOutputNameKind.DATA_TYPE
                    ref_file_kind = AInOutputNameKind.ENUM_TYPE_FILE_STEM if prop.reference.target_kind is AInDefinitionKind.ENUM else AInOutputNameKind.DATA_TYPE_FILE_STEM
                    ref_type = self.names.render(prop.reference.logical_name, prop.reference.version, request.naming_profile, ref_type_kind)
                    ref_file = self.names.render(prop.reference.logical_name, prop.reference.version, request.naming_profile, ref_file_kind)
                    imports.add(f"from .{ref_file} import {ref_type}")
                if not prop.required and "None" not in ptype:
                    ptype += " | None"
                property_name = self.names.property_name(prop.source_name, request.naming_profile)
                fields.append(f"    {property_name}: {ptype}" + ("" if prop.required else " = None"))
                attributes.append(f"{property_name}: {self._doc(prop.description, f'Value of canonical property {prop.source_name}.')}")
                mappings.append((property_name, prop.source_name))
            if not fields:
                fields.append("    pass")
            reference_imports = "\n".join(sorted(imports))
            if reference_imports:
                reference_imports += "\n"
            mapping_methods = ["", "    @classmethod", "    def from_mapping(cls, value: Mapping[str, object]):"]
            if mappings:
                arguments = ", ".join(f"{property_name}=value.get({source_name!r})" for property_name, source_name in mappings)
                mapping_methods.append(f"        return cls({arguments})")
            else:
                mapping_methods.append("        return cls()")
            mapping_methods.extend(["", "    def to_mapping(self) -> Mapping[str, object]:"] )
            if mappings:
                entries = ", ".join(f"{source_name!r}: self.{property_name}" for property_name, source_name in mappings)
                mapping_methods.append(f"        return {{{entries}}}")
            else:
                mapping_methods.append("        return {}")
            source = (
                "from __future__ import annotations\n\n"
                "from dataclasses import dataclass\n"
                "from typing import Any, Mapping\n"
                + reference_imports + "\n"
                "@dataclass(frozen=True, slots=True)\n"
                f"class {type_name}:\n"
                f"{self._type_docstring(request.definition, attributes)}"
                f"    __canonical_source_id__ = {request.definition.identity!r}\n"
                f"    __canonical_source_version__ = {request.definition.version!r}\n"
                f"    __canonical_source_resource__ = {request.definition.source_resource!r}\n"
                + "\n".join(fields + mapping_methods) + "\n"
            )
        return AIcdGeneratedSource(type_name, request.package_name.replace('.', '/') + f"/{file_stem}.py", source)

    @classmethod
    def _type_docstring(cls, definition, attributes=(), values=()) -> str:
        """Build the docstring for one generated Python type."""
        description = cls._doc(definition.description, f"Generated representation of canonical definition {definition.logical_name}.")
        rows = [f'    """{description}', "", f"    Generated from canonical definition {definition.identity}/{definition.version}. Source: {definition.source_resource}. Do not edit manually."]
        if attributes:
            rows.extend(["", "    Attributes:"])
            rows.extend(f"        {entry}" for entry in attributes)
        if values:
            rows.extend(["", "    Values:"])
            rows.extend(f"        {entry}" for entry in values)
        rows.append('    """')
        return "\n".join(rows) + "\n"

    @staticmethod
    def _doc(value: str | None, fallback: str) -> str:
        """Normalize canonical documentation for a one-line Python description."""
        return " ".join((value or fallback).replace('"""', '\\\"\\\"\\\"').split())
