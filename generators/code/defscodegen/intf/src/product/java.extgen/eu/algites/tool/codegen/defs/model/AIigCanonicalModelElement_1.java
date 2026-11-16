package eu.algites.tool.codegen.defs.model;

/**
 * Contract for CanonicalModelElement.
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}CanonicalModel#element; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "CanonicalModel")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "CanonicalModelElement")
public interface AIigCanonicalModelElement_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTCanonicalModelElement {
        /** Source identifier types. */
        String FIELD_NAME__TYPES = "types";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "types", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints(minItems = 1)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "types", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = -1)
    /** Value of schema field types. Field is required; cardinality 1..-1.
     * @return field value in its canonical representation
     */
    eu.algites.lib.common.list.AIiBoundedList<? extends AIigType_1> getTypesList();

}
