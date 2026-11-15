package eu.algites.tool.codegen.defs.model;

/**
 * Contract for TypeContentVariantStructure1.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/TypeContent/choice/choice/0#synthetic:synthetic_choice_variant_type; version: 1.</p>
 * @param field1 Schema field structure
 */
public record AIigTypeContentVariantStructure1_1(AIigStructure_1 field1) implements AIigTypeContent_1 {
    /**
     * Return the possible first XML QNames of this variant.
     * @return immutable set of expanded names without synthetic wrappers
     */
    public static java.util.Set<String> xmlFirstQNames() {
        return java.util.Set.of("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}structure");
    }

    /** Validate required fields on construction. */
    public AIigTypeContentVariantStructure1_1 {
        java.util.Objects.requireNonNull(field1, "structure");
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "structure", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "structure", order = 0)
    /** @return Value of structure (required) */
    public AIigStructure_1 getStructure() { return field1; }
}
