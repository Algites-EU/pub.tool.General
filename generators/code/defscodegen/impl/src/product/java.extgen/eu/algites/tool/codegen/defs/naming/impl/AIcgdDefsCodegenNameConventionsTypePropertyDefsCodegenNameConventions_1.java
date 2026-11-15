package eu.algites.tool.codegen.defs.naming.impl;

/** Generated mutable implementation of AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.naming.AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1.class})
public class AIcgdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1<eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1<?>> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1<?> getNameConventions() { return (eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1<?>) get_EffectiveField("NameConventions"); }
    @Override public void setNameConventions(eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1<?> aNameConventions) { set_RawField("NameConventions", aNameConventions); }
    @Override public eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1<?> _getRaw_NameConventions() { return (eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1<?>) get_RawField("NameConventions"); }
    @Override public boolean _isPresent_NameConventions() { return isPresent_Field("NameConventions"); }
    @Override public void _unset_NameConventions() { unset_Field("NameConventions"); }
}
