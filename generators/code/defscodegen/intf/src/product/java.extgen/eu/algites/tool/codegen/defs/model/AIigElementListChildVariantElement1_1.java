package eu.algites.tool.codegen.defs.model;

/**
 * Contract for ElementListChildVariantElement1.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/ElementListChild/choice/choice/0#synthetic:synthetic_choice_variant_type; version: 1.</p>
 * @param field1 Schema field Element
 */
public record AIigElementListChildVariantElement1_1(AIigElement_1 field1) implements AIigElementListChild_1 {
    /**
     * Return the possible first XML QNames of this variant.
     * @return immutable set of expanded names without synthetic wrappers
     */
    public static java.util.Set<String> xmlFirstQNames() {
        return java.util.Set.of("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}Element");
    }

    /** Validate required fields on construction. */
    public AIigElementListChildVariantElement1_1 {
        java.util.Objects.requireNonNull(field1, "Element");
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "Element", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "Element", order = 0)
    /** @return Value of Element (required) */
    public AIigElement_1 getElement() { return field1; }
}
