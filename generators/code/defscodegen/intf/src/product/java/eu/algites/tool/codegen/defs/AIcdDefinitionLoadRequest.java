package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;


import java.nio.file.Path;
import java.util.Objects;

/**
 * Request to load one source definition.
 *
 * @param path source definition path
 * @param sourceKind definition source family
 * @param namingProfile input naming and version profile
 * @param sourceNamingProfile explicit source structure profile determining the names of schema metadata properties
 */
public record AIcdDefinitionLoadRequest(Path path, AInDefinitionSourceKind sourceKind, AIiNameConventionCatalog namingProfile, String sourceNamingProfile) {
    /**
     * Backward-compatible request without an explicitly selected source-structure profile.
     *
     * @param path path of the input schema
     * @param sourceKind format of the schema definition
     * @param namingProfile naming catalog used for generated names
     */
    public AIcdDefinitionLoadRequest(Path path, AInDefinitionSourceKind sourceKind, AIiNameConventionCatalog namingProfile) {
        this(path, sourceKind, namingProfile, "");
    }
    /** Validates and normalizes the supplied data-object components. */
    public AIcdDefinitionLoadRequest {
        Objects.requireNonNull(path, "path");
        Objects.requireNonNull(sourceKind, "sourceKind");
        Objects.requireNonNull(namingProfile, "namingProfile");
        sourceNamingProfile = sourceNamingProfile == null ? "" : sourceNamingProfile;
    }
}
