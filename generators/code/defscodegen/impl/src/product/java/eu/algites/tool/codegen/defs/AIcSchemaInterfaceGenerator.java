package eu.algites.tool.codegen.defs;

import eu.algites.tool.codegen.defs.AInDefsNameRole;
import java.util.ArrayList;
import java.util.List;

/** Generates an interface contract and its concrete implementation from the same canonical object. */
public final class AIcSchemaInterfaceGenerator {
    private final AIcGenerationNames names = new AIcGenerationNames();

    /** The contract belongs to the interface artifact; the implementation belongs to its implementation artifact. */
    public record AIcdSources(AIcdGeneratedSource contract, AIcdGeneratedSource implementation) { }

    /** Render both native types without changing the existing standalone DTO API. */
    public AIcdSources generate(AIcdCodeGenerationRequest request) {
        if (request.definition().kind() == AInDefinitionKind.ENUM) {
            return new AIcdSources(new AIcDefaultDefsCodegenService().generate(request), null);
        }
        String interfaceName = names.typeName(request.definition(), request.namingProfile(), AInDefsNameRole.INTERFACE_TYPE);
        AIcdGeneratedSource dto = new AIcDefaultDefsCodegenService().generate(request);
        String contract;
        String implementation;
        String path = request.packageName().replace('.', '/') + "/";
        if (request.target() == AInCodeGenerationTarget.PYTHON) {
            String file = names.fileStem(request.definition(), request.namingProfile(), AInDefsNameRole.INTERFACE_TYPE_FILE_STEM);
            String marker = "@dataclass(frozen=True, slots=True)\nclass " + dto.typeName() + ":\n";
            int start = dto.source().indexOf(marker);
            if (start < 0) throw new IllegalStateException("Missing primary DTO declaration: " + dto.typeName());
            String body = dto.source().substring(start + marker.length());
            /* Reuse the backend's exact annotations and property documentation. */
            String fields = body.substring(0, body.indexOf("\n\n    def __post_init__"));
            fields = fields.replaceAll("(?m)^    ([a-zA-Z_][a-zA-Z0-9_]*: [^\\n]+?) = _AI_UNSET$", "    $1");
            fields = fields.replaceAll("(?m)^(    SCHEMA_FIELD_NAME__[A-Z0-9_]+) =", "$1: ClassVar[str] =");
            List<String> contractImports = new ArrayList<>();
            for (var property : request.definition().properties()) {
                var reference = property.reference();
                if (reference == null) continue;
                boolean isEnum = reference.targetKind() == AInDefinitionKind.ENUM;
                String concrete = names.referenceTypeName(reference.logicalName(), reference.version(), request.namingProfile(), isEnum ? AInDefsNameRole.ENUM_TYPE : AInDefsNameRole.DATA_TYPE);
                String abstractType = names.referenceTypeName(reference.logicalName(), reference.version(), request.namingProfile(), isEnum ? AInDefsNameRole.ENUM_TYPE : AInDefsNameRole.INTERFACE_TYPE);
                String abstractFile = names.referenceTypeName(reference.logicalName(), reference.version(), request.namingProfile(), isEnum ? AInDefsNameRole.ENUM_TYPE_FILE_STEM : AInDefsNameRole.INTERFACE_TYPE_FILE_STEM);
                fields = fields.replace(concrete, abstractType);
                contractImports.add("from ." + abstractFile + " import " + abstractType);
            }
            String helpers = "";
            if (fields.contains("AIcSchemaTemporalValue") || fields.contains("AIcSchemaDuration")) {
                helpers = dto.source().substring(dto.source().indexOf("from dataclasses import dataclass"), dto.source().indexOf("\ndef _ai_convert"));
            }
            StringBuilder metadata = new StringBuilder();
            metadata.append("    __data_object__ = AIcdDataObject(schema_id=")
                    .append(AIcScalarGeneration.jquote(request.definition().identity()))
                    .append(", schema_version=")
                    .append(request.definition().version() == null ? -1 : request.definition().version())
                    .append(", description=")
                    .append(AIcScalarGeneration.jquote(request.definition().description() == null ? "" : request.definition().description()))
                    .append(")\n    __data_object_fields__ = (\n");
            StringBuilder getters = new StringBuilder();
            for (AIcdPropertyDefinition property : request.definition().properties()) {
                String propertyName = pythonPropertyIdentifier(names.propertyName(property.sourceName(), request.namingProfile()));
                String suffix = Character.toUpperCase(propertyName.charAt(0)) + propertyName.substring(1);
                String getterName = "get" + suffix;
                metadata.append("        AIcdDataObjectField(name=")
                        .append(AIcScalarGeneration.jquote(property.sourceName()))
                        .append(", description=")
                        .append(AIcScalarGeneration.jquote(property.description() == null ? "" : property.description()))
                        .append(", presence_required=")
                        .append(property.required() ? "True" : "False")
                        .append(", allows_null=")
                        .append(property.nullable() ? "True" : "False")
                        .append(", getter_name=")
                        .append(AIcScalarGeneration.jquote(getterName))
                        .append("),\n");
                String returned = "";
                if (property.reference() != null && property.valueKind() == AInValueKind.REFERENCE
                        && property.reference().targetKind() != AInDefinitionKind.ENUM) {
                    var reference = property.reference();
                    returned = " -> " + names.referenceTypeName(reference.logicalName(), reference.version(),
                            request.namingProfile(), AInDefsNameRole.INTERFACE_TYPE)
                            + (property.nullable() ? " | None" : "");
                }
                getters.append("    def get").append(suffix).append("(self)").append(returned)
                        .append(":\n        return self.").append(propertyName).append("\n\n");
            }
            metadata.append("    )\n\n").append(getters);
            contract = "from __future__ import annotations\n\nfrom abc import ABC, abstractmethod\n"
                    + "from typing import Any, ClassVar, Mapping, TYPE_CHECKING\nfrom decimal import Decimal\n"
                    + "from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n"
                    + "from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n"
                    + "from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\n\n"
                    + helpers + String.join("\n", contractImports.stream().distinct().sorted().toList())
                    + "\n\nclass " + interfaceName + "(ABC, AIiDataObject):\n" + metadata + fields
                    + "\n\n    __slots__ = ()"
                    + "\n\n    @abstractmethod\n    def to_mapping(self) -> Mapping[str, object]:\n"
                    + "        \"\"\"Return canonical wire fields, omitting absent optional values.\"\"\"\n"
                    + "        raise NotImplementedError\n";
            /* The immutable field layout remains owned by the normal backend. */
            implementation = dto.source().replace(marker,
                    "from ." + file + " import " + interfaceName + "\n\n@dataclass(frozen=True, slots=True)\nclass "
                            + dto.typeName() + "(" + interfaceName + "):\n");
            if (!helpers.isEmpty()) {
                implementation = implementation.replace(helpers,
                        "from ." + file + " import AIcSchemaTemporalValue, AIcSchemaDuration\n"
                        + "from dataclasses import dataclass\nfrom decimal import Decimal\nimport base64\nimport re\nimport struct\n\n_AI_UNSET = object()\n");
            }
            return new AIcdSources(new AIcdGeneratedSource(interfaceName, path + file + ".py", contract,
                    List.of(AIcdGeneratedTypeIdentity.fromRequest(request, interfaceName, path + file + ".py", AInDefsNameRole.INTERFACE_TYPE))),
                    new AIcdGeneratedSource(dto.typeName(), dto.relativePath(), implementation, dto.generatedTypes()));
        }
        List<String> rows = new ArrayList<>();
        rows.add("package " + request.packageName() + ";\n\n/** Generated schema contract. Do not edit manually. */");
        rows.add("@eu.algites.lib.data.dataobject.AIaDataObject(schemaId = "
                + AIcScalarGeneration.jquote(request.definition().identity())
                + ", schemaVersion = " + (request.definition().version() == null ? -1 : request.definition().version())
                + ", description = " + AIcScalarGeneration.jquote(request.definition().description() == null ? "" : request.definition().description()) + ")");
        rows.add("public interface " + interfaceName + " extends eu.algites.lib.data.dataobject.AIiDataObject {");
        rows.add("    String CANONICAL_SOURCE_ID = " + AIcScalarGeneration.jquote(request.definition().identity()) + ";");
        rows.add("    Integer CANONICAL_SOURCE_VERSION = " + request.definition().version() + ";");
        rows.add("    String CANONICAL_SOURCE_RESOURCE = " + AIcScalarGeneration.jquote(request.definition().sourceResource()) + ";");
        for (AIcdPropertyDefinition property : request.definition().properties()) {
            String description = property.description() == null ? "Canonical field " + property.sourceName() + "." : property.description();
            description = description.replace("*/", "* /").replaceAll("\\s+", " ").replace("<", "&lt;").replace(">", "&gt;");
            String name = names.propertyName(property.sourceName(), request.namingProfile());
            if (JAVA_RESERVED.contains(name)) name += "_";
            rows.add("    /** <strong>Field Name:</strong> {@code " + property.sourceName().replace("*/", "* /") + "}. " + description + " */");
            rows.add("    String " + names.schemaFieldNameConstant(property.sourceName(), request.namingProfile()) + " = " + AIcScalarGeneration.jquote(property.sourceName()) + ";");
            rows.add("    /** " + description + " */");
            String propertyType = AIcScalarGeneration.javaType(property, request, names);
            if (property.reference() != null && property.reference().targetKind() != AInDefinitionKind.ENUM) {
                var reference = property.reference();
                String concrete = names.referenceTypeName(reference.logicalName(), reference.version(), request.namingProfile(), AInDefsNameRole.DATA_TYPE);
                String abstractType = names.referenceTypeName(reference.logicalName(), reference.version(), request.namingProfile(), AInDefsNameRole.INTERFACE_TYPE);
                propertyType = propertyType.replace(concrete, abstractType);
                if (property.valueKind() == AInValueKind.ARRAY) propertyType = propertyType.replace("<", "<? extends ");
            }
            rows.add("    @eu.algites.lib.data.dataobject.AIaDataObjectField(name = "
                    + AIcScalarGeneration.jquote(property.sourceName())
                    + ", description = " + AIcScalarGeneration.jquote(property.description() == null ? "" : property.description())
                    + ", presenceRequired = " + property.required() + ", allowsNull = " + property.nullable() + ")");
            rows.add("    " + propertyType + " " + name + "();");
        }
        rows.add("}");
        contract = String.join("\n", rows) + "\n";
        int recordEnd = dto.source().indexOf(") {\n");
        if (recordEnd < 0) throw new IllegalStateException("Missing record declaration: " + dto.typeName());
        implementation = dto.source().substring(0, recordEnd) + ") implements " + interfaceName + " {\n" + dto.source().substring(recordEnd + 4);
        return new AIcdSources(new AIcdGeneratedSource(interfaceName, path + interfaceName + ".java", contract,
                List.of(AIcdGeneratedTypeIdentity.fromRequest(request, interfaceName, path + interfaceName + ".java", AInDefsNameRole.INTERFACE_TYPE))),
                new AIcdGeneratedSource(dto.typeName(), dto.relativePath(), implementation, dto.generatedTypes()));
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
