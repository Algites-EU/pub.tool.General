package eu.algites.tool.codegen.defs.bootstrap.model.impl;

/** Generated mutable implementation of AIigEnum_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Canonical enumeration", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaJsonDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaYamlDataObject(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.bootstrap.model.AIigEnum_1.class})
public class AIcgdEnum_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdEnum_1<eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdEnumValue_1> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdEnum_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdEnum_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1 getBaseScalarType() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1) get_EffectiveField("BaseScalarType"); }
    @Override public void setBaseScalarType(eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1 aBaseScalarType) { set_RawField("BaseScalarType", aBaseScalarType); }
    @Override public eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1 _getRaw_BaseScalarType() { return (eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1) get_RawField("BaseScalarType"); }
    @Override public boolean _isPresent_BaseScalarType() { return isPresent_Field("BaseScalarType"); }
    @Override public void _unset_BaseScalarType() { unset_Field("BaseScalarType"); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdEnumValue_1> getValuesList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdEnumValue_1>) get_OrCreateCollectionField("ValuesList", false); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdEnumValue_1> _getRaw_ValuesList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.AIigdEnumValue_1>) get_RawField("ValuesList"); }
    @Override public boolean _isPresent_ValuesList() { return isPresent_Field("ValuesList"); }
    @Override public void _unset_ValuesList() { unset_Field("ValuesList"); }
}
