package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AIcdNamingProfile;


import java.nio.file.Path;
import java.util.Objects;

/**
 * Request to load one source definition.
 *
 * @param path source definition path
 * @param sourceKind definition source family
 * @param namingProfile input naming and version profile
 */
public record AIcdDefinitionLoadRequest(Path path, AInDefinitionSourceKind sourceKind, AIcdNamingProfile namingProfile) {
    /** Validates and normalizes the supplied data-object components. */
    public AIcdDefinitionLoadRequest {
        Objects.requireNonNull(path, "path");
        Objects.requireNonNull(sourceKind, "sourceKind");
        Objects.requireNonNull(namingProfile, "namingProfile");
    }
}
