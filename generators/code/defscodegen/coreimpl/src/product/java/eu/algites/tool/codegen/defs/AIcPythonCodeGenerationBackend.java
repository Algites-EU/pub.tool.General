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
        List<String> imports = new ArrayList<>();
        List<String> fields = new ArrayList<>();
        List<String> attributeDocs = new ArrayList<>();
        List<String> mappingArguments = new ArrayList<>();
        List<String> mappingEntries = new ArrayList<>();
        java.util.Set<String> usedNames = new java.util.HashSet<>();
        List<AIcdPropertyDefinition> orderedProperties = new ArrayList<>(request.definition().properties());
        orderedProperties.sort(java.util.Comparator.comparing(AIcdPropertyDefinition::required).reversed());
        for (AIcdPropertyDefinition property : orderedProperties) {
            String type = pythonType(property, request);
            if (property.reference() != null) {
                AInOutputNameKind typeKind = property.reference().targetKind() == AInDefinitionKind.ENUM
                        ? AInOutputNameKind.ENUM_TYPE : AInOutputNameKind.DATA_TYPE;
                AInOutputNameKind fileKind = property.reference().targetKind() == AInDefinitionKind.ENUM
                        ? AInOutputNameKind.ENUM_TYPE_FILE_STEM : AInOutputNameKind.DATA_TYPE_FILE_STEM;
                String refType = names.referenceTypeName(property.reference().logicalName(), property.reference().version(), request.namingProfile(), typeKind);
                String refFile = names.referenceTypeName(property.reference().logicalName(), property.reference().version(), request.namingProfile(), fileKind);
                imports.add("from ." + refFile + " import " + refType);
            }
            if (!property.required() && !type.contains("None")) type += " | None";
            String suffix = property.required() ? "" : " = None";
            String propertyName = pythonIdentifier(names.propertyName(property.sourceName(), request.namingProfile()));
            if (!usedNames.add(propertyName)) throw new IllegalArgumentException("Duplicate Python property name '" + propertyName + "' in " + request.definition().sourceResource());
            mappingArguments.add(propertyName + "=value.get(" + pythonQuote(property.sourceName()) + ")");
            mappingEntries.add(pythonQuote(property.sourceName()) + ": self." + propertyName);
            fields.add("    " + propertyName + ": " + type + suffix);
            attributeDocs.add(propertyName + ": " + pythonDocumentation(property.description(), "Value of canonical property " + property.sourceName() + "."));
        }
        if (fields.isEmpty()) fields.add("    pass");
        String referenceImports = imports.stream().distinct().sorted().collect(java.util.stream.Collectors.joining("\n"));
        if (!referenceImports.isEmpty()) referenceImports += "\n";
        return "from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom typing import Any, Mapping\n" +
                referenceImports + "\n" +
                "@dataclass(frozen=True, slots=True)\nclass " + typeName + ":\n" +
                pythonDocstring(request.definition(), attributeDocs, List.of()) +
                "    __canonical_source_id__ = " + pythonQuote(request.definition().identity()) + "\n" +
                "    __canonical_source_version__ = " + request.definition().version() + "\n" +
                "    __canonical_source_resource__ = " + pythonQuote(request.definition().sourceResource()) + "\n" +
                String.join("\n", fields) + "\n\n" +
                "    @classmethod\n    def from_mapping(cls, value: Mapping[str, object]):\n        return cls(" + String.join(", ", mappingArguments) + ")\n\n" +
                "    def to_mapping(self) -> Mapping[str, object]:\n        return {" + String.join(", ", mappingEntries) + "}\n";
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
