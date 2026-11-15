package eu.algites.tool.codegen.defs.model;

/**
 * Exact XML field QName and attribute/element kind, independent of semantic schema ID.
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}XmlWireName; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName", schemaVersion = 1)
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName", schemaVersion = 1)
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "XmlWireName")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "Exact XML field QName and attribute/element kind, independent of semantic schema ID.")
public interface AIigXmlWireName_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTXmlWireName {
        /** Source identifier namespace_uri. */
        String FIELD_NAME__NAMESPACE_URI = "namespace_uri";
        /** Source identifier local_name. */
        String FIELD_NAME__LOCAL_NAME = "local_name";
        /** Source identifier value_kind. */
        String FIELD_NAME__VALUE_KIND = "value_kind";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "namespace_uri", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "namespace_uri", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field namespace_uri. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    String getNamespaceUri();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "local_name", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "local_name", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 1, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field local_name. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    String getLocalName();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "value_kind", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "value_kind", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 2, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field value_kind. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIngXmlWireNameValueKind_1 getValueKind();

}
