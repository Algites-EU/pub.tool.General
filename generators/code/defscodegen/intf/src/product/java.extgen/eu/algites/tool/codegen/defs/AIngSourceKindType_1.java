package eu.algites.tool.codegen.defs;

/**
 * Selects the source-definition family handled by the frontend.
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.input-profile#/$defs/SourceKindType; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd}SourceKindType; version: 1.</p>
 */
public enum AIngSourceKindType_1 {
    /** Exact wire value yamldefs. */
    YAMLDEFS("yamldefs"),
    /** Exact wire value jsondefs. */
    JSONDEFS("jsondefs"),
    /** Exact wire value xmldefs. */
    XMLDEFS("xmldefs");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngSourceKindType_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
