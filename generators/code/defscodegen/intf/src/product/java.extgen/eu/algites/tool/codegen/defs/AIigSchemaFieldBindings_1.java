package eu.algites.tool.codegen.defs;

/**
 * Root document selecting schemas and generation targets.
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd}schema-field-bindings; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.jsondef.schema.json")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.yamldef.schema.json")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "schema-field-bindings")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "Root document selecting schemas and generation targets.")
public interface AIigSchemaFieldBindings_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTSchemaFieldBindings {
        /** Source identifier artifact. */
        String FIELD_NAME__ARTIFACT = "artifact";
        /** Source identifier implementation_artifact. */
        String FIELD_NAME__IMPLEMENTATION_ARTIFACT = "implementation_artifact";
        /** Source identifier languages. */
        String FIELD_NAME__LANGUAGES = "languages";
        /** Source identifier bindings. */
        String FIELD_NAME__BINDINGS = "bindings";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "artifact", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "artifact", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true)
    /** Specifies the artifact associated with this definition. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    String getArtifact();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "implementation_artifact", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "implementation_artifact", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 1, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true)
    /** Specifies the implementation artifact associated with this definition. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getImplementationArtifact();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "languages", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints(minItems = 1)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "languages", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 2, minItemCount = 1, maxItemCount = -1)
    /** Value of schema field languages. Field is required; cardinality 1..-1.
     * @return field value in its canonical representation
     */
    eu.algites.lib.common.list.AIiBoundedList<? extends AIngLanguageType_1> getLanguagesList();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "bindings", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints(minItems = 1)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "bindings", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 3, minItemCount = 1, maxItemCount = -1)
    /** Value of schema field bindings. Field is required; cardinality 1..-1.
     * @return field value in its canonical representation
     */
    eu.algites.lib.common.list.AIiBoundedList<? extends AIigFieldBindingType_1> getBindingsList();

}
