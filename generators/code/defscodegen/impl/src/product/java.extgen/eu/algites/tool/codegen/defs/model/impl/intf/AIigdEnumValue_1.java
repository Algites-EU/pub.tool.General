package eu.algites.tool.codegen.defs.model.impl.intf;

/** Generated mutable contract derived from AIigEnumValue_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Canonical enumeration value", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/EnumValue", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/EnumValue", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "EnumValue")
public interface AIigdEnumValue_1 extends eu.algites.tool.codegen.defs.model.AIigEnumValue_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field DisplayName under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "display_name", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 1, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Display name")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "display_name", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.String getDisplayName();
    void setDisplayName(java.lang.String aDisplayName);
    java.lang.String _getRaw_DisplayName();
    boolean _isPresent_DisplayName();
    void _unset_DisplayName();
    void _setEmpty_DisplayName();
    boolean _isEmpty_DisplayName();
    /** Typed writable access to field WireValue under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "wire_value", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Wire value")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "wire_value", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.String getWireValue();
    void setWireValue(java.lang.String aWireValue);
    java.lang.String _getRaw_WireValue();
    boolean _isPresent_WireValue();
    void _unset_WireValue();
    void _setEmpty_WireValue();
    boolean _isEmpty_WireValue();
}
