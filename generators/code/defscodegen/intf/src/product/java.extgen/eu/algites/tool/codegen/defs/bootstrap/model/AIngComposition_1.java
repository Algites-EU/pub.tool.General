package eu.algites.tool.codegen.defs.bootstrap.model;

/**
 * Group compositor; ALL is ordered for canonical traversal
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Composition; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}Composition; version: 1.</p>
 */
public enum AIngComposition_1 {
    /** Exact wire value SEQUENCE. */
    SEQUENCE("SEQUENCE"),
    /** Exact wire value ALL. */
    ALL("ALL"),
    /** Exact wire value CHOICE. */
    CHOICE("CHOICE");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngComposition_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
