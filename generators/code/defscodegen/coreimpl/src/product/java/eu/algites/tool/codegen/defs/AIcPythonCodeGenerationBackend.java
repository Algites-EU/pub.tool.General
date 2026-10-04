package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AInOutputNameKind;

import java.util.ArrayList;
import java.util.List;

/** Generates Python dataclasses and enums from normalized canonical definitions. */
public final class AIcPythonCodeGenerationBackend implements AIiCodeGenerationBackend {
    /** Creates the default Python code-generation backend. */
    public AIcPythonCodeGenerationBackend() {
    }
    private final AIcGenerationNames names = new AIcGenerationNames();

    /**
     * Returns the target technology handled by this backend.
     *
     * @return the Python target
     */
    @Override
    public AInCodeGenerationTarget target() {
        return AInCodeGenerationTarget.PYTHON;
    }

    /**
     * Generates one Python module from a canonical definition.
     *
     * @param request normalized definition and output policy
     * @return generated Python source
     */
    @Override
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest request) {
        boolean enumDefinition = request.definition().kind() == AInDefinitionKind.ENUM;
        String typeName = names.typeName(request.definition(), request.namingProfile(), enumDefinition ? AInOutputNameKind.ENUM_TYPE : AInOutputNameKind.DATA_TYPE);
        String source = enumDefinition ? enumSource(request, typeName) : dataSource(request, typeName);
        String fileStem = names.fileStem(request.definition(), request.namingProfile(), enumDefinition ? AInOutputNameKind.ENUM_TYPE_FILE_STEM : AInOutputNameKind.DATA_TYPE_FILE_STEM);
        String relative = request.packageName().replace('.', '/') + "/" + fileStem + ".py";
        return new AIcdGeneratedSource(typeName, relative, source);
    }

    /**
     * Generates a Python string enum preserving canonical serialized values.
     *
     * @param request generation request
     * @param typeName generated enum name
     * @return complete Python module source
     */
    private String enumSource(AIcdCodeGenerationRequest request, String typeName) {
        List<String> constants = request.definition().enumValues().stream()
                .map(value -> "    " + names.enumConstant(value.value(), request.namingProfile()) + " = " + pythonQuote(value.value())).toList();
        List<String> valueDocs = request.definition().enumValues().stream()
                .map(value -> names.enumConstant(value.value(), request.namingProfile()) + ": " + pythonDocumentation(value.description(), "Canonical enum value " + value.value() + "."))
                .toList();
        return "from enum import Enum\n\n\nclass " + typeName + "(str, Enum):\n" +
                pythonDocstring(request.definition(), List.of(), valueDocs) +
                "    __canonical_source_id__ = " + pythonQuote(request.definition().identity()) + "\n" +
                "    __canonical_source_version__ = " + request.definition().version() + "\n" +
                "    __canonical_source_resource__ = " + pythonQuote(request.definition().sourceResource()) + "\n" +
                String.join("\n", constants) + "\n";
    }

    /**
     * Generates a Python dataclass and carries property descriptions into its Attributes documentation.
     *
     * @param request generation request
     * @param typeName generated dataclass name
     * @return complete Python module source
     */
    private String dataSource(AIcdCodeGenerationRequest request, String typeName) {
        return AIcScalarGeneration.pythonData(request, typeName, names,
                docs -> pythonDocstring(request.definition(), docs, List.of()));
    }

    /** Projects a canonical field onto a legal Python identifier while preserving its separate wire key. */
    private static String pythonIdentifier(String name) {
        String result = name.replaceAll("[^a-zA-Z0-9_]", "_");
        if (result.isEmpty() || Character.isDigit(result.charAt(0))) result = "_" + result;
        if (java.util.Set.of("False", "None", "True", "and", "as", "assert", "async", "await", "break", "class", "continue",
                "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda",
                "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield").contains(result)) result += "_";
        return result;
    }

    /**
     * Builds the generated Python type docstring.
     *
     * @param definition canonical definition
     * @param attributeDocs optional attribute documentation entries
     * @param valueDocs optional enum-value documentation entries
     * @return indented Python docstring
     */
    private static String pythonDocstring(AIcdCanonicalDefinition definition, List<String> attributeDocs, List<String> valueDocs) {
        StringBuilder result = new StringBuilder();
        result.append("    \"\"\"").append(pythonDocumentation(definition.description(), "Generated representation of canonical definition " + definition.logicalName() + "."));
        result.append("\n\n    Generated from canonical definition ").append(definition.identity()).append('/').append(definition.version());
        result.append(". Source: ").append(definition.sourceResource()).append(". Do not edit manually.");
        if (!attributeDocs.isEmpty()) {
            result.append("\n\n    Attributes:\n");
            for (String attributeDoc : attributeDocs) result.append("        ").append(attributeDoc).append('\n');
            result.append("    ");
        }
        if (!valueDocs.isEmpty()) {
            result.append("\n\n    Values:\n");
            for (String valueDoc : valueDocs) result.append("        ").append(valueDoc).append('\n');
            result.append("    ");
        }
        result.append("\"\"\"\n");
        return result.toString();
    }

    /**
     * Maps one normalized property to its Python type annotation.
     *
     * @param property normalized property
     * @param request generation request
     * @return Python type annotation
     */
    private String pythonType(AIcdPropertyDefinition property, AIcdCodeGenerationRequest request) {
        if (property.reference() != null) return names.referenceTypeName(property.reference().logicalName(), property.reference().version(), request.namingProfile(), property.reference().targetKind() == AInDefinitionKind.ENUM ? AInOutputNameKind.ENUM_TYPE : AInOutputNameKind.DATA_TYPE);
        return switch (property.valueKind()) {
            case STRING -> "str";
            case INTEGER -> "int";
            case NUMBER -> "float";
            case BOOLEAN -> "bool";
            case ARRAY -> "tuple[" + scalarPythonType(property.itemValueKind()) + ", ...]";
            case OBJECT -> "Mapping[str, Any]";
            default -> "Any";
        };
    }

    /**
     * Maps an array item kind to a scalar Python type annotation.
     *
     * @param kind normalized item kind
     * @return Python scalar type annotation
     */
    private static String scalarPythonType(AInValueKind kind) {
        if (kind == null) return "Any";
        return switch (kind) {
            case STRING -> "str";
            case INTEGER -> "int";
            case NUMBER -> "float";
            case BOOLEAN -> "bool";
            default -> "Any";
        };
    }

    /**
     * Normalizes documentation text for a Python docstring.
     *
     * @param value canonical description
     * @param fallback fallback description
     * @return one-line docstring-safe description
     */
    private static String pythonDocumentation(String value, String fallback) {
        String selected = value == null || value.isBlank() ? fallback : value.strip();
        return selected.replace("\"\"\"", "\\\"\\\"\\\"").replaceAll("\\s+", " ");
    }

    /**
     * Quotes one Python string literal.
     *
     * @param value raw string value
     * @return quoted Python literal
     */
    private static String pythonQuote(String value) {
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'";
    }
}
