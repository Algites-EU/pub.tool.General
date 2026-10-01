package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AInOutputNameKind;

import java.util.ArrayList;
import java.util.List;

/** Generates Java records and enums from normalized canonical definitions. */
public final class AIcJavaCodeGenerationBackend implements AIiCodeGenerationBackend {
    /** Creates the default Java code-generation backend. */
    public AIcJavaCodeGenerationBackend() {
    }
    private final AIcGenerationNames names = new AIcGenerationNames();

    /**
     * Returns the target technology handled by this backend.
     *
     * @return the Java target
     */
    @Override
    public AInCodeGenerationTarget target() {
        return AInCodeGenerationTarget.JAVA;
    }

    /**
     * Generates one Java source file from a canonical definition.
     *
     * @param request normalized definition and output policy
     * @return generated Java source
     */
    @Override
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest request) {
        boolean enumDefinition = request.definition().kind() == AInDefinitionKind.ENUM;
        String typeName = names.typeName(request.definition(), request.namingProfile(), enumDefinition ? AInOutputNameKind.ENUM_TYPE : AInOutputNameKind.DATA_TYPE);
        String source = enumDefinition ? enumSource(request, typeName) : dataSource(request, typeName);
        String relative = request.packageName().replace('.', '/') + "/" + typeName + ".java";
        return new AIcdGeneratedSource(typeName, relative, source);
    }

    /**
     * Generates a Java enum preserving each canonical serialized value.
     *
     * @param request generation request
     * @param typeName generated enum name
     * @return complete Java source
     */
    private String enumSource(AIcdCodeGenerationRequest request, String typeName) {
        List<String> constants = request.definition().enumValues().stream()
                .map(value -> names.enumConstant(value, request.namingProfile()) + "(" + quote(value) + ")")
                .toList();
        return "package " + request.packageName() + ";\n\n" +
                typeJavadoc(request.definition(), List.of()) +
                "public enum " + typeName + " {\n    " + String.join(",\n    ", constants) + ";\n\n" +
                "    public static final String CANONICAL_SOURCE_ID = " + quote(request.definition().identity()) + ";\n" +
                "    public static final Integer CANONICAL_SOURCE_VERSION = " + request.definition().version() + ";\n" +
                "    public static final String CANONICAL_SOURCE_RESOURCE = " + quote(request.definition().sourceResource()) + ";\n\n" +
                "    private final String wireValue;\n\n" +
                "    " + typeName + "(String aWireValue) {\n        wireValue = aWireValue;\n    }\n\n" +
                "    /**\n" +
                "     * Returns the exact serialized value declared by the canonical definition.\n" +
                "     *\n" +
                "     * @return canonical wire value\n" +
                "     */\n" +
                "    public String wireValue() {\n        return wireValue;\n    }\n" +
                "}\n";
    }

    /**
     * Generates a Java record and documents its record components from source property descriptions.
     *
     * @param request generation request
     * @param typeName generated record name
     * @return complete Java source
     */
    private String dataSource(AIcdCodeGenerationRequest request, String typeName) {
        List<String> components = new ArrayList<>();
        List<String> parameterDocs = new ArrayList<>();
        for (AIcdPropertyDefinition property : request.definition().properties()) {
            String propertyName = names.propertyName(property.sourceName(), request.namingProfile());
            components.add(javaType(property, request) + " " + propertyName);
            parameterDocs.add(" * @param " + propertyName + " " + documentation(property.description(), "Value of canonical property " + property.sourceName() + "."));
        }
        return "package " + request.packageName() + ";\n\n" +
                typeJavadoc(request.definition(), parameterDocs) +
                "public record " + typeName + "(\n        " + String.join(",\n        ", components) + ") {\n" +
                "    public static final String CANONICAL_SOURCE_ID = " + quote(request.definition().identity()) + ";\n" +
                "    public static final Integer CANONICAL_SOURCE_VERSION = " + request.definition().version() + ";\n" +
                "    public static final String CANONICAL_SOURCE_RESOURCE = " + quote(request.definition().sourceResource()) + ";\n" +
                "}\n";
    }

    /**
     * Builds Javadoc shared by generated records and enums.
     *
     * @param definition canonical definition
     * @param parameterDocs optional record-component documentation lines
     * @return complete Javadoc block
     */
    private static String typeJavadoc(AIcdCanonicalDefinition definition, List<String> parameterDocs) {
        StringBuilder result = new StringBuilder();
        result.append("/**\n * ").append(documentation(definition.description(), "Generated representation of canonical definition " + definition.logicalName() + "."));
        result.append("\n *\n * <p>Generated from canonical definition ").append(escapeJavadoc(definition.identity())).append('/').append(definition.version());
        result.append(". Source: ").append(escapeJavadoc(definition.sourceResource())).append(". Do not edit manually.</p>\n");
        for (String parameterDoc : parameterDocs) result.append(parameterDoc).append('\n');
        result.append(" */\n");
        return result.toString();
    }

    /**
     * Maps one normalized property to its Java type.
     *
     * @param property normalized property
     * @param request generation request
     * @return Java source type
     */
    private String javaType(AIcdPropertyDefinition property, AIcdCodeGenerationRequest request) {
        if (property.reference() != null) return names.referenceTypeName(property.reference().logicalName(), property.reference().version(), request.namingProfile(), property.reference().targetKind() == AInDefinitionKind.ENUM ? AInOutputNameKind.ENUM_TYPE : AInOutputNameKind.DATA_TYPE);
        return switch (property.valueKind()) {
            case STRING -> "String";
            case INTEGER -> "Long";
            case NUMBER -> "Double";
            case BOOLEAN -> "Boolean";
            case ARRAY -> "java.util.List<" + scalarJavaType(property.itemValueKind()) + ">";
            case OBJECT -> "java.util.Map<String, Object>";
            default -> "Object";
        };
    }

    /**
     * Maps an array item kind to a scalar Java type.
     *
     * @param kind normalized item kind
     * @return Java scalar type
     */
    private static String scalarJavaType(AInValueKind kind) {
        if (kind == null) return "Object";
        return switch (kind) {
            case STRING -> "String";
            case INTEGER -> "Long";
            case NUMBER -> "Double";
            case BOOLEAN -> "Boolean";
            default -> "Object";
        };
    }

    /**
     * Selects and normalizes documentation text for generated source.
     *
     * @param value canonical description
     * @param fallback fallback description
     * @return safe one-line documentation text
     */
    private static String documentation(String value, String fallback) {
        String selected = value == null || value.isBlank() ? fallback : value.strip();
        return escapeJavadoc(selected.replaceAll("\\s+", " "));
    }

    /**
     * Escapes the Javadoc terminator sequence.
     *
     * @param value source documentation text
     * @return Javadoc-safe text
     */
    private static String escapeJavadoc(String value) {
        return value.replace("*/", "* /");
    }

    /**
     * Quotes one Java string literal.
     *
     * @param value raw string value
     * @return quoted Java literal
     */
    private static String quote(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }
}
