package eu.algites.tool.codegen.defs;

import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Keyed values. INTEGRATED_PROPERTY_MAP writes additionalProperties inside its
 * owning object without introducing an extra JSON/YAML object wrapper.
 *
 * @param name optional declared field or synthesized map role name
 * @param mapKind standalone versus integrated additional-properties semantics
 * @param keyType canonical key structure, typically STRING
 * @param valueType canonical value structure
 * @param sourceBindings exact map declaration provenance
 */
public record AIcdDefsCodegenMap(String name, AInDefsCodegenMapKind mapKind,
        AIiDefsCodegenStructure keyType, AIiDefsCodegenStructure valueType,
        Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> sourceBindings)
        implements AIiDefsCodegenStructure {
    /** Validates each required part while preserving a possibly unnamed inline map. */
    public AIcdDefsCodegenMap {
        name = name == null ? "" : name;
        Objects.requireNonNull(mapKind, "mapKind");
        Objects.requireNonNull(keyType, "keyType");
        Objects.requireNonNull(valueType, "valueType");
        sourceBindings = AIcDefsCodegenSourceBindings.freeze(sourceBindings);
    }
    /** {@inheritDoc} */
    @Override public AInDefsCodegenStructureKind kind() { return AInDefsCodegenStructureKind.MAP; }
}

