package eu.algites.tool.codegen.defs.bootstrap.model;

/**
 * Declared or synthesized during schema loading
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/TypeOrigin; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}TypeOrigin; version: 1.</p>
 */
public enum AIngTypeOrigin_1 {
    /** Exact wire value DECLARED. */
    DECLARED("DECLARED"),
    /** Exact wire value SYNTHETIC. */
    SYNTHETIC("SYNTHETIC");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngTypeOrigin_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
