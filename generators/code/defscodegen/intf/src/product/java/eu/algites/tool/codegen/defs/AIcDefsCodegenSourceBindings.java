package eu.algites.tool.codegen.defs;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Shared immutable provenance map operations used identically by both generator frontends. */
public final class AIcDefsCodegenSourceBindings {
    /** Prevents construction of a utility-only class. */
    private AIcDefsCodegenSourceBindings() { }

    /**
     * Copies an input technology-to-bindings map without discarding multiple bindings
     * belonging to the same source technology.
     *
     * @param source source mappings, or null for none
     * @return immutable map and immutable per-technology lists
     * @throws NullPointerException when a technology, list, or binding is null
     */
    public static Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> freeze(
            Map<AInDefsCodegenSourceInputKind, ? extends List<AIcdDefsCodegenSourceBinding>> source) {
        if (source == null || source.isEmpty()) return Map.of();
        EnumMap<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> result =
                new EnumMap<>(AInDefsCodegenSourceInputKind.class);
        for (var entry : source.entrySet()) {
            result.put(Objects.requireNonNull(entry.getKey(), "source kind"),
                    List.copyOf(Objects.requireNonNull(entry.getValue(), "source bindings")));
        }
        return Map.copyOf(result);
    }

    /**
     * Merges distinct and repeated technology bindings while preserving their insertion order.
     *
     * @param first provenance from the existing node, possibly empty
     * @param second additional provenance, possibly empty
     * @return a new immutable, accumulation-preserving mapping
     */
    public static Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> merge(
            Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> first,
            Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> second) {
        EnumMap<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> values =
                new EnumMap<>(AInDefsCodegenSourceInputKind.class);
        for (var mapping : List.of(freeze(first), freeze(second))) {
            for (var entry : mapping.entrySet()) {
                values.computeIfAbsent(entry.getKey(), ignored -> new ArrayList<>()).addAll(entry.getValue());
            }
        }
        return freeze(values);
    }
}

