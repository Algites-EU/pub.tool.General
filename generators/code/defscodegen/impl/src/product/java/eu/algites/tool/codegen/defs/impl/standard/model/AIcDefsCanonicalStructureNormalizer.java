package eu.algites.tool.codegen.defs.impl.standard.model;
import eu.algites.tool.codegen.defs.model.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Post-validation canonical normalization. Keeps declared/synthetic TYPE identities,
 * source provenance, map kinds and choice boundaries, and flattens only structurally
 * equivalent nested compositional groups. No key or uniqueness semantics are inferred.
 */
public final class AIcDefsCanonicalStructureNormalizer {
    /** Prevents construction of the stateless normalizer. */
    private AIcDefsCanonicalStructureNormalizer() { }

    /**
     * Recursively normalizes a previously validated canonical structure.
     *
     * @param node validated input node
     * @return normalized immutable canonical node
     * @throws NullPointerException if node is null
     */
    public static AIiDefsCanonicalStructure normalize(AIiDefsCanonicalStructure node) {
        Objects.requireNonNull(node, "node");
        if (node instanceof AIcDefsCanonicalType type) {
            if (type.resolutionState() != AIngResolutionState_1.RESOLVED ||
                    !type.targetIdentity().isEmpty()) return type;
            return new AIcDefsCanonicalType(type.identity(), type.name(), type.origin(), type.pathSegments(),
                    type.inheritedFromTypes(), normalize(type.structure()), type.resolutionState(),
                    type.sourceBindings(), type.targetIdentity(), type.schemaVersion(), type.description());
        }
        if (node instanceof AIcDefsCanonicalElementList list) {
            List<AIiDefsCanonicalStructure> children = new ArrayList<>();
            for (var child : list.children()) {
                var normalized = normalize(child);
                if (normalized instanceof AIcDefsCanonicalElementList nested &&
                        nested.composition() == list.composition() &&
                        list.composition() != AIngComposition_1.CHOICE &&
                        nested.minItemCount() == 1 && nested.maxItemCount() == 1 &&
                        nested.minProperties() == -1 && nested.maxProperties() == -1) {
                    children.addAll(nested.children());
                } else children.add(normalized);
            }
            return new AIcDefsCanonicalElementList(list.composition(), children,
                    list.minItemCount(), list.maxItemCount(), list.minProperties(), list.maxProperties());
        }
        if (node instanceof AIcDefsCanonicalElement element) {
            return new AIcDefsCanonicalElement(element.name(), normalize(element.structure()),
                    element.keyDefinitions(), element.sourceBindings(),
                    element.minItemCount(), element.maxItemCount(), element.description(), element.xmlWire(),
                    element.defaultKind(), element.defaultValue(), element.isEmptyAllowed(),
                    element.elementKind());
        }
        if (node instanceof AIcDefsCanonicalList list) {
            return new AIcDefsCanonicalList(list.name(), normalize(list.item()),
                    list.minItemCount(), list.maxItemCount(), list.keyDefinitions(), list.xmlWire(), list.uniqueItems());
        }
        if (node instanceof AIcDefsCanonicalMap map) {
            return new AIcDefsCanonicalMap(map.name(), map.mapKind(), normalize(map.keyType()),
                    normalize(map.valueType()), map.sourceBindings());
        }
        return node;
    }
}

