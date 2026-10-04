from __future__ import annotations

from eu.algites.lib.naming.convention.ain_output_name_kind import AInOutputNameKind
from eu.algites.tool.codegen.defs._support import _java_integer, _java_quote, _java_type
from eu.algites.tool.codegen.defs.aic_generation_names import AIcGenerationNames
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.tool.codegen.defs.aic_scalar_generation import java_validation, java_identifier


class AIcJavaCodeGenerationBackend:
    """Generates Java records and enums from normalized canonical definitions."""

    target = AInCodeGenerationTarget.JAVA

    def __init__(self) -> None:
        """Create the backend with the default generation-name service."""
        self.names = AIcGenerationNames()

    def generate(self, request) -> AIcdGeneratedSource:
        """Generate one Java source file from a canonical definition."""
        is_enum = request.definition.kind is AInDefinitionKind.ENUM
        kind = AInOutputNameKind.ENUM_TYPE if is_enum else AInOutputNameKind.DATA_TYPE
        type_name = self.names.type_name(request.definition, request.naming_profile, kind)
        if is_enum:
            body = ",\n".join(
                self._enum_constant(value, request)
                for value in request.definition.enum_values
            )
            source = (
                f"package {request.package_name};\n\n"
                f"{self._type_javadoc(request.definition)}"
                f"public enum {type_name} {{\n{body};\n\n"
                f"    public static final String CANONICAL_SOURCE_ID = {_java_quote(request.definition.identity)};\n"
                f"    public static final Integer CANONICAL_SOURCE_VERSION = {_java_integer(request.definition.version)};\n"
                f"    public static final String CANONICAL_SOURCE_RESOURCE = {_java_quote(request.definition.source_resource)};\n\n"
                "    private final String wireValue;\n\n"
                f"    {type_name}(String aWireValue) {{\n        wireValue = aWireValue;\n    }}\n\n"
                "    /**\n"
                "     * Returns the exact serialized value declared by the canonical definition.\n"
                "     *\n"
                "     * @return canonical wire value\n"
                "     */\n"
                "    public String wireValue() {\n        return wireValue;\n    }\n"
                "}\n"
            )
        else:
            field_rows = []
            parameter_docs = []
            for prop in request.definition.properties:
                property_name = java_identifier(self.names.property_name(prop.source_name, request.naming_profile))
                field_rows.append(f"{_java_type(prop, request, self.names)} {property_name}")
                parameter_docs.append(
                    f" * @param {property_name} {self._doc(prop.description, f'Value of canonical property {prop.source_name}.')}"
                )
            fields = ",\n        ".join(field_rows)
            source = (
                f"package {request.package_name};\n\n"
                f"{self._type_javadoc(request.definition, parameter_docs)}"
                f"public record {type_name}(\n        {fields}) {{\n"
                f"    public static final String CANONICAL_SOURCE_ID = {_java_quote(request.definition.identity)};\n"
                f"    public static final Integer CANONICAL_SOURCE_VERSION = {_java_integer(request.definition.version)};\n"
                f"    public static final String CANONICAL_SOURCE_RESOURCE = {_java_quote(request.definition.source_resource)};\n"
                "    /** Validates the scalar constraints retained from the canonical schema. */\n"
                f"    public {type_name} {{\n"
                + ''.join(java_validation(prop, java_identifier(self.names.property_name(prop.source_name, request.naming_profile))) for prop in request.definition.properties)
                + "    }\n}\n"
            )
        return AIcdGeneratedSource(type_name, request.package_name.replace('.', '/') + f"/{type_name}.java", source)

    def _enum_constant(self, value, request) -> str:
        """Generate one documented Java enum constant."""
        constant_name = self.names.enum_constant(value.value, request.naming_profile)
        description = self._doc(value.description, f"Canonical enum value {value.value}.")
        return (
            "    /**\n"
            f"     * {description}\n"
            "     */\n"
            f"    {constant_name}({_java_quote(value.value)})"
        )

    @classmethod
    def _type_javadoc(cls, definition, parameter_docs=()) -> str:
        """Build the Javadoc block for one generated Java type."""
        description = cls._doc(definition.description, f"Generated representation of canonical definition {definition.logical_name}.")
        rows = ["/**", f" * {description}", " *", f" * <p>Generated from canonical definition {cls._escape(definition.identity)}/{definition.version}. Source: {cls._escape(definition.source_resource)}. Do not edit manually.</p>"]
        rows.extend(parameter_docs)
        rows.append(" */")
        return "\n".join(rows) + "\n"

    @staticmethod
    def _doc(value: str | None, fallback: str) -> str:
        """Normalize canonical documentation for a one-line Javadoc description."""
        return AIcJavaCodeGenerationBackend._escape(" ".join((value or fallback).split()))

    @staticmethod
    def _escape(value: str) -> str:
        """Escape the Javadoc terminator sequence."""
        return value.replace("*/", "* /")
