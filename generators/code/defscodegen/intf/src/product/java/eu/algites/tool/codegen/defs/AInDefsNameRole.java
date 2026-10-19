package eu.algites.tool.codegen.defs;

/** Internal Defs renderer role; not part of the general-purpose naming language. */
public enum AInDefsNameRole {
    /** Generated concrete DTO class or record. */
    DATA_TYPE,
    /** Generated enumeration container. */
    ENUM_TYPE,
    /** Generated read-only schema contract. */
    INTERFACE_TYPE,
    /** Named XML global element read contract, separate from its content type. */
    XML_ELEMENT_INTERFACE_TYPE,
    /** Python filename stem for a named XML global element. */
    XML_ELEMENT_INTERFACE_TYPE_FILE_STEM,
    /** Identifier used for an individual canonical property. */
    PROPERTY,
    /** Generated enumeration constant preserving a serialized value. */
    ENUM_CONSTANT,
    /** Segment of a generated package path. */
    PACKAGE_SEGMENT,
    /** File stem shared by a generated source unit. */
    FILE_STEM,
    /** File stem for a concrete data type. */
    DATA_TYPE_FILE_STEM,
    /** File stem for an enumeration type. */
    ENUM_TYPE_FILE_STEM,
    /** File stem for a read-only interface. */
    INTERFACE_TYPE_FILE_STEM
}
