package eu.algites.tool.codegen.defs.model;

/**
 * Contract for StructureVariantElement3.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/Structure/choice/choice/2#synthetic:synthetic_choice_variant_type; version: 1.</p>
 * @param field1 Schema field Element
 */
public record AIigStructureVariantElement3_1(AIigElement_1 field1) implements AIigStructure_1 {
    /**
     * Return the possible first XML QNames of this variant.
     * @return immutable set of expanded names without synthetic wrappers
     */
    public static java.util.Set<String> xmlFirstQNames() {
        return java.util.Set.of("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}Element");
    }

    /** Validate required fields on construction. */
    public AIigStructureVariantElement3_1 {
        java.util.Objects.requireNonNull(field1, "Element");
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "Element", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "Element", order = 0)
    /** @return Value of Element (required) */
    public AIigElement_1 getElement() { return field1; }
}
