package eu.algites.tool.codegen.defs.naming;

/**
 * Contract for DefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConventionsType/complexContent/extension/sequence/sequence/0#synthetic:synthetic_property_type; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.AIaDataObject(description = "DefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions")
public interface AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions {
        /** Source identifier NameConventions. */
        String FIELD_NAME__NAME_CONVENTIONS = "NameConventions";
        /** Source identifier UniqueProfileIds. */
        String KEY_ID__UNIQUE_PROFILE_IDS = "UniqueProfileIds";
        /** Source identifier name. */
        String FIELD_NAME__NAME = "name";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "NameConventions", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = CONSTDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions.KEY_ID__UNIQUE_PROFILE_IDS, selector = "NameConvention", fields = {CONSTDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions.FIELD_NAME__NAME}, required = true)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameConventions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field NameConventions. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIigDefsCodegenNameConventionsTypePropertyNameConventions_1 getNameConventions();

}
