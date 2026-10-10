package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AIcdNamingProfile;


import java.util.Objects;

/**
 * Request to render one normalized definition into program source.
 *
 * @param definition normalized canonical definition
 * @param target target programming technology
 * @param packageName target package or module namespace
 * @param namingProfile input/output naming and version profile
 */
public record AIcdCodeGenerationRequest(
        AIcdCanonicalDefinition definition,
        AInCodeGenerationTarget target,
        String packageName,
        AIcdNamingProfile namingProfile) {
    /** Validates and normalizes the supplied data-object components. */
    public AIcdCodeGenerationRequest {
        Objects.requireNonNull(definition, "definition");
        Objects.requireNonNull(target, "target");
        Objects.requireNonNull(packageName, "packageName");
        Objects.requireNonNull(namingProfile, "namingProfile");
    }
}
