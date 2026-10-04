from __future__ import annotations

import keyword
import re

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
            from eu.algites.tool.codegen.defs.aic_scalar_generation import python_data_source
            source = python_data_source(request, self.names, type_name, self._type_docstring)
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
