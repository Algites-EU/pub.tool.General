package eu.algites.tool.codegen.defs.naming.impl.intf;

/** Generated mutable contract derived from AIigDefscodegenNamingConventionsPropertyNameConventions_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefscodegenNamingConventionsPropertyNameConventions", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type", schemaVersion = 1, schemaUrl = "", dataSourceSchemaUrlField = "", dataSourceSchemaIdentifierField = "", dataSourceSchemaVersionField = "")
public interface AIigdDefscodegenNamingConventionsPropertyNameConventions_1<TNameConventionList extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConvention_1<?>> extends eu.algites.tool.codegen.defs.naming.AIigDefscodegenNamingConventionsPropertyNameConventions_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field NameConventionList under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameConvention", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 0, minItemCount = 0, maxItemCount = -1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Name convention list")
        @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = "UniqueProfileIds", selector = "", fields = {"name"}, required = true)
            @Override eu.algites.lib.common.list.AIiMultiMappedList<? extends TNameConventionList> getNameConventionList();
    eu.algites.lib.common.list.AIiMultiMappedList<? extends TNameConventionList> _getRaw_NameConventionList();
    boolean _isPresent_NameConventionList();
    void _unset_NameConventionList();
}
