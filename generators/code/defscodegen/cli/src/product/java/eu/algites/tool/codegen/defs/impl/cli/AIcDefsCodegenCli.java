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
                case "generated-dataobject-method-naming-convention" -> {
                    if (!Set.of("java", "python").contains(locPair[0]))
                        throw new IllegalArgumentException("Unknown target technology: " + locPair[0]);
                    locMethods.put(locPair[0], locPair[1]);
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
                            || !Set.of("common", "xmldefs_type", "xmldefs_element", "xmldefs_namespace", "yamldefs", "jsondefs")
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
