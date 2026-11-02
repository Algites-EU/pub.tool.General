package eu.algites.tool.codegen.defs.impl.cli;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;

import eu.algites.tool.codegen.common.AIcCodegenDiagnostics;

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
        } catch (Exception locFailure) {
            AIcCodegenDiagnostics.exitOnExpectedError(locFailure, "Defs Codegen (Java)");
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
                throw new AIxCodegenValidationException("Invalid batch argument: " + locArgument, "Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.");
            String locKey = locArgument.substring(2, locEquals);
            String locValue = locArgument.substring(locEquals + 1);
            if (locKey.equals("setter-inheritance-policy")) {
                var locPolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.valueOf(locValue);
                if (locPolicy == eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.DEFAULT)
                    throw new AIxCodegenValidationException("Explicit default setter policy must be concrete", "Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.");
                System.setProperty("algites.defscodegen.setterInheritancePolicy", locPolicy.name());
                continue;
            }
            if (locKey.equals("repository-root")) {
                locRepository = Path.of(locValue).toAbsolutePath().normalize(); continue;
            }
            if (locKey.startsWith("naming-conventions-file:") && locKey.indexOf(':') < locKey.length()-1) {
                if (locValue.isBlank()) throw new AIxCodegenValidationException("Empty naming catalog path", "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
                locFiles.add(locValue); continue;
            }
            String[] locQualified = locKey.split(":", -1);
            String locBase = locQualified[0];
            switch (locBase) {
                case "schema-input-dir", "input-schema-naming-convention" -> {
                    require(locQualified, 2);
                    String locKind = locQualified[1];
                    if (!Set.of("xmldefs", "yamldefs", "jsondefs").contains(locKind))
                        throw new AIxCodegenValidationException("Unknown schema kind: " + locKind, "Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.");
                    if (locBase.equals("schema-input-dir")) locInputs.put(locKind, locValue);
                    else locInputProfiles.put(locKind, locValue);
                }
                case "generated-dataobject-method-naming-convention",
                     "technology-dointf-output-dir", "output-enum-technology-naming-convention",
                     "defs-input-artifacts" -> {
                    require(locQualified, 2);
                    String locTech = locQualified[1];
                    if (!Set.of("java", "python").contains(locTech))
                        throw new AIxCodegenValidationException("Unknown target technology: " + locTech, "Inspect the qualified CLI option and layered settings file; correct the indicated value or remove the conflicting option.");
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
                        throw new AIxCodegenValidationException("Expected :technology:role:defsintf in " + locArgument, "Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.");
                    ObjectNode locTechnology = locRoles.has(locQualified[1])
                            ? (ObjectNode) locRoles.get(locQualified[1])
                            : locRoles.putObject(locQualified[1]);
                    locTechnology.put(locQualified[2], locValue);
                }
                default -> throw new AIxCodegenValidationException("Unknown batch option: " + locKey, "Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.");
            }
        }
        for (String locFile : locFiles) locCatalogFiles.add(locFile);
        if (locFiles.isEmpty()) throw new AIxCodegenValidationException("Provide --naming-conventions-file", "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        if (locCheck && locClean) throw new AIxCodegenValidationException("--check conflicts with --clean-only", "Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.");
        if (!locClean && ((locInputs.isEmpty() && locArtifactSelectors.isEmpty()) || locOutputDirs.size() == 0))
            throw new AIxCodegenValidationException("Select at least one schema source and output technology", "Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.");
        for (String locKind : locInputs.keySet())
            if (!locClean && !locInputProfiles.has(locKind))
                throw new AIxCodegenValidationException("Missing input naming convention for " + locKind, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        for (var locTech : iterable(locRoles.fieldNames()))
            if (!locOutputDirs.has(locTech))
                throw new AIxCodegenValidationException("Naming role has no configured output root: " + locTech, "Rename the indicated type, method or field to match the selected naming convention and update every reference to the renamed declaration.");
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
                                throw new AIxCodegenValidationException("Archive member escapes input root: " + locName, "Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.");
                            Files.createDirectories(locTarget.getParent());
                            try (InputStream locInput = locZip.getInputStream(locEntry)) {
                                Files.copy(locInput, locTarget);
                            }
                            locArchiveRoots.put(locKind, locRoot);
                        }
                    }
                    for (var locRoot : locArchiveRoots.entrySet()) {
                        if (!locInputProfiles.has(locRoot.getKey()))
                            throw new AIxCodegenValidationException("Missing input schema convention for " + locRoot.getKey(), "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
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
            throw new AIxCodegenValidationException("Wrong qualified option: " + String.join(":", aName), "Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.");
    }

    private static <E> Iterable<E> iterable(java.util.Iterator<E> aItems) {
        return () -> aItems;
    }
}
