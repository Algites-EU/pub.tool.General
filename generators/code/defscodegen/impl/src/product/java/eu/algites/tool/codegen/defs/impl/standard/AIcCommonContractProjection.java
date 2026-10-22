package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.data.dataobject.AInFieldPresenceKind;
import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * Projects the semantic overlap of separately published schema representations.
 * Only the role named {@code common} may use this projection; XML, YAML and JSON
 * roles retain their complete source models and independent schema identities.
 * The projection deliberately removes source-specific XML bindings and scalar
 * restrictions, which remain owned by the specialized contracts.
 */
public final class AIcCommonContractProjection {
    private AIcCommonContractProjection() { }

    /**
     * Normalizes only the recognized format marker in an Algites URN.
     * Arbitrary URNs and already normalized publication URL identities are
     * unchanged, so unrelated schemas with the same generated filename still fail.
     *
     * @param aDefinition source representation whose kind identifies its alias
     * @param aPackage generated Java/Python package, used by implicit identities
     * @param aOriginal canonical identity from the existing URL/implicit resolver
     * @return identity used exclusively to compare common-role output collisions
     */
    public static Object canonicalIdentity(AIcdCanonicalDefinition aDefinition,
            String aPackage, Object aOriginal) {
        if (!(aOriginal instanceof List<?> locParts) || locParts.size() < 3
                || !Objects.equals(locParts.get(0), "explicit")) return aOriginal;
        String locIdentity = String.valueOf(locParts.get(1));
        if (!locIdentity.startsWith("urn:algites:")) return aOriginal;
        String locFormat = switch (aDefinition.sourceKind()) {
            case YAMLDEFS -> ":yamldef:";
            case JSONDEFS -> ":jsondef:";
            default -> "";
        };
        if (!locFormat.isEmpty()) locIdentity = locIdentity.replace(locFormat, ":");
        return java.util.Arrays.asList("explicit", locIdentity, locParts.get(2));
    }

    /**
     * Builds a common contract whose fields exist compatibly in every source.
     * A name present in only some formats belongs exclusively to those formats.
     * Fields sharing a name but disagreeing on structural type are rejected, not
     * silently removed from the common API. Cardinality and nullability are
     * relaxed to the least restrictive values supported by every representation.
     *
     * @param aDefinitions distinct schema representations for one common name
     * @return canonical intersection with all source identities documented
     * @throws IllegalArgumentException when shared names have incompatible shapes
     */
    public static AIcdCanonicalDefinition merge(List<AIcdCanonicalDefinition> aDefinitions) {
        if (aDefinitions.isEmpty()) throw new IllegalArgumentException("No common representations");
        AIcdCanonicalDefinition locFirst = aDefinitions.get(0);
        if (aDefinitions.size() == 1) return locFirst;
        for (int locIndex = 1; locIndex < aDefinitions.size(); locIndex++) {
            AIcdCanonicalDefinition locOther = aDefinitions.get(locIndex);
            if (locFirst.version() != null && !Objects.equals(locFirst.version(), locOther.version()))
                throw new IllegalArgumentException("Common contract version mismatch: " + locFirst.logicalName());
        }
        boolean locMixedRoot = aDefinitions.stream().anyMatch(aDefinition ->
                aDefinition.dataType().kind() != locFirst.dataType().kind());
        AIcdDataType locCommon;
        if (locMixedRoot) {
            if (aDefinitions.stream().anyMatch(aDefinition -> aDefinition.dataType().kind() != AInDataTypeKind.OBJECT
                    && aDefinition.dataType().kind() != AInDataTypeKind.ONE_OF
                    && aDefinition.dataType().kind() != AInDataTypeKind.ANY_OF))
                throw new IllegalArgumentException("Incompatible common root types: " + locFirst.logicalName());
            /* Object and closed-choice publications have no shared member API;
             * publish only the semantic common identity marker. */
            locCommon = AIcdDataType.object(List.of());
        } else if (locFirst.dataType().kind() == AInDataTypeKind.OBJECT) {
            locCommon = projectType(aDefinitions.stream().map(AIcdCanonicalDefinition::dataType).toList(),
                    locFirst.logicalName());
        } else {
            boolean locEquivalent = aDefinitions.stream().allMatch(aDefinition ->
                    aDefinition.dataType().equals(locFirst.dataType())
                    && aDefinition.enumValues().equals(locFirst.enumValues()));
            if (!locEquivalent) throw new IllegalArgumentException(
                    "Non-object common contracts must be identical: " + locFirst.logicalName());
            locCommon = locFirst.dataType();
        }
        String locProvenance = aDefinitions.stream().map(aDefinition ->
                aDefinition.sourceKind() + ": " + aDefinition.identity() + " ("
                        + aDefinition.sourceResource() + ")").distinct().collect(Collectors.joining("; "));
        String locDescription = locFirst.description() == null ? "" : locFirst.description() + "\n\n";
        String locIdentity = aDefinitions.stream().map(aDefinition -> {
            String locId = aDefinition.identity();
            if (!locId.startsWith("urn:algites:")) return "";
            String locMarker = switch (aDefinition.sourceKind()) {
                case YAMLDEFS -> ":yamldef:";
                case JSONDEFS -> ":jsondef:";
                default -> "";
            };
            return locMarker.isEmpty() ? locId : locId.replace(locMarker, ":");
        }).filter(aIdentity -> !aIdentity.isEmpty()).findFirst().orElse(locFirst.identity());
        return new AIcdCanonicalDefinition(locIdentity, locFirst.version(),
                locFirst.logicalName(), locFirst.sourceKind(), locFirst.sourceResource(),
                locDescription + "Common representations: " + locProvenance, locCommon,
                locFirst.enumValues(), locFirst.title());
    }

    /**
     * Intersects recursively named object fields while preserving value-category
     * structure. Wire-format facets and representation-only refinements remain
     * available through specialized contracts, not through the common projection.
     */
    private static AIcdDataType projectType(List<AIcdDataType> aTypes, String aContext) {
        AIcdDataType locFirst = aTypes.get(0);
        if (aTypes.stream().anyMatch(aType -> aType.kind() != locFirst.kind())) {
            /* XSD anyType is a genuine structural supertype, not an incompatible
             * scalar. The specialized representation retains its exact structure. */
            boolean locAny = aTypes.stream().anyMatch(aType -> aType.kind() == AInDataTypeKind.ANY);
            boolean locEnum = aTypes.stream().allMatch(aType -> aType.kind() == AInDataTypeKind.STRING
                    || (aType.kind() == AInDataTypeKind.REFERENCE && aType.reference().targetsEnum()));
            boolean locStructured = aTypes.stream().allMatch(aType ->
                    aType.kind() == AInDataTypeKind.OBJECT
                    || aType.kind() == AInDataTypeKind.ONE_OF
                    || aType.kind() == AInDataTypeKind.ANY_OF
                    || (aType.kind() == AInDataTypeKind.REFERENCE
                        && aType.reference().targetDataType() != null
                        && (aType.reference().targetDataType().kind() == AInDataTypeKind.OBJECT
                            || aType.reference().targetDataType().kind() == AInDataTypeKind.ONE_OF
                            || aType.reference().targetDataType().kind() == AInDataTypeKind.ANY_OF)));
            if (locAny || locEnum || locStructured)
                return AIcdDataType.atom(AInDataTypeKind.ANY, AIcdValueConstraints.empty());
            throw new IllegalArgumentException("Incompatible common field type: " + aContext);
        }
        AIcdValueConstraints locConstraints = aTypes.stream().allMatch(aType ->
                Objects.equals(aType.constraints(), locFirst.constraints()))
                ? locFirst.constraints() : AIcdValueConstraints.empty();
        return switch (locFirst.kind()) {
            case OBJECT -> {
                List<Map<String, AIcdPropertyDefinition>> locMaps = new ArrayList<>();
                for (AIcdDataType locType : aTypes) {
                    Map<String, AIcdPropertyDefinition> locFields = new LinkedHashMap<>();
                    locType.properties().forEach(aField -> locFields.put(aField.sourceName(), aField));
                    locMaps.add(locFields);
                }
                List<AIcdPropertyDefinition> locShared = new ArrayList<>();
                for (AIcdPropertyDefinition locFirstField : locFirst.properties()) {
                    String locName = locFirstField.sourceName();
                    List<AIcdPropertyDefinition> locFound = locMaps.stream()
                            .map(aFields -> aFields.get(locName)).toList();
                    /* Missing names are representation-specific, not common. */
                    if (locFound.contains(null)) continue;
                    AIcdDataType locChild = projectType(locFound.stream()
                            .map(AIcdPropertyDefinition::dataType).toList(), aContext + "." + locName);
                    AInFieldPresenceKind locPresence = locFound.stream().allMatch(aField ->
                            aField.presence() == AInFieldPresenceKind.REQUIRED)
                            ? AInFieldPresenceKind.REQUIRED : AInFieldPresenceKind.ALLOWED;
                    if (locFound.stream().anyMatch(aField -> aField.presence() == AInFieldPresenceKind.FORBIDDEN))
                        throw new IllegalArgumentException("Incompatible forbidden common field: " + aContext + "." + locName);
                    boolean locNullable = locFound.stream().anyMatch(AIcdPropertyDefinition::nullable);
                    locShared.add(new AIcdPropertyDefinition(locName, locChild, locPresence,
                            locNullable, locFirstField.description(), locFirstField.title(), null));
                }
                yield new AIcdDataType(AInDataTypeKind.OBJECT, null, locShared,
                        List.of(), null, locConstraints);
            }
            case ARRAY -> new AIcdDataType(AInDataTypeKind.ARRAY,
                    projectType(aTypes.stream().map(AIcdDataType::elementType).toList(),
                            aContext + "[]"), List.of(), List.of(), null, locConstraints);
            case ONE_OF, ANY_OF -> {
                int locCount = locFirst.alternatives().size();
                if (aTypes.stream().anyMatch(aType -> aType.alternatives().size() != locCount))
                    throw new IllegalArgumentException("Incompatible common choice: " + aContext);
                List<AIcdDataType> locChoices = new ArrayList<>();
                for (int locIndex = 0; locIndex < locCount; locIndex++) {
                    int locChoice = locIndex;
                    locChoices.add(projectType(aTypes.stream()
                            .map(aType -> aType.alternatives().get(locChoice)).toList(),
                            aContext + "[" + locIndex + "]"));
                }
                yield new AIcdDataType(locFirst.kind(), null, List.of(), locChoices, null, locConstraints);
            }
            case REFERENCE -> {
                if (aTypes.stream().anyMatch(aType -> !Objects.equals(
                        aType.reference().logicalName(), locFirst.reference().logicalName())
                        || !Objects.equals(aType.reference().version(), locFirst.reference().version())))
                    throw new IllegalArgumentException("Incompatible common reference: " + aContext);
                yield new AIcdDataType(AInDataTypeKind.REFERENCE, null, List.of(), List.of(),
                        locFirst.reference(), locConstraints);
            }
            default -> new AIcdDataType(locFirst.kind(), null, List.of(), List.of(), null, locConstraints);
        };
    }
}
