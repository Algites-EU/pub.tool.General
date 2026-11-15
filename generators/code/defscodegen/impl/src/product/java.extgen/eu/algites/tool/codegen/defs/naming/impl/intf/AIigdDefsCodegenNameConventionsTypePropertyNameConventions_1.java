package eu.algites.tool.codegen.defs.naming.impl.intf;

/** Generated mutable contract derived from AIigDefsCodegenNameConventionsTypePropertyNameConventions_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenNameConventionsTypePropertyNameConventions", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
public interface AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1<TNameConventionList extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConvention_1<?>> extends eu.algites.tool.codegen.defs.naming.AIigDefsCodegenNameConventionsTypePropertyNameConventions_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field NameConventionList under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameConvention", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 0, minItemCount = 0, maxItemCount = -1, isEmptyAllowed = false, defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.DECLARATION_ONLY, value = "", defined = false), setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Name convention list")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "NameConvention", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override eu.algites.lib.common.list.AIiMultiMappedList<? extends TNameConventionList> getNameConventionList();
    eu.algites.lib.common.list.AIiMultiMappedList<? extends TNameConventionList> _getRaw_NameConventionList();
    boolean _isPresent_NameConventionList();
    void _unset_NameConventionList();
}
