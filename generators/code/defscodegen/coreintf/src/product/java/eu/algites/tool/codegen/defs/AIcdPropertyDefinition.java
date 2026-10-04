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
 * @param constraints scalar semantics and validation constraints
 * @param itemConstraints array item semantics and constraints
 */
public record AIcdPropertyDefinition(
        String sourceName,
        AInValueKind valueKind,
        boolean required,
        boolean nullable,
        AInValueKind itemValueKind,
        AIcdDefinitionReference reference,
        String description,
        AIcdValueConstraints constraints,
        AIcdValueConstraints itemConstraints) {
    /** Keeps the original constructor available for existing bootstrap consumers. */
    public AIcdPropertyDefinition(String aSourceName, AInValueKind aValueKind, boolean aRequired, boolean aNullable,
            AInValueKind aItemValueKind, AIcdDefinitionReference aReference, String aDescription) {
        this(aSourceName, aValueKind, aRequired, aNullable, aItemValueKind, aReference, aDescription,
                AIcdValueConstraints.empty(), AIcdValueConstraints.empty());
    }
    /** Validates and normalizes the supplied data-object components. */
    public AIcdPropertyDefinition {
        Objects.requireNonNull(sourceName, "sourceName");
        Objects.requireNonNull(valueKind, "valueKind");
        constraints = constraints == null ? AIcdValueConstraints.empty() : constraints;
        itemConstraints = itemConstraints == null ? AIcdValueConstraints.empty() : itemConstraints;
    }
}
