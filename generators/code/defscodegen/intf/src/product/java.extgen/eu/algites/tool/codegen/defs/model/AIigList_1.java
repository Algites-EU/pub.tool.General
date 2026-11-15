package eu.algites.tool.codegen.defs.model;

/**
 * Homogeneous collection
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}List; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List", schemaVersion = 1)
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List", schemaVersion = 1)
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "List")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "Homogeneous collection")
public interface AIigList_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTList {
        /** Source identifier name. */
        String FIELD_NAME__NAME = "name";
        /** Source identifier item. */
        String FIELD_NAME__ITEM = "item";
        /** Source identifier min_item_count. */
        String FIELD_NAME__MIN_ITEM_COUNT = "min_item_count";
        /** Source identifier max_item_count. */
        String FIELD_NAME__MAX_ITEM_COUNT = "max_item_count";
        /** Source identifier xml_wire. */
        String FIELD_NAME__XML_WIRE = "xml_wire";
        /** Source identifier key_definitions. */
        String FIELD_NAME__KEY_DEFINITIONS = "key_definitions";
        /** Source identifier unique_items. */
        String FIELD_NAME__UNIQUE_ITEMS = "unique_items";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "name", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "name", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field name. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    String getName();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "item", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "item", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 1, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field item. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIigStructure_1 getItem();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "min_item_count", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "min_item_count", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 2, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field min_item_count. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    Long getMinItemCount();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "max_item_count", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "max_item_count", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 3, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field max_item_count. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    Long getMaxItemCount();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "xml_wire", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "xml_wire", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 4, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field xml_wire. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    AIigXmlWireName_1 getXmlWire();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "key_definitions", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "key_definitions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 5, minItemCount = 0, maxItemCount = -1)
    /** Value of schema field key_definitions. Field is optional; cardinality 0..-1.
     * @return field value in its canonical representation
     */
    eu.algites.lib.common.list.AIiBoundedList<? extends AIigKeyDefinition_1> getKeyDefinitionsList();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "unique_items", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "unique_items", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 6, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field unique_items. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Boolean getUniqueItems();

}
