package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcDefsCodegenSourceBindings;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenElement;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenElementList;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenEnum;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenList;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenMap;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenScalar;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenType;
import eu.algites.tool.codegen.defs.AIiDefsCodegenStructure;
import eu.algites.tool.codegen.defs.AInDefsCodegenTypeOrigin;
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
    public static List<AIcdDefsCodegenType> merge(List<AIcdDefsCodegenType> declarations) {
        Objects.requireNonNull(declarations, "declarations");
        Map<String, AIcdDefsCodegenType> output = new LinkedHashMap<>();
        for (AIcdDefsCodegenType type : declarations) {
            Objects.requireNonNull(type, "declaration");
            if (!type.targetIdentity().isEmpty()) {
                throw new IllegalArgumentException("Source declarations must not already be reference-linked");
            }
            AIcdDefsCodegenType previous = output.get(type.identity());
            output.put(type.identity(), previous == null ? type
                    : (AIcdDefsCodegenType) combine(previous, type, type.identity()));
        }
        return List.copyOf(output.values());
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
    private static AIiDefsCodegenStructure combine(AIiDefsCodegenStructure a,
            AIiDefsCodegenStructure b, String path) {
        if (a.getClass() != b.getClass()) {
            throw conflict(path, "structural kinds differ: " + a.kind() + " / " + b.kind());
        }
        if (a instanceof AIcdDefsCodegenType left && b instanceof AIcdDefsCodegenType right) {
            if (left.origin() != right.origin() || !left.name().equals(right.name())
                    || !left.pathSegments().equals(right.pathSegments())
                    || !left.inheritedFromTypes().equals(right.inheritedFromTypes())
                    || left.resolutionState() != right.resolutionState()
                    || !left.targetIdentity().equals(right.targetIdentity())
                    || !left.identity().equals(right.identity())
                        && left.origin() != AInDefsCodegenTypeOrigin.SYNTHETIC
                    || (left.structure() == null) != (right.structure() == null)
                    || (!left.schemaVersion().isEmpty() && !right.schemaVersion().isEmpty()
                            && !left.schemaVersion().equals(right.schemaVersion()))
                    || (!left.description().isEmpty() && !right.description().isEmpty()
                            && !left.description().equals(right.description()))) {
                throw conflict(path, "TYPE identities, origin, naming, ancestry or state differ");
            }
            var nested = left.structure() == null ? null
                    : combine(left.structure(), right.structure(), path + "/structure");
            return new AIcdDefsCodegenType(left.identity(), left.name(), left.origin(),
                    left.pathSegments(), left.inheritedFromTypes(), nested,
                    left.resolutionState(), AIcDefsCodegenSourceBindings.merge(
                            left.sourceBindings(), right.sourceBindings()), left.targetIdentity(),
                    left.schemaVersion().isEmpty() ? right.schemaVersion() : left.schemaVersion(),
                    left.description().isEmpty() ? right.description() : left.description());
        }
        if (a instanceof AIcdDefsCodegenElementList left && b instanceof AIcdDefsCodegenElementList right) {
            if (left.composition() != right.composition() || left.children().size() != right.children().size()
                    || left.minOccurs() != right.minOccurs() || left.maxOccurs() != right.maxOccurs()) {
                throw conflict(path, "group composition or child count differs");
            }
            List<AIiDefsCodegenStructure> children = new ArrayList<>();
            for (int index = 0; index < left.children().size(); index++) {
                children.add(combine(left.children().get(index), right.children().get(index),
                        path + "/children/" + index));
            }
            return new AIcdDefsCodegenElementList(left.composition(), children, left.minOccurs(), left.maxOccurs());
        }
        if (a instanceof AIcdDefsCodegenElement left && b instanceof AIcdDefsCodegenElement right) {
            if (!left.name().equals(right.name()) || !left.keyDefinitions().equals(right.keyDefinitions())
                    || left.minOccurs() != right.minOccurs() || left.maxOccurs() != right.maxOccurs()
                    || (left.xmlWire() != null && right.xmlWire() != null
                            && !left.xmlWire().equals(right.xmlWire()))
                    || (!left.description().isEmpty() && !right.description().isEmpty()
                            && !left.description().equals(right.description()))) {
                throw conflict(path, "field name, XML QName or key declarations differ");
            }
            return new AIcdDefsCodegenElement(left.name(),
                    combine(left.structure(), right.structure(), path + "/" + left.name()),
                    left.keyDefinitions(), AIcDefsCodegenSourceBindings.merge(
                            left.sourceBindings(), right.sourceBindings()),
                    left.minOccurs(), left.maxOccurs(),
                    left.description().isEmpty() ? right.description() : left.description(),
                    left.xmlWire() == null ? right.xmlWire() : left.xmlWire());
        }
        if (a instanceof AIcdDefsCodegenList left && b instanceof AIcdDefsCodegenList right) {
            if (!left.name().equals(right.name()) || left.minOccurs() != right.minOccurs()
                    || left.maxOccurs() != right.maxOccurs() || !left.keyDefinitions().equals(right.keyDefinitions())
                    || (left.xmlWire() != null && right.xmlWire() != null
                            && !left.xmlWire().equals(right.xmlWire())))
                throw conflict(path, "list names, XML QName, key definitions or occurrence bounds differ");
            return new AIcdDefsCodegenList(left.name(),
                    combine(left.item(), right.item(), path + "/items"), left.minOccurs(), left.maxOccurs(),
                    left.keyDefinitions(), left.xmlWire() == null ? right.xmlWire() : left.xmlWire());
        }
        if (a instanceof AIcdDefsCodegenMap left && b instanceof AIcdDefsCodegenMap right) {
            if (!left.name().equals(right.name()) || left.mapKind() != right.mapKind()) {
                throw conflict(path, "map name or kind differs");
            }
            return new AIcdDefsCodegenMap(left.name(), left.mapKind(),
                    combine(left.keyType(), right.keyType(), path + "/keys"),
                    combine(left.valueType(), right.valueType(), path + "/values"),
                    AIcDefsCodegenSourceBindings.merge(left.sourceBindings(), right.sourceBindings()));
        }
        if (a instanceof AIcdDefsCodegenScalar || a instanceof AIcdDefsCodegenEnum) {
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
