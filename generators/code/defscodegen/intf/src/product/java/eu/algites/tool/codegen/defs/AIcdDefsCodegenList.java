package eu.algites.tool.codegen.defs;

import java.util.List;
import java.util.Objects;

/**
 * Homogeneous collection. An XSD repeated particle is a direct LIST child
 * of ELEMENTLIST. Field-local key definitions belong to this collection,
 * rather than to an artificial ELEMENT wrapper.
 *
 * @param name collection member name when it is a direct group child
 * @param item typed nested item structure
 * @param minOccurs lower occurrence bound, inclusive
 * @param maxOccurs upper occurrence bound, or -1 for unbounded
 * @param keyDefinitions source ordered xs:key/xs:unique definitions, if any
 * @param xmlWire optional XML QName of the repeated element
 * @author linhart1
 */
public record AIcdDefsCodegenList(String name, AIiDefsCodegenStructure item,
        int minOccurs, int maxOccurs, List<AIcdDefsCodegenKeyDefinition> keyDefinitions,
        AIcdDefsCodegenXmlWireName xmlWire)
        implements AIiDefsCodegenStructure {
    /**
     * Creates a non-keyed collection without changing the old API signature.
     *
     * @param name original member name
     * @param item required nested item type
     * @param minOccurs lower cardinality bound
     * @param maxOccurs upper cardinality bound, -1 for unbounded
     */
    public AIcdDefsCodegenList(String name, AIiDefsCodegenStructure item,
            int minOccurs, int maxOccurs) {
        this(name, item, minOccurs, maxOccurs, List.of(), null);
    }

    /**
     * Compatibility constructor for an unconstrained, unkeyed collection.
     *
     * @param name original member name
     * @param item required nested item type
     */
    public AIcdDefsCodegenList(String name, AIiDefsCodegenStructure item) {
        this(name, item, 0, -1, List.of(), null);
    }

    /**
     * Compatibility constructor for a collection with no explicit XML wire QName.
     * @param name semantic member name
     * @param item canonical item structure
     * @param minOccurs minimum occurrences
     * @param maxOccurs maximum occurrences
     * @param keyDefinitions ordered key definitions
     */
    public AIcdDefsCodegenList(String name, AIiDefsCodegenStructure item, int minOccurs,
            int maxOccurs, List<AIcdDefsCodegenKeyDefinition> keyDefinitions) {
        this(name, item, minOccurs, maxOccurs, keyDefinitions, null);
    }

    /**
     * Checks the item and bounds and freezes local key definitions.
     *
     * @throws IllegalArgumentException for invalid occurrence bounds, empty
     *         keyed-list name or duplicate key identifiers
     * @throws NullPointerException when item or key definitions are null
     */
    public AIcdDefsCodegenList {
        name = name == null ? "" : name;
        Objects.requireNonNull(item, "item");
        AIcDefsCodegenOccurrences.check(minOccurs, maxOccurs);
        keyDefinitions = List.copyOf(Objects.requireNonNull(keyDefinitions, "keyDefinitions"));
        if (xmlWire != null && xmlWire.valueKind() != AInDefsCodegenXmlValueKind.ELEMENT) {
            throw new IllegalArgumentException("Repeated LIST cannot represent an XML attribute");
        }
        if (!keyDefinitions.isEmpty() && name.isBlank()) {
            throw new IllegalArgumentException("Keyed LIST must have a source field name");
        }
        if (keyDefinitions.stream().map(AIcdDefsCodegenKeyDefinition::identifier)
                .distinct().count() != keyDefinitions.size()) {
            throw new IllegalArgumentException("Duplicate keyed LIST constraint name");
        }
    }

    /** {@inheritDoc} */
    @Override public AInDefsCodegenStructureKind kind() { return AInDefsCodegenStructureKind.LIST; }
}
