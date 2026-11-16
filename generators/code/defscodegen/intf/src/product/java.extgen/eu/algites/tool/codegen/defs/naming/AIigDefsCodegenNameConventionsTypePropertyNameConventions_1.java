package eu.algites.tool.codegen.defs.naming;

/**
 * Contract for DefsCodegenNameConventionsTypePropertyNameConventions.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConventionsType/complexContent/extension/sequence/sequence/0/sequence/sequence/0#synthetic:synthetic_property_type; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "", namespaceLocalName = "generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConventionsType/complexContent/extension/sequence/sequence/0/sequence/sequence/0#synthetic:synthetic_property_type")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "DefsCodegenNameConventionsTypePropertyNameConventions")
public interface AIigDefsCodegenNameConventionsTypePropertyNameConventions_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTDefsCodegenNameConventionsTypePropertyNameConventions {
        /** Source identifier NameConvention. */
        String FIELD_NAME__NAME_CONVENTION = "NameConvention";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "NameConvention", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameConvention", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 0, minItemCount = 0, maxItemCount = -1)
    /** Value of schema field NameConvention. Field is optional; cardinality 0..-1.
     * @return field value in its canonical representation
     */
    eu.algites.lib.common.list.AIiMultiMappedList<? extends AIigDefsCodegenNameConvention_1> getNameConventionList();

}
