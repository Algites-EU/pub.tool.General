package eu.algites.tool.codegen.defs.naming.impl.intf;

/** Generated mutable contract derived from AIigDefsCodegenNameConvention_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenNameConvention", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd", namespaceLocalName = "DefsCodegenNameConvention")
public interface AIigdDefsCodegenNameConvention_1<TStructureNaming extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionPropertyStructureNaming_1<?>> extends eu.algites.tool.codegen.defs.naming.AIigDefsCodegenNameConvention_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field CommonNamingConvention under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "CommonNamingConvention", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Common naming convention")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "CommonNamingConvention", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.String getCommonNamingConvention();
    void setCommonNamingConvention(java.lang.String aCommonNamingConvention);
    java.lang.String _getRaw_CommonNamingConvention();
    boolean _isPresent_CommonNamingConvention();
    void _unset_CommonNamingConvention();
    void _setEmpty_CommonNamingConvention();
    boolean _isEmpty_CommonNamingConvention();
    /** Typed writable access to field Name under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "name", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 2, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1, maxLength = -1, pattern = "")
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Name")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "name", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ATTRIBUTE)
            @Override java.lang.String getName();
    void setName(java.lang.String aName);
    java.lang.String _getRaw_Name();
    boolean _isPresent_Name();
    void _unset_Name();
    void _setEmpty_Name();
    boolean _isEmpty_Name();
    /** Typed writable access to field StructureNaming under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "StructureNaming", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 1, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Structure naming")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "StructureNaming", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = "UniqueStructureRoles", selector = "Rule", fields = {"kind"}, required = true)
            @Override TStructureNaming getStructureNaming();
    void setStructureNaming(TStructureNaming aStructureNaming);
    TStructureNaming _getRaw_StructureNaming();
    boolean _isPresent_StructureNaming();
    void _unset_StructureNaming();
}
