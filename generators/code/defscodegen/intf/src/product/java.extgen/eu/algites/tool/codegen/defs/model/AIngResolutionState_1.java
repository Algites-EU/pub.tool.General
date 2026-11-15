package eu.algites.tool.codegen.defs.model;

/**
 * Temporary resolution state on TYPE; only RESOLVED survives finalization
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ResolutionState; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}ResolutionState; version: 1.</p>
 */
public enum AIngResolutionState_1 {
    /** Exact wire value RESOLVED. */
    RESOLVED("RESOLVED"),
    /** Exact wire value REFERENCE. */
    REFERENCE("REFERENCE"),
    /** Exact wire value UNDEFINED. */
    UNDEFINED("UNDEFINED");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngResolutionState_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
