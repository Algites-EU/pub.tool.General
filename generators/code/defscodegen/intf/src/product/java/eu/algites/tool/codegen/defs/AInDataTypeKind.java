package eu.algites.tool.codegen.defs;

/** Recursive structural data type kinds, independent of schema serialization. */
public enum AInDataTypeKind {
    /** Arbitrary value. */ ANY,
    /** Character data. */ STRING,
    /** Integral number. */ INTEGER,
    /** Decimal or floating-point number. */ NUMBER,
    /** Boolean value. */ BOOLEAN,
    /** Composite object with named properties. */ OBJECT,
    /** Sequence with a recursively described element type. */ ARRAY,
    /** Named or inline enumeration. */ ENUM,
    /** Reference to a separately declared canonical definition. */ REFERENCE,
    /** Exclusive closed alternative selection (JSON Schema oneOf). */ ONE_OF,
    /** Inclusive alternative selection (JSON Schema anyOf). */ ANY_OF
}
