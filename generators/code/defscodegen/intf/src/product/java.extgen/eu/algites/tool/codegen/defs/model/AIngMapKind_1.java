package eu.algites.tool.codegen.defs.model;

/**
 * Map participation and property-map policy
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/MapKind; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}MapKind; version: 1.</p>
 */
public enum AIngMapKind_1 {
    /** Exact wire value COMMON_MAP. */
    COMMON_MAP("COMMON_MAP"),
    /** Exact wire value INTEGRATED_PROPERTY_MAP. */
    INTEGRATED_PROPERTY_MAP("INTEGRATED_PROPERTY_MAP");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngMapKind_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
