package eu.algites.tool.codegen.defs;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Post-validation canonical normalization. Keeps declared/synthetic TYPE identities,
 * source provenance, map kinds and choice boundaries, and flattens only structurally
 * equivalent nested compositional groups. No key or uniqueness semantics are inferred.
 */
public final class AIcDefsCodegenStructureNormalizer {
    /** Prevents construction of the stateless normalizer. */
    private AIcDefsCodegenStructureNormalizer() { }

    /**
     * Recursively normalizes a previously validated canonical structure.
     *
     * @param node validated input node
     * @return normalized immutable canonical node
     * @throws NullPointerException if node is null
     */
    public static AIiDefsCodegenStructure normalize(AIiDefsCodegenStructure node) {
        Objects.requireNonNull(node, "node");
        if (node instanceof AIcdDefsCodegenType type) {
            if (type.resolutionState() != AInDefsCodegenResolutionState.RESOLVED ||
                    !type.targetIdentity().isEmpty()) return type;
            return new AIcdDefsCodegenType(type.identity(), type.name(), type.origin(), type.pathSegments(),
                    type.inheritedFromTypes(), normalize(type.structure()), type.resolutionState(),
                    type.sourceBindings(), type.targetIdentity(), type.schemaVersion(), type.description());
        }
        if (node instanceof AIcdDefsCodegenElementList list) {
            List<AIiDefsCodegenStructure> children = new ArrayList<>();
            for (var child : list.children()) {
                var normalized = normalize(child);
                if (normalized instanceof AIcdDefsCodegenElementList nested &&
                        nested.composition() == list.composition() &&
                        list.composition() != AInDefsCodegenComposition.CHOICE &&
                        nested.minOccurs() == 1 && nested.maxOccurs() == 1) {
                    children.addAll(nested.children());
                } else children.add(normalized);
            }
            return new AIcdDefsCodegenElementList(list.composition(), children,
                    list.minOccurs(), list.maxOccurs());
        }
        if (node instanceof AIcdDefsCodegenElement element) {
            return new AIcdDefsCodegenElement(element.name(), normalize(element.structure()),
                    element.keyDefinitions(), element.sourceBindings(),
                    element.minOccurs(), element.maxOccurs(), element.description(), element.xmlWire());
        }
        if (node instanceof AIcdDefsCodegenList list) {
            return new AIcdDefsCodegenList(list.name(), normalize(list.item()),
                    list.minOccurs(), list.maxOccurs(), list.keyDefinitions(), list.xmlWire());
        }
        if (node instanceof AIcdDefsCodegenMap map) {
            return new AIcdDefsCodegenMap(map.name(), map.mapKind(), normalize(map.keyType()),
                    normalize(map.valueType()), map.sourceBindings());
        }
        return node;
    }
}

