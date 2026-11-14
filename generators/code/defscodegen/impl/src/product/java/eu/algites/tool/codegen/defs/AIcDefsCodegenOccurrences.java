package eu.algites.tool.codegen.defs;

/** Validates the common Java/Python occurrence-bound representation. */
public final class AIcDefsCodegenOccurrences {
    /** Static utility, not instantiable. */
    private AIcDefsCodegenOccurrences() { }

    /**
     * Rejects impossible occurrence ranges before any output is generated.
     *
     * @param minimum inclusive nonnegative minimum
     * @param maximum inclusive maximum, or -1 to denote unbounded
     * @throws IllegalArgumentException for negative minimum or invalid maximum
     */
    public static void check(int minimum, int maximum) {
        if (minimum < 0 || maximum < -1 || maximum != -1 && maximum < minimum) {
            throw new IllegalArgumentException("Invalid occurrence bounds: " + minimum + ".." + maximum);
        }
    }
}
