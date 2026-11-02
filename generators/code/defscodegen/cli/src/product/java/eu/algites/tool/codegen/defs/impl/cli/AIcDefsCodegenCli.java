package eu.algites.tool.codegen.defs.impl.cli;


import eu.algites.tool.codegen.common.AIcCodegenArtifactResolver;
import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdGeneratedSource;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.impl.standard.AIcDefaultDefsCodegenService;
import eu.algites.tool.codegen.defs.impl.standard.AIcSchemaContractBindingsGenerator;
import eu.algites.tool.codegen.defs.impl.standard.AIcSchemaContractInterfaceGenerator;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.ZipFile;
import java.io.InputStream;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/** Native Java CLI for a single definition or a YAML-profile-driven repository batch. */
public final class AIcDefsCodegenCli {
    private AIcDefsCodegenCli() { }

    /**
     * Runs Defs generation from explicit role mappings or packaged default settings.
     *
     * @param aArguments kebab-case options; empty uses the packaged Algites defaults
     * @throws Exception when configuration, schema loading, or source generation fails
     */
    public static void main(String[] aArguments) throws Exception {
        String locPrevious = System.getProperty("algites.defscodegen.setterInheritancePolicy");
        try {
            batch(expandSettings(aArguments));
        } finally {
            if (locPrevious == null) System.clearProperty("algites.defscodegen.setterInheritancePolicy");
            else System.setProperty("algites.defscodegen.setterInheritancePolicy", locPrevious);
        }
    }

    private static String[] expandSettings(String[] aArgs) throws IOException {
        return AIcLayeredCodegenSettings.expand(aArgs, "defscodegen", "java", "defs");
    }

    private static void batch(String[] aArgs) throws Exception {
        ObjectMapper locMapper = new ObjectMapper();
        ObjectNode locManifest = locMapper.createObjectNode();
        ObjectNode locInputProfiles = locManifest.putObject("schema_input_naming_conventions");
        ObjectNode locOutputDirs = locManifest.putObject("technology_outputs");
        ObjectNode locRoles = locManifest.putObject("technology_output_naming_conventions");
        ObjectNode locEnums = locManifest.putObject("technology_enum_output_naming_conventions");
        ObjectNode locMethods = locManifest.putObject("generated_dataobject_method_naming_conventions");
        ArrayNode locCatalogFiles = locManifest.putArray("naming_convention_files");
        Path locRepository = Path.of(".").toAbsolutePath().normalize();
        boolean locCheck = false;
        boolean locClean = false;
        var locInputs = new LinkedHashMap<String, String>();
        var locFiles = new LinkedHashSet<String>();
        var locArtifactSelectors = new LinkedHashMap<String, String>();
        for (String locArgument : aArgs) {
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
            if (locKey.equals("setter-inheritance-policy")) {
                var locPolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.valueOf(locValue);
                if (locPolicy == eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.DEFAULT)
                    throw new IllegalArgumentException("Explicit default setter policy must be concrete");
                System.setProperty("algites.defscodegen.setterInheritancePolicy", locPolicy.name());
                continue;
            }
            if (locKey.equals("repository-root")) {
                locRepository = Path.of(locValue).toAbsolutePath().normalize(); continue;
            }
            if (locKey.startsWith("naming-conventions-file:") && locKey.indexOf(':') < locKey.length()-1) {
                if (locValue.isBlank()) throw new IllegalArgumentException("Empty naming catalog path");
                locFiles.add(locValue); continue;
            }
            String[] locQualified = locKey.split(":", -1);
            String locBase = locQualified[0];
            switch (locBase) {
                case "schema-input-dir", "input-schema-naming-convention" -> {
                    require(locQualified, 2);
                    String locKind = locQualified[1];
                    if (!Set.of("xmldefs", "yamldefs", "jsondefs").contains(locKind))
                        throw new IllegalArgumentException("Unknown schema kind: " + locKind);
                    if (locBase.equals("schema-input-dir")) locInputs.put(locKind, locValue);
                    else locInputProfiles.put(locKind, locValue);
                }
                case "generated-dataobject-method-naming-convention",
                     "technology-dointf-output-dir", "output-enum-technology-naming-convention",
                     "defs-input-artifacts" -> {
                    require(locQualified, 2);
                    String locTech = locQualified[1];
                    if (!Set.of("java", "python").contains(locTech))
                        throw new IllegalArgumentException("Unknown target technology: " + locTech);
                    switch (locBase) {
                        case "generated-dataobject-method-naming-convention" -> locMethods.put(locTech, locValue);
                        case "technology-dointf-output-dir" -> locOutputDirs.put(locTech, locValue);
                        case "output-enum-technology-naming-convention" -> locEnums.put(locTech, locValue);
                        default -> locArtifactSelectors.put(locTech, locValue);
                    }
                }
                case "output-interface-technology-naming-convention" -> {
                    require(locQualified, 4);
                    if (!Set.of("java", "python").contains(locQualified[1])
                            || !Set.of("common", "xmldefs_type", "xmldefs_element", "xmldefs_namespace", "yamldefs", "jsondefs")
                                    .contains(locQualified[2])
                            || !locQualified[3].equals("defsintf"))
                        throw new IllegalArgumentException("Expected :technology:role:defsintf in " + locArgument);
                    ObjectNode locTechnology = locRoles.has(locQualified[1])
                            ? (ObjectNode) locRoles.get(locQualified[1])
                            : locRoles.putObject(locQualified[1]);
                    locTechnology.put(locQualified[2], locValue);
                }
                default -> throw new IllegalArgumentException("Unknown batch option: " + locKey);
            }
        }
        for (String locFile : locFiles) locCatalogFiles.add(locFile);
        if (locFiles.isEmpty()) throw new IllegalArgumentException("Provide --naming-conventions-file");
        if (locCheck && locClean) throw new IllegalArgumentException("--check conflicts with --clean-only");
        if (!locClean && ((locInputs.isEmpty() && locArtifactSelectors.isEmpty()) || locOutputDirs.size() == 0))
            throw new IllegalArgumentException("Select at least one schema source and output technology");
        for (String locKind : locInputs.keySet())
            if (!locClean && !locInputProfiles.has(locKind))
                throw new IllegalArgumentException("Missing input naming convention for " + locKind);
        for (var locTech : iterable(locRoles.fieldNames()))
            if (!locOutputDirs.has(locTech))
                throw new IllegalArgumentException("Naming role has no configured output root: " + locTech);
        ArrayNode locSources = locManifest.putArray("schema_inputs");
        locInputs.forEach((locKind, locDir) -> {
            ObjectNode locEntry = locSources.addObject();
            locEntry.put("kind", locKind);
            locEntry.put("directory", locDir);
        });
        // Compiled schema resources are explicit inputs, not transitive dependencies.
        // They are materialized into an owned staging tree within this repository.
        Path locStage = locRepository.resolve("build/run/defs-codegen-input-artifacts");
        if (!locArtifactSelectors.isEmpty()) {
            if (Files.exists(locStage)) {
                try (var locWalk = Files.walk(locStage)) {
                    for (Path locItem : locWalk.sorted(java.util.Comparator.reverseOrder()).toList())
                        Files.delete(locItem);
                }
            }
            int locIndex = 0;
            for (var locSelection : locArtifactSelectors.entrySet()) {
                if (!locSelection.getKey().equals("java")) continue;
                for (Path locArtifact : AIcCodegenArtifactResolver.resolveJava(locSelection.getValue())) {
                    Map<String, Path> locArchiveRoots = new LinkedHashMap<>();
                    try (ZipFile locZip = new ZipFile(locArtifact.toFile())) {
                        var locEntries = locZip.entries();
                        while (locEntries.hasMoreElements()) {
                            var locEntry = locEntries.nextElement();
                            if (locEntry.isDirectory()) continue;
                            String locName = locEntry.getName();
                            String locKind = locName.endsWith(".xsd") ? "xmldefs"
                                    : locName.endsWith(".yamldef.schema.json") ? "yamldefs"
                                    : locName.endsWith(".jsondef.schema.json") ? "jsondefs" : null;
                            if (locKind == null) continue;
                            Path locRoot = locStage.resolve(locKind).resolve(String.valueOf(locIndex));
                            Path locTarget = locRoot.resolve(locName).normalize();
                            if (!locTarget.startsWith(locRoot))
                                throw new IllegalArgumentException("Archive member escapes input root: " + locName);
                            Files.createDirectories(locTarget.getParent());
                            try (InputStream locInput = locZip.getInputStream(locEntry)) {
                                Files.copy(locInput, locTarget);
                            }
                            locArchiveRoots.put(locKind, locRoot);
                        }
                    }
                    for (var locRoot : locArchiveRoots.entrySet()) {
                        if (!locInputProfiles.has(locRoot.getKey()))
                            throw new IllegalArgumentException("Missing input schema convention for " + locRoot.getKey());
                        ObjectNode locSource = locSources.addObject();
                        locSource.put("kind", locRoot.getKey());
                        locSource.put("directory", locRoot.getValue().toString());
                    }
                    locIndex++;
                }
            }
        }
        locManifest.put("artifact", ".");
        locManifest.put("clean_only", locClean);
        ArrayNode locLanguages = locManifest.putArray("languages");
        locOutputDirs.fieldNames().forEachRemaining(locLanguages::add);
        for (Map<String, String> locResult : new AIcSchemaContractBindingsGenerator()
                .generateManifest(locRepository, locManifest, locCheck))
            System.out.println(locResult.get("path"));
    }

    private static void require(String[] aName, int aExpected) {
        if (aName.length != aExpected)
            throw new IllegalArgumentException("Wrong qualified option: " + String.join(":", aName));
    }

    private static <E> Iterable<E> iterable(java.util.Iterator<E> aItems) {
        return () -> aItems;
    }
}
