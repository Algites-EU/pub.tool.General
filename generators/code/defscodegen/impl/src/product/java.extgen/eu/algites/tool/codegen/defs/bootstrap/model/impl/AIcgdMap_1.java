package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigMap_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Ordinary or integrated property map", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Map", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Map", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Map", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigMap_1.class})
public class AIcgdMap_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdMap_1<eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindings_1<?>> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdMap_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdMap_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 getKeyType() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1) get_EffectiveField("KeyType"); }
    @Override public void setKeyType(eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 aKeyType) { set_RawField("KeyType", aKeyType); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 _getRaw_KeyType() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1) get_RawField("KeyType"); }
    @Override public boolean _isPresent_KeyType() { return isPresent_Field("KeyType"); }
    @Override public void _unset_KeyType() { unset_Field("KeyType"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngMapKind_1 getMapKind() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngMapKind_1) get_EffectiveField("MapKind"); }
    @Override public void setMapKind(eu.algites.tool.codegen.defs.bootstrap.model.AIngMapKind_1 aMapKind) { set_RawField("MapKind", aMapKind); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngMapKind_1 _getRaw_MapKind() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngMapKind_1) get_RawField("MapKind"); }
    @Override public boolean _isPresent_MapKind() { return isPresent_Field("MapKind"); }
    @Override public void _unset_MapKind() { unset_Field("MapKind"); }
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
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 getValueType() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1) get_EffectiveField("ValueType"); }
    @Override public void setValueType(eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 aValueType) { set_RawField("ValueType", aValueType); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1 _getRaw_ValueType() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIigStructure_1) get_RawField("ValueType"); }
    @Override public boolean _isPresent_ValueType() { return isPresent_Field("ValueType"); }
    @Override public void _unset_ValueType() { unset_Field("ValueType"); }
}
