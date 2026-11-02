package eu.algites.tool.codegen.defs;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;

import java.util.List;
import java.util.Objects;

/**
 * Immutable description of one source-schema key defined on values in a
 * {@link AIcdDataType} keyed collection. Composite keys preserve the ordered
 * declaration of their member field paths. A virtual key is provided by the
 * containing JSON/YAML object's property name rather than by a serialized field
 * in the value object.
 *
 * @param name nonempty diagnostic identity of this key definition
 * @param fields one or more nonempty paths of key-bearing fields
 * @param unique whether duplicate complete keys must be rejected
 * @param required whether all selected objects must have complete key values
 * @param virtual whether the single key comes from the containing object property
 * @author linhart1
 */
public record AIcdKeyDefinition(String name, List<String> fields, boolean unique, boolean virtual, boolean required) {
    /**
     * Creates a required key definition compatible with previous schema contracts.
     *
     * @param name diagnostic key identity
     * @param fields ordered key field paths
     * @param unique whether complete duplicate key tuples are forbidden
     * @param virtual whether the key is derived from a containing map entry
     */
    public AIcdKeyDefinition(String name, List<String> fields, boolean unique, boolean virtual) {
        this(name, fields, unique, virtual, true);
    }
    /**
     * Validate the key identity, components and virtual-key cardinality.
     *
     * @throws NullPointerException if the name or fields are null
     * @throws IllegalArgumentException if either is empty, a path is empty,
     *                                  or a virtual key has multiple components
     */
    public AIcdKeyDefinition {
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(fields, "fields");
        fields = List.copyOf(fields);
        if (name.isBlank() || fields.isEmpty() || fields.stream().anyMatch(String::isBlank)
                || (virtual && fields.size() != 1))
            throw new AIxCodegenValidationException("Invalid canonical key definition: " + name, "Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.");
    }
}
