package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalSourceBindings;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalEnum;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalMap;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalScalar;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.impl.standard.model.AIiDefsCanonicalStructure;
import eu.algites.tool.codegen.defs.model.AIngTypeOrigin_1;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Combines logically equivalent declarations from XMLDEFS, JSONDEFS, and YAMLDEFS
 * while preserving every source location, including multiple bindings for one
 * technology. The first representation establishes the canonical type names,
 * source ordering, and synthetic type identities. Conflicting structures fail
 * with a path-qualified diagnostic rather than overwriting previously loaded data.
 */
public final class AIcDefsCodegenCanonicalModelMerger {
    /** Utility-only class; it does not hold mutable merge state. */
    private AIcDefsCodegenCanonicalModelMerger() { }

    /**
     * Accumulates canonical declarations with identical logical type identifiers.
     * Reference linking must happen <em>after</em> this merge, because each input
     * representation may have a different source resource for its local pointers.
     *
     * @param declarations source declarations, in stable input order
     * @return immutable ordered merged declarations with all source bindings retained
     * @throws NullPointerException for null input/declarations
     * @throws IllegalArgumentException if two declarations for an identity disagree
     */
    public static List<AIcDefsCanonicalType> merge(List<AIcDefsCanonicalType> declarations) {
        Objects.requireNonNull(declarations, "declarations");
        Map<String, AIcDefsCanonicalType> output = new LinkedHashMap<>();
        for (AIcDefsCanonicalType type : declarations) {
            Objects.requireNonNull(type, "declaration");
            if (!type.targetIdentity().isEmpty()) {
                throw new IllegalArgumentException("Source declarations must not already be reference-linked");
            }
            AIcDefsCanonicalType previous = output.get(type.identity());
            if (previous == null) {
                output.put(type.identity(), type);
            } else {
                try {
                    output.put(type.identity(),
                            (AIcDefsCanonicalType) combine(previous, type, type.identity()));
                } catch (IllegalArgumentException exception) {
                    throw new IllegalArgumentException(exception.getMessage() + " [sources: "
                            + provenance(previous) + "; " + provenance(type) + "]", exception);
                }
            }
        }
        return List.copyOf(output.values());
    }

    /**
     * Lists original document locations for one canonical root declaration.
     * @param root schema-generated canonical type carrying source bindings
     * @return semicolon-separated source resource and pointer references
     */
    private static String provenance(AIcDefsCanonicalType root) {
        return root.sourceBindings().values().stream().flatMap(List::stream)
                .map(binding -> binding.sourceResource() + binding.sourcePointer())
                .distinct().collect(java.util.stream.Collectors.joining(", "));
    }

    /**
     * Merges one pair of matching nodes while preserving their original binding sets.
     *
     * @param a existing canonical node
     * @param b equivalent input representation
     * @param path hierarchical diagnostic path of this node
     * @return merged immutable canonical node
     * @throws IllegalArgumentException on a structural or semantic disagreement
     */
    private static AIiDefsCanonicalStructure combine(AIiDefsCanonicalStructure a,
            AIiDefsCanonicalStructure b, String path) {
        if (a.getClass() != b.getClass()) {
            throw conflict(path, "structural kinds differ: " + a.kind() + " / " + b.kind());
        }
        if (a instanceof AIcDefsCanonicalType left && b instanceof AIcDefsCanonicalType right) {
            if (left.origin() != right.origin() || !left.name().equals(right.name())
                    || !left.pathSegments().equals(right.pathSegments())
                    || !left.inheritedFromTypes().equals(right.inheritedFromTypes())
                    || left.resolutionState() != right.resolutionState()
                    || !left.targetIdentity().equals(right.targetIdentity())
                    || !left.identity().equals(right.identity())
                        && left.origin() != AIngTypeOrigin_1.SYNTHETIC
                    || (left.structure() == null) != (right.structure() == null)
                    || (!left.schemaVersion().isEmpty() && !right.schemaVersion().isEmpty()
                            && !left.schemaVersion().equals(right.schemaVersion()))
                    || (!left.description().isEmpty() && !right.description().isEmpty()
                            && !left.description().equals(right.description()))
) {
                throw conflict(path, "TYPE identities, origin, naming, ancestry or state differ");
            }
            var nested = left.structure() == null ? null
                    : combine(left.structure(), right.structure(), path + "/structure");
            return new AIcDefsCanonicalType(left.identity(), left.name(), left.origin(),
                    left.pathSegments(), left.inheritedFromTypes(), nested,
                    left.resolutionState(), AIcDefsCanonicalSourceBindings.merge(
                            left.sourceBindings(), right.sourceBindings()), left.targetIdentity(),
                    left.schemaVersion().isEmpty() ? right.schemaVersion() : left.schemaVersion(),
                    left.description().isEmpty() ? right.description() : left.description());
        }
        if (a instanceof AIcDefsCanonicalElementList left && b instanceof AIcDefsCanonicalElementList right) {
            if (left.composition() != right.composition() || left.children().size() != right.children().size()
                    || left.minItemCount() != right.minItemCount() || left.maxItemCount() != right.maxItemCount()
                    || left.minProperties() != right.minProperties() || left.maxProperties() != right.maxProperties()) {
                throw conflict(path, "group composition or child count differs");
            }
            List<AIiDefsCanonicalStructure> children = new ArrayList<>();
            for (int index = 0; index < left.children().size(); index++) {
                children.add(combine(left.children().get(index), right.children().get(index),
                        path + "/children/" + index));
            }
            return new AIcDefsCanonicalElementList(left.composition(), children, left.minItemCount(), left.maxItemCount(), left.minProperties(), left.maxProperties());
        }
        if (a instanceof AIcDefsCanonicalElement left && b instanceof AIcDefsCanonicalElement right) {
            if (!left.name().equals(right.name()) || left.elementKind() != right.elementKind()
                    || !left.keyDefinitions().equals(right.keyDefinitions())
                    || left.minItemCount() != right.minItemCount() || left.maxItemCount() != right.maxItemCount()
                    || (left.xmlWire() != null && right.xmlWire() != null
                            && !left.xmlWire().equals(right.xmlWire()))
                    || (!left.description().isEmpty() && !right.description().isEmpty()
                            && !left.description().equals(right.description()))) {
                throw conflict(path, "field name, XML QName or key declarations differ");
            }
            return new AIcDefsCanonicalElement(left.name(),
                    combine(left.structure(), right.structure(), path + "/" + left.name()),
                    left.keyDefinitions(), AIcDefsCanonicalSourceBindings.merge(
                            left.sourceBindings(), right.sourceBindings()),
                    left.minItemCount(), left.maxItemCount(),
                    left.description().isEmpty() ? right.description() : left.description(),
                    left.xmlWire() == null ? right.xmlWire() : left.xmlWire(),
                    left.defaultKind().isEmpty() ? right.defaultKind() : left.defaultKind(),
                    left.defaultKind().isEmpty() ? right.defaultValue() : left.defaultValue(),
                    left.isEmptyAllowed() || right.isEmptyAllowed(), left.elementKind());
        }
        if (a instanceof AIcDefsCanonicalList left && b instanceof AIcDefsCanonicalList right) {
            if (!left.name().equals(right.name()) || left.minItemCount() != right.minItemCount()
                    || left.maxItemCount() != right.maxItemCount() || left.uniqueItems() != right.uniqueItems() || !left.keyDefinitions().equals(right.keyDefinitions())
                    || (left.xmlWire() != null && right.xmlWire() != null
                            && !left.xmlWire().equals(right.xmlWire())))
                throw conflict(path, "list names, XML QName, key definitions or occurrence bounds differ");
            return new AIcDefsCanonicalList(left.name(),
                    combine(left.item(), right.item(), path + "/items"), left.minItemCount(), left.maxItemCount(),
                    left.keyDefinitions(), left.xmlWire() == null ? right.xmlWire() : left.xmlWire(), left.uniqueItems());
        }
        if (a instanceof AIcDefsCanonicalMap left && b instanceof AIcDefsCanonicalMap right) {
            if (!left.name().equals(right.name()) || left.mapKind() != right.mapKind()) {
                throw conflict(path, "map name or kind differs");
            }
            return new AIcDefsCanonicalMap(left.name(), left.mapKind(),
                    combine(left.keyType(), right.keyType(), path + "/keys"),
                    combine(left.valueType(), right.valueType(), path + "/values"),
                    AIcDefsCanonicalSourceBindings.merge(left.sourceBindings(), right.sourceBindings()));
        }
        if (a instanceof AIcDefsCanonicalScalar || a instanceof AIcDefsCanonicalEnum) {
            if (!a.equals(b)) throw conflict(path, "scalar kind, format or enumeration values differ");
            return a;
        }
        throw conflict(path, "unrecognized canonical structure: " + a.getClass().getName());
    }

    /**
     * Formats a precise semantic merge conflict with its canonical path.
     *
     * @param path path to the incompatible node
     * @param description reason that the node is incompatible
     * @return exception to be thrown by the merging caller
     */
    private static IllegalArgumentException conflict(String path, String description) {
        return new IllegalArgumentException("Conflicting canonical definitions at " + path + ": " + description);
    }
}
