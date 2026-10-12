package eu.algites.tool.codegen.defs;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import eu.algites.lib.naming.convention.AIcAlgitesNamingProfiles;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/** Native Java CLI for a single definition or a YAML-profile-driven repository batch. */
public final class AIcDefsCodegenCli {
    private AIcDefsCodegenCli() { }

    /** Processes either the legacy five-argument call or the new declarative batch arguments. */
    public static void main(String[] args) throws Exception {
        if (Arrays.stream(args).anyMatch(a -> a.startsWith("--"))) {
            batch(args);
            return;
        }
        if (args.length != 5) throw new IllegalArgumentException("Usage: <yamldefs|jsondefs|xmldefs> <java|python> <input> <package> <output-root>");
        AInDefinitionSourceKind sourceKind = AInDefinitionSourceKind.valueOf(args[0].toUpperCase());
        AInCodeGenerationTarget target = AInCodeGenerationTarget.valueOf(args[1].toUpperCase());
        var profile = target == AInCodeGenerationTarget.JAVA ? AIcAlgitesNamingProfiles.javaProfile() : AIcAlgitesNamingProfiles.pythonProfile();
        var service = new AIcDefaultDefsCodegenService();
        var definition = service.load(new AIcdDefinitionLoadRequest(Path.of(args[2]), sourceKind, profile));
        AIcdGeneratedSource generated = new AIcSchemaContractInterfaceGenerator().generate(
                new AIcdCodeGenerationRequest(definition, target, args[3], profile));
        Path output = Path.of(args[4]).resolve(generated.relativePath());
        Files.createDirectories(output.getParent());
        Files.writeString(output, generated.source(), StandardCharsets.UTF_8);
        System.out.println(output);
    }

    private static void batch(String[] args) throws Exception {
        ObjectMapper locMapper = new ObjectMapper();
        ObjectNode locManifest = locMapper.createObjectNode();
        ArrayNode locSources = locManifest.putArray("schema_inputs");
        ObjectNode locInputProfiles = locManifest.putObject("schema_input_naming_profiles");
        ObjectNode locOutputDirs = locManifest.putObject("technology_outputs");
        ObjectNode locOutputProfiles = locManifest.putObject("technology_naming_profiles");
        Path locRepository = Path.of(".").toAbsolutePath().normalize();
        boolean locCheck = false;
        boolean locClean = false;
        for (String locArgument : args) {
            if (locArgument.equals("--check")) { locCheck = true; continue; }
            if (locArgument.equals("--clean-only")) { locClean = true; continue; }
            if (locArgument.equals("--allow-unversioned-schemas")) {
                locManifest.put("allow_unversioned_schemas", true); continue;
            }
            int locEquals = locArgument.indexOf('=');
            if (locEquals < 0 || !locArgument.startsWith("--"))
                throw new IllegalArgumentException("Invalid batch argument: " + locArgument);
            String locKey = locArgument.substring(2, locEquals);
            String locValue = locArgument.substring(locEquals + 1);
            if (locKey.equals("repository-root")) { locRepository = Path.of(locValue).toAbsolutePath().normalize(); continue; }
            int locColon = locValue.indexOf(':');
            if (locColon < 1 || locColon == locValue.length() - 1)
                throw new IllegalArgumentException(locKey + " expects kind:path");
            String locKind = locValue.substring(0, locColon);
            String locPath = locValue.substring(locColon + 1);
            switch (locKey) {
                case "schema-input-dir" -> {
                    if (!Set.of("yamldefs", "jsondefs", "xmldefs").contains(locKind))
                        throw new IllegalArgumentException("Unknown schema kind: " + locKind);
                    ObjectNode locEntry = locSources.addObject();
                    locEntry.put("kind", locKind);
                    locEntry.put("directory", locPath);
                }
                case "schema-input-naming-profile" -> putUnique(locInputProfiles, locKind, locPath);
                case "technology-dointf-output-dir" -> putUnique(locOutputDirs, locKind, locPath);
                case "technology-dointf-output-naming-profile" -> putUnique(locOutputProfiles, locKind, locPath);
                default -> throw new IllegalArgumentException("Unknown batch option: " + locKey);
            }
        }
        Set<String> locOutputs = new LinkedHashSet<>();
        locOutputDirs.fieldNames().forEachRemaining(locOutputs::add);
        Set<String> locProfiles = new LinkedHashSet<>();
        locOutputProfiles.fieldNames().forEachRemaining(locProfiles::add);
        if (locOutputs.isEmpty() || !locOutputs.equals(locProfiles))
            throw new IllegalArgumentException("Every requested technology requires an output directory and naming profile");
        if (!locClean && locSources.isEmpty())
            throw new IllegalArgumentException("Batch generation requires at least one schema input root");
        if (locCheck && locClean)
            throw new IllegalArgumentException("--check and --clean-only conflict");
        Set<String> locSourceKinds = new LinkedHashSet<>();
        for (var locEntry : locSources) locSourceKinds.add(locEntry.path("kind").asText());
        Set<String> locSourceProfiles = new LinkedHashSet<>();
        locInputProfiles.fieldNames().forEachRemaining(locSourceProfiles::add);
        if (!locClean && !locSourceKinds.equals(locSourceProfiles))
            throw new IllegalArgumentException("Each selected schema kind requires one input naming profile");
        for (String locTechnology : locOutputs)
            if (!Set.of("java", "python").contains(locTechnology))
                throw new IllegalArgumentException("Unknown target technology: " + locTechnology);
        locManifest.put("artifact", ".");
        locManifest.put("clean_only", locClean);
        ArrayNode locLanguages = locManifest.putArray("languages");
        for (String locTechnology : locOutputs) locLanguages.add(locTechnology);
        for (Map<String, String> locResult : new AIcSchemaContractBindingsGenerator()
                .generateManifest(locRepository, locManifest, locCheck))
            System.out.println(locResult.get("path"));
    }

    private static void putUnique(ObjectNode aTarget, String aKind, String aPath) {
        if (aTarget.has(aKind)) throw new IllegalArgumentException("Duplicate mapping for " + aKind);
        aTarget.put(aKind, aPath);
    }
}
