package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdGeneratedSource;
import eu.algites.tool.codegen.defs.AIcdGeneratedTypeIdentity;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import java.util.ArrayList;
import java.util.List;

/** Generate annotated read-only contracts directly from canonical definitions. */
public final class AIcSchemaContractInterfaceGenerator {
    private final AIcGenerationNames names = new AIcGenerationNames();

    /** Generate a read-only contract, optionally inheriting from an existing contract. */
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest aRequest, String aParentType, String aParentModule) {
        AIcdGeneratedSource locBase = generate(aRequest);
        if (aParentType == null) return locBase;
        if (aRequest.definition().dataType().kind() != AInDataTypeKind.OBJECT) {
            throw new IllegalArgumentException("Only object contracts can inherit");
        }
        String locSource = locBase.source();
        if (aRequest.target() == AInCodeGenerationTarget.PYTHON) {
            String locDeclaration = "class " + locBase.typeName() + "("
                    + AIcPythonSchemaContractRenderer.baseType(aRequest.definition().sourceKind()) + ", ABC):";
            if (!locSource.contains(locDeclaration)) throw new IllegalStateException("Cannot locate Python contract");
            locSource = locSource.replace(locDeclaration, "class " + locBase.typeName() + "(" + aParentType + "):");
            locSource = locSource.replace("from __future__ import annotations\n",
                    "from __future__ import annotations\nfrom " + aParentModule + " import " + aParentType + "\n");
        } else {
            String locDeclaration = "public interface " + locBase.typeName()
                    + " extends " + dataObjectParent(aRequest.definition().sourceKind()) + " {";
            if (!locSource.contains(locDeclaration)) throw new IllegalStateException("Cannot locate Java contract");
            locSource = locSource.replace(locDeclaration,
                    "public interface " + locBase.typeName() + " extends " + aParentModule + "." + aParentType + " {");
        }
        return new AIcdGeneratedSource(locBase.typeName(), locBase.relativePath(), locSource, locBase.generatedTypes());
    }

    /** Render all compilation units, including explicit closed-choice wrapper records. */
    public List<AIcdGeneratedSource> generateSources(AIcdCodeGenerationRequest aRequest,
            String aParentType, String aParentModule) {
        if (aRequest.definition().dataType().kind() == AInDataTypeKind.ONE_OF
                || aRequest.definition().dataType().kind() == AInDataTypeKind.ANY_OF) {
            if (aParentType != null) throw new IllegalArgumentException("Closed choice cannot inherit");
            return new AIcClosedChoiceGenerator().generate(aRequest);
        }
        return List.of(generate(aRequest, aParentType, aParentModule));
    }

    /** Render only an AIig read contract or a shared AIng enum; never render a DTO. */
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest aRequest) {
        if (aRequest.definition().dataType().kind() == AInDataTypeKind.ONE_OF
                || aRequest.definition().dataType().kind() == AInDataTypeKind.ANY_OF) {
            return new AIcClosedChoiceGenerator().generate(aRequest).get(0);
        }
        if (aRequest.definition().dataType().kind() == AInDataTypeKind.ENUM) {
            return new AIcDefaultDefsCodegenService().generate(aRequest);
        }
        String interfaceName = names.typeName(aRequest.definition(), aRequest.namingProfile(), AInDefsNameRole.INTERFACE_TYPE);
        if (aRequest.target() == AInCodeGenerationTarget.PYTHON) {
            return new AIcPythonSchemaContractRenderer().generate(aRequest);
        }
        String path = aRequest.packageName().replace('.', '/') + "/";
        List<String> rows = new ArrayList<>();
        rows.add("package " + aRequest.packageName() + ";\n\n/** Generated schema contract. Do not edit manually. */");
        rows.add("@eu.algites.lib.data.dataobject.AIaDataObject(schemaId = "
                + AIcScalarGeneration.jquote(aRequest.definition().identity())
                + ", schemaVersion = " + (aRequest.definition().version() == null ? -1 : aRequest.definition().version())
                + ", title = " + AIcScalarGeneration.jquote(visibleTitle(aRequest.definition().title(), aRequest.definition().logicalName()))
                + ", description = " + AIcScalarGeneration.jquote(aRequest.definition().description() == null ? "" : aRequest.definition().description()) + ")");
        if (aRequest.xmlTypeQName() != null) {
            String locQName = aRequest.xmlTypeQName();
            int locDelimiter = locQName.indexOf('}');
            rows.add("@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject("
                    + "definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, "
                    + "namespace = " + AIcScalarGeneration.jquote(locQName.substring(1, locDelimiter))
                    + ", namespaceLocalName = " + AIcScalarGeneration.jquote(locQName.substring(locDelimiter + 1)) + ")");
        }
        rows.add("public interface " + interfaceName + " extends " + dataObjectParent(aRequest.definition().sourceKind()) + " {");
        rows.add("    /** Canonical schema ID independent of any representation-specific publication URL. */");
        rows.add("    String CANONICAL_SOURCE_ID = " + AIcScalarGeneration.jquote(aRequest.definition().identity()) + ";");
        rows.add("    /** Version identifying the canonical schema definition. */");
        rows.add("    Integer CANONICAL_SOURCE_VERSION = " + aRequest.definition().version() + ";");
        rows.add("    /** Definition source resource retained for provenance and diagnostics. */");
        rows.add("    String CANONICAL_SOURCE_RESOURCE = " + AIcScalarGeneration.jquote(aRequest.definition().sourceResource()) + ";");
        int locXmlOrder = 0;
        for (AIcdPropertyDefinition property : aRequest.definition().dataType().properties()) {
            String description = property.description() == null ? "Canonical field " + property.sourceName() + "." : property.description();
            description = description.replace("*/", "* /").replaceAll("\\s+", " ").replace("<", "&lt;").replace(">", "&gt;");
            String name = names.propertyName(property.sourceName(), aRequest.namingProfile());
            if (JAVA_RESERVED.contains(name)) name += "_";
            rows.add("    /** <strong>Field Name:</strong> {@code " + property.sourceName().replace("*/", "* /") + "}. " + description + " */");
            rows.add("    String " + names.schemaFieldNameConstant(property.sourceName(), aRequest.namingProfile()) + " = " + AIcScalarGeneration.jquote(property.sourceName()) + ";");
            rows.add("    /** " + description + " */");
            String propertyType = AIcRecursiveContractType.render(property, aRequest, names,
                    true, java.util.Set.of());
            rows.add(fieldLabelAnnotation(property));
            rows.add("    @eu.algites.lib.data.dataobject.AIaDataObjectField(fieldName = "
                    + AIcScalarGeneration.jquote(property.sourceName())
                    + ", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind." + property.presence().name() + ", allowsNull = " + property.nullable() + ")");
            if (property.xmlField() != null) {
                var locXml = property.xmlField();
                rows.add("    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField(namespace = "
                        + AIcScalarGeneration.jquote(locXml.namespace()) + ", namespaceLocalName = "
                        + AIcScalarGeneration.jquote(locXml.namespaceLocalName())
                        + ", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind."
                         + locXml.valueKind().name() + ", order = " + locXmlOrder
                        + ", minOccurs = " + locXml.minOccurs()
                        + ", maxOccurs = " + locXml.maxOccurs() + ")");
            }
            rows.add("    " + propertyType + " " + name + "();");
            locXmlOrder++;
        }
        rows.add("}");
        String contract = String.join("\n", rows) + "\n";
        return new AIcdGeneratedSource(interfaceName, path + interfaceName + ".java", contract,
                List.of(AIcdGeneratedTypeIdentity.fromRequest(aRequest, interfaceName,
                    path + interfaceName + ".java", AInDefsNameRole.INTERFACE_TYPE)));
    }

    /**
     * Selects the source-technology marker rather than the untyped shared DataObject marker.
     * A generated schema contract retains its technology throughout read and mutable inheritance.
     *
     * @param aKind canonical source schema format
     * @return qualified parent interface of the corresponding technology
     */
    static String dataObjectParent(eu.algites.tool.codegen.defs.AInDefinitionSourceKind aKind) {
        return switch (aKind) {
            case XMLDEFS -> "eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject";
            case YAMLDEFS -> "eu.algites.lib.data.dataobject.yamldefs.AIiYamlDataObject";
            case JSONDEFS -> "eu.algites.lib.data.dataobject.jsondefs.AIiJsonDataObject";
        };
    }

    /** Use schema titles as fallbacks, never as resource identifiers. */
    private static String visibleTitle(String aTitle, String aName) {
        if (aTitle != null && !aTitle.isBlank()) return aTitle;
        String locWords = aName.replaceAll("([A-Z]+)([A-Z][a-z])", "$1 $2")
                .replaceAll("([a-z0-9])([A-Z])", "$1 $2").replace('_', ' ').replace('-', ' ')
                .trim().replaceAll("\\s+", " ");
        return locWords.isEmpty() ? aName : Character.toUpperCase(locWords.charAt(0)) + locWords.substring(1);
    }

    /** Emit a role-aware label; resolution source remains configurable outside Defs Codegen. */
    private static String fieldLabelAnnotation(AIcdPropertyDefinition aProperty) {
        String locTitle = visibleTitle(aProperty.title(), aProperty.sourceName());
        String locDescription = aProperty.description();
        String locEntry = locDescription == null || locDescription.isBlank() ? "" :
                ", labels = {@eu.algites.lib.common.object.props.labels.AIaFieldLabel.Entry(roleCode = "
                + "eu.algites.lib.common.object.props.labels.AIaFieldLabel.FIELD_DESCRIPTION" + ", label = "
                + AIcScalarGeneration.jquote(locDescription) + ")}";
        return "    @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "
                + AIcScalarGeneration.jquote(locTitle) + locEntry + ")";
    }

    /** Match the Python generator's normalization of field identifiers. */
    private static String pythonPropertyIdentifier(String name) {
        String result = name.replaceAll("[^a-zA-Z0-9_]", "_");
        if (result.isEmpty() || Character.isDigit(result.charAt(0))) result = "_" + result;
        if (PYTHON_RESERVED.contains(result)) result += "_";
        return result;
    }

    private static final java.util.Set<String> PYTHON_RESERVED = java.util.Set.of(
        "False", "None", "True", "and", "as", "assert", "async", "await", "break", "class", "continue",
        "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import",
        "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while",
        "with", "yield");

    private static final java.util.Set<String> JAVA_RESERVED = java.util.Set.of(
        "class", "interface", "enum", "default", "new", "return", "package", "private", "public", "protected",
        "static", "final", "void", "int", "long", "double", "float", "boolean", "char", "byte", "short", "null",
        "true", "false", "record", "var", "yield", "switch", "case", "if", "else", "for", "while", "do", "try",
        "catch", "finally", "throw", "throws", "extends", "implements", "abstract", "this", "super", "const", "goto",
        "instanceof", "native", "synchronized", "transient", "volatile", "strictfp", "assert", "break", "continue",
        "import", "sealed", "permits", "_", "clone", "finalize", "getClass", "hashCode", "notify", "notifyAll", "toString", "wait");
}
