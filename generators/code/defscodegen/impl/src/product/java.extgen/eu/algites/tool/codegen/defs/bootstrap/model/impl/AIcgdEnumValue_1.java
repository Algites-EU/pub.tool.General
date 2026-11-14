package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigEnumValue_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Canonical enumeration value", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/EnumValue", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/EnumValue", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/EnumValue", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigEnumValue_1.class})
public class AIcgdEnumValue_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdEnumValue_1 {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdEnumValue_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdEnumValue_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.lang.String getDisplayName() { return (java.lang.String) get_EffectiveField("DisplayName"); }
    @Override public void setDisplayName(java.lang.String aDisplayName) { set_RawField("DisplayName", aDisplayName); }
    @Override public java.lang.String _getRaw_DisplayName() { return (java.lang.String) get_RawField("DisplayName"); }
    @Override public boolean _isPresent_DisplayName() { return isPresent_Field("DisplayName"); }
    @Override public void _unset_DisplayName() { unset_Field("DisplayName"); }
    @Override public void _setEmpty_DisplayName() { set_EmptyField("DisplayName"); }
    @Override public boolean _isEmpty_DisplayName() { return isEmpty_Field("DisplayName"); }
    @Override public java.lang.String getWireValue() { return (java.lang.String) get_EffectiveField("WireValue"); }
    @Override public void setWireValue(java.lang.String aWireValue) { set_RawField("WireValue", aWireValue); }
    @Override public java.lang.String _getRaw_WireValue() { return (java.lang.String) get_RawField("WireValue"); }
    @Override public boolean _isPresent_WireValue() { return isPresent_Field("WireValue"); }
    @Override public void _unset_WireValue() { unset_Field("WireValue"); }
    @Override public void _setEmpty_WireValue() { set_EmptyField("WireValue"); }
    @Override public boolean _isEmpty_WireValue() { return isEmpty_Field("WireValue"); }
}
