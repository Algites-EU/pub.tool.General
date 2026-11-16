package eu.algites.tool.codegen.defs.naming.impl;

/** Generated mutable implementation of AIigDefsCodegenNameConventionPropertyStructureNaming_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenNameConventionPropertyStructureNaming", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "", namespaceLocalName = "generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConvention/sequence/sequence/1#synthetic:synthetic_property_type")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.naming.AIigDefsCodegenNameConventionPropertyStructureNaming_1.class})
public class AIcgdDefsCodegenNameConventionPropertyStructureNaming_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionPropertyStructureNaming_1<eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenStructureNamingRule_1> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdDefsCodegenNameConventionPropertyStructureNaming_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdDefsCodegenNameConventionPropertyStructureNaming_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.lib.common.list.AIiMultiMappedList<? extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenStructureNamingRule_1> getRuleList() { return (eu.algites.lib.common.list.AIiMultiMappedList<? extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenStructureNamingRule_1>) get_OrCreateCollectionField("RuleList", true); }
    @Override public eu.algites.lib.common.list.AIiMultiMappedList<? extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenStructureNamingRule_1> _getRaw_RuleList() { return (eu.algites.lib.common.list.AIiMultiMappedList<? extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenStructureNamingRule_1>) get_RawField("RuleList"); }
    @Override public boolean _isPresent_RuleList() { return isPresent_Field("RuleList"); }
    @Override public void _unset_RuleList() { unset_Field("RuleList"); }
}
