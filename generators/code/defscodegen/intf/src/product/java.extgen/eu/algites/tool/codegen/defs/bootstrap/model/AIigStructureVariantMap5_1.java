package eu.algites.tool.codegen.defs.bootstrap.model;

/**
 * Contract for StructureVariantMap5.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/Structure/choice/choice/4#synthetic:synthetic_choice_variant_type; version: 1.</p>
 * @param field1 Schema field Map
 */
public record AIigStructureVariantMap5_1(AIigMap_1 field1) implements AIigStructure_1 {
    /**
     * Return the possible first XML QNames of this variant.
     * @return immutable set of expanded names without synthetic wrappers
     */
    public static java.util.Set<String> xmlFirstQNames() {
        return java.util.Set.of("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}Map");
    }

    /** Validate required fields on construction. */
    public AIigStructureVariantMap5_1 {
        java.util.Objects.requireNonNull(field1, "Map");
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "Map", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "Map", order = 0)
    /** @return Value of Map (required) */
    public AIigMap_1 getMap() { return field1; }
}
