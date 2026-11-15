package eu.algites.tool.codegen.defs.naming.impl.intf;

/** Generated mutable contract derived from AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "DefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
public interface AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1<TNameConventions extends eu.algites.tool.codegen.defs.naming.impl.intf.AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1<?>> extends eu.algites.tool.codegen.defs.naming.AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field NameConventions under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "NameConventions", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false, setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Name conventions")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "", namespaceLocalName = "NameConventions", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = "UniqueProfileIds", selector = "NameConvention", fields = {"name"}, required = true)
            @Override TNameConventions getNameConventions();
    void setNameConventions(TNameConventions aNameConventions);
    TNameConventions _getRaw_NameConventions();
    boolean _isPresent_NameConventions();
    void _unset_NameConventions();
}
