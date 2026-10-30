package eu.algites.tool.codegen.defs;

/**
 * Identifies the addressing semantics of a canonical schema field independently
 * of its value type and independent of JSON, YAML or XML syntax.
 *
 * @author linhart1
 */
public enum AInFieldValueRole {
    /** One value identified by its schema-declared field name. */
    NAMED_VALUE,
    /** Arbitrarily many values identified by one or more typed keys. */
    KEYED_VALUES,
    /** An individual value whose type is selected by its sequence position. */
    POSITION_TYPED_VALUE,
    /** A homogeneous repeated sequence of values, preserving their order. */
    SEQUENTIAL_VALUES
}
