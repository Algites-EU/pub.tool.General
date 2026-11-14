package eu.algites.tool.codegen.defs.bootstrap.model;

/**
 * Contract for XmlWireNameValueKind.
 *
 * <p>Canonical identity: generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json#/$defs/XmlWireName/properties/value_kind#synthetic:synthetic_inline_enum_type; version: 1.</p>
 * <p>Equivalent schema identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/XmlWireName/sequence/sequence/2#synthetic:synthetic_inline_enum_type; version: 1.</p>
 * <p>Equivalent schema identity: generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.yamldef.schema.json#/$defs/XmlWireName/properties/value_kind#synthetic:synthetic_inline_enum_type; version: 1.</p>
 */
public enum AIngXmlWireNameValueKind_1 {
    /** Exact wire value ELEMENT. */
    ELEMENT("ELEMENT"),
    /** Exact wire value ATTRIBUTE. */
    ATTRIBUTE("ATTRIBUTE");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngXmlWireNameValueKind_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
