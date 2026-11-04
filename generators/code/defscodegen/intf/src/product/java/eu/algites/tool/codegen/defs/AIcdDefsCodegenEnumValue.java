package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * Enumeration value retaining the original lexical wire value and its human-readable label.
 *
 * @param wireValue lexical value in the original schema; never case-normalized
 * @param displayName optional label; empty means unspecified
 */
public record AIcdDefsCodegenEnumValue(String wireValue, String displayName) {
    /** Retains lexical values and normalizes only an absent optional label. */
    public AIcdDefsCodegenEnumValue {
        Objects.requireNonNull(wireValue, "wireValue");
        displayName = displayName == null ? "" : displayName;
    }
}

