package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * Generated source unit.
 *
 * @param typeName generated primary type name
 * @param relativePath generated source path relative to the target root
 * @param source complete generated source text
 */
public record AIcdGeneratedSource(String typeName, String relativePath, String source) {
    /** Validates and normalizes the supplied data-object components. */
    public AIcdGeneratedSource {
        Objects.requireNonNull(typeName, "typeName");
        Objects.requireNonNull(relativePath, "relativePath");
        Objects.requireNonNull(source, "source");
    }
}
