package eu.algites.tool.codegen.defs.model.impl.intf;

/** Generated mutable contract derived from AIigSourceBindings_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Ordered source binding groups by technology. Corresponds to JSON/YAML SourceBindings sequence.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindings", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindings", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "SourceBindings")
public interface AIigdSourceBindings_1<TSourceBindingGroupList extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdSourceBindingGroup_1<?>> extends eu.algites.tool.codegen.defs.model.AIigSourceBindings_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field SourceBindingGroupList under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "SourceBindingGroup", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 0, minItemCount = 0, maxItemCount = -1, isEmptyAllowed = false, setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Source binding group list")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "SourceBindingGroup", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override eu.algites.lib.common.list.AIiBoundedList<? extends TSourceBindingGroupList> getSourceBindingGroupList();
    eu.algites.lib.common.list.AIiBoundedList<? extends TSourceBindingGroupList> _getRaw_SourceBindingGroupList();
    boolean _isPresent_SourceBindingGroupList();
    void _unset_SourceBindingGroupList();
}
