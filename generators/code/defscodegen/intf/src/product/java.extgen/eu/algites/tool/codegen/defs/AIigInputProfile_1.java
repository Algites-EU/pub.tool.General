package eu.algites.tool.codegen.defs;

/**
 * Root document configuring one input-definition family.
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd}InputProfile; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.input-profile", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/input-profile_1.jsondef.schema.json")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.input-profile", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/input-profile_1.yamldef.schema.json")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "InputProfile")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "Root document configuring one input-definition family.")
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

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "SourceKind", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "SourceKind", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Selects the source-definition family handled by the frontend. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIngSourceKindType_1 getSourceKind();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "NamingProfile", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NamingProfile", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 1, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true)
    /** Names the naming profile applied while interpreting and generating identifiers. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getNamingProfile();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "RequireCanonicalIdentity", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "RequireCanonicalIdentity", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 2, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Requires every loaded definition to expose a canonical identity. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Boolean getRequireCanonicalIdentity();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "RequireDefinitionVersion", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "RequireDefinitionVersion", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 3, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Requires every loaded definition to expose a semantic version. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Boolean getRequireDefinitionVersion();

}
