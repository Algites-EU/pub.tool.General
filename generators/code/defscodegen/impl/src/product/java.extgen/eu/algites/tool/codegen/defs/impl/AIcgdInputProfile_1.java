package eu.algites.tool.codegen.defs.impl;

/** Generated mutable implementation of AIigInputProfile_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Root document configuring one input-definition family.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.input-profile", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/input-profile_1.jsondef.schema.json", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.input-profile", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/input-profile_1.yamldef.schema.json", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "InputProfile")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.AIigInputProfile_1.class})
public class AIcgdInputProfile_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.impl.intf.AIigdInputProfile_1 {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdInputProfile_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdInputProfile_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.lang.String getNamingProfile() { return (java.lang.String) get_EffectiveField("NamingProfile"); }
    @Override public void setNamingProfile(java.lang.String aNamingProfile) { set_RawField("NamingProfile", aNamingProfile); }
    @Override public java.lang.String _getRaw_NamingProfile() { return (java.lang.String) get_RawField("NamingProfile"); }
    @Override public boolean _isPresent_NamingProfile() { return isPresent_Field("NamingProfile"); }
    @Override public void _unset_NamingProfile() { unset_Field("NamingProfile"); }
    @Override public void _setEmpty_NamingProfile() { set_EmptyField("NamingProfile"); }
    @Override public boolean _isEmpty_NamingProfile() { return isEmpty_Field("NamingProfile"); }
    @Override public java.lang.Boolean getRequireCanonicalIdentity() { return (java.lang.Boolean) get_EffectiveField("RequireCanonicalIdentity"); }
    @Override public void setRequireCanonicalIdentity(java.lang.Boolean aRequireCanonicalIdentity) { set_RawField("RequireCanonicalIdentity", aRequireCanonicalIdentity); }
    @Override public java.lang.Boolean _getRaw_RequireCanonicalIdentity() { return (java.lang.Boolean) get_RawField("RequireCanonicalIdentity"); }
    @Override public boolean _isPresent_RequireCanonicalIdentity() { return isPresent_Field("RequireCanonicalIdentity"); }
    @Override public void _unset_RequireCanonicalIdentity() { unset_Field("RequireCanonicalIdentity"); }
    @Override public java.lang.Boolean getRequireDefinitionVersion() { return (java.lang.Boolean) get_EffectiveField("RequireDefinitionVersion"); }
    @Override public void setRequireDefinitionVersion(java.lang.Boolean aRequireDefinitionVersion) { set_RawField("RequireDefinitionVersion", aRequireDefinitionVersion); }
    @Override public java.lang.Boolean _getRaw_RequireDefinitionVersion() { return (java.lang.Boolean) get_RawField("RequireDefinitionVersion"); }
    @Override public boolean _isPresent_RequireDefinitionVersion() { return isPresent_Field("RequireDefinitionVersion"); }
    @Override public void _unset_RequireDefinitionVersion() { unset_Field("RequireDefinitionVersion"); }
    @Override public eu.algites.tool.codegen.defs.AIngSourceKindType_1 getSourceKind() { return (eu.algites.tool.codegen.defs.AIngSourceKindType_1) get_EffectiveField("SourceKind"); }
    @Override public void setSourceKind(eu.algites.tool.codegen.defs.AIngSourceKindType_1 aSourceKind) { set_RawField("SourceKind", aSourceKind); }
    @Override public eu.algites.tool.codegen.defs.AIngSourceKindType_1 _getRaw_SourceKind() { return (eu.algites.tool.codegen.defs.AIngSourceKindType_1) get_RawField("SourceKind"); }
    @Override public boolean _isPresent_SourceKind() { return isPresent_Field("SourceKind"); }
    @Override public void _unset_SourceKind() { unset_Field("SourceKind"); }
}
