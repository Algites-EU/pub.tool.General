package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * Describes one canonical enum wire value together with its human-readable documentation.
 *
 * @param value exact serialized enum value
 * @param description human-readable description of the enum value, or {@code null} when not supplied
 * @param title short English fallback title from the source schema
 */
public record AIcdEnumValueDefinition(
        String value,
        String description,
        String title) {
    /** Retains the original constructor for existing integrations. */
    public AIcdEnumValueDefinition(String aValue, String aDescription) {
        this(aValue, aDescription, null);
    }
    /** Validates the canonical enum-value data. */
    public AIcdEnumValueDefinition {
        Objects.requireNonNull(value, "value");
    }
}
