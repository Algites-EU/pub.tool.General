package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigSourceBindingGroup_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "One source technology and all ordered bindings from that technology.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindingGroup", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindingGroup", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindingGroup", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigSourceBindingGroup_1.class})
public class AIcgdSourceBindingGroup_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBindingGroup_1<eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBinding_1> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdSourceBindingGroup_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdSourceBindingGroup_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBinding_1> getBindingList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBinding_1>) get_OrCreateCollectionField("BindingList", false); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBinding_1> _getRaw_BindingList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdSourceBinding_1>) get_RawField("BindingList"); }
    @Override public boolean _isPresent_BindingList() { return isPresent_Field("BindingList"); }
    @Override public void _unset_BindingList() { unset_Field("BindingList"); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1 getInputKind() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1) get_EffectiveField("InputKind"); }
    @Override public void setInputKind(eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1 aInputKind) { set_RawField("InputKind", aInputKind); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1 _getRaw_InputKind() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1) get_RawField("InputKind"); }
    @Override public boolean _isPresent_InputKind() { return isPresent_Field("InputKind"); }
    @Override public void _unset_InputKind() { unset_Field("InputKind"); }
}
