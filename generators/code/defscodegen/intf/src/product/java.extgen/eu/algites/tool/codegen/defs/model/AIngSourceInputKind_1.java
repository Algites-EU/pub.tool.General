package eu.algites.tool.codegen.defs.model;

/**
 * Schema language provenance
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceInputKind; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}SourceInputKind; version: 1.</p>
 */
public enum AIngSourceInputKind_1 {
    /** Exact wire value XMLDEFS. */
    XMLDEFS("XMLDEFS"),
    /** Exact wire value YAMLDEFS. */
    YAMLDEFS("YAMLDEFS"),
    /** Exact wire value JSONDEFS. */
    JSONDEFS("JSONDEFS");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngSourceInputKind_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
