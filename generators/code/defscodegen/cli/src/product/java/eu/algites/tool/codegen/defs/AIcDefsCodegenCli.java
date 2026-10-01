package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AIcAlgitesNamingProfiles;


import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Command-line adapter for the default defs-codegen implementation. */
public final class AIcDefsCodegenCli {
    private AIcDefsCodegenCli() {
    }

    /**
     * Loads one canonical definition and generates one Java or Python source artifact.
     *
     * @param args source kind, target, input path, package/module name, and output root
     * @throws Exception when loading, generation, or output writing fails
     */
    public static void main(String[] args) throws Exception {
        if (args.length != 5) throw new IllegalArgumentException("Usage: <yamldefs|jsondefs|xmldefs> <java|python> <input> <package> <output-root>");
        AInDefinitionSourceKind sourceKind = AInDefinitionSourceKind.valueOf(args[0].toUpperCase());
        AInCodeGenerationTarget target = AInCodeGenerationTarget.valueOf(args[1].toUpperCase());
        var profile = target == AInCodeGenerationTarget.JAVA ? AIcAlgitesNamingProfiles.javaProfile() : AIcAlgitesNamingProfiles.pythonProfile();
        var service = new AIcDefaultDefsCodegenService();
        var definition = service.load(new AIcdDefinitionLoadRequest(Path.of(args[2]), sourceKind, profile));
        AIcdGeneratedSource generated = service.generate(new AIcdCodeGenerationRequest(definition, target, args[3], profile));
        Path output = Path.of(args[4]).resolve(generated.relativePath());
        Files.createDirectories(output.getParent());
        Files.writeString(output, generated.source(), StandardCharsets.UTF_8);
        System.out.println(output);
    }
}
