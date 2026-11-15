package eu.algites.tool.codegen.defs;

/**
 * Defines how defs-codegen interprets one supported source-definition family.
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.input-profile; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.input-profile", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/input-profile_1.jsondef.schema.json")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.input-profile", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/input-profile_1.yamldef.schema.json")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "Defines how defs-codegen interprets one supported source-definition family.")
public interface AIigInputProfile_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTInputProfile {
        /** Source identifier SourceKind. */
        String FIELD_NAME__SOURCE_KIND = "SourceKind";
        /** Source identifier NamingProfile. */
        String FIELD_NAME__NAMING_PROFILE = "NamingProfile";
        /** Source identifier RequireCanonicalIdentity. */
        String FIELD_NAME__REQUIRE_CANONICAL_IDENTITY = "RequireCanonicalIdentity";
        /** Source identifier RequireDefinitionVersion. */
        String FIELD_NAME__REQUIRE_DEFINITION_VERSION = "RequireDefinitionVersion";
    }

    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "SourceKind", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field SourceKind. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIngSourceKindType_1 getSourceKind();

    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NamingProfile", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 1, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Names the naming profile applied while interpreting and generating identifiers. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getNamingProfile();

    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "RequireCanonicalIdentity", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 2, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Requires every loaded definition to expose a canonical identity. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Boolean getRequireCanonicalIdentity();

    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "RequireDefinitionVersion", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 3, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Requires every loaded definition to expose a semantic version. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Boolean getRequireDefinitionVersion();

}
