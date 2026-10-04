package eu.algites.tool.codegen.defs;

import java.util.List;

/**
 * Scalar semantics and basic validation constraints retained across schema formats.
 * Numeric boundaries are decimal strings to preserve arbitrary precision.
 *
 * @param dataType exact scalar family, including XML lexical types when necessary
 * @param minimum inclusive or exclusive numeric lower boundary
 * @param maximum inclusive or exclusive numeric upper boundary
 * @param exclusiveMinimum whether the lower boundary is exclusive
 * @param exclusiveMaximum whether the upper boundary is exclusive
 * @param minLength minimum string/binary length
 * @param maxLength maximum string/binary length
 * @param pattern portable regular expression constraint
 * @param enumValues allowed scalar lexical values
 */
public record AIcdValueConstraints(String dataType, String minimum, String maximum,
        boolean exclusiveMinimum, boolean exclusiveMaximum, Integer minLength, Integer maxLength,
        String pattern, List<String> enumValues) {
    /** Copies the immutable enumeration constraint. */
    public AIcdValueConstraints { enumValues = enumValues == null ? List.of() : List.copyOf(enumValues); }
    /** Returns a constraint set without scalar hints or validation facets. */
    public static AIcdValueConstraints empty() { return new AIcdValueConstraints(null, null, null, false, false, null, null, null, List.of()); }
}
