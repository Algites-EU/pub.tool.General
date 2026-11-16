package eu.algites.tool.codegen.defs.model.impl.intf;

/** Generated mutable contract derived from AIigCanonicalModelElement_1. */
@eu.algites.lib.data.dataobject.AIaDataObject(title = "", description = "CanonicalModelElement", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "CanonicalModel")
public interface AIigdCanonicalModelElement_1<TTypesList extends eu.algites.tool.codegen.defs.model.impl.intf.AIigdType_1<?, ?, ?>> extends eu.algites.tool.codegen.defs.model.AIigCanonicalModelElement_1, eu.algites.lib.data.smartdataobject.AIiSmartDataObject {
    /** Typed writable access to field TypesList under the published setter policy. */
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "types", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = -1, isEmptyAllowed = false, setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints(minItems = 1, maxItems = -1, uniqueItems = false)
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = "Types list")
    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "types", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
            @Override eu.algites.lib.common.list.AIiBoundedList<? extends TTypesList> getTypesList();
    eu.algites.lib.common.list.AIiBoundedList<? extends TTypesList> _getRaw_TypesList();
    boolean _isPresent_TypesList();
    void _unset_TypesList();
}
