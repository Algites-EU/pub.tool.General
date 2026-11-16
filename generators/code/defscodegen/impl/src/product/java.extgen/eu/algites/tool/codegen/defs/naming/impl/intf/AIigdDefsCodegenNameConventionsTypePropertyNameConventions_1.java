package eu.algites.tool.codegen.defs.naming.impl.intf;

/** Generated mutable contract derived from AIigDefsCodegenNameConventionsTypePropertyNameConventions_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenNameConventionsTypePropertyNameConventions", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "", namespaceLocalName = "generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConventionsType/complexContent/extension/sequence/sequence/0/sequence/sequence/0#synthetic:synthetic_property_type")
public interface AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1<TNameConventionList extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConvention_1<?>> extends eu.algites.tool.codegen.defs.naming.AIigDefsCodegenNameConventionsTypePropertyNameConventions_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field NameConventionList under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameConvention", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 0, minItemCount = 0, maxItemCount = -1, isEmptyAllowed = false, setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Name convention list")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "NameConvention", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override eu.algites.lib.common.list.AIiMultiMappedList<? extends TNameConventionList> getNameConventionList();
    eu.algites.lib.common.list.AIiMultiMappedList<? extends TNameConventionList> _getRaw_NameConventionList();
    boolean _isPresent_NameConventionList();
    void _unset_NameConventionList();
}
