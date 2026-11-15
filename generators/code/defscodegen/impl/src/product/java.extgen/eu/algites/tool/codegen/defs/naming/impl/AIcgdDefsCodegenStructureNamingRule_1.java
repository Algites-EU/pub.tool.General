package eu.algites.tool.codegen.defs.naming.impl;

/** Generated mutable implementation of AIigDefsCodegenStructureNamingRule_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenStructureNamingRule", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd", namespaceLocalName = "DefsCodegenStructureNamingRule")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.naming.AIigDefsCodegenStructureNamingRule_1.class})
public class AIcgdDefsCodegenStructureNamingRule_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenStructureNamingRule_1 {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdDefsCodegenStructureNamingRule_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdDefsCodegenStructureNamingRule_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.tool.codegen.defs.naming.AIngDefscodegenStructureKind_1 getKind() { return (eu.algites.tool.codegen.defs.naming.AIngDefscodegenStructureKind_1) get_EffectiveField("Kind"); }
    @Override public void setKind(eu.algites.tool.codegen.defs.naming.AIngDefscodegenStructureKind_1 aKind) { set_RawField("Kind", aKind); }
    @Override public eu.algites.tool.codegen.defs.naming.AIngDefscodegenStructureKind_1 _getRaw_Kind() { return (eu.algites.tool.codegen.defs.naming.AIngDefscodegenStructureKind_1) get_RawField("Kind"); }
    @Override public boolean _isPresent_Kind() { return isPresent_Field("Kind"); }
    @Override public void _unset_Kind() { unset_Field("Kind"); }
    @Override public java.lang.String getValue() { return (java.lang.String) get_EffectiveField("Value"); }
    @Override public void setValue(java.lang.String aValue) { set_RawField("Value", aValue); }
    @Override public java.lang.String _getRaw_Value() { return (java.lang.String) get_RawField("Value"); }
    @Override public boolean _isPresent_Value() { return isPresent_Field("Value"); }
    @Override public void _unset_Value() { unset_Field("Value"); }
    @Override public void _setEmpty_Value() { set_EmptyField("Value"); }
    @Override public boolean _isEmpty_Value() { return isEmpty_Field("Value"); }
}
