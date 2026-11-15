package eu.algites.tool.codegen.defs.naming.impl;

/** Generated mutable implementation of AIigDefscodegenNamingConventionsPropertyNameConventions_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefscodegenNamingConventionsPropertyNameConventions", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.naming.AIigDefscodegenNamingConventionsPropertyNameConventions_1.class})
public class AIcgdDefscodegenNamingConventionsPropertyNameConventions_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyNameConventions_1<eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConvention_1<?>> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdDefscodegenNamingConventionsPropertyNameConventions_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdDefscodegenNamingConventionsPropertyNameConventions_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.lib.common.list.AIiMultiMappedList<? extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConvention_1<?>> getNameConventionList() { return (eu.algites.lib.common.list.AIiMultiMappedList<? extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConvention_1<?>>) get_OrCreateCollectionField("NameConventionList", true); }
    @Override public eu.algites.lib.common.list.AIiMultiMappedList<? extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConvention_1<?>> _getRaw_NameConventionList() { return (eu.algites.lib.common.list.AIiMultiMappedList<? extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConvention_1<?>>) get_RawField("NameConventionList"); }
    @Override public boolean _isPresent_NameConventionList() { return isPresent_Field("NameConventionList"); }
    @Override public void _unset_NameConventionList() { unset_Field("NameConventionList"); }
}
