package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigList_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Homogeneous collection", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigList_1.class})
public class AIcgdList_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdList_1<eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>, eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdList_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdList_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 getItem() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1) get_EffectiveField("Item"); }
    @Override public void setItem(eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 aItem) { set_RawField("Item", aItem); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 _getRaw_Item() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1) get_RawField("Item"); }
    @Override public boolean _isPresent_Item() { return isPresent_Field("Item"); }
    @Override public void _unset_Item() { unset_Field("Item"); }
    @Override public java.util.List<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>> getKeyDefinitionsList() { return (java.util.List<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>>) get_OrCreateCollectionField("KeyDefinitionsList", false); }
    @Override public java.util.List<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>> _getRaw_KeyDefinitionsList() { return (java.util.List<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdKeyDefinition_1<?>>) get_RawField("KeyDefinitionsList"); }
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
    @Override public java.lang.Boolean getUniqueItems() { return (java.lang.Boolean) get_EffectiveField("UniqueItems"); }
    @Override public void setUniqueItems(java.lang.Boolean aUniqueItems) { set_RawField("UniqueItems", aUniqueItems); }
    @Override public java.lang.Boolean _getRaw_UniqueItems() { return (java.lang.Boolean) get_RawField("UniqueItems"); }
    @Override public boolean _isPresent_UniqueItems() { return isPresent_Field("UniqueItems"); }
    @Override public void _unset_UniqueItems() { unset_Field("UniqueItems"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1 getXmlWire() { return (eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1) get_EffectiveField("XmlWire"); }
    @Override public void setXmlWire(eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1 aXmlWire) { set_RawField("XmlWire", aXmlWire); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1 _getRaw_XmlWire() { return (eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdXmlWireName_1) get_RawField("XmlWire"); }
    @Override public boolean _isPresent_XmlWire() { return isPresent_Field("XmlWire"); }
    @Override public void _unset_XmlWire() { unset_Field("XmlWire"); }
}
