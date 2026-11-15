package eu.algites.tool.codegen.defs.naming;

/**
 * Contract for DefsCodegenNameConventionsType.
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd}DefsCodegenNameConventionsType; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd", namespaceLocalName = "DefsCodegenNameConventionsType")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "DefsCodegenNameConventionsType")
public interface AIigDefsCodegenNameConventionsType_1 extends eu.algites.lib.naming.convention.AIigCommonNamingConventions_1 {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTDefsCodegenNameConventionsType {
        /** Source identifier DefsCodegenNameConventions. */
        String FIELD_NAME__DEFS_CODEGEN_NAME_CONVENTIONS = "DefsCodegenNameConventions";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "DefsCodegenNameConventions", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "DefsCodegenNameConventions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field DefsCodegenNameConventions. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1 getDefsCodegenNameConventions();

}
