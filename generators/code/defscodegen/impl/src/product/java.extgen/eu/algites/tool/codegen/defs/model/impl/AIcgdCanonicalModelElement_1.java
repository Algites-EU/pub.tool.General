package eu.algites.tool.codegen.defs.model.impl;

/** Generated mutable implementation of AIigCanonicalModelElement_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "CanonicalModelElement", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "CanonicalModel")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.model.AIigCanonicalModelElement_1.class})
public class AIcgdCanonicalModelElement_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.model.impl.intf.AIigdCanonicalModelElement_1<eu.algites.tool.codegen.defs.model.impl.intf.AIigdType_1<?, ?, ?>> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdCanonicalModelElement_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdCanonicalModelElement_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdType_1<?, ?, ?>> getTypesList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdType_1<?, ?, ?>>) get_OrCreateCollectionField("TypesList", false); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdType_1<?, ?, ?>> _getRaw_TypesList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdType_1<?, ?, ?>>) get_RawField("TypesList"); }
    @Override public boolean _isPresent_TypesList() { return isPresent_Field("TypesList"); }
    @Override public void _unset_TypesList() { unset_Field("TypesList"); }
}
