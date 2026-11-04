package eu.algites.tool.codegen.defs;

import java.util.List;
import java.util.Objects;

/**
 * Source-ordered XML {@code xs:key}/{@code xs:unique} information attached
 * to a particular collection, without assuming XPath field resolution.
 *
 * @param identifier original key/unique constraint identifier, nonempty
 * @param selector original namespace-aware selector expression, nonempty
 * @param sourcePointer exact source path of the declaration, nonempty
 * @param fields original ordered {@code xs:field} XPath expressions; may be
 *        empty only while the definition has not been fully interpreted
 * @param required true for {@code xs:key}, false for {@code xs:unique}
 *        (an incomplete key is permitted by {@code xs:unique})
 * @author linhart1
 */
public record AIcdDefsCodegenKeyDefinition(String identifier, String selector,
        String sourcePointer, List<String> fields, boolean required) {
    /**
     * Compatibility constructor for a deferred, field-unresolved XML key.
     * The native emitter will not generate a keyed collection from this
     * incomplete definition.
     *
     * @param identifier original constraint name
     * @param selector original selector XPath
     * @param sourcePointer original constraint location
     */
    public AIcdDefsCodegenKeyDefinition(String identifier, String selector, String sourcePointer) {
        this(identifier, selector, sourcePointer, List.of(), true);
    }

    /**
     * Validates the original source information without rewriting XPath tokens.
     *
     * @throws IllegalArgumentException for empty strings or repeated field paths
     * @throws NullPointerException for null components
     */
    public AIcdDefsCodegenKeyDefinition {
        Objects.requireNonNull(identifier, "identifier");
        Objects.requireNonNull(selector, "selector");
        Objects.requireNonNull(sourcePointer, "sourcePointer");
        if (identifier.isBlank() || selector.isBlank() || sourcePointer.isBlank()) {
            throw new IllegalArgumentException("XML key name, selector and source location must be nonempty");
        }
        fields = List.copyOf(Objects.requireNonNull(fields, "fields"));
        if (fields.stream().anyMatch(String::isBlank) ||
                fields.stream().distinct().count() != fields.size()) {
            throw new IllegalArgumentException("XML key field paths must be nonempty and unique");
        }
    }
}
