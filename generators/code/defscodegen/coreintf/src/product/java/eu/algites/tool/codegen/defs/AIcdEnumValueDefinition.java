package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * Describes one canonical enum wire value together with its human-readable documentation.
 *
 * @param value exact serialized enum value
 * @param description human-readable description of the enum value, or {@code null} when not supplied
 */
public record AIcdEnumValueDefinition(
        String value,
        String description) {
    /** Validates the canonical enum-value data. */
    public AIcdEnumValueDefinition {
        Objects.requireNonNull(value, "value");
    }
}
