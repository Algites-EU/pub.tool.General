package eu.algites.tool.codegen.defs.naming.impl.intf;

/** Generated mutable contract derived from AIigDefsCodegenNameConventionPropertyStructureNaming_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenNameConventionPropertyStructureNaming", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "", namespaceLocalName = "generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConvention/sequence/sequence/1#synthetic:synthetic_property_type")
public interface AIigdDefsCodegenNameConventionPropertyStructureNaming_1<TRuleList extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenStructureNamingRule_1> extends eu.algites.tool.codegen.defs.naming.AIigDefsCodegenNameConventionPropertyStructureNaming_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field RuleList under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "Rule", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 0, minItemCount = 0, maxItemCount = -1, isEmptyAllowed = false, setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Rule list")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "Rule", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override eu.algites.lib.common.list.AIiMultiMappedList<? extends TRuleList> getRuleList();
    eu.algites.lib.common.list.AIiMultiMappedList<? extends TRuleList> _getRaw_RuleList();
    boolean _isPresent_RuleList();
    void _unset_RuleList();
}
