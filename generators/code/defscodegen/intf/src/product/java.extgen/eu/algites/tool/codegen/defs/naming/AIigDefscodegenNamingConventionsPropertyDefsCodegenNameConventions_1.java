package eu.algites.tool.codegen.defs.naming;

/**
 * Contract for DefscodegenNamingConventionsPropertyDefsCodegenNameConventions.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions#synthetic:synthetic_property_type; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions#synthetic:synthetic_property_type", schemaVersion = 1)
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/properties/DefsCodegenNameConventions#synthetic:synthetic_property_type", schemaVersion = 1)
@eu.algites.lib.data.dataobject.AIaDataObject(description = "DefscodegenNamingConventionsPropertyDefsCodegenNameConventions")
public interface AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTDefscodegenNamingConventionsPropertyDefsCodegenNameConventions {
        /** Source identifier NameConventions. */
        String FIELD_NAME__NAME_CONVENTIONS = "NameConventions";
    }

    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameConventions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field NameConventions. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIigDefscodegenNamingConventionsPropertyNameConventions_1 getNameConventions();

}
