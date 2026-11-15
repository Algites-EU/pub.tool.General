package eu.algites.tool.codegen.defs.naming.impl.intf;

/** Generated mutable contract derived from AIigDefsCodegenStructureNamingRule_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenStructureNamingRule", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd", namespaceLocalName = "DefsCodegenStructureNamingRule")
public interface AIigdDefsCodegenStructureNamingRule_1 extends eu.algites.tool.codegen.defs.naming.AIigDefsCodegenStructureNamingRule_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field Kind under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "kind", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 1, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Kind")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "kind", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ATTRIBUTE)
            @Override eu.algites.tool.codegen.defs.naming.AIngDefscodegenStructureKind_1 getKind();
    void setKind(eu.algites.tool.codegen.defs.naming.AIngDefscodegenStructureKind_1 aKind);
    eu.algites.tool.codegen.defs.naming.AIngDefscodegenStructureKind_1 _getRaw_Kind();
    boolean _isPresent_Kind();
    void _unset_Kind();
    /** Typed writable access to field Value under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "Value", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = true, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Value")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "Value", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.String getValue();
    void setValue(java.lang.String aValue);
    java.lang.String _getRaw_Value();
    boolean _isPresent_Value();
    void _unset_Value();
    void _setEmpty_Value();
    boolean _isEmpty_Value();
}
