package eu.algites.tool.codegen.defs.bootstrap.model;

/**
 * Seven canonical kinds
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/StructureKind; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}StructureKind; version: 1.</p>
 */
public enum AIngStructureKind_1 {
    /** Exact wire value TYPE. */
    TYPE("TYPE"),
    /** Exact wire value ELEMENTLIST. */
    ELEMENTLIST("ELEMENTLIST"),
    /** Exact wire value ELEMENT. */
    ELEMENT("ELEMENT"),
    /** Exact wire value LIST. */
    LIST("LIST"),
    /** Exact wire value MAP. */
    MAP("MAP"),
    /** Exact wire value SCALAR. */
    SCALAR("SCALAR"),
    /** Exact wire value ENUM. */
    ENUM("ENUM");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngStructureKind_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
