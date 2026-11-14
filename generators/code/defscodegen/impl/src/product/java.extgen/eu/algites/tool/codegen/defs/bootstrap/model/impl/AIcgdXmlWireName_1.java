package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigXmlWireName_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Exact XML field QName and attribute/element kind, independent of semantic schema ID.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigXmlWireName_1.class})
public class AIcgdXmlWireName_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1 {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdXmlWireName_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdXmlWireName_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.lang.String getLocalName() { return (java.lang.String) get_EffectiveField("LocalName"); }
    @Override public void setLocalName(java.lang.String aLocalName) { set_RawField("LocalName", aLocalName); }
    @Override public java.lang.String _getRaw_LocalName() { return (java.lang.String) get_RawField("LocalName"); }
    @Override public boolean _isPresent_LocalName() { return isPresent_Field("LocalName"); }
    @Override public void _unset_LocalName() { unset_Field("LocalName"); }
    @Override public void _setEmpty_LocalName() { set_EmptyField("LocalName"); }
    @Override public boolean _isEmpty_LocalName() { return isEmpty_Field("LocalName"); }
    @Override public java.lang.String getNamespaceUri() { return (java.lang.String) get_EffectiveField("NamespaceUri"); }
    @Override public void setNamespaceUri(java.lang.String aNamespaceUri) { set_RawField("NamespaceUri", aNamespaceUri); }
    @Override public java.lang.String _getRaw_NamespaceUri() { return (java.lang.String) get_RawField("NamespaceUri"); }
    @Override public boolean _isPresent_NamespaceUri() { return isPresent_Field("NamespaceUri"); }
    @Override public void _unset_NamespaceUri() { unset_Field("NamespaceUri"); }
    @Override public void _setEmpty_NamespaceUri() { set_EmptyField("NamespaceUri"); }
    @Override public boolean _isEmpty_NamespaceUri() { return isEmpty_Field("NamespaceUri"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngXmlWireNameValueKind_1 getValueKind() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngXmlWireNameValueKind_1) get_EffectiveField("ValueKind"); }
    @Override public void setValueKind(eu.algites.tool.codegen.defs.bootstrap.model.AIngXmlWireNameValueKind_1 aValueKind) { set_RawField("ValueKind", aValueKind); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngXmlWireNameValueKind_1 _getRaw_ValueKind() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngXmlWireNameValueKind_1) get_RawField("ValueKind"); }
    @Override public boolean _isPresent_ValueKind() { return isPresent_Field("ValueKind"); }
    @Override public void _unset_ValueKind() { unset_Field("ValueKind"); }
}
