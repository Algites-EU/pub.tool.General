package eu.algites.tool.codegen.defs.model.impl;

/** Generated mutable implementation of AIigSourceBindings_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Ordered source binding groups by technology. Corresponds to JSON/YAML SourceBindings sequence.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindings", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindings", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "SourceBindings")
@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding(readContracts = {eu.algites.tool.codegen.defs.model.AIigSourceBindings_1.class})
public class AIcgdSourceBindings_1 extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject implements eu.algites.tool.codegen.defs.model.impl.intf.AIigdSourceBindings_1<eu.algites.tool.codegen.defs.model.impl.intf.AIigdSourceBindingGroup_1<?>> {
    /** Create an object whose raw fields are initially absent. */
    public AIcgdSourceBindings_1() { super(); }
    /** Reconstruct an identity-preserving typed SmartDataObject graph. */
    public AIcgdSourceBindings_1(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdSourceBindingGroup_1<?>> getSourceBindingGroupList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdSourceBindingGroup_1<?>>) get_OrCreateCollectionField("SourceBindingGroupList", false); }
    @Override public eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdSourceBindingGroup_1<?>> _getRaw_SourceBindingGroupList() { return (eu.algites.lib.common.list.AIiBoundedList<? extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdSourceBindingGroup_1<?>>) get_RawField("SourceBindingGroupList"); }
    @Override public boolean _isPresent_SourceBindingGroupList() { return isPresent_Field("SourceBindingGroupList"); }
    @Override public void _unset_SourceBindingGroupList() { unset_Field("SourceBindingGroupList"); }
}
