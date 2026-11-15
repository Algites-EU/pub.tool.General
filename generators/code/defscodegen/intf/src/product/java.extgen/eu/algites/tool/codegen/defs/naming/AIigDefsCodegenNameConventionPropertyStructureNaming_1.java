package eu.algites.tool.codegen.defs.naming;

/**
 * Contract for DefsCodegenNameConventionPropertyStructureNaming.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConvention/sequence/sequence/1#synthetic:synthetic_property_type; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type", schemaVersion = 1)
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type", schemaVersion = 1)
@eu.algites.lib.data.dataobject.AIaDataObject(description = "DefsCodegenNameConventionPropertyStructureNaming")
public interface AIigDefsCodegenNameConventionPropertyStructureNaming_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTDefsCodegenNameConventionPropertyStructureNaming {
        /** Source identifier Rule. */
        String FIELD_NAME__RULE = "Rule";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "Rule", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "Rule", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 0, minItemCount = 0, maxItemCount = -1)
    /** Value of schema field Rule. Field is optional; cardinality 0..-1.
     * @return field value in its canonical representation
     */
    eu.algites.lib.common.list.AIiMultiMappedList<? extends AIigDefsCodegenStructureNamingRule_1> getRuleList();

}
