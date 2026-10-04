package eu.algites.tool.codegen.defs;

import java.util.List;
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
        AIcdCanonicalDefinition locFirst = aDefinitions.get(0);
        for (AIcdCanonicalDefinition locDefinition : aDefinitions) {
            if (!Objects.equals(locFirst.logicalName(), locDefinition.logicalName())
                    || !Objects.equals(locFirst.version(), locDefinition.version())
                    || locFirst.kind() != locDefinition.kind()
                    || !AIcPropertyShapes(locFirst).equals(AIcPropertyShapes(locDefinition))
                    || !locFirst.enumValues().stream().map(AIcdEnumValueDefinition::value).toList()
                        .equals(locDefinition.enumValues().stream().map(AIcdEnumValueDefinition::value).toList())) {
                throw new IllegalArgumentException("Incompatible canonical representations: "
                        + locFirst.sourceResource() + " and " + locDefinition.sourceResource());
            }
        }
        if (aDefinitions.size() == 1) return locFirst;
        List<AIcdPropertyDefinition> locProperties = locFirst.properties().stream().map(aProperty ->
                new AIcdPropertyDefinition(aProperty.sourceName(), aProperty.valueKind(), aProperty.required(),
                        aProperty.nullable(), aProperty.itemValueKind(), aProperty.reference(),
                        AIcDocumentation(aDefinitions.stream().flatMap(aDefinition -> aDefinition.properties().stream())
                                .filter(aCandidate -> aCandidate.sourceName().equals(aProperty.sourceName()))
                                .map(AIcdPropertyDefinition::description).toList()))).toList();
        List<AIcdEnumValueDefinition> locValues = locFirst.enumValues().stream().map(aValue ->
                new AIcdEnumValueDefinition(aValue.value(), AIcDocumentation(aDefinitions.stream()
                        .flatMap(aDefinition -> aDefinition.enumValues().stream())
                        .filter(aCandidate -> aCandidate.value().equals(aValue.value()))
                        .map(AIcdEnumValueDefinition::description).toList()))).toList();
        String locDescription = AIcDocumentation(aDefinitions.stream().map(AIcdCanonicalDefinition::description).toList());
        String locOrigins = aDefinitions.stream().map(aDefinition -> aDefinition.sourceKind() + ": "
                + aDefinition.identity() + " (" + aDefinition.sourceResource() + ")").distinct()
                .collect(Collectors.joining("; "));
        return new AIcdCanonicalDefinition(locFirst.identity(), locFirst.version(), locFirst.logicalName(),
                locFirst.kind(), locFirst.sourceKind(), locFirst.sourceResource(),
                (locDescription == null ? "" : locDescription + "\n\n") + "Canonical representations: " + locOrigins,
                locProperties, locValues);
    }

    private record AIcdPropertyShape(String name, AInValueKind kind, boolean required, boolean nullable,
            AInValueKind itemKind, String referenceName, Integer referenceVersion, AInDefinitionKind referenceKind) { }

    private static List<AIcdPropertyShape> AIcPropertyShapes(AIcdCanonicalDefinition aDefinition) {
        return aDefinition.properties().stream().map(aProperty -> {
            AIcdDefinitionReference locReference = aProperty.reference();
            return new AIcdPropertyShape(aProperty.sourceName(), aProperty.valueKind(), aProperty.required(),
                    aProperty.nullable(), aProperty.itemValueKind(), locReference == null ? null : locReference.logicalName(),
                    locReference == null ? null : locReference.version(), locReference == null ? null : locReference.targetKind());
        }).sorted(java.util.Comparator.comparing(AIcdPropertyShape::name)).toList();
    }

    private static String AIcDocumentation(List<String> aDescriptions) {
        String locResult = aDescriptions.stream().filter(Objects::nonNull).map(String::strip)
                .filter(aDescription -> !aDescription.isEmpty()).distinct().collect(Collectors.joining("\n\n"));
        return locResult.isEmpty() ? null : locResult;
    }
}
