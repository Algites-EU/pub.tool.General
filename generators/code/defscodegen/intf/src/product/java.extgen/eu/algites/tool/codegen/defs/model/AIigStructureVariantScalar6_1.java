package eu.algites.tool.codegen.defs.model;

/**
 * Contract for StructureVariantScalar6.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/Structure/choice/choice/5#synthetic:synthetic_choice_variant_type; version: 1.</p>
 * @param field1 Schema field Scalar
 */
public record AIigStructureVariantScalar6_1(AIigScalar_1 field1) implements AIigStructure_1 {
    /**
     * Return the possible first XML QNames of this variant.
     * @return immutable set of expanded names without synthetic wrappers
     */
    public static java.util.Set<String> xmlFirstQNames() {
        return java.util.Set.of("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}Scalar");
    }

    /** Validate required fields on construction. */
    public AIigStructureVariantScalar6_1 {
        java.util.Objects.requireNonNull(field1, "Scalar");
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "Scalar", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "Scalar", order = 0)
    /** @return Value of Scalar (required) */
    public AIigScalar_1 getScalar() { return field1; }
}
