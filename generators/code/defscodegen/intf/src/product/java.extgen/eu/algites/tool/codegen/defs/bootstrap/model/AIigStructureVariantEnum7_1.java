package eu.algites.tool.codegen.defs.bootstrap.model;

/**
 * Contract for StructureVariantEnum7.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/Structure/choice/choice/6#synthetic:synthetic_choice_variant_type; version: 1.</p>
 * @param field1 Schema field Enum
 */
public record AIigStructureVariantEnum7_1(AIigEnum_1 field1) implements AIigStructure_1 {
    /**
     * Return the possible first XML QNames of this variant.
     * @return immutable set of expanded names without synthetic wrappers
     */
    public static java.util.Set<String> xmlFirstQNames() {
        return java.util.Set.of("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}Enum");
    }

    /** Validate required fields on construction. */
    public AIigStructureVariantEnum7_1 {
        java.util.Objects.requireNonNull(field1, "Enum");
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "Enum", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "Enum", order = 0)
    /** @return Value of Enum (required) */
    public AIigEnum_1 getEnum() { return field1; }
}
