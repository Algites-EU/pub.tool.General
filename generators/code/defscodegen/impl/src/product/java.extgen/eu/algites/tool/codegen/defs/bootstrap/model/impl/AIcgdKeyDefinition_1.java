package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigKeyDefinition_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Deferred XML key constraint", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigKeyDefinition_1.class})
public class AIcgdKeyDefinition_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<java.lang.String> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdKeyDefinition_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdKeyDefinition_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.util.List<? extends java.lang.String> getFieldsList() { return (java.util.List<? extends java.lang.String>) get_OrCreateCollectionField("FieldsList", false); }
    @Override public java.util.List<? extends java.lang.String> _getRaw_FieldsList() { return (java.util.List<? extends java.lang.String>) get_RawField("FieldsList"); }
    @Override public boolean _isPresent_FieldsList() { return isPresent_Field("FieldsList"); }
    @Override public void _unset_FieldsList() { unset_Field("FieldsList"); }
    @Override public java.lang.String getIdentifier() { return (java.lang.String) get_EffectiveField("Identifier"); }
    @Override public void setIdentifier(java.lang.String aIdentifier) { set_RawField("Identifier", aIdentifier); }
    @Override public java.lang.String _getRaw_Identifier() { return (java.lang.String) get_RawField("Identifier"); }
    @Override public boolean _isPresent_Identifier() { return isPresent_Field("Identifier"); }
    @Override public void _unset_Identifier() { unset_Field("Identifier"); }
    @Override public void _setEmpty_Identifier() { set_EmptyField("Identifier"); }
    @Override public boolean _isEmpty_Identifier() { return isEmpty_Field("Identifier"); }
    @Override public java.lang.Boolean getRequired() { return (java.lang.Boolean) get_EffectiveField("Required"); }
    @Override public void setRequired(java.lang.Boolean aRequired) { set_RawField("Required", aRequired); }
    @Override public java.lang.Boolean _getRaw_Required() { return (java.lang.Boolean) get_RawField("Required"); }
    @Override public boolean _isPresent_Required() { return isPresent_Field("Required"); }
    @Override public void _unset_Required() { unset_Field("Required"); }
    @Override public java.lang.String getSelector() { return (java.lang.String) get_EffectiveField("Selector"); }
    @Override public void setSelector(java.lang.String aSelector) { set_RawField("Selector", aSelector); }
    @Override public java.lang.String _getRaw_Selector() { return (java.lang.String) get_RawField("Selector"); }
    @Override public boolean _isPresent_Selector() { return isPresent_Field("Selector"); }
    @Override public void _unset_Selector() { unset_Field("Selector"); }
    @Override public void _setEmpty_Selector() { set_EmptyField("Selector"); }
    @Override public boolean _isEmpty_Selector() { return isEmpty_Field("Selector"); }
    @Override public java.lang.String getSourcePointer() { return (java.lang.String) get_EffectiveField("SourcePointer"); }
    @Override public void setSourcePointer(java.lang.String aSourcePointer) { set_RawField("SourcePointer", aSourcePointer); }
    @Override public java.lang.String _getRaw_SourcePointer() { return (java.lang.String) get_RawField("SourcePointer"); }
    @Override public boolean _isPresent_SourcePointer() { return isPresent_Field("SourcePointer"); }
    @Override public void _unset_SourcePointer() { unset_Field("SourcePointer"); }
    @Override public void _setEmpty_SourcePointer() { set_EmptyField("SourcePointer"); }
    @Override public boolean _isEmpty_SourcePointer() { return isEmpty_Field("SourcePointer"); }
}
