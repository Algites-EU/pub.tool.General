package eu.algites.tool.codegen.defs.impl;

/** Generated mutable implementation of AIigFieldBindingType_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Maps a schema resource and JSON pointer to an optional generated field binding.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "FieldBindingType")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.AIigFieldBindingType_1.class})
public class AIcgdFieldBindingType_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.impl.intf.AIigdFieldBindingType_1 {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdFieldBindingType_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdFieldBindingType_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.lang.Boolean getCommonOneOfFields() { return (java.lang.Boolean) get_EffectiveField("CommonOneOfFields"); }
    @Override public void setCommonOneOfFields(java.lang.Boolean aCommonOneOfFields) { set_RawField("CommonOneOfFields", aCommonOneOfFields); }
    @Override public java.lang.Boolean _getRaw_CommonOneOfFields() { return (java.lang.Boolean) get_RawField("CommonOneOfFields"); }
    @Override public boolean _isPresent_CommonOneOfFields() { return isPresent_Field("CommonOneOfFields"); }
    @Override public void _unset_CommonOneOfFields() { unset_Field("CommonOneOfFields"); }
    @Override public java.lang.String getName() { return (java.lang.String) get_EffectiveField("Name"); }
    @Override public void setName(java.lang.String aName) { set_RawField("Name", aName); }
    @Override public java.lang.String _getRaw_Name() { return (java.lang.String) get_RawField("Name"); }
    @Override public boolean _isPresent_Name() { return isPresent_Field("Name"); }
    @Override public void _unset_Name() { unset_Field("Name"); }
    @Override public void _setEmpty_Name() { set_EmptyField("Name"); }
    @Override public boolean _isEmpty_Name() { return isEmpty_Field("Name"); }
    @Override public java.lang.String getPointer() { return (java.lang.String) get_EffectiveField("Pointer"); }
    @Override public void setPointer(java.lang.String aPointer) { set_RawField("Pointer", aPointer); }
    @Override public java.lang.String _getRaw_Pointer() { return (java.lang.String) get_RawField("Pointer"); }
    @Override public boolean _isPresent_Pointer() { return isPresent_Field("Pointer"); }
    @Override public void _unset_Pointer() { unset_Field("Pointer"); }
    @Override public void _setEmpty_Pointer() { set_EmptyField("Pointer"); }
    @Override public boolean _isEmpty_Pointer() { return isEmpty_Field("Pointer"); }
    @Override public java.lang.String getSchema() { return (java.lang.String) get_EffectiveField("Schema"); }
    @Override public void setSchema(java.lang.String aSchema) { set_RawField("Schema", aSchema); }
    @Override public java.lang.String _getRaw_Schema() { return (java.lang.String) get_RawField("Schema"); }
    @Override public boolean _isPresent_Schema() { return isPresent_Field("Schema"); }
    @Override public void _unset_Schema() { unset_Field("Schema"); }
    @Override public void _setEmpty_Schema() { set_EmptyField("Schema"); }
    @Override public boolean _isEmpty_Schema() { return isEmpty_Field("Schema"); }
}
