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
 * @param schemaUrl optional published URL from the configured schema-source metadata field
 * @param dataSourceSchemaUrlField target field used to emit the source schema URL into a data document, or empty to disable
 * @param dataSourceSchemaIdentifierField target field used to emit the logical schema ID, or empty to disable
 * @param dataSourceSchemaVersionField target field used to emit the logical schema version, or empty to disable
 * @param schemaSourceSchemaUrlField configured source field for schema URL, empty to omit the annotation member; null for legacy callers
 * @param schemaSourceSchemaIdentifierField configured source field for logical schema ID, empty to omit the annotation member; null for legacy callers
 * @param schemaSourceSchemaVersionField configured source field for version, empty to omit the annotation member; null for legacy callers
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
        String title,
        String schemaUrl,
        String dataSourceSchemaUrlField,
        String dataSourceSchemaIdentifierField,
        String dataSourceSchemaVersionField,
        String schemaSourceSchemaUrlField,
        String schemaSourceSchemaIdentifierField,
        String schemaSourceSchemaVersionField) {
    /**
     * Preserves legacy callers that provide only instance-document metadata mappings.
     * An absent source-metadata profile retains the original annotation behavior;
     * explicitly configured blank source fields suppress the respective members.
     *
     * @param identity stable canonical identity
     * @param version canonical schema version
     * @param logicalName schema logical name
     * @param sourceKind input schema technology
     * @param sourceResource schema provenance
     * @param description source documentation
     * @param dataType recursive schema type
     * @param enumValues root enumeration values
     * @param title optional display title
     * @param schemaUrl published representation URL
     * @param dataSourceSchemaUrlField output schema URL field
     * @param dataSourceSchemaIdentifierField output schema ID field
     * @param dataSourceSchemaVersionField output schema version field
     */
    public AIcdCanonicalDefinition(String identity, Integer version, String logicalName,
            AInDefinitionSourceKind sourceKind, String sourceResource, String description,
            AIcdDataType dataType, List<AIcdEnumValueDefinition> enumValues, String title,
            String schemaUrl, String dataSourceSchemaUrlField,
            String dataSourceSchemaIdentifierField, String dataSourceSchemaVersionField) {
        this(identity, version, logicalName, sourceKind, sourceResource, description,
                dataType, enumValues, title, schemaUrl, dataSourceSchemaUrlField,
                dataSourceSchemaIdentifierField, dataSourceSchemaVersionField, null, null, null);
    }

    /**
     * Backward-compatible canonical model without an instance-document metadata mapping.
     *
     * @param identity stable logical identity
     * @param version numeric schema version, if known
     * @param logicalName logical schema name
     * @param sourceKind schema format
     * @param sourceResource resource provenance
     * @param description source documentation
     * @param dataType required schema structure
     * @param enumValues enumerated values
     * @param title schema title
     * @param schemaUrl source schema URL, independently of identity
     */
    public AIcdCanonicalDefinition(String identity, Integer version, String logicalName,
            AInDefinitionSourceKind sourceKind, String sourceResource, String description,
            AIcdDataType dataType, List<AIcdEnumValueDefinition> enumValues, String title, String schemaUrl) {
        this(identity, version, logicalName, sourceKind, sourceResource, description,
                dataType, enumValues, title, schemaUrl, "", "", "");
    }

    /**
     * Compatibility constructor for callers that do not supply schema URL metadata.
     * The URL is not inferred from schema identity or the local file location.
     */
    public AIcdCanonicalDefinition(String identity, Integer version, String logicalName,
            AInDefinitionSourceKind sourceKind, String sourceResource, String description,
            AIcdDataType dataType, List<AIcdEnumValueDefinition> enumValues, String title) {
        this(identity, version, logicalName, sourceKind, sourceResource, description,
                dataType, enumValues, title, "");
    }

    /** Validates canonical identity and freezes enumerated source metadata. */
    public AIcdCanonicalDefinition {
        Objects.requireNonNull(identity, "identity");
        Objects.requireNonNull(logicalName, "logicalName");
        Objects.requireNonNull(sourceKind, "sourceKind");
        Objects.requireNonNull(sourceResource, "sourceResource");
        Objects.requireNonNull(dataType, "dataType");
        schemaUrl = schemaUrl == null ? "" : schemaUrl;
        dataSourceSchemaUrlField = dataSourceSchemaUrlField == null ? "" : dataSourceSchemaUrlField;
        dataSourceSchemaIdentifierField = dataSourceSchemaIdentifierField == null ? "" : dataSourceSchemaIdentifierField;
        dataSourceSchemaVersionField = dataSourceSchemaVersionField == null ? "" : dataSourceSchemaVersionField;
        enumValues = List.copyOf(enumValues == null ? List.of() : enumValues);
        if (!enumValues.isEmpty() && dataType.kind() != AInDataTypeKind.ENUM)
            throw new IllegalArgumentException("Enumeration wire values require an ENUM root type");
    }
}
