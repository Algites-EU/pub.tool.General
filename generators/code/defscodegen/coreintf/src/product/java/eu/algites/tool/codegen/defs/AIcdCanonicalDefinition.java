package eu.algites.tool.codegen.defs;

import java.util.List;
import java.util.Objects;

/**
 * Format-independent canonical definition used by code-generation backends.
 *
 * @param identity canonical definition identity
 * @param version canonical definition version
 * @param logicalName logical definition name independent of source serialization
 * @param kind normalized definition kind
 * @param sourceKind source definition family
 * @param sourceResource source resource path used for provenance
 * @param description human-readable canonical definition description
 * @param properties normalized object properties
 * @param enumValues canonical enum wire values
 */
public record AIcdCanonicalDefinition(
        String identity,
        Integer version,
        String logicalName,
        AInDefinitionKind kind,
        AInDefinitionSourceKind sourceKind,
        String sourceResource,
        String description,
        List<AIcdPropertyDefinition> properties,
        List<String> enumValues) {
    /** Validates and normalizes the supplied data-object components. */
    public AIcdCanonicalDefinition {
        Objects.requireNonNull(identity, "identity");
        Objects.requireNonNull(logicalName, "logicalName");
        Objects.requireNonNull(kind, "kind");
        Objects.requireNonNull(sourceKind, "sourceKind");
        Objects.requireNonNull(sourceResource, "sourceResource");
        properties = List.copyOf(properties == null ? List.of() : properties);
        enumValues = List.copyOf(enumValues == null ? List.of() : enumValues);
    }
}
