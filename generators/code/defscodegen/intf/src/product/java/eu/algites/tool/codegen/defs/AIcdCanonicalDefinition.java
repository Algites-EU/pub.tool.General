package eu.algites.tool.codegen.defs;

import java.util.List;
import java.util.Objects;

/**
 * Source-independent canonical definition whose shape is represented exclusively by a recursive type.
 * For object definitions the complete field hierarchy is held by {@code dataType.properties()}.
 * Enumeration labels are wire-value metadata and do not duplicate the structural type.
 *
 * @param identity canonical published definition identity
 * @param version canonical definition version, if known
 * @param logicalName unversioned logical name
 * @param sourceKind source schema family
 * @param sourceResource originating schema location or canonical pointer
 * @param description optional source documentation
 * @param dataType required root recursive data type
 * @param enumValues named enumeration values when the root type is ENUM
 * @param title optional short source title
 */
public record AIcdCanonicalDefinition(
        String identity,
        Integer version,
        String logicalName,
        AInDefinitionSourceKind sourceKind,
        String sourceResource,
        String description,
        AIcdDataType dataType,
        List<AIcdEnumValueDefinition> enumValues,
        String title) {
    /** Validates canonical identity and freezes enumerated source metadata. */
    public AIcdCanonicalDefinition {
        Objects.requireNonNull(identity, "identity");
        Objects.requireNonNull(logicalName, "logicalName");
        Objects.requireNonNull(sourceKind, "sourceKind");
        Objects.requireNonNull(sourceResource, "sourceResource");
        Objects.requireNonNull(dataType, "dataType");
        enumValues = List.copyOf(enumValues == null ? List.of() : enumValues);
        if (!enumValues.isEmpty() && dataType.kind() != AInDataTypeKind.ENUM)
            throw new IllegalArgumentException("Enumeration wire values require an ENUM root type");
    }
}
