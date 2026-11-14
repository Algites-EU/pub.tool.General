package eu.algites.tool.codegen.sdo.impl.cli;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;

import eu.algites.tool.codegen.common.AIcCodegenDiagnostics;
import eu.algites.tool.codegen.common.AIcCodegenWorkspace;
import eu.algites.tool.codegen.common.AIcCodegenRunLog;
import eu.algites.lib.naming.convention.impl.standard.AIcNameConventionCatalog;
import eu.algites.tool.codegen.common.AIcCodegenArtifactResolver;
import eu.algites.tool.codegen.sdo.AIcdGeneratedSdoSource;
import eu.algites.tool.codegen.sdo.AIcdSdoGenerationResult;
import eu.algites.tool.codegen.sdo.impl.standard.AIcSdoCodegenService;
import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.jar.JarFile;

/**
 * Generates SDO source contracts from source or compiled DataObjects using explicit semantic naming roles.
 *
 * <p>A separate input-artifact selector determines the classes to process, while
 * {@code --dointf-classpath} contains transitively required types only. Java modules
 * are scanned as ordinary classpath JARs, without requiring opens declarations.
 */
public final class AIcSdoCodegenCli {
    /** All SDO types use one schema-neutral naming role. */
    private static final String SDO_ROLE = "common";

    private AIcSdoCodegenCli() { }

    /**
     * Parses an optional settings file followed by CLI overrides and generates selected outputs.
     *
     * @param aArguments repeatable kebab-case CLI settings; none loads packaged Algites defaults
     * @throws Exception when configuration, compilation, classpath access, or writing fails
     */
    public static void main(String[] aArguments) throws Exception {
        String locPrevious = System.getProperty("algites.sdocodegen.setterInheritancePolicy");
        try {
            String[] locExpanded = expandSettings(aArguments);
            try (var locLog = AIcCodegenRunLog.fromArguments("SDO Codegen", "java",
                    locExpanded, "technology-sdointf-output-dir:java")) {
                batch(locExpanded);
            }
        } catch (Exception locFailure) {
            AIcCodegenDiagnostics.exitOnExpectedError(locFailure, "SDO Codegen (Java)");
        } finally {
            if (locPrevious == null) System.clearProperty("algites.sdocodegen.setterInheritancePolicy");
            else System.setProperty("algites.sdocodegen.setterInheritancePolicy", locPrevious);
        }
    }

    private static String[] expandSettings(String[] aArgs) throws IOException {
        return AIcLayeredCodegenSettings.expand(aArgs, "sdocodegen", "java", "sdo");
    }

    private static void requireQualifiers(String[] aQualified, String aTechnology) {
        if (aQualified.length != 2 || !aQualified[1].equals(aTechnology))
            throw new AIxCodegenValidationException("Expected option qualified by :" + aTechnology
                    + " but received " + String.join(":", aQualified), "Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.");
    }

    private static void batch(String[] aArgs) throws Exception {
        Path locRepository = Path.of(".").toAbsolutePath().normalize();
        Map<String, String> locDirectories = new LinkedHashMap<>();
        Map<String, String> locInputRoles = new LinkedHashMap<>();
        Map<String, String> locMutableRoles = new LinkedHashMap<>();
        Map<String, String> locConcreteRoles = new LinkedHashMap<>();
        List<String> locCatalogSources = new ArrayList<>();
        List<String> locArtifacts = new ArrayList<>();
        List<String> locResolvedArtifacts = new ArrayList<>();
        List<String> locDependencyArtifacts = new ArrayList<>();
        List<String> locClasses = new ArrayList<>();
        List<String> locClassPathParts = new ArrayList<>();
        String locMutableSubpackage = "";
        String locConcreteSubpackage = "";
        String locGeneratedMethodsProfile = null;
        String locCommonCodegenProfile = null;
        String locSdoCodegenProfile = null;
        Set<String> locCatalogKinds = new LinkedHashSet<>();
        boolean locCheck = false;
        boolean locClean = false;
        boolean locCleanup = false;
        boolean locOneAtATime = eu.algites.tool.codegen.common.AIcCodegenValidationBatch.defaultPolicy();
        for (String locOption : aArgs) {
            if (locOption.equals("--check")) { locCheck = true; continue; }
            if (locOption.equals("--clean-only")) { locClean = true; continue; }
            int locEquals = locOption.indexOf('=');
            if (locEquals < 3 || !locOption.startsWith("--"))
                throw new AIxCodegenValidationException("Invalid SDO CLI option: " + locOption, "Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.");
            String locName = locOption.substring(2, locEquals);
            String locValue = locOption.substring(locEquals + 1);
            String[] locQualified = locName.split(":");
            String locBase = locQualified[0];
            if (locQualified.length > 1 && locQualified[1].equals("python")) continue;
            switch (locBase) {
                case "setter-inheritance-policy" -> {
                    var locPolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.valueOf(locValue);
                    if (locPolicy == eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.DEFAULT)
                        throw new AIxCodegenValidationException("Explicit default setter policy must be concrete", "Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.");
                    System.setProperty("algites.sdocodegen.setterInheritancePolicy", locPolicy.name());
                }
                case "repository-root" -> locRepository = Path.of(locValue).toAbsolutePath().normalize();
                case "cleanup-output-folder-before-generation" -> {
                    if (locQualified.length != 1 || !(locValue.equals("true") || locValue.equals("false")))
                        throw new AIxCodegenValidationException(
                                "Expected --cleanup-output-folder-before-generation=true|false",
                                "Use an unqualified boolean cleanup setting.");
                    locCleanup = Boolean.parseBoolean(locValue);
                }
                case "naming-conventions-file" -> {
                    if (locQualified.length != 2 || locQualified[1].isBlank())
                        throw new AIxCodegenValidationException("Catalog option needs a unique qualifier: " + locOption, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
                    locCatalogKinds.add(locQualified[1]);
                    locCatalogSources.add(locValue);
                }
                case "codegen-validate-one-input-at-a-time-only" -> {
                    if (locQualified.length != 1)
                        throw new AIxCodegenValidationException("Validation policy is not technology-qualified: " + locOption,
                                "Use --codegen-validate-one-input-at-a-time-only=true or =false.");
                    locOneAtATime = eu.algites.tool.codegen.common.AIcCodegenValidationBatch.parseBoolean(locValue);
                }
                case "generated-dataobject-method-naming-convention" -> {
                    requireQualifiers(locQualified, "java");
                    locGeneratedMethodsProfile = locValue;
                }
                case "common-codegen-naming-convention" -> {
                    requireQualifiers(locQualified, "java");
                    locCommonCodegenProfile = locValue;
                }
                case "sdo-codegen-naming-convention" -> {
                    requireQualifiers(locQualified, "java");
                    locSdoCodegenProfile = locValue;
                }
                case "sdo-dependency-artifacts" -> {
                    requireQualifiers(locQualified, "java");
                    for (String part : locValue.split(";")) if (!part.isBlank()) locDependencyArtifacts.add(part);
                }
                case "sdo-dependency-paths" -> {
                    requireQualifiers(locQualified, "java");
                    for (String part : locValue.split(";")) if (!part.isBlank()) locClassPathParts.add(part);
                }
                case "sdo-input-artifacts" -> {
                    requireQualifiers(locQualified, "java");
                    for (String part : locValue.split(";")) if (!part.isBlank()) locResolvedArtifacts.add(part);
                }
                case "sdo-input-paths" -> {
                    requireQualifiers(locQualified, "java");
                    for (String part : locValue.split(";")) if (!part.isBlank()) locArtifacts.add(part);
                }
                case "dointf-input-classes" -> {
                    requireQualifiers(locQualified, "java");
                    locClasses.addAll(Arrays.asList(locValue.split(";", -1)));
                }
                case "sdointf-subpackage" -> locMutableSubpackage = locValue;
                case "sdoclass-subpackage" -> locConcreteSubpackage = locValue;
                case "technology-sdointf-output-dir", "technology-sdoimpl-output-dir" -> {
                    requireQualifiers(locQualified, "java");
                    locDirectories.put(locBase, locValue);
                }
                case "dointf-naming-convention" -> {
                    requireQualifiers(locQualified, "java");
                    locInputRoles.put(SDO_ROLE, locValue);
                }
                case "sdointf-naming-convention" -> {
                    requireQualifiers(locQualified, "java");
                    locMutableRoles.put(SDO_ROLE, locValue);
                }
                case "sdoimpl-naming-convention" -> {
                    requireQualifiers(locQualified, "java");
                    locConcreteRoles.put(SDO_ROLE, locValue);
                }
                default -> throw new AIxCodegenValidationException("Unknown SDO CLI argument: " + locOption, "Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.");
            }
        }
        if (locCheck && locCleanup) throw new AIxCodegenValidationException(
                "--check conflicts with --cleanup-output-folder-before-generation=true",
                "Run cleanup only while generating sources.");
        if (locCheck && locClean) throw new AIxCodegenValidationException("--check conflicts with --clean-only", "Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.");
        Path locMutableRoot = root(locRepository, locDirectories.get("technology-sdointf-output-dir"));
        Path locConcreteRoot = root(locRepository, locDirectories.get("technology-sdoimpl-output-dir"));
        if (locMutableRoot == null || locConcreteRoot == null)
            throw new AIxCodegenValidationException("Configure both Java SDO output roots", "Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.");
        var locValidation = new eu.algites.tool.codegen.common.AIcCodegenValidationBatch(locOneAtATime);
        List<String> locSources = new ArrayList<>();
        for (String locItem : locCatalogSources) {
            String locResolved = AIcNamingCatalogSource.normalize(locItem);
            locSources.add(locResolved.startsWith("resource:")
                    ? locResolved : root(locRepository, locResolved).toString());
        }
        AIcNameConventionCatalog locNames = AIcNamingCatalogCollector.load(locSources);
        if (locCommonCodegenProfile != null || locSdoCodegenProfile != null) {
            if (locCommonCodegenProfile == null || locSdoCodegenProfile == null
                    || locGeneratedMethodsProfile != null
                    || !locCatalogKinds.contains("codegen_common")
                    || !locCatalogKinds.contains("codegen_sdo"))
                throw new AIxCodegenValidationException("SDO needs both Common and SDO naming profiles "
                        + "and codegen_common/codegen_sdo catalogs", "Use the paired new naming profile selectors.");
            locNames = locNames.withCodegenNamingProfiles(locCommonCodegenProfile, locSdoCodegenProfile, "sdo");
        } else if (locGeneratedMethodsProfile != null) {
            locNames = locNames.withGeneratedMethodProfile(locGeneratedMethodsProfile);
        }
        if (!locInputRoles.containsKey(SDO_ROLE) || !locMutableRoles.containsKey(SDO_ROLE)
                || !locConcreteRoles.containsKey(SDO_ROLE))
            throw new AIxCodegenValidationException(
                    "Select --dointf-naming-convention:java, --sdointf-naming-convention:java and --sdoimpl-naming-convention:java",
                    "Supply one schema-neutral naming profile for each SDO input/output role.");
        AIcNameConventionCatalog locInputNames = locNames.withRoles(locInputRoles);
        AIcNameConventionCatalog locMutableNames = locNames.withRoles(locMutableRoles);
        AIcNameConventionCatalog locConcreteNames = locNames.withRoles(locConcreteRoles);
        Path locArtifact = AIcCodegenWorkspace.artifactRoot(locRepository, locMutableRoot);
        if (!locArtifact.equals(AIcCodegenWorkspace.artifactRoot(locRepository, locConcreteRoot)))
            throw new IOException("SDO output roots must belong to one artifact");
        if (locClean) {
            try (var workspace = new AIcCodegenWorkspace(locRepository, locArtifact, "sdocodegen")) {
                workspace.publish(Map.of(), false, true);
            }
            AIcCodegenWorkspace.cleanupInactive(locRepository, locArtifact, "sdocodegen");
            return;
        }
        var locService = new AIcSdoCodegenService();
        Map<String, AIcdSdoGenerationResult> locResults = new LinkedHashMap<>();
        List<Path> locDependencies = new ArrayList<>();
        for (String locPart : locClassPathParts) locDependencies.add(root(locRepository, locPart));
        if (!locDependencyArtifacts.isEmpty())
            locDependencies.addAll(AIcCodegenArtifactResolver.resolveJava(
                    String.join(";", locDependencyArtifacts)));
        // Validate the shared dependency set ONCE. Otherwise, source-input
        // batching repeats one missing classpath entry as an error for every
        // annotated DataObject in the same artifact.
        for (Path locDependency : locDependencies) {
            if (!Files.exists(locDependency))
                throw new AIxCodegenValidationException(
                        "Missing Java SDO dependency classpath entry: " + locDependency,
                        "Supply an existing JAR or compiled class/resource directory using "
                        + "--sdo-dependency-paths:java. Unmaterialized optional Gradle "
                        + "output directories must not be passed to SDO Codegen.",
                        locDependency.toString(), null);
        }
        List<Path> locSourceRoots = new ArrayList<>();
        List<Path> locBinaryPaths = new ArrayList<>();
        for (String input : locArtifacts) {
            Path selected = root(locRepository, input);
            if (!Files.exists(selected)) throw new IOException("SDO input path does not exist: " + selected);
            if (Files.isDirectory(selected)) {
                try (var walk = Files.walk(selected)) {
                    if (walk.anyMatch(path -> path.toString().endsWith(".java"))) locSourceRoots.add(selected);
                    else locBinaryPaths.add(selected);
                }
            } else if (selected.toString().endsWith(".java")) {
                locSourceRoots.add(selected.getParent());
            } else locBinaryPaths.add(selected);
        }
        for (Path locSourceRoot : locSourceRoots) {
            List<Path> locContracts = new ArrayList<>();
            try (var locWalk = Files.walk(locSourceRoot)) {
                for (Path locSource : locWalk.filter(aPath -> aPath.toString().endsWith(".java")).sorted().toList()) {
                    String locText = Files.readString(locSource, StandardCharsets.UTF_8);
                    // All source interfaces are type-checked after compilation.
                    // Only the reflected neutral @AIaDataObject declaration or
                    // an inherited neutral annotation may select an SDO input.
                    // A filename/naming convention is NOT a selection criterion.
                    if (locText.matches("(?s).*\\binterface\\s+\\w+.*"))
                        locContracts.add(locSource);
                }
            }
            if (!locContracts.isEmpty()) {
                // In aggregate mode each source is isolated so later input
                // failures are still reported. Never write output before finish().
                List<List<Path>> locGroups = new ArrayList<>();
                for (Path locContract : locContracts) locGroups.add(List.of(locContract));
                for (List<Path> locGroup : locGroups) {
                    try {
                        Map<Path, AIcdSdoGenerationResult> locGenerated = locService.generateFromSources(
                                locSourceRoot, locGroup, "d", locDependencies, locInputNames,
                                locMutableNames, locConcreteNames, locMutableSubpackage, locConcreteSubpackage,
                                locInputRoles.keySet().stream().filter(locMutableRoles::containsKey)
                                        .filter(locConcreteRoles::containsKey)
                                        .collect(java.util.stream.Collectors.toSet()));
                        locGenerated.forEach((aPath, aOutput) -> locResults.put(aPath.toString(), aOutput));
                    } catch (AIxCodegenValidationException error) {
                        locValidation.add(error, locGroup.iterator().next().toString());
                    }
                    locValidation.finishInput(locGroup.iterator().next().toString());
                }
            }
        }
        List<Path> locBinaryInputs = new ArrayList<>();
        if (!locResolvedArtifacts.isEmpty())
            locBinaryInputs.addAll(AIcCodegenArtifactResolver.resolveJava(
                    String.join(";", locResolvedArtifacts)));
        locBinaryInputs.addAll(locBinaryPaths);
        List<URL> locUrls = new ArrayList<>();
        for (Path locDependency : locDependencies) locUrls.add(locDependency.toUri().toURL());
        for (Path locInput : locBinaryInputs) locUrls.add(locInput.toUri().toURL());
        try (var locLoader = new URLClassLoader(locUrls.toArray(URL[]::new), AIcSdoCodegenCli.class.getClassLoader())) {
            Set<String> locCandidates = new LinkedHashSet<>(locClasses);
            for (Path locBinary : locBinaryInputs) locCandidates.addAll(scanClassNames(locBinary));
            for (String locClassName : locCandidates) {
                try {
                Class<?> locClass = Class.forName(locClassName, false, locLoader);
                // The service owns DataObject eligibility. In particular,
                // namespace marker interfaces extend AIiDataObject indirectly
                // but must not be sent to SDO generation as independent inputs.
                if (!AIcSdoCodegenService.isSdoInput(locClass)) continue;
                String locRole = SDO_ROLE;
                if (!locInputRoles.containsKey(locRole) || !locMutableRoles.containsKey(locRole)
                        || !locConcreteRoles.containsKey(locRole)) continue;
                locResults.put(locClassName, locService.generate(locClass, "d", locInputNames,
                        locMutableNames, locConcreteNames, locMutableSubpackage, locConcreteSubpackage));
                } catch (AIxCodegenValidationException error) {
                    locValidation.add(error, locClassName);
                } catch (ClassNotFoundException | LinkageError error) {
                    locValidation.add(new AIxCodegenValidationException(
                            "Unable to load Java DataObject input " + locClassName + ": " + error,
                            "Verify that the compiled input class and its API dependencies are on the SDO classpath.",
                            locClassName, null, error), locClassName);
                }
                locValidation.finishInput(locClassName);
            }
        }
        locValidation.finish();
        locValidation.reportNonErrors("SDO Codegen (Java)", System.err);
        Set<Path> locPaths = new LinkedHashSet<>();
        for (AIcdSdoGenerationResult locResult : locResults.values()) {
            Path locMutablePath = locMutableRoot.resolve(locResult.mutableInterface().relativePath()).normalize();
            Path locConcretePath = locConcreteRoot.resolve(locResult.implementation().relativePath()).normalize();
            if (!locPaths.add(locMutablePath) || !locPaths.add(locConcretePath))
                throw new AIxCodegenValidationException("SDO naming roles generate duplicate output path: "
                        + locMutablePath + " / " + locConcretePath, "Rename the indicated type, method or field to match the selected naming convention and update every reference to the renamed declaration.");
        }
        Map<Path, String> locPending = new LinkedHashMap<>();
        for (AIcdSdoGenerationResult locResult : locResults.values()) {
            Path mutable = locMutableRoot.resolve(locResult.mutableInterface().relativePath()).normalize();
            Path concrete = locConcreteRoot.resolve(locResult.implementation().relativePath()).normalize();
            if (locPending.putIfAbsent(mutable, locResult.mutableInterface().source()) != null
                    || locPending.putIfAbsent(concrete, locResult.implementation().source()) != null)
                throw new IOException("Duplicate SDO output path " + mutable + " / " + concrete);
        }
        try (var workspace = new AIcCodegenWorkspace(locRepository, locArtifact, "sdocodegen")) {
            workspace.publish(locPending, locCheck, locCleanup);
        }
        locPending.keySet().forEach(System.out::println);
    }

    /**
     * Removes stale generated output files without reintroducing a blanket
     * restriction on separate roles sharing a physical source directory.
     *
     * @param aMutableRoot generated mutable interface output root
     * @param aConcreteRoot generated implementation output root
     * @param aCatalog merged catalog containing both output role families
     * @param aMutableRoles configured mutable output convention identifiers
     * @param aConcreteRoles configured implementation convention identifiers
     * @throws IOException if an existing generated output cannot be removed
     */
    private static void cleanOutputs(Path aMutableRoot, Path aConcreteRoot,
            AIcNameConventionCatalog aCatalog, Map<String, String> aMutableRoles,
            Map<String, String> aConcreteRoles) throws IOException {
        if (aMutableRoot.equals(aConcreteRoot)) {
            Set<String> locConventions = new LinkedHashSet<>(aMutableRoles.values());
            locConventions.addAll(aConcreteRoles.values());
            aCatalog.clean(aMutableRoot, locConventions);
        } else {
            aCatalog.clean(aMutableRoot, Set.copyOf(aMutableRoles.values()));
            aCatalog.clean(aConcreteRoot, Set.copyOf(aConcreteRoles.values()));
        }
    }

    private static Set<String> scanClassNames(Path aRoot) throws IOException {
        if (!Files.exists(aRoot)) throw new IOException("Missing binary DataObject input: " + aRoot);
        Set<String> locNames = new LinkedHashSet<>();
        if (Files.isDirectory(aRoot)) {
            try (var locWalk = Files.walk(aRoot)) {
                for (Path locFile : locWalk.filter(a -> a.toString().endsWith(".class")).toList())
                    addClassName(locNames, aRoot.relativize(locFile).toString());
            }
        } else if (aRoot.toString().endsWith(".jar")) {
            try (var locJar = new JarFile(aRoot.toFile())) {
                var locEntries = locJar.entries();
                while (locEntries.hasMoreElements()) addClassName(locNames, locEntries.nextElement().getName());
            }
        } else throw new IOException("Expected JAR or compiled class directory: " + aRoot);
        return locNames;
    }

    private static void addClassName(Set<String> aNames, String aRelativePath) {
        if (!aRelativePath.endsWith(".class") || aRelativePath.contains("$")
                || aRelativePath.equals("module-info.class") || aRelativePath.endsWith("/package-info.class")) return;
        String locBinary = aRelativePath.substring(0, aRelativePath.length() - 6)
                .replace('/', '.').replace('\\', '.');
        if (!locBinary.startsWith("META-INF.")) aNames.add(locBinary);
    }

    private static Path root(Path aRepository, String aValue) {
        return aValue == null ? null : aRepository.resolve(aValue).normalize().toAbsolutePath();
    }

    private static void write(Path aRoot, AIcdGeneratedSdoSource aSource, boolean aCheck) throws IOException {
        Path locFile = aRoot.resolve(aSource.relativePath()).normalize();
        if (!locFile.startsWith(aRoot)) throw new AIxCodegenValidationException("Generated output escapes root", "Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.");
        if (aCheck) {
            if (!Files.isRegularFile(locFile) || !Files.readString(locFile).equals(aSource.source()))
                throw new AIxCodegenValidationException("Outdated generated SDO source: " + locFile, "Run SDO Codegen in generation mode to update its managed output, then repeat --check.");
        } else {
            Files.createDirectories(locFile.getParent());
            if (!Files.isRegularFile(locFile) || !Files.readString(locFile).equals(aSource.source()))
                Files.writeString(locFile, aSource.source(), StandardCharsets.UTF_8);
        }
        System.out.println(locFile);
    }
}
