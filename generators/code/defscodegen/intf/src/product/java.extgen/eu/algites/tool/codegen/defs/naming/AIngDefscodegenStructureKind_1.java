package eu.algites.tool.codegen.defs.naming;

/**
 * Strictly typed naming role vocabulary for the defs domain. Roles in other domains are forbidden.
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.naming.defscodegen-structure-kind; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-structure-kind_1.xsd}DefscodegenStructureKind; version: 1.</p>
 */
public enum AIngDefscodegenStructureKind_1 {
    /** Exact wire value synthetic_property_type. */
    SYNTHETIC_PROPERTY_TYPE("synthetic_property_type"),
    /** Exact wire value synthetic_inline_enum_type. */
    SYNTHETIC_INLINE_ENUM_TYPE("synthetic_inline_enum_type"),
    /** Exact wire value synthetic_list_item_type. */
    SYNTHETIC_LIST_ITEM_TYPE("synthetic_list_item_type"),
    /** Exact wire value synthetic_map_value_type. */
    SYNTHETIC_MAP_VALUE_TYPE("synthetic_map_value_type"),
    /** Exact wire value synthetic_positional_item_type. */
    SYNTHETIC_POSITIONAL_ITEM_TYPE("synthetic_positional_item_type"),
    /** Exact wire value synthetic_choice_variant_type. */
    SYNTHETIC_CHOICE_VARIANT_TYPE("synthetic_choice_variant_type"),
    /** Exact wire value synthetic_group_type. */
    SYNTHETIC_GROUP_TYPE("synthetic_group_type"),
    /** Exact wire value string_enum_item. */
    STRING_ENUM_ITEM("string_enum_item"),
    /** Exact wire value non_string_enum_item. */
    NON_STRING_ENUM_ITEM("non_string_enum_item");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngDefscodegenStructureKind_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
