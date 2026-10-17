package eu.algites.tool.codegen.defs.impl.standard;






import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdParsedVersionedName;
import java.nio.file.Path;

/** Resolves logical name and version while keeping version outside ordinary name tokenization. */
final class AIcDefinitionIdentityResolver {

    AIcdParsedVersionedName fromFileName(AIcdDefinitionLoadRequest request, Integer explicitVersion) {
        String fileName = request.path().getFileName().toString();
        String stem = stripDefinitionExtensions(fileName);
        return parseVersionedStem(stem, explicitVersion);
    }

    /** Extracts an optional numeric version and checks consistency with explicit metadata. */
    static AIcdParsedVersionedName parseVersionedStem(String aStem, Integer aExplicitVersion) {
        var locMatch = java.util.regex.Pattern.compile("^(.*)_([0-9]+)$").matcher(aStem);
        Integer locFileVersion = locMatch.matches() ? Integer.valueOf(locMatch.group(2)) : null;
        String locLogical = locFileVersion == null ? aStem : locMatch.group(1);
        if (locFileVersion != null && aExplicitVersion != null && !locFileVersion.equals(aExplicitVersion))
            throw new IllegalArgumentException("Definition version metadata " + aExplicitVersion
                    + " does not match file-name version " + locFileVersion + " for " + aStem);
        Integer locVersion = aExplicitVersion == null ? locFileVersion : aExplicitVersion;
        if (locVersion != null && locVersion < 1)
            throw new IllegalArgumentException("Definition version must be positive for " + aStem);
        return new AIcdParsedVersionedName(locLogical, locVersion);
    }

    static String stripDefinitionExtensions(String fileName) {
        String result = fileName;
        for (String suffix : new String[] {".yamldef.schema.json", ".jsondef.schema.json", ".schema.json", ".json", ".yaml", ".yml", ".xsd"}) {
            if (result.endsWith(suffix)) return result.substring(0, result.length() - suffix.length());
        }
        int dot = result.lastIndexOf('.');
        return dot < 0 ? result : result.substring(0, dot);
    }
}
