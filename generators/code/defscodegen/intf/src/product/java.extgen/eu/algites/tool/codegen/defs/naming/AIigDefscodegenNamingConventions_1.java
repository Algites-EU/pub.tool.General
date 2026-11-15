package eu.algites.tool.codegen.defs.naming;

/**
 * New defs naming profiles; other-domain roles forbidden.
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "New defs naming profiles; other-domain roles forbidden.")
public interface AIigDefscodegenNamingConventions_1 extends eu.algites.lib.naming.convention.AIigCommonNamingConventions_1 {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTDefscodegenNamingConventions {
        /** Source identifier DefsCodegenNameConventions. */
        String FIELD_NAME__DEFS_CODEGEN_NAME_CONVENTIONS = "DefsCodegenNameConventions";
    }

    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "DefsCodegenNameConventions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field DefsCodegenNameConventions. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1 getDefsCodegenNameConventions();

}
