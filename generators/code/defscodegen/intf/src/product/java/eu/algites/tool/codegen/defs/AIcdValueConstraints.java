package eu.algites.tool.codegen.defs;

import java.util.List;

/**
 * Scalar and array validation constraints retained across schema formats.
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
 * @param minItems minimum number of items in an array, if specified
 * @param maxItems maximum number of items in an array, if specified
 */
public record AIcdValueConstraints(String dataType, String minimum, String maximum,
        boolean exclusiveMinimum, boolean exclusiveMaximum, Integer minLength, Integer maxLength,
        String pattern, List<String> enumValues, Integer minItems, Integer maxItems) {
    /**
     * Freeze enumerations and reject invalid lengths or array cardinality intervals.
     * Bounds remain optional because schema formats may omit them.
     */
    public AIcdValueConstraints {
        enumValues = enumValues == null ? List.of() : List.copyOf(enumValues);
        for (Integer locValue : new Integer[] { minItems, maxItems, minLength, maxLength }) {
            if (locValue != null && locValue < 0)
                throw new IllegalArgumentException("Constraint bounds cannot be negative");
        }
        if (minItems != null && maxItems != null && minItems > maxItems)
            throw new IllegalArgumentException("minItems exceeds maxItems");
        if (minLength != null && maxLength != null && minLength > maxLength)
            throw new IllegalArgumentException("minLength exceeds maxLength");
    }

    /**
     * Construct scalar-only constraints from existing source parsers. The omitted
     * array bounds have no constraint, rather than implicit zero/one semantics.
     */
    public AIcdValueConstraints(String aDataType, String aMinimum, String aMaximum,
            boolean aExclusiveMinimum, boolean aExclusiveMaximum, Integer aMinLength,
            Integer aMaxLength, String aPattern, List<String> aEnumValues) {
        this(aDataType, aMinimum, aMaximum, aExclusiveMinimum, aExclusiveMaximum,
                aMinLength, aMaxLength, aPattern, aEnumValues, null, null);
    }

    /**
     * Copy scalar facets with independently derived array bounds. This permits
     * preserving source array cardinality without changing element constraints.
     *
     * @param aMinItems required minimum count, or null when unspecified
     * @param aMaxItems required maximum count, or null when unbounded
     * @return immutable constraints including the supplied array interval
     */
    public AIcdValueConstraints withArrayBounds(Integer aMinItems, Integer aMaxItems) {
        return new AIcdValueConstraints(dataType, minimum, maximum, exclusiveMinimum,
                exclusiveMaximum, minLength, maxLength, pattern, enumValues, aMinItems, aMaxItems);
    }
    /** Returns a constraint set without scalar hints or validation facets. */
    public static AIcdValueConstraints empty() { return new AIcdValueConstraints(null, null, null, false, false, null, null, null, List.of()); }
}
