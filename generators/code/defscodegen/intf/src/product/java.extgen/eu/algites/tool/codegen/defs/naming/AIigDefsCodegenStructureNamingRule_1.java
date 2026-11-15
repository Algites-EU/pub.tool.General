package eu.algites.tool.codegen.defs.naming;

/**
 * Contract for DefsCodegenStructureNamingRule.
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd}DefsCodegenStructureNamingRule; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule", schemaVersion = 1)
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule", schemaVersion = 1)
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd", namespaceLocalName = "DefsCodegenStructureNamingRule")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "DefsCodegenStructureNamingRule")
public interface AIigDefsCodegenStructureNamingRule_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTDefsCodegenStructureNamingRule {
        /** Source identifier Value. */
        String FIELD_NAME__VALUE = "Value";
        /** Source identifier kind. */
        String FIELD_NAME__KIND = "kind";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "Value", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "Value", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field Value. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    String getValue();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "kind", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ATTRIBUTE)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "kind", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 1, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field kind. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIngDefscodegenStructureKind_1 getKind();

}
