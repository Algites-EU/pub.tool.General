package eu.algites.tool.codegen.defs.impl;

/** Generated mutable implementation of AIigSchemaFieldBindingsType_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Generator instructions identifying canonical JSON Schema resources and optional field-binding projections.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/SchemaFieldBindingsType", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/SchemaFieldBindingsType", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "SchemaFieldBindingsType")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.AIigSchemaFieldBindingsType_1.class})
public class AIcgdSchemaFieldBindingsType_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.impl.intf.AIigdSchemaFieldBindingsType_1<eu.algites.tool.codegen.defs.impl.intf.AIigdFieldBindingType_1, eu.algites.tool.codegen.defs.AIngLanguageType_1> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdSchemaFieldBindingsType_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdSchemaFieldBindingsType_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.lang.String getArtifact() { return (java.lang.String) get_EffectiveField("Artifact"); }
    @Override public void setArtifact(java.lang.String aArtifact) { set_RawField("Artifact", aArtifact); }
    @Override public java.lang.String _getRaw_Artifact() { return (java.lang.String) get_RawField("Artifact"); }
    @Override public boolean _isPresent_Artifact() { return isPresent_Field("Artifact"); }
    @Override public void _unset_Artifact() { unset_Field("Artifact"); }
    @Override public void _setEmpty_Artifact() { set_EmptyField("Artifact"); }
    @Override public boolean _isEmpty_Artifact() { return isEmpty_Field("Artifact"); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.impl.intf.AIigdFieldBindingType_1> getBindingsList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.impl.intf.AIigdFieldBindingType_1>) get_OrCreateCollectionField("BindingsList", false); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.impl.intf.AIigdFieldBindingType_1> _getRaw_BindingsList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.impl.intf.AIigdFieldBindingType_1>) get_RawField("BindingsList"); }
    @Override public boolean _isPresent_BindingsList() { return isPresent_Field("BindingsList"); }
    @Override public void _unset_BindingsList() { unset_Field("BindingsList"); }
    @Override public java.lang.String getImplementationArtifact() { return (java.lang.String) get_EffectiveField("ImplementationArtifact"); }
    @Override public void setImplementationArtifact(java.lang.String aImplementationArtifact) { set_RawField("ImplementationArtifact", aImplementationArtifact); }
    @Override public java.lang.String _getRaw_ImplementationArtifact() { return (java.lang.String) get_RawField("ImplementationArtifact"); }
    @Override public boolean _isPresent_ImplementationArtifact() { return isPresent_Field("ImplementationArtifact"); }
    @Override public void _unset_ImplementationArtifact() { unset_Field("ImplementationArtifact"); }
    @Override public void _setEmpty_ImplementationArtifact() { set_EmptyField("ImplementationArtifact"); }
    @Override public boolean _isEmpty_ImplementationArtifact() { return isEmpty_Field("ImplementationArtifact"); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.AIngLanguageType_1> getLanguagesList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.AIngLanguageType_1>) get_OrCreateCollectionField("LanguagesList", false); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.AIngLanguageType_1> _getRaw_LanguagesList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.AIngLanguageType_1>) get_RawField("LanguagesList"); }
    @Override public boolean _isPresent_LanguagesList() { return isPresent_Field("LanguagesList"); }
    @Override public void _unset_LanguagesList() { unset_Field("LanguagesList"); }
}
