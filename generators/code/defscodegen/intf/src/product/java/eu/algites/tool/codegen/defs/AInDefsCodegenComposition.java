package eu.algites.tool.codegen.defs;

/** Meaning of an element-list group, preserving source declaration ordering. */
public enum AInDefsCodegenComposition {
    /** Children are composed in declaration order. */
    SEQUENCE,
    /** All children participate, with their original declaration order retained. */
    ALL,
    /** Children represent alternatives; flattening across choice is forbidden. */
    CHOICE
}

