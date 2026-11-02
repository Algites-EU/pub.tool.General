package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdParsedVersionedName;
import java.util.Map;

/**
 * Extracts source definition identifiers and versions exclusively using the
 * naming catalog's declared filename compositions.
 *
 * @author linhart1
 */
final class AIcDefinitionIdentityResolver {

    /**
     * Parse one source filename using the explicitly selected source profile or
     * the unique matching filename profile in its catalog.
     *
     * @param request definition load request with its source naming catalog
     * @param explicitVersion optional schema-declared version
     * @return parsed logical name and effective positive version
     * @throws IllegalArgumentException if the filename is ambiguous, invalid,
     *         missing its identifier or conflicts with schema version metadata
     */
    AIcdParsedVersionedName fromFileName(AIcdDefinitionLoadRequest request, Integer explicitVersion) {
        AIiNameConventionCatalog catalog = request.namingProfile();
        String filename = request.path().getFileName().toString();
        String profile = request.sourceNamingProfile();
        Map<String, String> vars = null;
        if (!profile.isBlank()) {
            vars = matchFilename(catalog, profile, filename);
            if (vars == null) throw new AIxCodegenValidationException(
                    "Filename does not match explicitly selected source naming profile: " + filename + " / " + profile, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        } else {
            for (String candidate : catalog.names()) {
                Map<String, String> matched = matchFilename(catalog, candidate, filename);
                if (matched == null) continue;
                if (vars != null) throw new AIxCodegenValidationException(
                        "Ambiguous filename naming conventions for " + filename, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
                vars = matched;
                profile = candidate;
            }
        }
        if (vars == null) throw new AIxCodegenValidationException(
                "No source filename naming convention matches " + filename, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        String identifier = vars.get("identifier");
        if (identifier == null || identifier.isBlank()) throw new AIxCodegenValidationException(
                "Source filename profile has no identifier: " + profile, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        Integer fileVersion = vars.containsKey("version") ? Integer.valueOf(vars.get("version")) : null;
        if (fileVersion != null && fileVersion < 1 || explicitVersion != null && explicitVersion < 1)
            throw new AIxCodegenValidationException("Schema version must be positive: " + filename, "Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.");
        if (fileVersion != null && explicitVersion != null && !fileVersion.equals(explicitVersion))
            throw new AIxCodegenValidationException("Schema metadata version " + explicitVersion
                    + " differs from filename version " + fileVersion + ": " + filename, "Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.");
        return new AIcdParsedVersionedName(identifier,
                explicitVersion == null ? fileVersion : explicitVersion);
    }

    /**
     * Resolve the exact naming profile matching a source filename, without
     * guessing the extension or the position of a version delimiter.
     *
     * @param request source file to identify
     * @return selected or uniquely matching source profile
     * @throws IllegalArgumentException for missing or ambiguous profiles
     */
    static String sourceProfile(AIcdDefinitionLoadRequest request) {
        if (!request.sourceNamingProfile().isBlank()) return request.sourceNamingProfile();
        String selected = null;
        for (String candidate : request.namingProfile().names()) {
            if (matchFilename(request.namingProfile(), candidate,
                    request.path().getFileName().toString()) == null) continue;
            if (selected != null)
                throw new AIxCodegenValidationException("Ambiguous source naming profile: " + request.path(), "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
            selected = candidate;
        }
        if (selected == null) throw new AIxCodegenValidationException(
                "Missing source naming convention for " + request.path(), "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        return selected;
    }

    private static Map<String, String> matchFilename(AIiNameConventionCatalog catalog,
            String profile, String filename) {
        try {
            String suffix = catalog.format(profile, "file_name_suffix", Map.of(), null);
            if (!filename.endsWith(suffix)) return null;
            String stem = filename.substring(0, filename.length() - suffix.length());
            return catalog.parse(profile, "file_name_stem", stem);
        } catch (IllegalArgumentException error) {
            return null;
        }
    }
}
