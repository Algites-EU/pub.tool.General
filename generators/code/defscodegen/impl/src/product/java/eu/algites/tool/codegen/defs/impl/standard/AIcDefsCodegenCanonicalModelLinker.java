package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalStructureNormalizer;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalMap;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalSourceBinding;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.impl.standard.model.AIiDefsCanonicalStructure;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1;
import java.net.URI;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Consumer;

/**
 * Resolves symbolic canonical TYPE references after all source declarations have been
 * collected. References to self-recursive or mutually recursive types become symbolic
 * {@code targetIdentity} links, rather than cyclic object graphs. Both JSONDEFS/YAMLDEFS
 * local pointers and named XMLDEFS types are supported; unresolved or ambiguous edges
 * are reported with source locations and never silently become {@code ANY}.
 *
 * <p>All seven canonical kinds and their source bindings remain intact. Structural
 * normalization is deliberately performed only <em>after</em> linking and after the
 * supplied schema-validation callback has accepted the unnormalized representation.
 */
public final class AIcDefsCodegenCanonicalModelLinker {
    /** Stateless utility; not instantiable. */
    private AIcDefsCodegenCanonicalModelLinker() { }

    /**
     * Links and structurally checks a complete set of declarations, then normalizes it.
     * The schema-validation overload should be preferred by production callers.
     *
     * @param declarations all source declarations, in deterministic output order
     * @return immutable linked, normalized declarations, preserving their order
     * @throws NullPointerException when declarations or a declaration is null
     * @throws IllegalArgumentException for duplicate declarations, invalid roots,
     *         ambiguous references, unresolved symbols, or cyclic inheritance
     */
    public static List<AIcDefsCanonicalType> link(List<AIcDefsCanonicalType> declarations) {
        return link(declarations, ignored -> { });
    }

    /**
     * Links references, validates the <em>unnormalized</em> contract, then normalizes.
     * The callback can use the published generated canonical-model schema to check
     * structural and semantic constraints before any normalization discards grouping.
     *
     * @param declarations complete input declarations in their source order
     * @param validateUnnormalizedContract callback accepting the exact schema payload;
     *        callback exceptions abort linking and no normalized output is returned
     * @return linked and normalized immutable canonical definitions
     * @throws NullPointerException if an input or callback is null
     * @throws IllegalArgumentException for a malformed canonical graph
     */
    public static List<AIcDefsCanonicalType> link(List<AIcDefsCanonicalType> declarations,
            Consumer<Map<String, Object>> validateUnnormalizedContract) {
        return link(declarations, validateUnnormalizedContract, Set.of());
    }

    /**
     * Link canonical declarations with precisely declared external parent identities.
     * Reference-only parents remain external: no source TYPE is fabricated or emitted.
     * @param declarations current generator input declarations
     * @param validateUnnormalizedContract required canonical-model validator
     * @param externalParentIds verified, preexisting parent TYPE identities
     * @return normalized graph with external parent references preserved
     * @throws IllegalArgumentException on malformed or unresolved links
     * @throws NullPointerException on null input
     */
    public static List<AIcDefsCanonicalType> link(List<AIcDefsCanonicalType> declarations,
            Consumer<Map<String, Object>> validateUnnormalizedContract,
            Set<String> externalParentIds) {
        return link(declarations, validateUnnormalizedContract, externalParentIds, Map.of());
    }

    /**
     * Links source TYPEs using both their logical identities and declared schema URLs.
     *
     * @param declarations complete input declarations
     * @param validateUnnormalizedContract mandatory schema validator callback
     * @param externalParentIds verified external parent identities
     * @param documentUris mapping from source resource path to its original `$id` URI
     * @return linked and normalized canonical types
     * @throws IllegalArgumentException on invalid or ambiguous source references
     * @throws NullPointerException on missing inputs
     */
    public static List<AIcDefsCanonicalType> link(List<AIcDefsCanonicalType> declarations,
            Consumer<Map<String, Object>> validateUnnormalizedContract,
            Set<String> externalParentIds, Map<String, String> documentUris) {
        Objects.requireNonNull(documentUris, "documentUris");
        Objects.requireNonNull(declarations, "declarations");
        Objects.requireNonNull(validateUnnormalizedContract, "validateUnnormalizedContract");
        Objects.requireNonNull(externalParentIds, "externalParentIds");
        Map<String, AIcDefsCanonicalType> types = new LinkedHashMap<>();
        Map<String, Set<String>> aliases = new LinkedHashMap<>();
        List<String> errors = new ArrayList<>();
        for (AIcDefsCanonicalType type : declarations) {
            Objects.requireNonNull(type, "declaration");
            if (type.resolutionState() != AIngResolutionState_1.RESOLVED
                    || type.structure() == null || !type.targetIdentity().isEmpty()) {
                errors.add("Invalid top-level TYPE declaration: " + type.identity());
                continue;
            }
            if (types.putIfAbsent(type.identity(), type) != null) {
                errors.add("Duplicate canonical TYPE declaration: " + type.identity());
                continue;
            }
            alias(aliases, type.identity(), type.identity());
            alias(aliases, type.name(), type.identity());
            for (var entries : type.sourceBindings().entrySet()) {
                for (AIcDefsCanonicalSourceBinding binding : entries.getValue()) {
                    String resource = binding.sourceResource();
                    alias(aliases, resource + "::" + type.name(), type.identity());
                    if (binding.sourcePointer().startsWith("#")) {
                        alias(aliases, resource + binding.sourcePointer(), type.identity());
                        String declaredUri = documentUris.get(resource);
                        if (declaredUri != null && !declaredUri.isBlank()) {
                            String normalized = declaredUri.endsWith("#")
                                    ? declaredUri.substring(0, declaredUri.length() - 1) : declaredUri;
                            alias(aliases, normalized + ("#".equals(binding.sourcePointer())
                                    ? "" : binding.sourcePointer()), type.identity());
                        }
                        if ("#".equals(binding.sourcePointer())) {
                            alias(aliases, resource, type.identity());
                        }
                    }
                }
            }
        }
        for (String parent : externalParentIds) {
            if (types.containsKey(parent)) {
                throw new IllegalArgumentException("External parent overlaps local declaration: " + parent);
            }
            alias(aliases, parent, parent);
        }
        if (!errors.isEmpty()) {
            throw new IllegalArgumentException("Canonical declarations are invalid:\n"
                    + String.join("\n", errors));
        }
        List<AIcDefsCanonicalType> linked = new ArrayList<>();
        for (AIcDefsCanonicalType type : declarations) {
            linked.add((AIcDefsCanonicalType) visit(type, types, aliases, errors));
        }
        checkInheritance(linked, errors);
        if (!errors.isEmpty()) {
            throw new IllegalArgumentException("Canonical model reference resolution failed:\n"
                    + String.join("\n", errors));
        }
        validateUnnormalizedContract.accept(AIcDefsCodegenCanonicalContractPayload.emit(linked));
        return linked.stream().map(node ->
                (AIcDefsCanonicalType) AIcDefsCanonicalStructureNormalizer.normalize(node)).toList();
    }

    /**
     * Registers a source alias without replacing another declaration with the same name.
     *
     * @param aliases lookup index of source identities
     * @param key qualified or unqualified reference spelling
     * @param identity canonical declaration identity
     */
    private static void alias(Map<String, Set<String>> aliases, String key, String identity) {
        aliases.computeIfAbsent(key, ignored -> new LinkedHashSet<>()).add(identity);
    }

    /**
     * Resolves one symbolic edge in its source-resource context.
     *
     * @param reference original reference text
     * @param bindings source locations of the referencing node
     * @param aliases previously indexed declaration aliases
     * @param errors mutable diagnostic collection
     * @return resolved canonical target identifier, or the original reference on error
     */
    private static String lookup(String reference,
            Map<?, List<AIcDefsCanonicalSourceBinding>> bindings,
            Map<String, Set<String>> aliases, List<String> errors) {
        String resource = "";
        String location = "(no source location)";
        for (var values : bindings.values()) {
            if (!values.isEmpty()) {
                var binding = values.get(0);
                resource = binding.sourceResource();
                location = resource + binding.sourcePointer();
                break;
            }
        }
        List<String> names = new ArrayList<>();
        if (reference.startsWith("#") && !resource.isEmpty()) {
            names.add(resource + reference);
        } else if (!resource.isEmpty()) {
            names.add(resource + "::" + reference);
            try {
                names.add(URI.create(resource).resolve(reference).toString());
            } catch (IllegalArgumentException ignored) {
                /* Unqualified XML QName identifiers can still resolve by their local names. */
            }
        }
        names.add(reference);
        for (String name : names) {
            Set<String> matches = aliases.get(name);
            if (matches == null || matches.isEmpty()) continue;
            if (matches.size() != 1) {
                errors.add(location + ": ambiguous TYPE reference '" + reference + "': "
                        + String.join(", ", matches));
                return reference;
            }
            return matches.iterator().next();
        }
        errors.add(location + ": unresolved TYPE reference '" + reference
                + "'; include the declared type or an explicitly supported source dependency");
        return reference;
    }

    /**
     * Walks the finite declaration tree, retaining symbolic edges for recursive types.
     *
     * @param node source node
     * @param declarations canonical declarations indexed by identity
     * @param aliases accepted source reference aliases
     * @param errors accumulated diagnostics with source locations
     * @return graph node containing resolved references
     */
    private static AIiDefsCanonicalStructure visit(AIiDefsCanonicalStructure node,
            Map<String, AIcDefsCanonicalType> declarations, Map<String, Set<String>> aliases,
            List<String> errors) {
        if (node instanceof AIcDefsCanonicalType type) {
            if (type.resolutionState() == AIngResolutionState_1.UNDEFINED) {
                errors.add("Undefined canonical TYPE: " + type.identity());
                return type;
            }
            if (type.resolutionState() == AIngResolutionState_1.REFERENCE) {
                String id = lookup(type.identity(), type.sourceBindings(), aliases, errors);
                AIcDefsCanonicalType target = declarations.get(id);
                if (target == null) return type;
                return new AIcDefsCanonicalType(target.identity(), target.name(), target.origin(),
                        type.pathSegments(), List.of(), null, AIngResolutionState_1.RESOLVED,
                        type.sourceBindings(), target.identity(),
                        target.schemaVersion(), target.description());
            }
            if (!type.targetIdentity().isEmpty()) {
                if (!declarations.containsKey(type.targetIdentity())) {
                    errors.add("Linked TYPE '" + type.identity() + "' refers to an unknown target '"
                            + type.targetIdentity() + "'");
                }
                return type;
            }
            List<String> inherited = new ArrayList<>();
            for (String base : type.inheritedFromTypes()) {
                inherited.add(lookup(base, type.sourceBindings(), aliases, errors));
            }
            return new AIcDefsCanonicalType(type.identity(), type.name(), type.origin(),
                    type.pathSegments(), inherited, visit(type.structure(), declarations, aliases, errors),
                    type.resolutionState(), type.sourceBindings(), "",
                    type.schemaVersion(), type.description());
        }
        if (node instanceof AIcDefsCanonicalElementList list) {
            return new AIcDefsCanonicalElementList(list.composition(), list.children().stream()
                    .map(child -> visit(child, declarations, aliases, errors)).toList(),
                    list.minItemCount(), list.maxItemCount(), list.minProperties(), list.maxProperties());
        }
        if (node instanceof AIcDefsCanonicalElement element) {
            return new AIcDefsCanonicalElement(element.name(),
                    visit(element.structure(), declarations, aliases, errors),
                    element.keyDefinitions(), element.sourceBindings(),
                    element.minItemCount(), element.maxItemCount(), element.description(), element.xmlWire(),
                    element.defaultKind(), element.defaultValue(), element.isEmptyAllowed(),
                    element.elementKind());
        }
        if (node instanceof AIcDefsCanonicalList list) {
            return new AIcDefsCanonicalList(list.name(),
                    visit(list.item(), declarations, aliases, errors),
                    list.minItemCount(), list.maxItemCount(), list.keyDefinitions(), list.xmlWire(), list.uniqueItems());
        }
        if (node instanceof AIcDefsCanonicalMap map) {
            return new AIcDefsCanonicalMap(map.name(), map.mapKind(),
                    visit(map.keyType(), declarations, aliases, errors),
                    visit(map.valueType(), declarations, aliases, errors), map.sourceBindings());
        }
        return node;
    }

    /**
     * Rejects cyclic inherited TYPE graphs while allowing self-recursive fields.
     *
     * @param linked reference-resolved top-level declarations
     * @param errors aggregated reference-resolution diagnostics
     */
    private static void checkInheritance(List<AIcDefsCanonicalType> linked, List<String> errors) {
        Map<String, AIcDefsCanonicalType> types = new HashMap<>();
        for (AIcDefsCanonicalType type : linked) types.put(type.identity(), type);
        Set<String> completed = new HashSet<>();
        Set<String> active = new LinkedHashSet<>();
        for (AIcDefsCanonicalType type : linked) {
            checkInheritance(type.identity(), types, active, completed, errors);
        }
    }

    /**
     * Checks one edge of a declarative inheritance DAG.
     *
     * @param id current declaration
     * @param types canonical declarations by identifier
     * @param active current DFS path
     * @param completed fully checked declarations
     * @param errors collected cycle diagnostics
     */
    private static void checkInheritance(String id, Map<String, AIcDefsCanonicalType> types,
            Set<String> active, Set<String> completed, List<String> errors) {
        if (completed.contains(id)) return;
        if (!active.add(id)) {
            errors.add("Cyclic TYPE inheritance: " + String.join(" -> ", active) + " -> " + id);
            return;
        }
        AIcDefsCanonicalType type = types.get(id);
        if (type != null) {
            for (String base : type.inheritedFromTypes()) {
                if (types.containsKey(base)) checkInheritance(base, types, active, completed, errors);
            }
        }
        active.remove(id);
        completed.add(id);
    }
}
