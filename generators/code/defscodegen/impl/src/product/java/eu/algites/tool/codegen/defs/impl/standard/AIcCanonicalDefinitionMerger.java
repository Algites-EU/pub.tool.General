package eu.algites.tool.codegen.defs.impl.standard;


import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdDefinitionReference;
import eu.algites.tool.codegen.defs.AIcdEnumValueDefinition;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import java.util.List;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.nio.file.Path;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.net.URI;
import java.util.Objects;
import java.util.stream.Collectors;

/** Combines compatible serialization representations without discarding their documentation or provenance. */
public final class AIcCanonicalDefinitionMerger {
    private AIcCanonicalDefinitionMerger() { }

    /**
     * Merges representations of one logical type and rejects incompatible contracts.
     * The first representation supplies the primary canonical identity; all origins remain documented.
     *
     * @param aDefinitions representations in deterministic primary-first order
     * @return one compatible canonical definition
     */
    public static AIcdCanonicalDefinition AIcMerge(List<AIcdCanonicalDefinition> aDefinitions) {
        if (aDefinitions.isEmpty()) throw new IllegalArgumentException("No canonical definitions to merge.");
        AIcValidate(aDefinitions, false, Path.of("").toAbsolutePath());
        AIcdCanonicalDefinition locFirst = aDefinitions.get(0);
        if (aDefinitions.size() == 1) return locFirst;
        List<AIcdPropertyDefinition> locProperties = locFirst.dataType().properties().stream().map(aProperty ->
                new AIcdPropertyDefinition(aProperty.sourceName(), AIcNormalizedMergedPropertyType(aProperty, aDefinitions), aProperty.presence(), aProperty.nullable(), AIcDocumentation(aDefinitions.stream().flatMap(aDefinition -> aDefinition.dataType().properties().stream())
                                .filter(aCandidate -> aCandidate.sourceName().equals(aProperty.sourceName()))
                                .map(AIcdPropertyDefinition::description).toList()), AIcFirstTitle(aProperty.title(), aDefinitions.stream().flatMap(aDefinition -> aDefinition.dataType().properties().stream())
                                .filter(aCandidate -> aCandidate.sourceName().equals(aProperty.sourceName()))
                                .map(AIcdPropertyDefinition::title).toList()), aProperty.xmlField())).toList();
        List<AIcdEnumValueDefinition> locValues = locFirst.enumValues().stream().map(aValue ->
                new AIcdEnumValueDefinition(aValue.value(), AIcDocumentation(aDefinitions.stream()
                        .flatMap(aDefinition -> aDefinition.enumValues().stream())
                        .filter(aCandidate -> aCandidate.value().equals(aValue.value()))
                        .map(AIcdEnumValueDefinition::description).toList()),
                        AIcFirstTitle(aValue.title(), aDefinitions.stream().flatMap(aDefinition -> aDefinition.enumValues().stream())
                                .filter(aCandidate -> aCandidate.value().equals(aValue.value()))
                                .map(AIcdEnumValueDefinition::title).toList()))).toList();
        String locDescription = AIcDocumentation(aDefinitions.stream().map(AIcdCanonicalDefinition::description).toList());
        String locOrigins = aDefinitions.stream().map(aDefinition -> aDefinition.sourceKind() + ": "
                + aDefinition.identity() + " (" + aDefinition.sourceResource() + ")").distinct()
                .collect(Collectors.joining("; "));
        return new AIcdCanonicalDefinition(locFirst.identity(), locFirst.version(), locFirst.logicalName(), locFirst.sourceKind(), locFirst.sourceResource(), (locDescription == null ? "" : locDescription + "\n\n") + "Canonical representations: " + locOrigins, (locFirst.dataType().kind() == eu.algites.tool.codegen.defs.AInDataTypeKind.OBJECT ? locFirst.dataType().withProperties(locProperties) : locFirst.dataType()), locValues, AIcFirstTitle(locFirst.title(), aDefinitions.stream()
                        .map(AIcdCanonicalDefinition::title).toList()), locFirst.schemaUrl(),
                        locFirst.dataSourceSchemaUrlField(), locFirst.dataSourceSchemaIdentifierField(),
                        locFirst.dataSourceSchemaVersionField(), locFirst.schemaSourceSchemaUrlField(),
                        locFirst.schemaSourceSchemaIdentifierField(), locFirst.schemaSourceSchemaVersionField());
    }

    /**
     * Merges published multi-format contracts, including an exact documentation parity check.
     * The documented source root resolves relative source-resource paths without relying on
     * the Gradle daemon's working directory.
     */
    public static AIcdCanonicalDefinition AIcMergeStrict(List<AIcdCanonicalDefinition> aDefinitions, Path aSourceRoot) {
        AIcValidate(aDefinitions, true, aSourceRoot);
        return AIcMerge(aDefinitions);
    }

    /** Validates every pair and reports all disagreements, including absolute file locations. */
    public static void AIcValidate(List<AIcdCanonicalDefinition> aDefinitions,
            boolean aCheckDocumentation, Path aSourceRoot) {
        if (aDefinitions.isEmpty()) throw new IllegalArgumentException("No canonical definitions to merge.");
        if (aDefinitions.size() == 1) return;
        List<String> locPairResults = new ArrayList<>();
        boolean locIncompatible = false;
        for (int locLeft = 0; locLeft < aDefinitions.size(); locLeft++) {
            for (int locRight = locLeft + 1; locRight < aDefinitions.size(); locRight++) {
                var locA = aDefinitions.get(locLeft);
                var locB = aDefinitions.get(locRight);
                List<AIcdDifference> locDiffs = AIcDifferences(locA, locB, aCheckDocumentation);
                locPairResults.add("  [" + (locLeft + 1) + "] " + locA.sourceKind() + " vs ["
                        + (locRight + 1) + "] " + locB.sourceKind() + ": "
                        + (locDiffs.isEmpty() ? "CONSISTENT" : "INCONSISTENT"));
                for (AIcdDifference locDifference : locDiffs) {
                    locPairResults.add("    - " + locDifference.subject() + ": "
                            + "[" + (locLeft + 1) + "] " + AIcValue(locDifference.left()) + " ("
                            + AIcLocation(locA, aSourceRoot, locDifference.field(), locDifference.member()) + ") vs "
                            + "[" + (locRight + 1) + "] " + AIcValue(locDifference.right()) + " ("
                            + AIcLocation(locB, aSourceRoot, locDifference.field(), locDifference.member()) + ")");
                }
                locIncompatible |= !locDiffs.isEmpty();
            }
        }
        if (!locIncompatible) return;
        StringBuilder locReport = new StringBuilder("Incompatible canonical definitions (")
                .append(aDefinitions.size()).append(" representations):\nSources:");
        for (int locIndex = 0; locIndex < aDefinitions.size(); locIndex++) {
            var locDefinition = aDefinitions.get(locIndex);
            locReport.append("\n  [").append(locIndex + 1).append("] ")
                    .append(locDefinition.sourceKind()).append(": ")
                    .append(AIcLocation(locDefinition, aSourceRoot, null, null));
        }
        locReport.append("\nPairwise comparison:\n").append(String.join("\n", locPairResults));
        throw new IllegalArgumentException(locReport.toString());
    }

    private record AIcdDifference(String subject, String field, String member, Object left, Object right) { }

    private static void AIcCompare(List<AIcdDifference> aDiffs, String aSubject, String aField,
            String aMember, Object aLeft, Object aRight) {
        if (!Objects.equals(aLeft, aRight))
            aDiffs.add(new AIcdDifference(aSubject, aField, aMember, aLeft, aRight));
    }

    private static List<AIcdDifference> AIcDifferences(AIcdCanonicalDefinition aLeft,
            AIcdCanonicalDefinition aRight, boolean aDocs) {
        List<AIcdDifference> locResult = new ArrayList<>();
        AIcCompare(locResult, "logicalName", null, null, aLeft.logicalName(), aRight.logicalName());
        AIcCompare(locResult, "version", null, null, aLeft.version(), aRight.version());
        AIcCompare(locResult, "kind", null, null, aLeft.dataType().kind(), aRight.dataType().kind());
        if (aDocs) {
            AIcCompare(locResult, "title", null, "title", aLeft.title(), aRight.title());
            AIcCompare(locResult, "description", null, "description", aLeft.description(), aRight.description());
        }
        if (aLeft.dataType().kind() != AInDataTypeKind.OBJECT
                || aRight.dataType().kind() != AInDataTypeKind.OBJECT)
            AIcCompareDataType(locResult, "root.dataType", null, aLeft.dataType(), aRight.dataType(), aDocs);
        if (aLeft.dataType().kind() == AInDataTypeKind.OBJECT
                && aRight.dataType().kind() == AInDataTypeKind.OBJECT) {
            AIcCompare(locResult, "root.constraints.minProperties", null, "minProperties",
                    aLeft.dataType().constraints().minProperties(), aRight.dataType().constraints().minProperties());
            AIcCompare(locResult, "root.constraints.maxProperties", null, "maxProperties",
                    aLeft.dataType().constraints().maxProperties(), aRight.dataType().constraints().maxProperties());
        }
        Map<String, AIcdPropertyDefinition> locLeft = new LinkedHashMap<>();
        Map<String, AIcdPropertyDefinition> locRight = new LinkedHashMap<>();
        for (var locField : aLeft.dataType().properties()) locLeft.put(locField.sourceName(), locField);
        for (var locField : aRight.dataType().properties()) locRight.put(locField.sourceName(), locField);
        for (String locName : java.util.stream.Stream.concat(locLeft.keySet().stream(), locRight.keySet().stream()).distinct().sorted().toList()) {
            var locA = locLeft.get(locName);
            var locB = locRight.get(locName);
            /* The serialization self-link is not a data field in XML and cannot be
             * represented as an XML NCName. All unrelated $schema fields remain strict. */
            if (locA == null && locB != null && AIcSelfPublicationSchema(locB, aRight)
                    && aLeft.sourceKind() == eu.algites.tool.codegen.defs.AInDefinitionSourceKind.XMLDEFS) continue;
            if (locB == null && locA != null && AIcSelfPublicationSchema(locA, aLeft)
                    && aRight.sourceKind() == eu.algites.tool.codegen.defs.AInDefinitionSourceKind.XMLDEFS) continue;
            if (locA == null || locB == null) {
                AIcCompare(locResult, "field '" + locName + "' presence", locName, null,
                        locA == null ? "<missing>" : "present", locB == null ? "<missing>" : "present");
                continue;
            }
            if (aLeft.sourceKind() == eu.algites.tool.codegen.defs.AInDefinitionSourceKind.XMLDEFS
                    && aRight.sourceKind() == eu.algites.tool.codegen.defs.AInDefinitionSourceKind.XMLDEFS)
                AIcCompare(locResult, "field '" + locName + "'.xmlField", locName, "xmlField",
                        locA.xmlField(), locB.xmlField());
            String locPrefix = "field '" + locName + "'.";
            AIcCompare(locResult, locPrefix + "presence", locName, "presence", locA.presence(), locB.presence());
            AIcCompare(locResult, locPrefix + "nullable", locName, "nillable", locA.nullable(), locB.nullable());
            /* The publication's $schema self-link has a format-specific URL.
             * Compare its normalized constraints, not its representation URL. */
            if (AIcSelfPublicationSchema(locA, aLeft) || AIcSelfPublicationSchema(locB, aRight)) {
                AIcConstraints(locResult, locPrefix + "constraints.", locName, "",
                        AIcComparableConstraints(locA, aLeft), AIcComparableConstraints(locB, aRight));
            } else if (aLeft.sourceKind() != eu.algites.tool.codegen.defs.AInDefinitionSourceKind.XMLDEFS
                    && aRight.sourceKind() != eu.algites.tool.codegen.defs.AInDefinitionSourceKind.XMLDEFS) {
                AIcCompareDataType(locResult, locPrefix + "dataType", locName,
                        locA.dataType(), locB.dataType(), aDocs);
            } else {
                /* XML complexContent expansion is not yet guaranteed to project
                 * nested particles identically to JSON/YAML. Compare the direct
                 * node type without dereferencing absent array members. */
                AIcCompare(locResult, locPrefix + "dataType.kind", locName, "type",
                        locA.dataType().kind(), locB.dataType().kind());
                AIcCompare(locResult, locPrefix + "dataType.reference", locName, "$ref",
                        AIcReference(locA.dataType().referencedDefinition()),
                        AIcReference(locB.dataType().referencedDefinition()));
                AIcConstraints(locResult, locPrefix + "dataType.constraints.", locName, "",
                        locA.dataType().constraints(), locB.dataType().constraints());
                if (AIcScalarArrayShape(locA.dataType()) && AIcScalarArrayShape(locB.dataType()))
                    AIcCompareStructuralDataType(locResult, locPrefix + "dataType", locName,
                            locA.dataType(), locB.dataType());
                if (aLeft.sourceKind() == aRight.sourceKind())
                    AIcCompareArrayBounds(locResult, locPrefix + "dataType.constraints.", locName,
                            locA.dataType().constraints(), locB.dataType().constraints());
            }
            if (aDocs) {
                AIcCompare(locResult, locPrefix + "title", locName, "title", locA.title(), locB.title());
                AIcCompare(locResult, locPrefix + "description", locName, "description", locA.description(), locB.description());
            }
        }
        Map<String, AIcdEnumValueDefinition> locLeftEnums = new LinkedHashMap<>();
        Map<String, AIcdEnumValueDefinition> locRightEnums = new LinkedHashMap<>();
        for (var locValue : aLeft.enumValues()) locLeftEnums.put(locValue.value(), locValue);
        for (var locValue : aRight.enumValues()) locRightEnums.put(locValue.value(), locValue);
        for (String locValue : java.util.stream.Stream.concat(locLeftEnums.keySet().stream(), locRightEnums.keySet().stream()).distinct().sorted().toList()) {
            var locA = locLeftEnums.get(locValue);
            var locB = locRightEnums.get(locValue);
            if (locA == null || locB == null) {
                AIcCompare(locResult, "enum '" + locValue + "' presence", null, "enum", locA == null ? "<missing>" : "present", locB == null ? "<missing>" : "present");
            } else if (aDocs) {
                AIcCompare(locResult, "enum '" + locValue + "'.title", null, "title", locA.title(), locB.title());
                AIcCompare(locResult, "enum '" + locValue + "'.description", null, "description", locA.description(), locB.description());
            }
        }
        return locResult;
    }

    /** Compare the complete recursive schema structure, preserving nested arrays and alternatives. */
    private static void AIcCompareDataType(List<AIcdDifference> aDiffs, String aPrefix, String aField,
            AIcdDataType aLeft, AIcdDataType aRight, boolean aDocs) {
        if (aLeft == null || aRight == null) {
            AIcCompare(aDiffs, aPrefix, aField, "dataType", aLeft, aRight);
            return;
        }
        AIcCompare(aDiffs, aPrefix + ".kind", aField, "dataType/kind", aLeft.kind(), aRight.kind());
        if (aLeft.kind() != aRight.kind()) return;
        switch (aLeft.kind()) {
            case REFERENCE -> AIcCompare(aDiffs, aPrefix + ".reference", aField, "dataType/reference",
                    AIcReference(aLeft.reference()), AIcReference(aRight.reference()));
            case ARRAY -> AIcCompareDataType(aDiffs, aPrefix + ".items", aField,
                    aLeft.elementType(), aRight.elementType(), aDocs);
            case ONE_OF, ANY_OF -> {
                AIcCompare(aDiffs, aPrefix + ".alternativeCount", aField, "dataType/alternatives",
                        aLeft.alternatives().size(), aRight.alternatives().size());
                for (int locIndex = 0; locIndex < Math.min(aLeft.alternatives().size(), aRight.alternatives().size()); locIndex++)
                    AIcCompareDataType(aDiffs, aPrefix + ".alternatives[" + locIndex + "]", aField,
                            aLeft.alternatives().get(locIndex), aRight.alternatives().get(locIndex), aDocs);
            }
            case OBJECT -> {
                AIcCompare(aDiffs, aPrefix + ".constraints.minProperties", aField, "dataType/constraints/minProperties",
                        aLeft.constraints().minProperties(), aRight.constraints().minProperties());
                AIcCompare(aDiffs, aPrefix + ".constraints.maxProperties", aField, "dataType/constraints/maxProperties",
                        aLeft.constraints().maxProperties(), aRight.constraints().maxProperties());
                Map<String, AIcdPropertyDefinition> locLeft = new LinkedHashMap<>();
                Map<String, AIcdPropertyDefinition> locRight = new LinkedHashMap<>();
                aLeft.properties().forEach(aItem -> locLeft.put(aItem.sourceName(), aItem));
                aRight.properties().forEach(aItem -> locRight.put(aItem.sourceName(), aItem));
                for (String locName : java.util.stream.Stream.concat(locLeft.keySet().stream(), locRight.keySet().stream()).distinct().sorted().toList()) {
                    var locA = locLeft.get(locName);
                    var locB = locRight.get(locName);
                    String locKey = aPrefix + ".properties[" + locName + "]";
                    if (locA == null || locB == null) {
                        AIcCompare(aDiffs, locKey + ".presence", aField, "dataType/properties/" + locName,
                                locA != null, locB != null);
                        continue;
                    }
                    AIcCompare(aDiffs, locKey + ".presence", aField, "presence", locA.presence(), locB.presence());
                    AIcCompare(aDiffs, locKey + ".nullable", aField, "nullable", locA.nullable(), locB.nullable());
                    if (aDocs) {
                        AIcCompare(aDiffs, locKey + ".title", aField, "title", locA.title(), locB.title());
                        AIcCompare(aDiffs, locKey + ".description", aField, "description", locA.description(), locB.description());
                    }
                    AIcCompareDataType(aDiffs, locKey + ".dataType", aField,
                            locA.dataType(), locB.dataType(), aDocs);
                }
            }
            default -> { }
        }
        if (aLeft.kind() != eu.algites.tool.codegen.defs.AInDataTypeKind.OBJECT
                && aLeft.kind() != eu.algites.tool.codegen.defs.AInDataTypeKind.REFERENCE)
            AIcConstraints(aDiffs, aPrefix + ".constraints.", aField,
                    "dataType/constraints", aLeft.constraints(), aRight.constraints());
        if (aLeft.kind() == AInDataTypeKind.ARRAY && aRight.kind() == AInDataTypeKind.ARRAY)
            AIcCompareArrayBounds(aDiffs, aPrefix + ".constraints.", aField,
                    aLeft.constraints(), aRight.constraints());
    }

    /** Return true for fully representable scalar types and arbitrarily nested scalar arrays. */
    private static boolean AIcScalarArrayShape(AIcdDataType aType) {
        return aType.kind() == AInDataTypeKind.ARRAY ? AIcScalarArrayShape(aType.elementType())
                : Set.of(AInDataTypeKind.STRING, AInDataTypeKind.INTEGER, AInDataTypeKind.NUMBER,
                        AInDataTypeKind.BOOLEAN, AInDataTypeKind.ANY, AInDataTypeKind.ENUM).contains(aType.kind());
    }

    /** Compare the array restrictions of two equally representable canonical nodes. */
    private static void AIcCompareArrayBounds(List<AIcdDifference> aDiffs, String aPrefix,
            String aField, AIcdValueConstraints aLeft, AIcdValueConstraints aRight) {
        AIcCompare(aDiffs, aPrefix + "minItems", aField, "dataType/constraints/minItems",
                aLeft.minItems(), aRight.minItems());
        AIcCompare(aDiffs, aPrefix + "maxItems", aField, "dataType/constraints/maxItems",
                aLeft.maxItems(), aRight.maxItems());
    }

    /**
     * Compare the complete recursive structural shape across serialization families.
     * Lexical facets are not part of this check because XML, JSON and YAML can use
     * different lexical encodings for equivalent structural types.
     */
    private static void AIcCompareStructuralDataType(List<AIcdDifference> aDiffs,
            String aPrefix, String aField, AIcdDataType aLeft, AIcdDataType aRight) {
        AIcCompare(aDiffs, aPrefix + ".kind", aField, "dataType/kind", aLeft.kind(), aRight.kind());
        if (aLeft.kind() != aRight.kind()) return;
        switch (aLeft.kind()) {
            case ARRAY -> AIcCompareStructuralDataType(aDiffs, aPrefix + ".items", aField,
                    aLeft.elementType(), aRight.elementType());
            case REFERENCE -> AIcCompare(aDiffs, aPrefix + ".reference", aField, "dataType/reference",
                    AIcReference(aLeft.reference()), AIcReference(aRight.reference()));
            case ONE_OF, ANY_OF -> {
                AIcCompare(aDiffs, aPrefix + ".alternativeCount", aField, "dataType/alternatives",
                        aLeft.alternatives().size(), aRight.alternatives().size());
                for (int locIndex = 0; locIndex < Math.min(aLeft.alternatives().size(), aRight.alternatives().size()); locIndex++)
                    AIcCompareStructuralDataType(aDiffs, aPrefix + ".alternatives[" + locIndex + "]", aField,
                            aLeft.alternatives().get(locIndex), aRight.alternatives().get(locIndex));
            }
            case OBJECT -> {
                Map<String, AIcdPropertyDefinition> locLeft = new LinkedHashMap<>();
                Map<String, AIcdPropertyDefinition> locRight = new LinkedHashMap<>();
                aLeft.properties().forEach(aItem -> locLeft.put(aItem.sourceName(), aItem));
                aRight.properties().forEach(aItem -> locRight.put(aItem.sourceName(), aItem));
                for (String locName : java.util.stream.Stream.concat(locLeft.keySet().stream(),
                        locRight.keySet().stream()).distinct().sorted().toList()) {
                    var locA = locLeft.get(locName);
                    var locB = locRight.get(locName);
                    String locKey = aPrefix + ".properties[" + locName + "]";
                    if (locA == null || locB == null) {
                        AIcCompare(aDiffs, locKey + ".presence", aField,
                                "dataType/properties/" + locName, locA != null, locB != null);
                    } else {
                        AIcCompare(aDiffs, locKey + ".presence", aField, "presence", locA.presence(), locB.presence());
                        AIcCompare(aDiffs, locKey + ".nullable", aField, "nullable", locA.nullable(), locB.nullable());
                        AIcCompareStructuralDataType(aDiffs, locKey + ".dataType", aField,
                                locA.dataType(), locB.dataType());
                    }
                }
            }
            default -> { }
        }
    }

    private static Object AIcReference(AIcdDefinitionReference aRef) {
        return aRef == null ? null : java.util.Arrays.asList(aRef.logicalName(), aRef.version(), aRef.targetDataType());
    }

    private static void AIcConstraints(List<AIcdDifference> aDiffs, String aPrefix, String aField,
            String aNested, AIcdValueConstraints aLeft, AIcdValueConstraints aRight) {
        AIcCompare(aDiffs, aPrefix + "dataType", aField, aNested + "/type", aLeft.dataType(), aRight.dataType());
        AIcCompare(aDiffs, aPrefix + "minimum", aField, aNested + "/minimum", aLeft.minimum(), aRight.minimum());
        AIcCompare(aDiffs, aPrefix + "maximum", aField, aNested + "/maximum", aLeft.maximum(), aRight.maximum());
        AIcCompare(aDiffs, aPrefix + "exclusiveMinimum", aField, aNested + "/exclusiveMinimum", aLeft.exclusiveMinimum(), aRight.exclusiveMinimum());
        AIcCompare(aDiffs, aPrefix + "exclusiveMaximum", aField, aNested + "/exclusiveMaximum", aLeft.exclusiveMaximum(), aRight.exclusiveMaximum());
        AIcCompare(aDiffs, aPrefix + "minLength", aField, aNested + "/minLength", aLeft.minLength(), aRight.minLength());
        AIcCompare(aDiffs, aPrefix + "maxLength", aField, aNested + "/maxLength", aLeft.maxLength(), aRight.maxLength());
        AIcCompare(aDiffs, aPrefix + "pattern", aField, aNested + "/pattern", aLeft.pattern(), aRight.pattern());
        AIcCompare(aDiffs, aPrefix + "enumValues", aField, aNested + "/enum", aLeft.enumValues(), aRight.enumValues());

    }

    private static String AIcValue(Object aValue) {
        if (aValue == null) return "<none>";
        String locText = String.valueOf(aValue).replace("\n", "\\n");
        return "'" + (locText.length() > 180 ? locText.substring(0, 177) + "..." : locText) + "'";
    }

    private static String AIcLocation(AIcdCanonicalDefinition aDefinition, Path aRoot,
            String aField, String aMember) {
        String locResource = aDefinition.sourceResource().split("#", 2)[0];
        Path locSource = Path.of(locResource);
        if (!locSource.isAbsolute()) locSource = aRoot.toAbsolutePath().resolve(locSource);
        locSource = locSource.normalize();
        int locLine = AIcFindLine(locSource, aField, aMember);
        return locSource + (locLine > 0 ? ":" + locLine : " (line unknown)");
    }

    /** Locate the actual field declaration and, if possible, its conflicting member. */
    private static int AIcFindLine(Path aSource, String aField, String aMember) {
        if (!Files.isRegularFile(aSource)) return -1;
        try {
            List<String> locLines = Files.readAllLines(aSource, StandardCharsets.UTF_8);
            boolean locXml = aSource.toString().endsWith(".xsd");
            int locStart = 0;
            if (aField != null) {
                String locKey = locXml ? "name=\"" + aField + "\"" : "\"" + aField + "\"";
                boolean locInProperties = locXml;
                for (int locIndex = 0; locIndex < locLines.size(); locIndex++) {
                    if (locLines.get(locIndex).contains("\"properties\"") || locXml) locInProperties = true;
                    if (locInProperties && locLines.get(locIndex).contains(locKey)
                            && (!locXml || locLines.get(locIndex).contains("<xs:element"))) {
                        locStart = locIndex;
                        break;
                    }
                }
                if (locStart == 0 && locLines.stream().noneMatch(locLine -> locLine.contains(locKey))) return -1;
            } else if (locXml) {
                for (int locIndex = 0; locIndex < locLines.size(); locIndex++) {
                    if (locLines.get(locIndex).contains("<xs:complexType")) { locStart = locIndex; break; }
                }
            }
            if (aMember != null && !aMember.isBlank()) {
                String locMember = aMember.substring(aMember.lastIndexOf('/') + 1);
                if (locXml && "description".equals(locMember)) locMember = "<xs:documentation";
                if (locXml && "title".equals(locMember)) locMember = "<algdoc:title";
                if (locXml && "minLength".equals(locMember)) locMember = "<xs:minLength";
                if (locXml && "required".equals(locMember)) locMember = "minOccurs=";
                if (locXml && "type".equals(locMember)) locMember = "type=";
                if (!locXml) locMember = "\"" + locMember + "\"";
                int locLimit = aField == null ? locLines.size() : Math.min(locLines.size(), locStart + 24);
                for (int locIndex = locStart; locIndex < locLimit; locIndex++) {
                    if (locLines.get(locIndex).contains(locMember)) return locIndex + 1;
                }
            }
            return locStart + 1;
        } catch (java.io.IOException locFailure) {
            return -1;
        }
    }

    /** Prefer the primary representation title; otherwise choose the first explicitly supplied title. */
    private static String AIcFirstTitle(String aPrimary, List<String> aCandidates) {
        if (aPrimary != null && !aPrimary.isBlank()) return aPrimary;
        return aCandidates.stream().filter(Objects::nonNull).filter(aTitle -> !aTitle.isBlank())
                .findFirst().orElse(null);
    }

    /**
     * The canonical $schema property identifies the concrete serialization document.
     * Its format-specific published URI is not a data-model constraint. Only an
     * exact self-publication constant may be ignored; unrelated const values and
     * all other field constraints remain subject to strict compatibility checks.
     */
    private static boolean AIcSelfPublicationSchema(AIcdPropertyDefinition aProperty,
            AIcdCanonicalDefinition aDefinition) {
        if (!"$schema".equals(aProperty.sourceName())
                || aProperty.dataType().kind() != AInDataTypeKind.STRING
                || aProperty.dataType().constraints().enumValues().size() != 1) return false;
        String locKind = switch (aDefinition.sourceKind()) {
            case JSONDEFS -> "jsondefs";
            case YAMLDEFS -> "yamldefs";
            default -> "";
        };
        if (locKind.isBlank()) return false;
        String locSource = aDefinition.sourceResource().replace('\\', '/');
        String locMarker = "src/product/" + locKind + "/";
        int locIndex = locSource.indexOf(locMarker);
        if (locIndex < 0 || (locIndex > 0 && locSource.charAt(locIndex - 1) != '/')) return false;
        String locRelative = locSource.substring(locIndex + locMarker.length());
        try {
            URI locUri = URI.create(aProperty.dataType().constraints().enumValues().get(0));
            return "https".equals(locUri.getScheme())
                    && locUri.getHost() != null
                    && locUri.getRawFragment() == null
                    && locUri.getPath().endsWith("/api/" + locKind + "/" + locRelative);
        } catch (IllegalArgumentException locInvalid) {
            return false;
        }
    }

    private static AIcdValueConstraints AIcComparableConstraints(AIcdPropertyDefinition aProperty,
            AIcdCanonicalDefinition aDefinition) {
        if (!AIcSelfPublicationSchema(aProperty, aDefinition)) return aProperty.dataType().constraints();
        AIcdValueConstraints locValue = aProperty.dataType().constraints();
        return new AIcdValueConstraints(locValue.dataType(), locValue.minimum(), locValue.maximum(),
                locValue.exclusiveMinimum(), locValue.exclusiveMaximum(), locValue.minLength(),
                locValue.maxLength(), locValue.pattern(), List.of(), locValue.minItems(), locValue.maxItems(),
                locValue.minProperties(), locValue.maxProperties());
    }

    /**
     * Preserve structural metadata while removing a serialization-specific
     * publication self-link from the merged canonical representation. The
     * individual YAML/JSON source models retain their real, format-specific
     * {@code $schema} constants for validation and publication.
     *
     * @param aProperty property in the primary source representation
     * @param aDefinitions compatible source representations in merge order
     * @return normalized recursive property type for the merged contract
     */
    private static AIcdDataType AIcNormalizedMergedPropertyType(AIcdPropertyDefinition aProperty,
            List<AIcdCanonicalDefinition> aDefinitions) {
        AIcdValueConstraints locConstraints = AIcMergeConstraints(aProperty, aDefinitions);
        AIcdDataType locType = aProperty.dataType();
        if (locConstraints.equals(locType.constraints())) return locType;
        return new AIcdDataType(locType.kind(), locType.elementType(), locType.properties(),
                locType.alternatives(), locType.reference(), locConstraints);
    }

    private static AIcdValueConstraints AIcMergeConstraints(AIcdPropertyDefinition aProperty,
            List<AIcdCanonicalDefinition> aDefinitions) {
        if (aDefinitions.size() < 2 || aDefinitions.stream().noneMatch(aDefinition ->
                aDefinition.dataType().properties().stream().anyMatch(aCandidate ->
                        aCandidate.sourceName().equals(aProperty.sourceName())
                        && AIcSelfPublicationSchema(aCandidate, aDefinition)))) return aProperty.dataType().constraints();
        return AIcComparableConstraints(aProperty, aDefinitions.get(0));
    }

    private static String AIcDocumentation(List<String> aDescriptions) {
        String locResult = aDescriptions.stream().filter(Objects::nonNull).map(String::strip)
                .filter(aDescription -> !aDescription.isEmpty()).distinct().collect(Collectors.joining("\n\n"));
        return locResult.isEmpty() ? null : locResult;
    }
}
