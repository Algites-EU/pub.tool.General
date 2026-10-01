package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * One normalized object property.
 *
 * @param sourceName canonical source property name
 * @param valueKind normalized value kind
 * @param required whether the property is required
 * @param nullable whether the property accepts null
 * @param itemValueKind normalized array item kind when applicable
 * @param reference referenced canonical definition when applicable
 * @param description human-readable property description
 */
public record AIcdPropertyDefinition(
        String sourceName,
        AInValueKind valueKind,
        boolean required,
        boolean nullable,
        AInValueKind itemValueKind,
        AIcdDefinitionReference reference,
        String description) {
    /** Validates and normalizes the supplied data-object components. */
    public AIcdPropertyDefinition {
        Objects.requireNonNull(sourceName, "sourceName");
        Objects.requireNonNull(valueKind, "valueKind");
    }
}
