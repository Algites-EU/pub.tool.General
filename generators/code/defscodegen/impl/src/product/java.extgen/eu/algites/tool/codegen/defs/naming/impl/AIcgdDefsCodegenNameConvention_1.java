package eu.algites.tool.codegen.defs.naming.impl;

/** Generated mutable implementation of AIigDefsCodegenNameConvention_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenNameConvention", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd", namespaceLocalName = "DefsCodegenNameConvention")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.naming.AIigDefsCodegenNameConvention_1.class})
public class AIcgdDefsCodegenNameConvention_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConvention_1<eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionPropertyStructureNaming_1<?>> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdDefsCodegenNameConvention_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdDefsCodegenNameConvention_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.lang.String getCommonNamingConvention() { return (java.lang.String) get_EffectiveField("CommonNamingConvention"); }
    @Override public void setCommonNamingConvention(java.lang.String aCommonNamingConvention) { set_RawField("CommonNamingConvention", aCommonNamingConvention); }
    @Override public java.lang.String _getRaw_CommonNamingConvention() { return (java.lang.String) get_RawField("CommonNamingConvention"); }
    @Override public boolean _isPresent_CommonNamingConvention() { return isPresent_Field("CommonNamingConvention"); }
    @Override public void _unset_CommonNamingConvention() { unset_Field("CommonNamingConvention"); }
    @Override public void _setEmpty_CommonNamingConvention() { set_EmptyField("CommonNamingConvention"); }
    @Override public boolean _isEmpty_CommonNamingConvention() { return isEmpty_Field("CommonNamingConvention"); }
    @Override public java.lang.String getName() { return (java.lang.String) get_EffectiveField("Name"); }
    @Override public void setName(java.lang.String aName) { set_RawField("Name", aName); }
    @Override public java.lang.String _getRaw_Name() { return (java.lang.String) get_RawField("Name"); }
    @Override public boolean _isPresent_Name() { return isPresent_Field("Name"); }
    @Override public void _unset_Name() { unset_Field("Name"); }
    @Override public void _setEmpty_Name() { set_EmptyField("Name"); }
    @Override public boolean _isEmpty_Name() { return isEmpty_Field("Name"); }
    @Override public eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionPropertyStructureNaming_1<?> getStructureNaming() { return (eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionPropertyStructureNaming_1<?>) get_EffectiveField("StructureNaming"); }
    @Override public void setStructureNaming(eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionPropertyStructureNaming_1<?> aStructureNaming) { set_RawField("StructureNaming", aStructureNaming); }
    @Override public eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionPropertyStructureNaming_1<?> _getRaw_StructureNaming() { return (eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionPropertyStructureNaming_1<?>) get_RawField("StructureNaming"); }
    @Override public boolean _isPresent_StructureNaming() { return isPresent_Field("StructureNaming"); }
    @Override public void _unset_StructureNaming() { unset_Field("StructureNaming"); }
}
