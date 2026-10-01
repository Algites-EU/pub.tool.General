package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.conversion.AIcDefaultNameConverter;
import eu.algites.lib.naming.conversion.AIcdParsedVersionedName;


import java.nio.file.Path;

/** Resolves logical name and version while keeping version outside ordinary name tokenization. */
final class AIcDefinitionIdentityResolver {
    private final AIcDefaultNameConverter converter = new AIcDefaultNameConverter();

    AIcdParsedVersionedName fromFileName(AIcdDefinitionLoadRequest request, Integer explicitVersion) {
        String fileName = request.path().getFileName().toString();
        String stem = stripDefinitionExtensions(fileName);
        return converter.parseVersionedName(stem, explicitVersion, request.namingProfile().inputVersionPolicy());
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
