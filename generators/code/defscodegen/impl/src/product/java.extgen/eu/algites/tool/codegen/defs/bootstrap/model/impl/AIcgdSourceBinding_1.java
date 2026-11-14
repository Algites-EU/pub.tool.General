package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigSourceBinding_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Exact source binding", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBinding", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBinding", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBinding", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigSourceBinding_1.class})
public class AIcgdSourceBinding_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBinding_1 {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdSourceBinding_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdSourceBinding_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.lang.String getRepresentationKind() { return (java.lang.String) get_EffectiveField("RepresentationKind"); }
    @Override public void setRepresentationKind(java.lang.String aRepresentationKind) { set_RawField("RepresentationKind", aRepresentationKind); }
    @Override public java.lang.String _getRaw_RepresentationKind() { return (java.lang.String) get_RawField("RepresentationKind"); }
    @Override public boolean _isPresent_RepresentationKind() { return isPresent_Field("RepresentationKind"); }
    @Override public void _unset_RepresentationKind() { unset_Field("RepresentationKind"); }
    @Override public void _setEmpty_RepresentationKind() { set_EmptyField("RepresentationKind"); }
    @Override public boolean _isEmpty_RepresentationKind() { return isEmpty_Field("RepresentationKind"); }
    @Override public java.lang.String getSourcePointer() { return (java.lang.String) get_EffectiveField("SourcePointer"); }
    @Override public void setSourcePointer(java.lang.String aSourcePointer) { set_RawField("SourcePointer", aSourcePointer); }
    @Override public java.lang.String _getRaw_SourcePointer() { return (java.lang.String) get_RawField("SourcePointer"); }
    @Override public boolean _isPresent_SourcePointer() { return isPresent_Field("SourcePointer"); }
    @Override public void _unset_SourcePointer() { unset_Field("SourcePointer"); }
    @Override public void _setEmpty_SourcePointer() { set_EmptyField("SourcePointer"); }
    @Override public boolean _isEmpty_SourcePointer() { return isEmpty_Field("SourcePointer"); }
    @Override public java.lang.String getSourceResource() { return (java.lang.String) get_EffectiveField("SourceResource"); }
    @Override public void setSourceResource(java.lang.String aSourceResource) { set_RawField("SourceResource", aSourceResource); }
    @Override public java.lang.String _getRaw_SourceResource() { return (java.lang.String) get_RawField("SourceResource"); }
    @Override public boolean _isPresent_SourceResource() { return isPresent_Field("SourceResource"); }
    @Override public void _unset_SourceResource() { unset_Field("SourceResource"); }
    @Override public void _setEmpty_SourceResource() { set_EmptyField("SourceResource"); }
    @Override public boolean _isEmpty_SourceResource() { return isEmpty_Field("SourceResource"); }
}
