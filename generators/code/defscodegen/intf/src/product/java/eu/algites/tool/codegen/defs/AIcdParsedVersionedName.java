package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * Logical source name with a separately tracked canonical definition version.
 *
 * @param logicalName logical name without the governed version suffix
 * @param version canonical definition version, or null when absent
 */
public record AIcdParsedVersionedName(String logicalName, Integer version) {
    /** Validates and normalizes the supplied data-object components. */
    public AIcdParsedVersionedName {
        Objects.requireNonNull(logicalName, "logicalName");
    }
}
