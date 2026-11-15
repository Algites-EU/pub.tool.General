package eu.algites.tool.codegen.defs.naming;

/**
 * Contract for DefscodegenNamingConventionsPropertyNameConventions.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type", schemaVersion = 1)
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type", schemaVersion = 1)
@eu.algites.lib.data.dataobject.AIaDataObject(description = "DefscodegenNamingConventionsPropertyNameConventions")
public interface AIigDefscodegenNamingConventionsPropertyNameConventions_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTDefscodegenNamingConventionsPropertyNameConventions {
        /** Source identifier NameConvention. */
        String FIELD_NAME__NAME_CONVENTION = "NameConvention";
        /** Source identifier UniqueProfileIds. */
        String KEY_ID__UNIQUE_PROFILE_IDS = "UniqueProfileIds";
        /** Source identifier name. */
        String FIELD_NAME__NAME = "name";
    }

    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = CONSTDefscodegenNamingConventionsPropertyNameConventions.KEY_ID__UNIQUE_PROFILE_IDS, fields = {CONSTDefscodegenNamingConventionsPropertyNameConventions.FIELD_NAME__NAME}, required = true)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameConvention", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 0, minItemCount = 0, maxItemCount = -1)
    /** Value of schema field NameConvention. Field is optional; cardinality 0..-1.
     * @return field value in its canonical representation
     */
    eu.algites.lib.common.list.AIiMultiMappedList<? extends AIigDefsCodegenNameConvention_1> getNameConventionList();

}
