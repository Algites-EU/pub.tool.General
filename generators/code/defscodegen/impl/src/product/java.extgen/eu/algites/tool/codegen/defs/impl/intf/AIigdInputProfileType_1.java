package eu.algites.tool.codegen.defs.impl.intf;

/** Generated mutable contract derived from AIigInputProfileType_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "Defines how defs-codegen interprets one supported source-definition family.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.input-profile#/$defs/InputProfileType", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.input-profile#/$defs/InputProfileType", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "InputProfileType")
public interface AIigdInputProfileType_1 extends eu.algites.tool.codegen.defs.AIigInputProfileType_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field NamingProfile under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NamingProfile", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 1, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Naming profile")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "NamingProfile", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.String getNamingProfile();
    void setNamingProfile(java.lang.String aNamingProfile);
    java.lang.String _getRaw_NamingProfile();
    boolean _isPresent_NamingProfile();
    void _unset_NamingProfile();
    void _setEmpty_NamingProfile();
    boolean _isEmpty_NamingProfile();
    /** Typed writable access to field RequireCanonicalIdentity under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "RequireCanonicalIdentity", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 2, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Require canonical identity")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "RequireCanonicalIdentity", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.Boolean getRequireCanonicalIdentity();
    void setRequireCanonicalIdentity(java.lang.Boolean aRequireCanonicalIdentity);
    java.lang.Boolean _getRaw_RequireCanonicalIdentity();
    boolean _isPresent_RequireCanonicalIdentity();
    void _unset_RequireCanonicalIdentity();
    /** Typed writable access to field RequireDefinitionVersion under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "RequireDefinitionVersion", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 3, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Require definition version")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "RequireDefinitionVersion", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.Boolean getRequireDefinitionVersion();
    void setRequireDefinitionVersion(java.lang.Boolean aRequireDefinitionVersion);
    java.lang.Boolean _getRaw_RequireDefinitionVersion();
    boolean _isPresent_RequireDefinitionVersion();
    void _unset_RequireDefinitionVersion();
    /** Typed writable access to field SourceKind under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "SourceKind", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Source kind")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd", namespaceLocalName = "SourceKind", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override eu.algites.tool.codegen.defs.AIngSourceKindType_1 getSourceKind();
    void setSourceKind(eu.algites.tool.codegen.defs.AIngSourceKindType_1 aSourceKind);
    eu.algites.tool.codegen.defs.AIngSourceKindType_1 _getRaw_SourceKind();
    boolean _isPresent_SourceKind();
    void _unset_SourceKind();
}
