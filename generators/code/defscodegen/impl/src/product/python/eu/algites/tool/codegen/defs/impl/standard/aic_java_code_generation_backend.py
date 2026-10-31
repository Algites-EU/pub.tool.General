from __future__ import annotations

from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.impl.standard._support import _java_integer, _java_quote, _java_type
from eu.algites.tool.codegen.defs.impl.standard.aic_generation_names import AIcGenerationNames
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.aicd_generated_type_identity import AIcdGeneratedTypeIdentity
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.impl.standard.aic_scalar_generation import java_validation, java_identifier


class AIcJavaCodeGenerationBackend:
    """Generates Java records and enums from normalized canonical definitions."""

    target = AInCodeGenerationTarget.JAVA

    def __init__(self) -> None:
        """Create the backend with the default generation-name service."""
        self.names = AIcGenerationNames()

    def generate(self, request) -> AIcdGeneratedSource:
        """Generate one Java source file from a canonical definition."""
        is_enum = request.definition.data_type.kind is AInDataTypeKind.ENUM
        kind = AInDefsNameRole.ENUM_TYPE if is_enum else AInDefsNameRole.DATA_TYPE
        type_name = self.names.type_name(request.definition, request.naming_profile, kind)
        if is_enum:
            body = ",\n".join(
                self._enum_constant(value, request)
                for value in request.definition.enum_values
            )
            const_rows = "\n".join(
                '        /** Canonical serialized field name for enum member '
                + self.names.enum_constant(value.value, request.naming_profile) + '. */\n'
                + '        String ' + self.names.enum_field_name_constant(value.value, request.naming_profile)
                + ' = ' + _java_quote(value.value) + ';'
                for value in request.definition.enum_values
            )
            source = (
                f"package {request.package_name};\n\n"
                f"{self._type_javadoc(request.definition)}"
                f"public enum {type_name} implements eu.algites.lib.common.enums.AIiEnumItem {{\n{body};\n\n"
                f"    /** Canonical identity of this schema definition. */\n"
                f"    public static final String CANONICAL_SOURCE_ID = {_java_quote(request.definition.identity)};\n"
                f"    /** Version of this schema definition. */\n"
                f"    public static final Integer CANONICAL_SOURCE_VERSION = {_java_integer(request.definition.version)};\n"
                f"    /** Source location of the schema definition. */\n"
                f"    public static final String CANONICAL_SOURCE_RESOURCE = {_java_quote(request.definition.source_resource)};\n\n"
                "    private final String code;\n\n"
                f"    {type_name}(String aCode) {{\n        code = aCode;\n    }}\n\n"
                "    /**\n"
                "     * Returns the exact serialized enum value, independently of the Java enum name.\n"
                "     *\n"
                "     * @return canonical wire-level code\n"
                "     */\n"
                "    @Override public String code() {\n        return code;\n    }\n\n"
                "    /**\n"
                "     * Schema-defined serialized enum codes. These constants preserve the\n"
                "     * original wire values independently of Java member identifiers.\n"
                "     */\n"
                "    public interface CONST {\n"
                f"{const_rows}\n"
                "    }\n"
                "}\n"
            )
        else:
            field_rows = []
            parameter_docs = []
            for prop in request.definition.data_type.properties:
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
                f"    public static final String CANONICAL_SOURCE_RESOURCE = {_java_quote(request.definition.source_resource)};\n\n"
                f"{self._schema_field_constants(request)}"
                "    /** Validates the scalar constraints retained from the canonical schema. */\n"
                f"    public {type_name} {{\n"
                + ''.join(java_validation(prop, java_identifier(self.names.property_name(prop.source_name, request.naming_profile))) for prop in request.definition.data_type.properties)
                + "    }\n}\n"
            )
        relative = request.package_name.replace('.', '/') + f"/{type_name}.java"
        return AIcdGeneratedSource(type_name, relative, source,
            (AIcdGeneratedTypeIdentity.from_request(request, type_name, relative, kind),))

    def _enum_constant(self, value, request) -> str:
        """Generate one documented Java enum constant."""
        constant_name = self.names.enum_constant(value.value, request.naming_profile)
        description = self._doc(value.description, f"Canonical enum value {value.value}.")
        return (
            "    /**\n"
            f"     * {description}\n"
            "     */\n"
            f"    {constant_name}(CONST.{self.names.enum_field_name_constant(value.value, request.naming_profile)})"
        )

    def _schema_field_constants(self, request) -> str:
        """Generate documented constants for canonical schema field names."""
        rows = []
        for prop in request.definition.data_type.properties:
            rows.extend([
                "    /**",
                f"     * <strong>Field Name:</strong> {{@code {self._escape_html(prop.source_name)}}}" + ("<br/>" if prop.description else ""),
            ])
            if prop.description:
                rows.append(f"     * <strong>Field Description:</strong> {self._doc(prop.description, '')}")
            rows.extend([
                "     */",
                f"    public static final String {self.names.schema_field_name_constant(prop.source_name, request.naming_profile)} = {_java_quote(prop.source_name)};",
                "",
            ])
        return "\n".join(rows) + ("\n" if rows else "")

    @classmethod
    def _type_javadoc(cls, definition, parameter_docs=()) -> str:
        """Build the Javadoc block for one generated Java type."""
        description = cls._doc(definition.description, f"Generated representation of canonical definition {definition.logical_name}.")
        rows = ["/**", f" * {description}", " *", f" * <p>Generated from canonical definition {cls._escape(definition.identity)}/{definition.version}. Source: {cls._escape(definition.source_resource)}. Do not edit manually.</p>"]
        rows.extend(parameter_docs)
        rows.extend([" *", " * @author linhart1", " */"])
        return "\n".join(rows) + "\n"

    @staticmethod
    def _doc(value: str | None, fallback: str) -> str:
        """Normalize canonical documentation for a one-line Javadoc description."""
        return AIcJavaCodeGenerationBackend._escape_html(" ".join((value or fallback).split()))

    @staticmethod
    def _escape(value: str) -> str:
        """Escape the Javadoc terminator sequence."""
        return value.replace("*/", "* /")

    @staticmethod
    def _escape_html(value: str) -> str:
        """Escape canonical text embedded as ordinary HTML text in Javadoc."""
        return AIcJavaCodeGenerationBackend._escape(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
