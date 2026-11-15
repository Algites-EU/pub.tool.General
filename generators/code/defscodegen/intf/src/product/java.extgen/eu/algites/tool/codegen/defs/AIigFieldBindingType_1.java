package eu.algites.tool.codegen.defs;

/**
 * Maps a schema resource and JSON pointer to an optional generated field binding.
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd}FieldBindingType; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType", schemaVersion = 1)
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType", schemaVersion = 1)
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "FieldBindingType")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "Maps a schema resource and JSON pointer to an optional generated field binding.")
public interface AIigFieldBindingType_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTFieldBindingType {
        /** Source identifier schema. */
        String FIELD_NAME__SCHEMA = "schema";
        /** Source identifier pointer. */
        String FIELD_NAME__POINTER = "pointer";
        /** Source identifier name. */
        String FIELD_NAME__NAME = "name";
        /** Source identifier common_one_of_fields. */
        String FIELD_NAME__COMMON_ONE_OF_FIELDS = "common_one_of_fields";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "schema", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "schema", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true)
    /** Canonical URI or path identifying the source schema. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    String getSchema();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "pointer", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "pointer", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 1, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true)
    /** Optional JSON Pointer identifying a particular position within the schema. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getPointer();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "name", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "name", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 2, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true)
    /** Optional override of the generated binding name. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getName();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "common_one_of_fields", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "common_one_of_fields", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 3, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Whether shared fields from oneOf branches are retained in bindings. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Boolean getCommonOneOfFields();

}
