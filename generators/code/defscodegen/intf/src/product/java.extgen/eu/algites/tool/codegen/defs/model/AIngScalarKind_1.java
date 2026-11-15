package eu.algites.tool.codegen.defs.model;

/**
 * Canonical scalar type
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ScalarKind; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}ScalarKind; version: 1.</p>
 */
public enum AIngScalarKind_1 {
    /** Exact wire value ANY. */
    ANY("ANY"),
    /** Exact wire value STRING. */
    STRING("STRING"),
    /** Exact wire value INTEGER. */
    INTEGER("INTEGER"),
    /** Exact wire value NUMBER. */
    NUMBER("NUMBER"),
    /** Exact wire value BOOLEAN. */
    BOOLEAN("BOOLEAN"),
    /** Exact wire value NULL. */
    NULL("NULL");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngScalarKind_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
