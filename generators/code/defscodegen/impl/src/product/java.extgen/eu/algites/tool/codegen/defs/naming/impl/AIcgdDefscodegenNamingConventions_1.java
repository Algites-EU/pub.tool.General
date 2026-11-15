package eu.algites.tool.codegen.defs.naming.impl;

/** Generated mutable implementation of AIigDefscodegenNamingConventions_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "New defs naming profiles; other-domain roles forbidden.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.naming.AIigDefscodegenNamingConventions_1.class})
public class AIcgdDefscodegenNamingConventions_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventions_1<eu.algites.lib.naming.convention.impl.intf.AIigdIdentifierConventions_1<?>, eu.algites.lib.naming.convention.impl.intf.AIigdNameCompositions_1<?>, eu.algites.lib.naming.convention.impl.intf.AIigdNameFragments_1<?>, eu.algites.lib.naming.convention.impl.intf.AIigdVersionConventions_1<?>, eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1<?>> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdDefscodegenNamingConventions_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdDefscodegenNamingConventions_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.lib.naming.convention.impl.intf.AIigdIdentifierConventions_1<?> getIdentifierConventions() { return (eu.algites.lib.naming.convention.impl.intf.AIigdIdentifierConventions_1<?>) get_EffectiveField("IdentifierConventions"); }
    @Override public void setIdentifierConventions(eu.algites.lib.naming.convention.impl.intf.AIigdIdentifierConventions_1<?> aIdentifierConventions) { set_RawField("IdentifierConventions", aIdentifierConventions); }
    @Override public eu.algites.lib.naming.convention.impl.intf.AIigdIdentifierConventions_1<?> _getRaw_IdentifierConventions() { return (eu.algites.lib.naming.convention.impl.intf.AIigdIdentifierConventions_1<?>) get_RawField("IdentifierConventions"); }
    @Override public boolean _isPresent_IdentifierConventions() { return isPresent_Field("IdentifierConventions"); }
    @Override public void _unset_IdentifierConventions() { unset_Field("IdentifierConventions"); }
    @Override public eu.algites.lib.naming.convention.impl.intf.AIigdNameCompositions_1<?> getNameCompositions() { return (eu.algites.lib.naming.convention.impl.intf.AIigdNameCompositions_1<?>) get_EffectiveField("NameCompositions"); }
    @Override public void setNameCompositions(eu.algites.lib.naming.convention.impl.intf.AIigdNameCompositions_1<?> aNameCompositions) { set_RawField("NameCompositions", aNameCompositions); }
    @Override public eu.algites.lib.naming.convention.impl.intf.AIigdNameCompositions_1<?> _getRaw_NameCompositions() { return (eu.algites.lib.naming.convention.impl.intf.AIigdNameCompositions_1<?>) get_RawField("NameCompositions"); }
    @Override public boolean _isPresent_NameCompositions() { return isPresent_Field("NameCompositions"); }
    @Override public void _unset_NameCompositions() { unset_Field("NameCompositions"); }
    @Override public eu.algites.lib.naming.convention.impl.intf.AIigdNameFragments_1<?> getNameFragments() { return (eu.algites.lib.naming.convention.impl.intf.AIigdNameFragments_1<?>) get_EffectiveField("NameFragments"); }
    @Override public void setNameFragments(eu.algites.lib.naming.convention.impl.intf.AIigdNameFragments_1<?> aNameFragments) { set_RawField("NameFragments", aNameFragments); }
    @Override public eu.algites.lib.naming.convention.impl.intf.AIigdNameFragments_1<?> _getRaw_NameFragments() { return (eu.algites.lib.naming.convention.impl.intf.AIigdNameFragments_1<?>) get_RawField("NameFragments"); }
    @Override public boolean _isPresent_NameFragments() { return isPresent_Field("NameFragments"); }
    @Override public void _unset_NameFragments() { unset_Field("NameFragments"); }
    @Override public java.lang.String getStandardConventionsFile() { return (java.lang.String) get_EffectiveField("StandardConventionsFile"); }
    @Override public void setStandardConventionsFile(java.lang.String aStandardConventionsFile) { set_RawField("StandardConventionsFile", aStandardConventionsFile); }
    @Override public java.lang.String _getRaw_StandardConventionsFile() { return (java.lang.String) get_RawField("StandardConventionsFile"); }
    @Override public boolean _isPresent_StandardConventionsFile() { return isPresent_Field("StandardConventionsFile"); }
    @Override public void _unset_StandardConventionsFile() { unset_Field("StandardConventionsFile"); }
    @Override public void _setEmpty_StandardConventionsFile() { set_EmptyField("StandardConventionsFile"); }
    @Override public boolean _isEmpty_StandardConventionsFile() { return isEmpty_Field("StandardConventionsFile"); }
    @Override public eu.algites.lib.naming.convention.impl.intf.AIigdVersionConventions_1<?> getVersionConventions() { return (eu.algites.lib.naming.convention.impl.intf.AIigdVersionConventions_1<?>) get_EffectiveField("VersionConventions"); }
    @Override public void setVersionConventions(eu.algites.lib.naming.convention.impl.intf.AIigdVersionConventions_1<?> aVersionConventions) { set_RawField("VersionConventions", aVersionConventions); }
    @Override public eu.algites.lib.naming.convention.impl.intf.AIigdVersionConventions_1<?> _getRaw_VersionConventions() { return (eu.algites.lib.naming.convention.impl.intf.AIigdVersionConventions_1<?>) get_RawField("VersionConventions"); }
    @Override public boolean _isPresent_VersionConventions() { return isPresent_Field("VersionConventions"); }
    @Override public void _unset_VersionConventions() { unset_Field("VersionConventions"); }
    @Override public eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1<?> getDefsCodegenNameConventions() { return (eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1<?>) get_EffectiveField("DefsCodegenNameConventions"); }
    @Override public void setDefsCodegenNameConventions(eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1<?> aDefsCodegenNameConventions) { set_RawField("DefsCodegenNameConventions", aDefsCodegenNameConventions); }
    @Override public eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1<?> _getRaw_DefsCodegenNameConventions() { return (eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1<?>) get_RawField("DefsCodegenNameConventions"); }
    @Override public boolean _isPresent_DefsCodegenNameConventions() { return isPresent_Field("DefsCodegenNameConventions"); }
    @Override public void _unset_DefsCodegenNameConventions() { unset_Field("DefsCodegenNameConventions"); }
}
