package eu.algites.tool.codegen.defs.naming.impl;

/** Generated mutable implementation of AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefscodegenNamingConventionsPropertyDefsCodegenNameConventions", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/properties/DefsCodegenNameConventions#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.naming.AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1.class})
public class AIcgdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1<eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyNameConventions_1<?>> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyNameConventions_1<?> getNameConventions() { return (eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyNameConventions_1<?>) get_EffectiveField("NameConventions"); }
    @Override public void setNameConventions(eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyNameConventions_1<?> aNameConventions) { set_RawField("NameConventions", aNameConventions); }
    @Override public eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyNameConventions_1<?> _getRaw_NameConventions() { return (eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyNameConventions_1<?>) get_RawField("NameConventions"); }
    @Override public boolean _isPresent_NameConventions() { return isPresent_Field("NameConventions"); }
    @Override public void _unset_NameConventions() { unset_Field("NameConventions"); }
}
