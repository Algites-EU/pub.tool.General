package eu.algites.tool.codegen.defs.model;

/**
 * Contract for TypeContentVariantTargetIdentity2.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/TypeContent/choice/choice/1#synthetic:synthetic_choice_variant_type; version: 1.</p>
 * @param field1 Schema field target_identity
 */
public record AIigTypeContentVariantTargetIdentity2_1(String field1) implements AIigTypeContent_1 {
    /**
     * Return the possible first XML QNames of this variant.
     * @return immutable set of expanded names without synthetic wrappers
     */
    public static java.util.Set<String> xmlFirstQNames() {
        return java.util.Set.of("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}target_identity");
    }

    /** Validate required fields on construction. */
    public AIigTypeContentVariantTargetIdentity2_1 {
        java.util.Objects.requireNonNull(field1, "target_identity");
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "target_identity", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "target_identity", order = 0)
    @eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = 1)
    /** @return Value of target_identity (required) */
    public String getTargetIdentity() { return field1; }
}
