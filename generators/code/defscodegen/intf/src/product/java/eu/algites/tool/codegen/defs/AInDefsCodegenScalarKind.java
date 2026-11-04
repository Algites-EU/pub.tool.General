package eu.algites.tool.codegen.defs;

/** Canonical schema scalar types independent of Java/Python output representation. */
public enum AInDefsCodegenScalarKind {
    /** Unconstrained source value. */
    ANY,
    /** String value. */
    STRING,
    /** Integral numeric value. */
    INTEGER,
    /** Real number represented without truncation. */
    NUMBER,
    /** Boolean value. */
    BOOLEAN,
    /** Null-only value. */
    NULL
}

