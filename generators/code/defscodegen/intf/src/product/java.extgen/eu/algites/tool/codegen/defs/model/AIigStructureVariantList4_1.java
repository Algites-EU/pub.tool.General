package eu.algites.tool.codegen.defs.model;

/**
 * Contract for StructureVariantList4.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/Structure/choice/choice/3#synthetic:synthetic_choice_variant_type; version: 1.</p>
 * @param field1 Schema field List
 */
public record AIigStructureVariantList4_1(AIigList_1 field1) implements AIigStructure_1 {
    /**
     * Return the possible first XML QNames of this variant.
     * @return immutable set of expanded names without synthetic wrappers
     */
    public static java.util.Set<String> xmlFirstQNames() {
        return java.util.Set.of("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}List");
    }

    /** Validate required fields on construction. */
    public AIigStructureVariantList4_1 {
        java.util.Objects.requireNonNull(field1, "List");
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "List", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "List", order = 0)
    /** @return Value of List (required) */
    public AIigList_1 getList() { return field1; }
}
