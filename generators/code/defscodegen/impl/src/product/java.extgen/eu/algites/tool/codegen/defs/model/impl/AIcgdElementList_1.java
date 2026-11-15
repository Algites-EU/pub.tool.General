package eu.algites.tool.codegen.defs.model.impl;

/** Generated mutable implementation of AIigElementList_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Ordered composition of structural children", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementList", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementList", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "ElementList")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.model.AIigElementList_1.class})
public class AIcgdElementList_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.model.impl.intf.AIigdElementList_1<eu.algites.tool.codegen.defs.model.AIigElementListChild_1> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdElementList_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdElementList_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.AIigElementListChild_1> getChildrenList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.AIigElementListChild_1>) get_OrCreateCollectionField("ChildrenList", false); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.AIigElementListChild_1> _getRaw_ChildrenList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.AIigElementListChild_1>) get_RawField("ChildrenList"); }
    @Override public boolean _isPresent_ChildrenList() { return isPresent_Field("ChildrenList"); }
    @Override public void _unset_ChildrenList() { unset_Field("ChildrenList"); }
    @Override public eu.algites.tool.codegen.defs.model.AIngComposition_1 getComposition() { return (eu.algites.tool.codegen.defs.model.AIngComposition_1) get_EffectiveField("Composition"); }
    @Override public void setComposition(eu.algites.tool.codegen.defs.model.AIngComposition_1 aComposition) { set_RawField("Composition", aComposition); }
    @Override public eu.algites.tool.codegen.defs.model.AIngComposition_1 _getRaw_Composition() { return (eu.algites.tool.codegen.defs.model.AIngComposition_1) get_RawField("Composition"); }
    @Override public boolean _isPresent_Composition() { return isPresent_Field("Composition"); }
    @Override public void _unset_Composition() { unset_Field("Composition"); }
    @Override public java.lang.Long getMaxItemCount() { return (java.lang.Long) get_EffectiveField("MaxItemCount"); }
    @Override public void setMaxItemCount(java.lang.Long aMaxItemCount) { set_RawField("MaxItemCount", aMaxItemCount); }
    @Override public java.lang.Long _getRaw_MaxItemCount() { return (java.lang.Long) get_RawField("MaxItemCount"); }
    @Override public boolean _isPresent_MaxItemCount() { return isPresent_Field("MaxItemCount"); }
    @Override public void _unset_MaxItemCount() { unset_Field("MaxItemCount"); }
    @Override public java.lang.Long getMaxProperties() { return (java.lang.Long) get_EffectiveField("MaxProperties"); }
    @Override public void setMaxProperties(java.lang.Long aMaxProperties) { set_RawField("MaxProperties", aMaxProperties); }
    @Override public java.lang.Long _getRaw_MaxProperties() { return (java.lang.Long) get_RawField("MaxProperties"); }
    @Override public boolean _isPresent_MaxProperties() { return isPresent_Field("MaxProperties"); }
    @Override public void _unset_MaxProperties() { unset_Field("MaxProperties"); }
    @Override public java.lang.Long getMinItemCount() { return (java.lang.Long) get_EffectiveField("MinItemCount"); }
    @Override public void setMinItemCount(java.lang.Long aMinItemCount) { set_RawField("MinItemCount", aMinItemCount); }
    @Override public java.lang.Long _getRaw_MinItemCount() { return (java.lang.Long) get_RawField("MinItemCount"); }
    @Override public boolean _isPresent_MinItemCount() { return isPresent_Field("MinItemCount"); }
    @Override public void _unset_MinItemCount() { unset_Field("MinItemCount"); }
    @Override public java.lang.Long getMinProperties() { return (java.lang.Long) get_EffectiveField("MinProperties"); }
    @Override public void setMinProperties(java.lang.Long aMinProperties) { set_RawField("MinProperties", aMinProperties); }
    @Override public java.lang.Long _getRaw_MinProperties() { return (java.lang.Long) get_RawField("MinProperties"); }
    @Override public boolean _isPresent_MinProperties() { return isPresent_Field("MinProperties"); }
    @Override public void _unset_MinProperties() { unset_Field("MinProperties"); }
}
