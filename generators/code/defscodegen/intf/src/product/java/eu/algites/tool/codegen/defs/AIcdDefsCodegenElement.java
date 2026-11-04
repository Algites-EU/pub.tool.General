package eu.algites.tool.codegen.defs;

import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Named field representing a source element, object property, or declared wrapper.
 * Context-local key definitions are preserved, but not interpreted in the first backend.
 *
 * @param name original declared field name
 * @param structure the field's nested canonical structure
 * @param keyDefinitions context-local key declarations, possibly empty
 * @param sourceBindings original field locations for all input technologies
 * @param minOccurs minimum occurrences; zero means optional
 * @param maxOccurs maximum occurrences; minus one means unbounded
 * @param description original documentation for this field, empty when absent
 * @param xmlWire optional exact XML QName and element/attribute wire kind
 */
public record AIcdDefsCodegenElement(String name, AIiDefsCodegenStructure structure,
        List<AIcdDefsCodegenKeyDefinition> keyDefinitions,
        Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> sourceBindings,
        int minOccurs, int maxOccurs, String description, AIcdDefsCodegenXmlWireName xmlWire)
        implements AIiDefsCodegenStructure {
    /** Compatibility constructor: optional single property. */
    public AIcdDefsCodegenElement(String name, AIiDefsCodegenStructure structure,
            List<AIcdDefsCodegenKeyDefinition> keyDefinitions,
            Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> sourceBindings) {
        this(name, structure, keyDefinitions, sourceBindings, 0, 1, "", null);
    }
    /**
     * Compatibility constructor preserving explicit cardinalities.
     *
     * @param name declared field name
     * @param structure nested canonical structure
     * @param keyDefinitions source key declarations
     * @param sourceBindings exact field provenance
     * @param minOccurs inclusive minimum occurrences
     * @param maxOccurs inclusive maximum occurrences, -1 if unlimited
     */
    public AIcdDefsCodegenElement(String name, AIiDefsCodegenStructure structure,
            List<AIcdDefsCodegenKeyDefinition> keyDefinitions,
            Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> sourceBindings,
            int minOccurs, int maxOccurs) {
        this(name, structure, keyDefinitions, sourceBindings, minOccurs, maxOccurs, "", null);
    }
    /**
     * Compatibility constructor for a member without explicit XML wire metadata.
     * @param name semantic field name
     * @param structure nested canonical structure
     * @param keyDefinitions identity constraints
     * @param sourceBindings source locations
     * @param minOccurs minimum occurrences
     * @param maxOccurs maximum occurrences
     * @param description field documentation
     */
    public AIcdDefsCodegenElement(String name, AIiDefsCodegenStructure structure,
            List<AIcdDefsCodegenKeyDefinition> keyDefinitions,
            Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> sourceBindings,
            int minOccurs, int maxOccurs, String description) {
        this(name, structure, keyDefinitions, sourceBindings, minOccurs, maxOccurs, description, null);
    }
    /** Validates the member and freezes its metadata. */
    public AIcdDefsCodegenElement {
        Objects.requireNonNull(name, "name");
        if (name.isBlank()) throw new IllegalArgumentException("ELEMENT name must not be blank");
        Objects.requireNonNull(structure, "structure");
        Objects.requireNonNull(description, "description");
        keyDefinitions = List.copyOf(keyDefinitions == null ? List.of() : keyDefinitions);
        sourceBindings = AIcDefsCodegenSourceBindings.freeze(sourceBindings);
        AIcDefsCodegenOccurrences.check(minOccurs, maxOccurs);
        if (xmlWire != null && xmlWire.valueKind() == AInDefsCodegenXmlValueKind.ATTRIBUTE
                && (minOccurs > 1 || maxOccurs != 1)) {
            throw new IllegalArgumentException("XML attributes can occur only zero or one time");
        }
    }
    /** {@inheritDoc} */
    @Override public AInDefsCodegenStructureKind kind() { return AInDefsCodegenStructureKind.ELEMENT; }
}

