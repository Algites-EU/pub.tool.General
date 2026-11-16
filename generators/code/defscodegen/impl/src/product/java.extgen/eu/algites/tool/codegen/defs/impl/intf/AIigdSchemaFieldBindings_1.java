package eu.algites.tool.codegen.defs.impl.intf;

/** Generated mutable contract derived from AIigSchemaFieldBindings_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Root document selecting schemas and generation targets.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.jsondef.schema.json", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.schema-field-bindings", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.yamldef.schema.json", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "schema-field-bindings")
public interface AIigdSchemaFieldBindings_1<TBindingsList extends eu.algites.tool.codegen.defs.impl.intf.AIigdFieldBindingType_1, TLanguagesList extends eu.algites.tool.codegen.defs.AIngLanguageType_1> extends eu.algites.tool.codegen.defs.AIigSchemaFieldBindings_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field Artifact under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "artifact", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true, setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1, maxLength = -1, pattern = "")
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Artifact")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "artifact", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.String getArtifact();
    void setArtifact(java.lang.String aArtifact);
    java.lang.String _getRaw_Artifact();
    boolean _isPresent_Artifact();
    void _unset_Artifact();
    void _setEmpty_Artifact();
    boolean _isEmpty_Artifact();
    /** Typed writable access to field BindingsList under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "bindings", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 3, minItemCount = 1, maxItemCount = -1, isEmptyAllowed = false, setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints(minItems = 1, maxItems = -1, uniqueItems = false)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Bindings list")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "bindings", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override eu.algites.lib.common.list.AIiBoundedList<? extends TBindingsList> getBindingsList();
    eu.algites.lib.common.list.AIiBoundedList<? extends TBindingsList> _getRaw_BindingsList();
    boolean _isPresent_BindingsList();
    void _unset_BindingsList();
    /** Typed writable access to field ImplementationArtifact under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "implementation_artifact", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 1, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true, setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1, maxLength = -1, pattern = "")
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Implementation artifact")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "implementation_artifact", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.String getImplementationArtifact();
    void setImplementationArtifact(java.lang.String aImplementationArtifact);
    java.lang.String _getRaw_ImplementationArtifact();
    boolean _isPresent_ImplementationArtifact();
    void _unset_ImplementationArtifact();
    void _setEmpty_ImplementationArtifact();
    boolean _isEmpty_ImplementationArtifact();
    /** Typed writable access to field LanguagesList under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "languages", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 2, minItemCount = 1, maxItemCount = -1, isEmptyAllowed = false, setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints(minItems = 1, maxItems = -1, uniqueItems = false)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Languages list")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd", namespaceLocalName = "languages", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override eu.algites.lib.common.list.AIiBoundedList<? extends TLanguagesList> getLanguagesList();
    eu.algites.lib.common.list.AIiBoundedList<? extends TLanguagesList> _getRaw_LanguagesList();
    boolean _isPresent_LanguagesList();
    void _unset_LanguagesList();
}
