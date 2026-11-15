package eu.algites.tool.codegen.defs.naming;

/**
 * Contract for DefsCodegenNameConvention.
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd}DefsCodegenNameConvention; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention", schemaVersion = 1)
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention", schemaVersion = 1)
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd", namespaceLocalName = "DefsCodegenNameConvention")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "DefsCodegenNameConvention")
public interface AIigDefsCodegenNameConvention_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTDefsCodegenNameConvention {
        /** Source identifier CommonNamingConvention. */
        String FIELD_NAME__COMMON_NAMING_CONVENTION = "CommonNamingConvention";
        /** Source identifier StructureNaming. */
        String FIELD_NAME__STRUCTURE_NAMING = "StructureNaming";
        /** Source identifier name. */
        String FIELD_NAME__NAME = "name";
        /** Source identifier UniqueStructureRoles. */
        String KEY_ID__UNIQUE_STRUCTURE_ROLES = "UniqueStructureRoles";
        /** Source identifier kind. */
        String FIELD_NAME__KIND = "kind";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "CommonNamingConvention", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "CommonNamingConvention", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field CommonNamingConvention. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    String getCommonNamingConvention();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "StructureNaming", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = CONSTDefsCodegenNameConvention.KEY_ID__UNIQUE_STRUCTURE_ROLES, selector = "Rule", fields = {CONSTDefsCodegenNameConvention.FIELD_NAME__KIND}, required = true)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "StructureNaming", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 1, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field StructureNaming. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIigDefsCodegenNameConventionPropertyStructureNaming_1 getStructureNaming();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "name", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ATTRIBUTE)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "name", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 2, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field name. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    String getName();

}
