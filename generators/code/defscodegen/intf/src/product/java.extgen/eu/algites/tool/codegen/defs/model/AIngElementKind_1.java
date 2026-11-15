package eu.algites.tool.codegen.defs.model;

/**
 * Serialized field with a wire name (REFERENCED) or inline, unnamed structural group (EMBEDDED); independent of TypeOrigin.
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementKind; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}ElementKind; version: 1.</p>
 */
public enum AIngElementKind_1 {
    /** Exact wire value REFERENCED. */
    REFERENCED("REFERENCED"),
    /** Exact wire value EMBEDDED. */
    EMBEDDED("EMBEDDED");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngElementKind_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
