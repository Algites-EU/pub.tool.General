package eu.algites.tool.codegen.defs;

/** Temporary frontend resolution status, not a canonical structure kind. */
public enum AInDefsCodegenResolutionState {
    /** The referenced structure and its constraints are available. */
    RESOLVED,
    /** The input contains an unresolved reference to a declared type. */
    REFERENCE,
    /** The input temporarily lacks a resolved type. */
    UNDEFINED
}

