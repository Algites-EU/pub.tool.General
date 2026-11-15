package eu.algites.tool.codegen.defs.model.impl;

/** Generated mutable implementation of AIigScalar_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Canonical scalar value", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "Scalar")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.model.AIigScalar_1.class})
public class AIcgdScalar_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.model.impl.intf.AIigdScalar_1 {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdScalar_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdScalar_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public java.lang.Boolean getExclusiveMaximum() { return (java.lang.Boolean) get_EffectiveField("ExclusiveMaximum"); }
    @Override public void setExclusiveMaximum(java.lang.Boolean aExclusiveMaximum) { set_RawField("ExclusiveMaximum", aExclusiveMaximum); }
    @Override public java.lang.Boolean _getRaw_ExclusiveMaximum() { return (java.lang.Boolean) get_RawField("ExclusiveMaximum"); }
    @Override public boolean _isPresent_ExclusiveMaximum() { return isPresent_Field("ExclusiveMaximum"); }
    @Override public void _unset_ExclusiveMaximum() { unset_Field("ExclusiveMaximum"); }
    @Override public java.lang.Boolean getExclusiveMinimum() { return (java.lang.Boolean) get_EffectiveField("ExclusiveMinimum"); }
    @Override public void setExclusiveMinimum(java.lang.Boolean aExclusiveMinimum) { set_RawField("ExclusiveMinimum", aExclusiveMinimum); }
    @Override public java.lang.Boolean _getRaw_ExclusiveMinimum() { return (java.lang.Boolean) get_RawField("ExclusiveMinimum"); }
    @Override public boolean _isPresent_ExclusiveMinimum() { return isPresent_Field("ExclusiveMinimum"); }
    @Override public void _unset_ExclusiveMinimum() { unset_Field("ExclusiveMinimum"); }
    @Override public java.lang.String getFormat() { return (java.lang.String) get_EffectiveField("Format"); }
    @Override public void setFormat(java.lang.String aFormat) { set_RawField("Format", aFormat); }
    @Override public java.lang.String _getRaw_Format() { return (java.lang.String) get_RawField("Format"); }
    @Override public boolean _isPresent_Format() { return isPresent_Field("Format"); }
    @Override public void _unset_Format() { unset_Field("Format"); }
    @Override public void _setEmpty_Format() { set_EmptyField("Format"); }
    @Override public boolean _isEmpty_Format() { return isEmpty_Field("Format"); }
    @Override public java.lang.Long getMaxLength() { return (java.lang.Long) get_EffectiveField("MaxLength"); }
    @Override public void setMaxLength(java.lang.Long aMaxLength) { set_RawField("MaxLength", aMaxLength); }
    @Override public java.lang.Long _getRaw_MaxLength() { return (java.lang.Long) get_RawField("MaxLength"); }
    @Override public boolean _isPresent_MaxLength() { return isPresent_Field("MaxLength"); }
    @Override public void _unset_MaxLength() { unset_Field("MaxLength"); }
    @Override public java.lang.String getMaximum() { return (java.lang.String) get_EffectiveField("Maximum"); }
    @Override public void setMaximum(java.lang.String aMaximum) { set_RawField("Maximum", aMaximum); }
    @Override public java.lang.String _getRaw_Maximum() { return (java.lang.String) get_RawField("Maximum"); }
    @Override public boolean _isPresent_Maximum() { return isPresent_Field("Maximum"); }
    @Override public void _unset_Maximum() { unset_Field("Maximum"); }
    @Override public void _setEmpty_Maximum() { set_EmptyField("Maximum"); }
    @Override public boolean _isEmpty_Maximum() { return isEmpty_Field("Maximum"); }
    @Override public java.lang.Long getMinLength() { return (java.lang.Long) get_EffectiveField("MinLength"); }
    @Override public void setMinLength(java.lang.Long aMinLength) { set_RawField("MinLength", aMinLength); }
    @Override public java.lang.Long _getRaw_MinLength() { return (java.lang.Long) get_RawField("MinLength"); }
    @Override public boolean _isPresent_MinLength() { return isPresent_Field("MinLength"); }
    @Override public void _unset_MinLength() { unset_Field("MinLength"); }
    @Override public java.lang.String getMinimum() { return (java.lang.String) get_EffectiveField("Minimum"); }
    @Override public void setMinimum(java.lang.String aMinimum) { set_RawField("Minimum", aMinimum); }
    @Override public java.lang.String _getRaw_Minimum() { return (java.lang.String) get_RawField("Minimum"); }
    @Override public boolean _isPresent_Minimum() { return isPresent_Field("Minimum"); }
    @Override public void _unset_Minimum() { unset_Field("Minimum"); }
    @Override public void _setEmpty_Minimum() { set_EmptyField("Minimum"); }
    @Override public boolean _isEmpty_Minimum() { return isEmpty_Field("Minimum"); }
    @Override public java.lang.String getMultipleOf() { return (java.lang.String) get_EffectiveField("MultipleOf"); }
    @Override public void setMultipleOf(java.lang.String aMultipleOf) { set_RawField("MultipleOf", aMultipleOf); }
    @Override public java.lang.String _getRaw_MultipleOf() { return (java.lang.String) get_RawField("MultipleOf"); }
    @Override public boolean _isPresent_MultipleOf() { return isPresent_Field("MultipleOf"); }
    @Override public void _unset_MultipleOf() { unset_Field("MultipleOf"); }
    @Override public void _setEmpty_MultipleOf() { set_EmptyField("MultipleOf"); }
    @Override public boolean _isEmpty_MultipleOf() { return isEmpty_Field("MultipleOf"); }
    @Override public java.lang.String getPattern() { return (java.lang.String) get_EffectiveField("Pattern"); }
    @Override public void setPattern(java.lang.String aPattern) { set_RawField("Pattern", aPattern); }
    @Override public java.lang.String _getRaw_Pattern() { return (java.lang.String) get_RawField("Pattern"); }
    @Override public boolean _isPresent_Pattern() { return isPresent_Field("Pattern"); }
    @Override public void _unset_Pattern() { unset_Field("Pattern"); }
    @Override public void _setEmpty_Pattern() { set_EmptyField("Pattern"); }
    @Override public boolean _isEmpty_Pattern() { return isEmpty_Field("Pattern"); }
    @Override public eu.algites.tool.codegen.defs.model.AIngScalarKind_1 getScalarKind() { return (eu.algites.tool.codegen.defs.model.AIngScalarKind_1) get_EffectiveField("ScalarKind"); }
    @Override public void setScalarKind(eu.algites.tool.codegen.defs.model.AIngScalarKind_1 aScalarKind) { set_RawField("ScalarKind", aScalarKind); }
    @Override public eu.algites.tool.codegen.defs.model.AIngScalarKind_1 _getRaw_ScalarKind() { return (eu.algites.tool.codegen.defs.model.AIngScalarKind_1) get_RawField("ScalarKind"); }
    @Override public boolean _isPresent_ScalarKind() { return isPresent_Field("ScalarKind"); }
    @Override public void _unset_ScalarKind() { unset_Field("ScalarKind"); }
}
