package eu.algites.tool.codegen.defs.model;

/**
 * Contract for ElementListChildVariantElementList2.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/ElementListChild/choice/choice/1#synthetic:synthetic_choice_variant_type; version: 1.</p>
 * @param field1 Schema field ElementList
 */
public record AIigElementListChildVariantElementList2_1(AIigElementList_1 field1) implements AIigElementListChild_1 {
    /**
     * Return the possible first XML QNames of this variant.
     * @return immutable set of expanded names without synthetic wrappers
     */
    public static java.util.Set<String> xmlFirstQNames() {
        return java.util.Set.of("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}ElementList");
    }

    /** Validate required fields on construction. */
    public AIigElementListChildVariantElementList2_1 {
        java.util.Objects.requireNonNull(field1, "ElementList");
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "ElementList", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "ElementList", order = 0)
    /** @return Value of ElementList (required) */
    public AIigElementList_1 getElementList() { return field1; }
}
