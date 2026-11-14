package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigType_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Declared or synthetic named type", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigType_1.class})
public class AIcgdType_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdType_1<java.lang.String, java.lang.String, eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?>> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdType_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdType_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigTypeContent_1 getContent() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigTypeContent_1) get_EffectiveField("Content"); }
    @Override public void setContent(eu.algites.tool.codegen.defs.bootstrap.model.AIigTypeContent_1 aContent) { set_RawField("Content", aContent); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigTypeContent_1 _getRaw_Content() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigTypeContent_1) get_RawField("Content"); }
    @Override public boolean _isPresent_Content() { return isPresent_Field("Content"); }
    @Override public void _unset_Content() { unset_Field("Content"); }
    @Override public java.lang.String getDescription() { return (java.lang.String) get_EffectiveField("Description"); }
    @Override public void setDescription(java.lang.String aDescription) { set_RawField("Description", aDescription); }
    @Override public java.lang.String _getRaw_Description() { return (java.lang.String) get_RawField("Description"); }
    @Override public boolean _isPresent_Description() { return isPresent_Field("Description"); }
    @Override public void _unset_Description() { unset_Field("Description"); }
    @Override public void _setEmpty_Description() { set_EmptyField("Description"); }
    @Override public boolean _isEmpty_Description() { return isEmpty_Field("Description"); }
    @Override public java.lang.String getIdentity() { return (java.lang.String) get_EffectiveField("Identity"); }
    @Override public void setIdentity(java.lang.String aIdentity) { set_RawField("Identity", aIdentity); }
    @Override public java.lang.String _getRaw_Identity() { return (java.lang.String) get_RawField("Identity"); }
    @Override public boolean _isPresent_Identity() { return isPresent_Field("Identity"); }
    @Override public void _unset_Identity() { unset_Field("Identity"); }
    @Override public void _setEmpty_Identity() { set_EmptyField("Identity"); }
    @Override public boolean _isEmpty_Identity() { return isEmpty_Field("Identity"); }
    @Override public java.util.List<? extends java.lang.String> getInheritedFromTypesList() { return (java.util.List<? extends java.lang.String>) get_OrCreateCollectionField("InheritedFromTypesList", false); }
    @Override public java.util.List<? extends java.lang.String> _getRaw_InheritedFromTypesList() { return (java.util.List<? extends java.lang.String>) get_RawField("InheritedFromTypesList"); }
    @Override public boolean _isPresent_InheritedFromTypesList() { return isPresent_Field("InheritedFromTypesList"); }
    @Override public void _unset_InheritedFromTypesList() { unset_Field("InheritedFromTypesList"); }
    @Override public java.lang.String getName() { return (java.lang.String) get_EffectiveField("Name"); }
    @Override public void setName(java.lang.String aName) { set_RawField("Name", aName); }
    @Override public java.lang.String _getRaw_Name() { return (java.lang.String) get_RawField("Name"); }
    @Override public boolean _isPresent_Name() { return isPresent_Field("Name"); }
    @Override public void _unset_Name() { unset_Field("Name"); }
    @Override public void _setEmpty_Name() { set_EmptyField("Name"); }
    @Override public boolean _isEmpty_Name() { return isEmpty_Field("Name"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngTypeOrigin_1 getOrigin() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngTypeOrigin_1) get_EffectiveField("Origin"); }
    @Override public void setOrigin(eu.algites.tool.codegen.defs.bootstrap.model.AIngTypeOrigin_1 aOrigin) { set_RawField("Origin", aOrigin); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngTypeOrigin_1 _getRaw_Origin() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngTypeOrigin_1) get_RawField("Origin"); }
    @Override public boolean _isPresent_Origin() { return isPresent_Field("Origin"); }
    @Override public void _unset_Origin() { unset_Field("Origin"); }
    @Override public java.util.List<? extends java.lang.String> getPathSegmentsList() { return (java.util.List<? extends java.lang.String>) get_OrCreateCollectionField("PathSegmentsList", false); }
    @Override public java.util.List<? extends java.lang.String> _getRaw_PathSegmentsList() { return (java.util.List<? extends java.lang.String>) get_RawField("PathSegmentsList"); }
    @Override public boolean _isPresent_PathSegmentsList() { return isPresent_Field("PathSegmentsList"); }
    @Override public void _unset_PathSegmentsList() { unset_Field("PathSegmentsList"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1 getResolutionState() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1) get_EffectiveField("ResolutionState"); }
    @Override public void setResolutionState(eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1 aResolutionState) { set_RawField("ResolutionState", aResolutionState); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1 _getRaw_ResolutionState() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1) get_RawField("ResolutionState"); }
    @Override public boolean _isPresent_ResolutionState() { return isPresent_Field("ResolutionState"); }
    @Override public void _unset_ResolutionState() { unset_Field("ResolutionState"); }
    @Override public java.lang.String getSchemaVersion() { return (java.lang.String) get_EffectiveField("SchemaVersion"); }
    @Override public void setSchemaVersion(java.lang.String aSchemaVersion) { set_RawField("SchemaVersion", aSchemaVersion); }
    @Override public java.lang.String _getRaw_SchemaVersion() { return (java.lang.String) get_RawField("SchemaVersion"); }
    @Override public boolean _isPresent_SchemaVersion() { return isPresent_Field("SchemaVersion"); }
    @Override public void _unset_SchemaVersion() { unset_Field("SchemaVersion"); }
    @Override public void _setEmpty_SchemaVersion() { set_EmptyField("SchemaVersion"); }
    @Override public boolean _isEmpty_SchemaVersion() { return isEmpty_Field("SchemaVersion"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?> getSourceBindings() { return (eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?>) get_EffectiveField("SourceBindings"); }
    @Override public void setSourceBindings(eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?> aSourceBindings) { set_RawField("SourceBindings", aSourceBindings); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?> _getRaw_SourceBindings() { return (eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?>) get_RawField("SourceBindings"); }
    @Override public boolean _isPresent_SourceBindings() { return isPresent_Field("SourceBindings"); }
    @Override public void _unset_SourceBindings() { unset_Field("SourceBindings"); }
}
