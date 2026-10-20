package eu.algites.tool.codegen.defs.impl.cli;


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
import eu.algites.lib.naming.convention.impl.algites.AIcAlgitesNamingProfiles_1;

import java.io.IOException;
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

    /**
     * Runs Defs generation from explicit role mappings or packaged default settings.
     *
     * @param aArguments kebab-case options; empty uses the packaged Algites defaults
     * @throws Exception when configuration, schema loading, or source generation fails
     */
    public static void main(String[] aArguments) throws Exception {
        batch(expandSettings(aArguments));
    }

    private static String[] expandSettings(String[] aArgs) throws IOException {
        String locSettings = null;
        var locRemaining = new java.util.ArrayList<String>();
        for (String locArg : aArgs) {
            if (locArg.startsWith("--settings-file=")) {
                if (locSettings != null) throw new IllegalArgumentException("Duplicate --settings-file");
                locSettings = locArg.substring("--settings-file=".length());
            } else locRemaining.add(locArg);
        }
        if (locSettings == null && !locRemaining.isEmpty()) return aArgs;
        String locText;
        if (locSettings != null) {
            locText = Files.readString(Path.of(locSettings));
        } else {
            String locDefault = "algites-defscodegen-java-default.settings";
            Path locCheckout = Path.of("generators/code/defscodegen/intf/src/product/config/eu/algites/tool/codegen/defs", locDefault);
            if (Files.isRegularFile(locCheckout)) locText = Files.readString(locCheckout);
            else {
                var locResource = AIcDefsCodegenCli.class.getClassLoader().getResourceAsStream("eu/algites/tool/codegen/defs/" + locDefault);
                if (locResource == null)
                    throw new IOException("Missing packaged default Defs settings: " + locDefault);
                try (locResource) { locText = new String(locResource.readAllBytes(), StandardCharsets.UTF_8); }
            }
        }
        var locExpanded = new java.util.ArrayList<String>();
        int locLineNo = 0;
        for (String locLine : locText.lines().toList()) {
            locLineNo++;
            locLine = locLine.strip();
            if (locLine.isEmpty() || locLine.startsWith("#")) continue;
            if (!locLine.startsWith("--") || locLine.contains(" ") || locLine.startsWith("--settings-file"))
                throw new IllegalArgumentException("Invalid settings option at line " + locLineNo);
            locExpanded.add(locLine);
        }
        locExpanded.addAll(locRemaining);
        return locExpanded.toArray(String[]::new);
    }

    private static void batch(String[] aArgs) throws Exception {
        ObjectMapper locMapper = new ObjectMapper();
        ObjectNode locManifest = locMapper.createObjectNode();
        ObjectNode locInputProfiles = locManifest.putObject("schema_input_naming_conventions");
        ObjectNode locOutputDirs = locManifest.putObject("technology_outputs");
        ObjectNode locRoles = locManifest.putObject("technology_output_naming_conventions");
        ObjectNode locEnums = locManifest.putObject("technology_enum_output_naming_conventions");
        ArrayNode locCatalogFiles = locManifest.putArray("naming_convention_files");
        Path locRepository = Path.of(".").toAbsolutePath().normalize();
        boolean locCheck = false;
        boolean locClean = false;
        var locInputs = new LinkedHashMap<String, String>();
        var locFiles = new LinkedHashSet<String>();
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
            if (locKey.equals("repository-root")) {
                locRepository = Path.of(locValue).toAbsolutePath().normalize(); continue;
            }
            if (locKey.equals("naming-conventions-file")) {
                if (locValue.isBlank()) throw new IllegalArgumentException("Empty naming catalog path");
                locFiles.add(locValue); continue;
            }
            String[] locPair = locValue.split(":", 2);
            if (locPair.length != 2 || locPair[1].isBlank())
                throw new IllegalArgumentException("Expected kind:value in " + locArgument);
            switch (locKey) {
                case "schema-input-dir", "input-schema-naming-convention" -> {
                    if (!Set.of("xmldefs", "yamldefs", "jsondefs").contains(locPair[0]))
                        throw new IllegalArgumentException("Unknown schema kind: " + locPair[0]);
                    if (locKey.equals("schema-input-dir")) locInputs.put(locPair[0], locPair[1]);
                    else locInputProfiles.put(locPair[0], locPair[1]);
                }
                case "technology-dointf-output-dir", "output-enum-technology-naming-convention" -> {
                    if (!Set.of("java", "python").contains(locPair[0]))
                        throw new IllegalArgumentException("Unknown target technology: " + locPair[0]);
                    if (locKey.equals("technology-dointf-output-dir")) locOutputDirs.put(locPair[0], locPair[1]);
                    else locEnums.put(locPair[0], locPair[1]);
                }
                case "output-interface-technology-naming-convention" -> {
                    String[] locTriplet = locValue.split(":", 3);
                    if (locTriplet.length != 3 || !Set.of("java", "python").contains(locTriplet[0])
                            || !Set.of("common", "xmldefs_type", "xmldefs_element", "yamldefs", "jsondefs")
                                    .contains(locTriplet[1])
                            || !locTriplet[2].startsWith("defsintf=")
                            || locTriplet[2].length() <= "defsintf=".length())
                        throw new IllegalArgumentException("Expected technology:role:defsintf=<id>: " + locValue);
                    ObjectNode locTechnology = locRoles.has(locTriplet[0])
                            ? (ObjectNode) locRoles.get(locTriplet[0])
                            : locRoles.putObject(locTriplet[0]);
                    locTechnology.put(locTriplet[1], locTriplet[2].substring("defsintf=".length()));
                }
                default -> throw new IllegalArgumentException("Unknown batch option: " + locKey);
            }
        }
        for (String locFile : locFiles) locCatalogFiles.add(locFile);
        if (locFiles.isEmpty()) throw new IllegalArgumentException("Provide --naming-conventions-file");
        if (locCheck && locClean) throw new IllegalArgumentException("--check conflicts with --clean-only");
        if (!locClean && (locInputs.isEmpty() || locOutputDirs.isEmpty()))
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
        locManifest.put("artifact", ".");
        locManifest.put("clean_only", locClean);
        ArrayNode locLanguages = locManifest.putArray("languages");
        locOutputDirs.fieldNames().forEachRemaining(locLanguages::add);
        for (Map<String, String> locResult : new AIcSchemaContractBindingsGenerator()
                .generateManifest(locRepository, locManifest, locCheck))
            System.out.println(locResult.get("path"));
    }

    private static <E> Iterable<E> iterable(java.util.Iterator<E> aItems) {
        return () -> aItems;
    }
}
