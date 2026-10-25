package eu.algites.tool.codegen.sdo.impl.cli;

import eu.algites.lib.data.dataobject.AIiDataObject;
import eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1;
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
    private static final Set<String> ROLES = Set.of(
            "common", "xmldefs_type", "xmldefs_element", "yamldefs", "jsondefs");

    private AIcSdoCodegenCli() { }

    /**
     * Parses an optional settings file followed by CLI overrides and generates selected outputs.
     *
     * @param aArguments repeatable kebab-case CLI settings; none loads packaged Algites defaults
     * @throws Exception when configuration, compilation, classpath access, or writing fails
     */
    public static void main(String[] aArguments) throws Exception {
        String[] locArgs = expandSettings(aArguments);
        String locPrevious = System.getProperty("algites.sdocodegen.setterInheritancePolicy");
        try {
            batch(locArgs);
        } finally {
            if (locPrevious == null) System.clearProperty("algites.sdocodegen.setterInheritancePolicy");
            else System.setProperty("algites.sdocodegen.setterInheritancePolicy", locPrevious);
        }
    }

    private static String[] expandSettings(String[] aArgs) throws IOException {
        return AIcLayeredCodegenSettings.expand(aArgs, "sdocodegen", "java", "sdo");
    }

    private static void batch(String[] aArgs) throws Exception {
        Path locRepository = Path.of(".").toAbsolutePath().normalize();
        Map<String, String> locDirectories = new LinkedHashMap<>();
        Map<String, String> locInputRoles = new LinkedHashMap<>();
        Map<String, String> locMutableRoles = new LinkedHashMap<>();
        Map<String, String> locConcreteRoles = new LinkedHashMap<>();
        List<String> locCatalogSources = new ArrayList<>();
        List<String> locArtifacts = new ArrayList<>();
        List<String> locClasses = new ArrayList<>();
        List<String> locClassPathParts = new ArrayList<>();
        String locMutableSubpackage = "";
        String locConcreteSubpackage = "";
        String locGeneratedMethodsProfile = null;
        boolean locCheck = false;
        boolean locClean = false;
        for (String locOption : aArgs) {
            if (locOption.equals("--check")) { locCheck = true; continue; }
            if (locOption.equals("--clean-only")) { locClean = true; continue; }
            int locEquals = locOption.indexOf('=');
            if (locEquals < 3 || !locOption.startsWith("--"))
                throw new IllegalArgumentException("Invalid SDO CLI option: " + locOption);
            String locName = locOption.substring(2, locEquals);
            String locValue = locOption.substring(locEquals + 1);
            switch (locName) {
                case "setter-inheritance-policy" -> {
                    var locPolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.valueOf(locValue);
                    if (locPolicy == eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.DEFAULT)
                        throw new IllegalArgumentException("Explicit default setter policy must be concrete");
                    System.setProperty("algites.sdocodegen.setterInheritancePolicy", locPolicy.name());
                }
                case "repository-root" -> locRepository = Path.of(locValue).toAbsolutePath().normalize();
                case "naming-conventions-file" -> locCatalogSources.add(locValue);
                case "generated-dataobject-method-naming-convention" -> {
                    String[] locSelected = locValue.split(":", 2);
                    if (locSelected.length != 2 || locSelected[1].isBlank())
                        throw new IllegalArgumentException("Expected technology:method-profile: " + locValue);
                    if (locSelected[0].equals("java")) locGeneratedMethodsProfile = locSelected[1];
                    else if (!locSelected[0].equals("python"))
                        throw new IllegalArgumentException("Unsupported technology: " + locSelected[0]);
                }
                case "dointf-classpath" -> locClassPathParts.addAll(Arrays.asList(
                        locValue.split(java.util.regex.Pattern.quote(java.io.File.pathSeparator))));
                case "dointf-input-artifact" -> locArtifacts.add(locValue);
                case "dointf-input-class" -> locClasses.add(locValue);
                case "sdointf-subpackage" -> locMutableSubpackage = locValue;
                case "sdoclass-subpackage" -> locConcreteSubpackage = locValue;
                case "technology-dointf-input-dir", "technology-sdointf-output-dir",
                        "technology-sdoimpl-output-dir" -> {
                    String[] locParts = locValue.split(":", 2);
                    if (locParts.length != 2 || !locParts[0].equals("java") || locParts[1].isBlank()) {
                        if (!locValue.startsWith("python:"))
                            throw new IllegalArgumentException("Expected java:path in " + locOption);
                    } else locDirectories.put(locName, locParts[1]);
                }
                case "input-technology-naming-convention" -> {
                    String[] locParts = locValue.split(":", 3);
                    if (locParts.length != 3 || !ROLES.contains(locParts[1]) || !locParts[2].startsWith("defsintf=")
                            || locParts[2].length() <= 9)
                        throw new IllegalArgumentException("Expected technology:role:defsintf=<id>: " + locValue);
                    if (locParts[0].equals("java")) locInputRoles.put(locParts[1], locParts[2].substring(9));
                    else if (!locParts[0].equals("python")) throw new IllegalArgumentException("Unsupported technology: " + locParts[0]);
                }
                case "output-technology-naming-convention" -> {
                    String[] locParts = locValue.split(":", 3);
                    if (locParts.length != 3 || !ROLES.contains(locParts[1]))
                        throw new IllegalArgumentException("Expected technology:role:sdointf=id,sdoclass=id: " + locValue);
                    if (!locParts[0].equals("java") && !locParts[0].equals("python"))
                        throw new IllegalArgumentException("Unknown technology " + locParts[0]);
                    for (String locEntry : locParts[2].split(",")) {
                        String[] locAssignment = locEntry.split("=", 2);
                        if (locAssignment.length != 2 || locAssignment[1].isBlank())
                            throw new IllegalArgumentException("Invalid SDO role assignment: " + locEntry);
                        if (locParts[0].equals("python")) continue;
                        if (locAssignment[0].equals("sdointf")) locMutableRoles.put(locParts[1], locAssignment[1]);
                        else if (locAssignment[0].equals("sdoclass")) locConcreteRoles.put(locParts[1], locAssignment[1]);
                        else throw new IllegalArgumentException("Unknown SDO output role: " + locAssignment[0]);
                    }
                }
                default -> throw new IllegalArgumentException("Unknown SDO CLI argument: " + locOption);
            }
        }
        if (locCheck && locClean) throw new IllegalArgumentException("--check conflicts with --clean-only");
        Path locMutableRoot = root(locRepository, locDirectories.get("technology-sdointf-output-dir"));
        Path locConcreteRoot = root(locRepository, locDirectories.get("technology-sdoimpl-output-dir"));
        if (locMutableRoot == null || locConcreteRoot == null)
            throw new IllegalArgumentException("Configure both Java SDO output roots");
        List<String> locSources = new ArrayList<>();
        for (String locItem : locCatalogSources) {
            String locResolved = AIcNamingCatalogSource.normalize(locItem);
            locSources.add(locResolved.startsWith("resource:")
                    ? locResolved : root(locRepository, locResolved).toString());
        }
        AIcNameConventionCatalog_1 locNames = AIcNamingCatalogCollector.load(locSources);
        if (locGeneratedMethodsProfile != null)
            locNames = locNames.withGeneratedMethodProfile(locGeneratedMethodsProfile);
        AIcNameConventionCatalog_1 locInputNames = locNames.withRoles(locInputRoles);
        AIcNameConventionCatalog_1 locMutableNames = locNames.withRoles(locMutableRoles);
        AIcNameConventionCatalog_1 locConcreteNames = locNames.withRoles(locConcreteRoles);
        if (locClean) {
            cleanOutputs(locMutableRoot, locConcreteRoot, locNames, locMutableRoles, locConcreteRoles);
            return;
        }
        var locService = new AIcSdoCodegenService();
        Map<String, AIcdSdoGenerationResult> locResults = new LinkedHashMap<>();
        List<Path> locDependencies = new ArrayList<>();
        for (String locPart : locClassPathParts) locDependencies.add(root(locRepository, locPart));
        Path locSourceRoot = root(locRepository, locDirectories.get("technology-dointf-input-dir"));
        if (locSourceRoot != null && !Files.isDirectory(locSourceRoot))
            System.err.println("SDO Codegen: skipping configured input directory (not found): " + locSourceRoot);
        if (locSourceRoot != null && Files.isDirectory(locSourceRoot)) {
            List<Path> locContracts = new ArrayList<>();
            try (var locWalk = Files.walk(locSourceRoot)) {
                for (Path locSource : locWalk.filter(aPath -> aPath.toString().endsWith(".java")).sorted().toList()) {
                    String locText = Files.readString(locSource, StandardCharsets.UTF_8);
                    if (locText.matches("(?s).*\\binterface\\s+\\w+.*")
                            && (locText.contains("@AIaDataObject")
                                || locText.contains("@eu.algites.lib.data.dataobject.AIaDataObject"))) {
                        locContracts.add(locSource);
                        continue;
                    }
                    for (String locProfile : locInputRoles.values()) {
                        if (locInputNames.recognizeFilename(locSource.getFileName().toString(), Set.of(locProfile)) != null) {
                            locContracts.add(locSource);
                            break;
                        }
                    }
                }
            }
            if (!locContracts.isEmpty()) {
                Map<Path, AIcdSdoGenerationResult> locGenerated = locService.generateFromSources(
                        locSourceRoot, locContracts, "d", locDependencies, locInputNames,
                        locMutableNames, locConcreteNames, locMutableSubpackage, locConcreteSubpackage,
                        locInputRoles.keySet().stream().filter(locMutableRoles::containsKey)
                                .filter(locConcreteRoles::containsKey)
                                .collect(java.util.stream.Collectors.toSet()));
                locGenerated.forEach((aPath, aOutput) -> locResults.put(aPath.toString(), aOutput));
            }
        }
        List<Path> locBinaryInputs = new ArrayList<>();
        for (String locItem : locArtifacts) locBinaryInputs.add(root(locRepository, locItem));
        List<URL> locUrls = new ArrayList<>();
        for (Path locDependency : locDependencies) locUrls.add(locDependency.toUri().toURL());
        for (Path locInput : locBinaryInputs) locUrls.add(locInput.toUri().toURL());
        try (var locLoader = new URLClassLoader(locUrls.toArray(URL[]::new), AIcSdoCodegenCli.class.getClassLoader())) {
            Set<String> locCandidates = new LinkedHashSet<>(locClasses);
            for (Path locBinary : locBinaryInputs) locCandidates.addAll(scanClassNames(locBinary));
            for (String locClassName : locCandidates) {
                Class<?> locClass = Class.forName(locClassName, false, locLoader);
                if (!locClass.isInterface() || !AIiDataObject.class.isAssignableFrom(locClass)
                        || locClass.getPackageName().startsWith("eu.algites.lib.data.dataobject")) continue;
                String locRole = role(locClass);
                if (!locInputRoles.containsKey(locRole) || !locMutableRoles.containsKey(locRole)
                        || !locConcreteRoles.containsKey(locRole)) continue;
                locResults.put(locClassName, locService.generate(locClass, "d", locInputNames,
                        locMutableNames, locConcreteNames, locMutableSubpackage, locConcreteSubpackage));
            }
        }
        for (AIcdSdoGenerationResult locResult : locResults.values()) {
            String locMutableRole = outputRole(locResult.mutableInterface(), locMutableRoles);
            String locConcreteRole = outputRole(locResult.implementation(), locConcreteRoles);
            if (locMutableRole == null || locConcreteRole == null)
                throw new IllegalArgumentException("SDO output naming profile mismatch: " + locResult.mutableInterface().typeName());
        }
        Set<Path> locPaths = new LinkedHashSet<>();
        for (AIcdSdoGenerationResult locResult : locResults.values()) {
            Path locMutablePath = locMutableRoot.resolve(locResult.mutableInterface().relativePath()).normalize();
            Path locConcretePath = locConcreteRoot.resolve(locResult.implementation().relativePath()).normalize();
            if (!locPaths.add(locMutablePath) || !locPaths.add(locConcretePath))
                throw new IllegalArgumentException("SDO naming roles generate duplicate output path: "
                        + locMutablePath + " / " + locConcretePath);
        }
        if (!locCheck)
            cleanOutputs(locMutableRoot, locConcreteRoot, locNames, locMutableRoles, locConcreteRoles);
        for (AIcdSdoGenerationResult locResult : locResults.values()) {
            write(locMutableRoot, locResult.mutableInterface(), locCheck);
            write(locConcreteRoot, locResult.implementation(), locCheck);
        }
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
            AIcNameConventionCatalog_1 aCatalog, Map<String, String> aMutableRoles,
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

    private static String outputRole(AIcdGeneratedSdoSource aOutput, Map<String, String> aRoles) {
        if (aOutput == null) return null;
        for (String locRole : aRoles.keySet())
            if (aOutput.source().contains("namingConvention = \"" + aRoles.get(locRole) + "\""))
                return locRole;
        return null;
    }

    private static String role(Class<?> aClass) {
        if (eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject.class.isAssignableFrom(aClass)) {
            var locAnnotation = aClass.getDeclaredAnnotation(eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject.class);
            return locAnnotation != null && locAnnotation.definitionKind()
                    == eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT
                    ? "xmldefs_element" : "xmldefs_type";
        }
        if (eu.algites.lib.data.dataobject.yamldefs.AIiYamlDataObject.class.isAssignableFrom(aClass)) return "yamldefs";
        if (eu.algites.lib.data.dataobject.jsondefs.AIiJsonDataObject.class.isAssignableFrom(aClass)) return "jsondefs";
        return "common";
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
        if (!locFile.startsWith(aRoot)) throw new IllegalArgumentException("Generated output escapes root");
        if (aCheck) {
            if (!Files.isRegularFile(locFile) || !Files.readString(locFile).equals(aSource.source()))
                throw new IllegalStateException("Outdated generated SDO source: " + locFile);
        } else {
            Files.createDirectories(locFile.getParent());
            if (!Files.isRegularFile(locFile) || !Files.readString(locFile).equals(aSource.source()))
                Files.writeString(locFile, aSource.source(), StandardCharsets.UTF_8);
        }
        System.out.println(locFile);
    }
}
