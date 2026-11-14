package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigElement_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Member of an ELEMENTLIST: referenced serialized member or unnamed embedded structural group.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigElement_1.class})
public class AIcgdElement_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdElement_1<eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>, eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?>, eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdElement_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdElement_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.lang.String getDefaultKind() { return (java.lang.String) get_EffectiveField("DefaultKind"); }
    @Override public void setDefaultKind(java.lang.String aDefaultKind) { set_RawField("DefaultKind", aDefaultKind); }
    @Override public java.lang.String _getRaw_DefaultKind() { return (java.lang.String) get_RawField("DefaultKind"); }
    @Override public boolean _isPresent_DefaultKind() { return isPresent_Field("DefaultKind"); }
    @Override public void _unset_DefaultKind() { unset_Field("DefaultKind"); }
    @Override public void _setEmpty_DefaultKind() { set_EmptyField("DefaultKind"); }
    @Override public boolean _isEmpty_DefaultKind() { return isEmpty_Field("DefaultKind"); }
    @Override public java.lang.String getDefaultValue() { return (java.lang.String) get_EffectiveField("DefaultValue"); }
    @Override public void setDefaultValue(java.lang.String aDefaultValue) { set_RawField("DefaultValue", aDefaultValue); }
    @Override public java.lang.String _getRaw_DefaultValue() { return (java.lang.String) get_RawField("DefaultValue"); }
    @Override public boolean _isPresent_DefaultValue() { return isPresent_Field("DefaultValue"); }
    @Override public void _unset_DefaultValue() { unset_Field("DefaultValue"); }
    @Override public void _setEmpty_DefaultValue() { set_EmptyField("DefaultValue"); }
    @Override public boolean _isEmpty_DefaultValue() { return isEmpty_Field("DefaultValue"); }
    @Override public java.lang.String getDescription() { return (java.lang.String) get_EffectiveField("Description"); }
    @Override public void setDescription(java.lang.String aDescription) { set_RawField("Description", aDescription); }
    @Override public java.lang.String _getRaw_Description() { return (java.lang.String) get_RawField("Description"); }
    @Override public boolean _isPresent_Description() { return isPresent_Field("Description"); }
    @Override public void _unset_Description() { unset_Field("Description"); }
    @Override public void _setEmpty_Description() { set_EmptyField("Description"); }
    @Override public boolean _isEmpty_Description() { return isEmpty_Field("Description"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngElementKind_1 getElementKind() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngElementKind_1) get_EffectiveField("ElementKind"); }
    @Override public void setElementKind(eu.algites.tool.codegen.defs.bootstrap.model.AIngElementKind_1 aElementKind) { set_RawField("ElementKind", aElementKind); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngElementKind_1 _getRaw_ElementKind() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngElementKind_1) get_RawField("ElementKind"); }
    @Override public boolean _isPresent_ElementKind() { return isPresent_Field("ElementKind"); }
    @Override public void _unset_ElementKind() { unset_Field("ElementKind"); }
    @Override public java.lang.Boolean getIsEmptyAllowed() { return (java.lang.Boolean) get_EffectiveField("IsEmptyAllowed"); }
    @Override public void setIsEmptyAllowed(java.lang.Boolean aIsEmptyAllowed) { set_RawField("IsEmptyAllowed", aIsEmptyAllowed); }
    @Override public java.lang.Boolean _getRaw_IsEmptyAllowed() { return (java.lang.Boolean) get_RawField("IsEmptyAllowed"); }
    @Override public boolean _isPresent_IsEmptyAllowed() { return isPresent_Field("IsEmptyAllowed"); }
    @Override public void _unset_IsEmptyAllowed() { unset_Field("IsEmptyAllowed"); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>> getKeyDefinitionsList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>>) get_OrCreateCollectionField("KeyDefinitionsList", false); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>> _getRaw_KeyDefinitionsList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>>) get_RawField("KeyDefinitionsList"); }
    @Override public boolean _isPresent_KeyDefinitionsList() { return isPresent_Field("KeyDefinitionsList"); }
    @Override public void _unset_KeyDefinitionsList() { unset_Field("KeyDefinitionsList"); }
    @Override public java.lang.Long getMaxItemCount() { return (java.lang.Long) get_EffectiveField("MaxItemCount"); }
    @Override public void setMaxItemCount(java.lang.Long aMaxItemCount) { set_RawField("MaxItemCount", aMaxItemCount); }
    @Override public java.lang.Long _getRaw_MaxItemCount() { return (java.lang.Long) get_RawField("MaxItemCount"); }
    @Override public boolean _isPresent_MaxItemCount() { return isPresent_Field("MaxItemCount"); }
    @Override public void _unset_MaxItemCount() { unset_Field("MaxItemCount"); }
    @Override public java.lang.Long getMinItemCount() { return (java.lang.Long) get_EffectiveField("MinItemCount"); }
    @Override public void setMinItemCount(java.lang.Long aMinItemCount) { set_RawField("MinItemCount", aMinItemCount); }
    @Override public java.lang.Long _getRaw_MinItemCount() { return (java.lang.Long) get_RawField("MinItemCount"); }
    @Override public boolean _isPresent_MinItemCount() { return isPresent_Field("MinItemCount"); }
    @Override public void _unset_MinItemCount() { unset_Field("MinItemCount"); }
    @Override public java.lang.String getName() { return (java.lang.String) get_EffectiveField("Name"); }
    @Override public void setName(java.lang.String aName) { set_RawField("Name", aName); }
    @Override public java.lang.String _getRaw_Name() { return (java.lang.String) get_RawField("Name"); }
    @Override public boolean _isPresent_Name() { return isPresent_Field("Name"); }
    @Override public void _unset_Name() { unset_Field("Name"); }
    @Override public void _setEmpty_Name() { set_EmptyField("Name"); }
    @Override public boolean _isEmpty_Name() { return isEmpty_Field("Name"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?> getSourceBindings() { return (eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?>) get_EffectiveField("SourceBindings"); }
    @Override public void setSourceBindings(eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?> aSourceBindings) { set_RawField("SourceBindings", aSourceBindings); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?> _getRaw_SourceBindings() { return (eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?>) get_RawField("SourceBindings"); }
    @Override public boolean _isPresent_SourceBindings() { return isPresent_Field("SourceBindings"); }
    @Override public void _unset_SourceBindings() { unset_Field("SourceBindings"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 getStructure() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1) get_EffectiveField("Structure"); }
    @Override public void setStructure(eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 aStructure) { set_RawField("Structure", aStructure); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 _getRaw_Structure() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1) get_RawField("Structure"); }
    @Override public boolean _isPresent_Structure() { return isPresent_Field("Structure"); }
    @Override public void _unset_Structure() { unset_Field("Structure"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1 getXmlWire() { return (eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1) get_EffectiveField("XmlWire"); }
    @Override public void setXmlWire(eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1 aXmlWire) { set_RawField("XmlWire", aXmlWire); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1 _getRaw_XmlWire() { return (eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1) get_RawField("XmlWire"); }
    @Override public boolean _isPresent_XmlWire() { return isPresent_Field("XmlWire"); }
    @Override public void _unset_XmlWire() { unset_Field("XmlWire"); }
}
