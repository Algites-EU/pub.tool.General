package eu.algites.tool.codegen.defs;

import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * A named contract or a synthetic contract introduced while reading an inline schema.
 * A synthetic type retains its source-derived naming path; normalization never removes
 * a type when it is required for a generated interface or distinct source binding.
 *
 * @param identity stable unique type identity, including for synthesized contracts
 * @param name unversioned naming candidate; formatter applies the naming convention
 * @param origin whether the type was source-declared or synthetic
 * @param pathSegments ordered semantic path segments, before lexical formatting
 * @param inheritedFromTypes ordered identifiers of inherited types
 * @param structure nested canonical structure, absent only for unresolved states
 * @param resolutionState state of frontend reference resolution
 * @param sourceBindings exact provenance grouped by input technology
 * @param targetIdentity resolved symbolic link to a separately declared TYPE,
 *      or empty when this TYPE owns its nested structure
 * @param schemaVersion exact source version token, empty when unspecified
 * @param description documentation from the source declaration, empty when absent
 */
public record AIcdDefsCodegenType(
        String identity, String name, AInDefsCodegenTypeOrigin origin,
        List<String> pathSegments, List<String> inheritedFromTypes,
        AIiDefsCodegenStructure structure, AInDefsCodegenResolutionState resolutionState,
        Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> sourceBindings,
        String targetIdentity, String schemaVersion, String description)
        implements AIiDefsCodegenStructure {
    /**
     * Creates a normal declared/synthetic or pending reference TYPE without a linked target.
     *
     * @param identity stable type or reference identity
     * @param name source or generated type name
     * @param origin whether declared or synthetic
     * @param pathSegments source-derived semantic naming path
     * @param inheritedFromTypes direct parent type identities
     * @param structure structure of a definition, null for unresolved references
     * @param resolutionState current reference-resolution state
     * @param sourceBindings exact per-technology provenance
     */
    public AIcdDefsCodegenType(String identity, String name, AInDefsCodegenTypeOrigin origin,
            List<String> pathSegments, List<String> inheritedFromTypes, AIiDefsCodegenStructure structure,
            AInDefsCodegenResolutionState resolutionState,
            Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> sourceBindings) {
        this(identity, name, origin, pathSegments, inheritedFromTypes, structure,
                resolutionState, sourceBindings, "");
    }

    /**
     * Compatibility constructor preserving the original nine-argument API.
     *
     * @param identity source type identity
     * @param name declared or synthetic type name
     * @param origin source declaration origin
     * @param pathSegments semantic naming path
     * @param inheritedFromTypes parent type references
     * @param structure nested canonical graph or null for references
     * @param resolutionState current resolution state
     * @param sourceBindings exact source provenance
     * @param targetIdentity symbolic reference identity or empty string
     */
    public AIcdDefsCodegenType(String identity, String name, AInDefsCodegenTypeOrigin origin,
            List<String> pathSegments, List<String> inheritedFromTypes, AIiDefsCodegenStructure structure,
            AInDefsCodegenResolutionState resolutionState,
            Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> sourceBindings,
            String targetIdentity) {
        this(identity, name, origin, pathSegments, inheritedFromTypes, structure,
                resolutionState, sourceBindings, targetIdentity, "", "");
    }

    /** Copies all collections and requires a resolved type to have a nested structure. */
    public AIcdDefsCodegenType {
        Objects.requireNonNull(identity, "identity");
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(origin, "origin");
        Objects.requireNonNull(resolutionState, "resolutionState");
        Objects.requireNonNull(targetIdentity, "targetIdentity");
        Objects.requireNonNull(schemaVersion, "schemaVersion");
        Objects.requireNonNull(description, "description");
        if (identity.isBlank()) throw new IllegalArgumentException("Type identity must not be blank");
        pathSegments = List.copyOf(pathSegments == null ? List.of() : pathSegments);
        inheritedFromTypes = List.copyOf(inheritedFromTypes == null ? List.of() : inheritedFromTypes);
        sourceBindings = AIcDefsCodegenSourceBindings.freeze(sourceBindings);
        if (resolutionState == AInDefsCodegenResolutionState.RESOLVED) {
            if ((structure == null) == targetIdentity.isEmpty()) {
                throw new IllegalArgumentException("Resolved TYPE requires exactly one structure or linked target identity");
            }
        } else if (!targetIdentity.isEmpty()) {
            throw new IllegalArgumentException("Pending TYPE cannot already have a linked target");
        }
        if (origin == AInDefsCodegenTypeOrigin.SYNTHETIC && pathSegments.isEmpty()) {
            throw new IllegalArgumentException("Synthetic TYPE requires semantic naming path segments");
        }
    }

    /** {@inheritDoc} */
    @Override public AInDefsCodegenStructureKind kind() { return AInDefsCodegenStructureKind.TYPE; }
}

