package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AInOutputNameKind;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/** Emits exact native scalar representations and portable basic validation. */
final class AIcScalarGeneration {
    private AIcScalarGeneration() { }
    private static final Set<String> TEMPORAL = Set.of("date", "time", "dateTime", "dateTimeStamp", "gYearMonth", "gYear", "gMonthDay", "gDay", "gMonth");
    private static final Set<String> DURATION = Set.of("duration", "yearMonthDuration", "dayTimeDuration");
    private static final Set<String> BINARY = Set.of("hexBinary", "base64Binary");
    static String scalar(AInValueKind aKind, AIcdValueConstraints aConstraints, boolean aJava) {
        String locType = aConstraints.dataType() == null ? "" : aConstraints.dataType();
        if (BINARY.contains(locType)) return aJava ? "byte[]" : "bytes";
        if (TEMPORAL.contains(locType)) return aJava ? "javax.xml.datatype.XMLGregorianCalendar" : "AIcSchemaTemporalValue";
        if (DURATION.contains(locType)) return aJava ? "javax.xml.datatype.Duration" : "AIcSchemaDuration";
        if (aKind == AInValueKind.INTEGER) return aJava ? "java.math.BigInteger" : "int";
        if (aKind == AInValueKind.NUMBER) {
            if (Set.of("float", "double").contains(locType)) return aJava ? ("float".equals(locType) ? "Float" : "Double") : "float";
            return aJava ? "java.math.BigDecimal" : "Decimal";
        }
        if (aKind == AInValueKind.STRING) return aJava ? "String" : "str";
        if (aKind == AInValueKind.BOOLEAN) return aJava ? "Boolean" : "bool";
        if (aKind == AInValueKind.OBJECT) return aJava ? "java.util.Map<String, Object>" : "Mapping[str, Any]";
        return aJava ? "Object" : "Any";
    }
    static String javaType(AIcdPropertyDefinition aProperty, AIcdCodeGenerationRequest aRequest, AIcGenerationNames aNames) {
        boolean locArray = aProperty.valueKind() == AInValueKind.ARRAY;
        String locItem = aProperty.reference() != null ? reference(aProperty, aRequest, aNames, false)
                : scalar(locArray ? aProperty.itemValueKind() : aProperty.valueKind(), locArray ? aProperty.itemConstraints() : aProperty.constraints(), true);
        return locArray ? "java.util.List<" + locItem + ">" : locItem;
    }
    static String javaValidation(AIcdPropertyDefinition aProperty, String aName) {
        StringBuilder locCode = new StringBuilder();
        if (aProperty.required() && !aProperty.nullable()) locCode.append("        java.util.Objects.requireNonNull(").append(aName).append(", ").append(jquote(aProperty.sourceName())).append(");\n");
        locCode.append("        if (").append(aName).append(" != null) {\n");
        if (aProperty.valueKind() == AInValueKind.ARRAY) {
            locCode.append("            for (var locItem : ").append(aName).append(") {\n                java.util.Objects.requireNonNull(locItem, \"Array item\");\n");
            locCode.append(javaFacets(aProperty.itemValueKind(), aProperty.itemConstraints(), "locItem", "                "));
            locCode.append("            }\n");
        } else locCode.append(javaFacets(aProperty.valueKind(), aProperty.constraints(), aName, "            "));
        locCode.append("        }\n");
        return locCode.toString();
    }
    private static String javaFacets(AInValueKind aKind, AIcdValueConstraints aConstraints, String aValue, String aIndent) {
        StringBuilder locCode = new StringBuilder();
        String locType = aConstraints.dataType() == null ? "" : aConstraints.dataType();
        if (TEMPORAL.contains(locType)) {
            String locExpected = "dateTimeStamp".equals(locType) ? "dateTime" : locType;
            locCode.append(check("!" + aValue + ".isValid() || !" + jquote(locExpected) + ".equals(" + aValue + ".getXMLSchemaType().getLocalPart())", aIndent));
            if ("dateTimeStamp".equals(locType)) locCode.append(check(aValue + ".getTimezone() == javax.xml.datatype.DatatypeConstants.FIELD_UNDEFINED", aIndent));
        }
        if (aConstraints.minimum() != null) locCode.append(check("new java.math.BigDecimal(" + aValue + ".toString()).compareTo(new java.math.BigDecimal(" + jquote(aConstraints.minimum()) + ")) " + (aConstraints.exclusiveMinimum() ? "<=" : "<") + " 0", aIndent));
        if (aConstraints.maximum() != null) locCode.append(check("new java.math.BigDecimal(" + aValue + ".toString()).compareTo(new java.math.BigDecimal(" + jquote(aConstraints.maximum()) + ")) " + (aConstraints.exclusiveMaximum() ? ">=" : ">") + " 0", aIndent));
        String locLength = BINARY.contains(locType) ? aValue + ".length" : aValue + ".codePointCount(0, " + aValue + ".length())";
        if (aConstraints.minLength() != null) locCode.append(check(locLength + " < " + aConstraints.minLength(), aIndent));
        if (aConstraints.maxLength() != null) locCode.append(check(locLength + " > " + aConstraints.maxLength(), aIndent));
        if (aConstraints.pattern() != null) locCode.append(check("!java.util.regex.Pattern.compile(" + jquote(aConstraints.pattern()) + ").matcher(" + aValue + ".toString()).find()", aIndent));
        if (!aConstraints.enumValues().isEmpty()) locCode.append(check("!java.util.List.of(" + String.join(", ", aConstraints.enumValues().stream().map(AIcScalarGeneration::jquote).toList()) + ").contains(" + aValue + ".toString())", aIndent));
        return locCode.toString();
    }
    private static String check(String aCondition, String aIndent) { return aIndent + "if (" + aCondition + ") throw new IllegalArgumentException(\"Schema value violates its constraints.\");\n"; }
    private static String reference(AIcdPropertyDefinition aProperty, AIcdCodeGenerationRequest aRequest, AIcGenerationNames aNames, boolean aFile) {
        boolean locEnum = aProperty.reference().targetKind() == AInDefinitionKind.ENUM;
        return aNames.referenceTypeName(aProperty.reference().logicalName(), aProperty.reference().version(), aRequest.namingProfile(),
                aFile ? (locEnum ? AInOutputNameKind.ENUM_TYPE_FILE_STEM : AInOutputNameKind.DATA_TYPE_FILE_STEM) : (locEnum ? AInOutputNameKind.ENUM_TYPE : AInOutputNameKind.DATA_TYPE));
    }
    static String pythonData(AIcdCodeGenerationRequest aRequest, String aTypeName, AIcGenerationNames aNames, java.util.function.Function<List<String>, String> aDocumentation) {
        List<String> locImports = new ArrayList<>(), locFields = new ArrayList<>(), locDocs = new ArrayList<>(), locArguments = new ArrayList<>(), locValidations = new ArrayList<>(), locEntries = new ArrayList<>(), locSchemaFieldConstants = new ArrayList<>();
        var locProperties = new ArrayList<>(aRequest.definition().properties());
        locProperties.sort(java.util.Comparator.comparing(AIcdPropertyDefinition::required).reversed());
        Set<String> locUsed = new java.util.HashSet<>();
        for (AIcdPropertyDefinition locProperty : locProperties) {
            String locName = aNames.propertyName(locProperty.sourceName(), aRequest.namingProfile()).replaceAll("[^a-zA-Z0-9_]", "_");
            if (locName.isEmpty() || Character.isDigit(locName.charAt(0))) locName = "_" + locName;
            if (Set.of("False", "None", "True", "and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield").contains(locName)) locName += "_";
            if (!locUsed.add(locName)) throw new IllegalArgumentException("Duplicate Python property name " + locName);
            boolean locArray = locProperty.valueKind() == AInValueKind.ARRAY;
            AInValueKind locKind = locArray ? locProperty.itemValueKind() : locProperty.valueKind();
            AIcdValueConstraints locConstraints = locArray ? locProperty.itemConstraints() : locProperty.constraints();
            String locRef = locProperty.reference() == null ? null : reference(locProperty, aRequest, aNames, false);
            if (locRef != null) locImports.add("from ." + reference(locProperty, aRequest, aNames, true) + " import " + locRef);
            String locType = locRef == null ? scalar(locKind, locConstraints, false) : locRef;
            if (locArray) locType = "tuple[" + locType + ", ...]";
            if (locProperty.nullable()) locType += " | None";
            locFields.add("    " + locName + ": " + locType + (locProperty.required() ? "" : " = _AI_UNSET"));
            locDocs.add(locName + ": " + (locProperty.description() == null ? "Value of canonical property " + locProperty.sourceName() + "." : locProperty.description()).strip().replaceAll("\\s+", " "));
            locSchemaFieldConstants.add(pythonSchemaFieldConstant(locProperty, aRequest, aNames));
            String locRaw = locProperty.required() ? "value[" + pyquote(locProperty.sourceName()) + "]" : "value.get(" + pyquote(locProperty.sourceName()) + ", _AI_UNSET)";
            String locConvert = pythonConvert(locProperty, locArray ? "item" : locRaw, locKind, locConstraints, locRef);
            if (locArray) locConvert = "tuple(" + locConvert + " for item in " + locRaw + ")";
            locArguments.add(locName + "=(" + locRaw + " if " + locRaw + " is _AI_UNSET or " + locRaw + " is None else " + locConvert + ")");
            locValidations.add("        if self." + locName + " is not _AI_UNSET:");
            locValidations.add("            if self." + locName + " is None:");
            locValidations.add("                " + (locProperty.nullable() ? "pass" : "raise ValueError(" + pyquote(locProperty.sourceName()) + " + \": null is not permitted\")"));
            locValidations.add("            else:");
            String locValue = "self." + locName, locIndent = "                ";
            if (locArray) {
                locValidations.add("                if not isinstance(self." + locName + ", (tuple, list)): raise TypeError(" + pyquote(locProperty.sourceName()) + " + \": expected collection\")");
                locValidations.add("                for item in self." + locName + ":");
                locValue = "item"; locIndent = "                    ";
            }
            locValidations.add(locIndent + (locRef == null ? "_ai_validate(" + locValue + ", " + pyquote(locKind == null ? "ANY" : locKind.name()) + ", " + pythonConstraints(locConstraints) + ", " + pyquote(locProperty.sourceName()) + ")"
                    : "if not isinstance(" + locValue + ", " + locRef + "): raise TypeError(" + pyquote(locProperty.sourceName()) + " + \": incorrect referenced type\")"));
            if (locProperty.required()) locValidations.add("        else: raise ValueError(" + pyquote(locProperty.sourceName()) + " + \": value is required\")");
            locEntries.add("            " + pyquote(locProperty.sourceName()) + ": _ai_wire(self." + locName + ", " + pyquote(locConstraints.dataType()) + "),");
        }
        String locRuntime;
        try (var locStream = AIcScalarGeneration.class.getResourceAsStream("schema-python-runtime.py")) {
            if (locStream == null) throw new IllegalStateException("Missing embedded Python schema runtime.");
            locRuntime = new String(locStream.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException locFailure) { throw new IllegalStateException("Cannot load embedded Python schema runtime.", locFailure); }
        return "from __future__ import annotations\n\nfrom typing import Any, Mapping\n" + locRuntime + "\n" + String.join("\n", locImports.stream().distinct().sorted().toList()) + "\n\n"
                + "@dataclass(frozen=True, slots=True)\nclass " + aTypeName + ":\n" + aDocumentation.apply(locDocs)
                + "    __canonical_source_id__ = " + pyquote(aRequest.definition().identity()) + "\n    __canonical_source_version__ = " + aRequest.definition().version() + "\n    __canonical_source_resource__ = " + pyquote(aRequest.definition().sourceResource()) + "\n\n"
                + String.join("\n", locSchemaFieldConstants) + (locSchemaFieldConstants.isEmpty() ? "" : "\n\n")
                + String.join("\n", locFields.isEmpty() ? List.of("    pass") : locFields)
                + "\n\n    def __post_init__(self):\n" + String.join("\n", locValidations.isEmpty() ? List.of("        pass") : locValidations)
                + "\n\n    @classmethod\n    def from_mapping(cls, value: Mapping[str, object]):\n        return cls(" + String.join(", ", locArguments) + ")\n"
                + "\n    def to_mapping(self) -> Mapping[str, object]:\n        return {key: value for key, value in {\n" + String.join("\n", locEntries) + "\n        }.items() if value is not _AI_UNSET}\n";
    }
    private static String pythonSchemaFieldConstant(AIcdPropertyDefinition aProperty, AIcdCodeGenerationRequest aRequest, AIcGenerationNames aNames) {
        StringBuilder locResult = new StringBuilder();
        locResult.append("    ").append(aNames.schemaFieldNameConstant(aProperty.sourceName(), aRequest.namingProfile()))
                .append(" = ").append(pyquote(aProperty.sourceName())).append("\n");
        locResult.append("    \"\"\"**Field Name:** ``").append(pythonDocText(aProperty.sourceName())).append("``");
        if (aProperty.description() != null && !aProperty.description().isBlank()) {
            locResult.append("\n\n    **Field Description:** ")
                    .append(pythonDocText(aProperty.description().strip().replaceAll("\\s+", " ")));
        }
        locResult.append("\"\"\"");
        return locResult.toString();
    }

    private static String pythonDocText(String aValue) {
        return aValue.replace("\\", "\\\\").replace("\"\"\"", "\\\"\\\"\\\"");
    }

    private static String pythonConvert(AIcdPropertyDefinition aProperty, String aValue, AInValueKind aKind, AIcdValueConstraints aConstraints, String aRef) {
        if (aRef != null) return "(" + aValue + " if isinstance(" + aValue + ", " + aRef + ") else " + aRef + (aProperty.reference().targetKind() == AInDefinitionKind.ENUM ? "(" : ".from_mapping(") + aValue + "))";
        return "_ai_convert(" + aValue + ", " + pyquote(aConstraints.dataType()) + ", " + pyquote(aKind == null ? "ANY" : aKind.name()) + ")";
    }
    private static String pythonConstraints(AIcdValueConstraints aValue) {
        return "(" + pyquote(aValue.dataType()) + ", " + pyquote(aValue.minimum()) + ", " + pyquote(aValue.maximum()) + ", " + (aValue.exclusiveMinimum() ? "True" : "False") + ", " + (aValue.exclusiveMaximum() ? "True" : "False")
                + ", " + (aValue.minLength() == null ? "None" : aValue.minLength()) + ", " + (aValue.maxLength() == null ? "None" : aValue.maxLength()) + ", " + pyquote(aValue.pattern()) + ", (" + String.join(", ", aValue.enumValues().stream().map(AIcScalarGeneration::pyquote).toList()) + (aValue.enumValues().isEmpty() ? "" : ",") + "))";
    }
    private static String jquote(String aValue) { return "\"" + aValue.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r") + "\""; }
    private static String pyquote(String aValue) { return aValue == null ? "None" : jquote(aValue); }
}
