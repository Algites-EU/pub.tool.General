package eu.algites.tool.codegen.defs.naming.impl.intf;

/** Generated mutable contract derived from AIigDefscodegenNamingConventions_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "New defs naming profiles; other-domain roles forbidden.", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions", schemaVersion = 1, schemaUrl = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
public interface AIigdDefscodegenNamingConventions_1<TIdentifierConventions extends eu.algites.lib.naming.convention.impl.intf.AIigdIdentifierConventions_1<?>, TNameCompositions extends eu.algites.lib.naming.convention.impl.intf.AIigdNameCompositions_1<?>, TNameFragments extends eu.algites.lib.naming.convention.impl.intf.AIigdNameFragments_1<?>, TVersionConventions extends eu.algites.lib.naming.convention.impl.intf.AIigdVersionConventions_1<?>, TDefsCodegenNameConventions extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1<?>> extends eu.algites.tool.codegen.defs.naming.AIigDefscodegenNamingConventions_1, eu.algites.lib.naming.convention.impl.intf.AIigdCommonNamingConventions_1<TIdentifierConventions, TNameCompositions, TNameFragments, TVersionConventions>, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field IdentifierConventions under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "IdentifierConventions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 1, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Identifier conventions")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "IdentifierConventions", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = "UniqueIdentifierConventionNames", selector = "IdentifierConvention", fields = {"name"}, required = true)
            @Override TIdentifierConventions getIdentifierConventions();
    void setIdentifierConventions(TIdentifierConventions aIdentifierConventions);
    TIdentifierConventions _getRaw_IdentifierConventions();
    boolean _isPresent_IdentifierConventions();
    void _unset_IdentifierConventions();
    /** Typed writable access to field NameCompositions under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameCompositions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 4, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Name compositions")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "NameCompositions", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = "UniqueNameCompositionNames", selector = "NameComposition", fields = {"name"}, required = true)
            @Override TNameCompositions getNameCompositions();
    void setNameCompositions(TNameCompositions aNameCompositions);
    TNameCompositions _getRaw_NameCompositions();
    boolean _isPresent_NameCompositions();
    void _unset_NameCompositions();
    /** Typed writable access to field NameFragments under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameFragments", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 3, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Name fragments")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "NameFragments", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = "UniqueNameFragmentNames", selector = "NameFragment", fields = {"name"}, required = true)
            @Override TNameFragments getNameFragments();
    void setNameFragments(TNameFragments aNameFragments);
    TNameFragments _getRaw_NameFragments();
    boolean _isPresent_NameFragments();
    void _unset_NameFragments();
    /** Typed writable access to field StandardConventionsFile under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "StandardConventionsFile", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 0, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Standard conventions file")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "StandardConventionsFile", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override java.lang.String getStandardConventionsFile();
    void setStandardConventionsFile(java.lang.String aStandardConventionsFile);
    java.lang.String _getRaw_StandardConventionsFile();
    boolean _isPresent_StandardConventionsFile();
    void _unset_StandardConventionsFile();
    void _setEmpty_StandardConventionsFile();
    boolean _isEmpty_StandardConventionsFile();
    /** Typed writable access to field VersionConventions under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "VersionConventions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 2, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Version conventions")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "VersionConventions", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = "UniqueVersionConventionNames", selector = "VersionConvention", fields = {"name"}, required = true)
            @Override TVersionConventions getVersionConventions();
    void setVersionConventions(TVersionConventions aVersionConventions);
    TVersionConventions _getRaw_VersionConventions();
    boolean _isPresent_VersionConventions();
    void _unset_VersionConventions();
    /** Typed writable access to field DefsCodegenNameConventions under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "DefsCodegenNameConventions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Defs codegen name conventions")
                @Override TDefsCodegenNameConventions getDefsCodegenNameConventions();
    void setDefsCodegenNameConventions(TDefsCodegenNameConventions aDefsCodegenNameConventions);
    TDefsCodegenNameConventions _getRaw_DefsCodegenNameConventions();
    boolean _isPresent_DefsCodegenNameConventions();
    void _unset_DefsCodegenNameConventions();
}
