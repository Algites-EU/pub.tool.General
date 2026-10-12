package eu.algites.tool.codegen.sdo;

import eu.algites.lib.naming.convention.AIcNameConventionCatalog;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Native Java SDO CLI; accepts legacy single-contract calls and YAML naming profile batches. */
public final class AIcSdoCodegenCli {
    private AIcSdoCodegenCli() { }

    /** Generate independent mutable-contract and concrete implementation files. */
    public static void main(String[] aArguments) throws Exception {
        if (java.util.Arrays.stream(aArguments).anyMatch(a -> a.startsWith("--technology-") || a.equals("--clean-only"))) {
            batch(aArguments);
            return;
        }
        if (aArguments.length < 3 || aArguments.length > 5)
            throw new IllegalArgumentException("Usage: <class> <mutable-root> <implementation-root> [marker] [--check]");
        boolean locCheck = false;
        String locMarker = "d";
        for (int i = 3; i < aArguments.length; i++) {
            if (aArguments[i].equals("--check")) locCheck = true;
            else if (locMarker.equals("d")) locMarker = aArguments[i];
            else throw new IllegalArgumentException("Invalid generator argument: " + aArguments[i]);
        }
        Path locMutableRoot = Path.of(aArguments[1]).toAbsolutePath().normalize();
        Path locImplementationRoot = Path.of(aArguments[2]).toAbsolutePath().normalize();
        if (locMutableRoot.equals(locImplementationRoot))
            throw new IllegalArgumentException("Mutable interfaces and implementations must have separate output roots");
        var locGenerated = new AIcSdoCodegenService().generate(Class.forName(aArguments[0]), locMarker);
        write(locMutableRoot, locGenerated.mutableInterface(), locCheck);
        write(locImplementationRoot, locGenerated.implementation(), locCheck);
    }

    private static void batch(String[] aArguments) throws Exception {
        Map<String, Path> locDirectories = new LinkedHashMap<>();
        Map<String, Path> locProfiles = new LinkedHashMap<>();
        List<Path> locClassPaths = new ArrayList<>();
        boolean locCheck = false;
        boolean locClean = false;
        for (String locArgument : aArguments) {
            if (locArgument.equals("--check")) { locCheck = true; continue; }
            if (locArgument.equals("--clean-only")) { locClean = true; continue; }
            if (locArgument.startsWith("--dointf-classpath=")) {
                for (String locPart : locArgument.substring("--dointf-classpath=".length()).split(java.io.File.pathSeparator))
                    locClassPaths.add(Path.of(locPart).toAbsolutePath().normalize());
                continue;
            }
            int locEquals = locArgument.indexOf('=');
            if (locEquals < 0 || !locArgument.startsWith("--technology-"))
                throw new IllegalArgumentException("Unknown batch argument: " + locArgument);
            String locKey = locArgument.substring(2, locEquals);
            String locValue = locArgument.substring(locEquals + 1);
            if (!locValue.startsWith("java:"))
                throw new IllegalArgumentException("Native Java SDO CLI requires java:path in " + locKey);
            Path locPath = Path.of(locValue.substring(5)).toAbsolutePath().normalize();
            if (locKey.endsWith("-naming-profile")) {
                if (locProfiles.putIfAbsent(locKey, locPath) != null)
                    throw new IllegalArgumentException("Duplicate profile for " + locKey);
            } else if (locKey.endsWith("-dir")) {
                if (locDirectories.putIfAbsent(locKey, locPath) != null)
                    throw new IllegalArgumentException("Duplicate directory for " + locKey);
            } else throw new IllegalArgumentException("Unknown batch option: " + locKey);
        }
        String locInput = "technology-dointf-input";
        String locMutable = "technology-sdointf-output";
        String locConcrete = "technology-sdoimpl-output";
        for (String locGroup : List.of(locMutable, locConcrete)) {
            if (!locDirectories.containsKey(locGroup + "-dir") || !locProfiles.containsKey(locGroup + "-naming-profile"))
                throw new IllegalArgumentException("Missing directory or naming catalog: " + locGroup);
        }
        if (!locClean && (!locDirectories.containsKey(locInput + "-dir") || !locProfiles.containsKey(locInput + "-naming-profile")))
            throw new IllegalArgumentException("Missing DO contract input directory and naming catalog");
        if (locClean && locCheck) throw new IllegalArgumentException("--clean-only conflicts with --check");
        Path locMutableRoot = locDirectories.get(locMutable + "-dir");
        Path locConcreteRoot = locDirectories.get(locConcrete + "-dir");
        AIcNameConventionCatalog locMutableNames = AIcNameConventionCatalog.load(locProfiles.get(locMutable + "-naming-profile"));
        AIcNameConventionCatalog locConcreteNames = AIcNameConventionCatalog.load(locProfiles.get(locConcrete + "-naming-profile"));
        Set<String> locMutableRole = Set.of("algites-java-gen-data-intf-versioned");
        Set<String> locConcreteRole = Set.of("algites-java-gen-data-class-versioned");
        if (!locCheck) {
            locMutableNames.clean(locMutableRoot, locMutableRole);
            locConcreteNames.clean(locConcreteRoot, locConcreteRole);
        }
        if (locClean) return;
        Path locInputRoot = locDirectories.get(locInput + "-dir");
        AIcNameConventionCatalog locInputNames = AIcNameConventionCatalog.load(locProfiles.get(locInput + "-naming-profile"));
        if (!Files.isDirectory(locInputRoot))
            throw new IllegalArgumentException("DO source root does not exist: " + locInputRoot);
        List<URL> locUrls = new ArrayList<>();
        for (Path locPath : locClassPaths) locUrls.add(locPath.toUri().toURL());
        try (URLClassLoader locLoader = new URLClassLoader(locUrls.toArray(URL[]::new),
                AIcSdoCodegenCli.class.getClassLoader()); var locFiles = Files.walk(locInputRoot)) {
            for (Path locSource : locFiles.filter(Files::isRegularFile).sorted().toList()) {
                var locMatch = locInputNames.recognizeFilename(locSource.getFileName().toString(),
                        Set.of("algites-java-gen-intf-versioned"));
                if (locMatch == null) continue;
                String locName = locInputNames.format(locMatch.conventionName(), "main_container_name",
                        locMatch.variables(), "upper_camel_case");
                Path locRelative = locInputRoot.relativize(locSource.getParent());
                String locQualified = locRelative.toString().replace('/', '.').replace('\\', '.');
                if (!locQualified.isEmpty()) locQualified += ".";
                locQualified += locName;
                Class<?> locContract;
                try {
                    locContract = Class.forName(locQualified, false, locLoader);
                } catch (ClassNotFoundException locError) {
                    throw new IllegalArgumentException("Compile the generated DO interfaces before running Java SDO codegen, "
                            + "and supply their classes via --dointf-classpath: " + locQualified, locError);
                }
                var locGenerated = new AIcSdoCodegenService().generate(locContract, "d",
                        locInputNames, locMutableNames, locConcreteNames);
                if (locMutableNames.recognizeFilename(Path.of(locGenerated.mutableInterface().relativePath())
                        .getFileName().toString(), locMutableRole) == null
                        || locConcreteNames.recognizeFilename(Path.of(locGenerated.implementation().relativePath())
                        .getFileName().toString(), locConcreteRole) == null)
                    throw new IllegalArgumentException("SDO output violates YAML naming profile: " + locQualified);
                write(locMutableRoot, locGenerated.mutableInterface(), locCheck);
                write(locConcreteRoot, locGenerated.implementation(), locCheck);
            }
        }
    }

    private static void write(Path aRoot, AIcdGeneratedSdoSource aSource, boolean aCheck) throws IOException {
        Path locOutput = aRoot.resolve(aSource.relativePath()).normalize();
        if (!locOutput.startsWith(aRoot)) throw new IllegalArgumentException("Generated path escapes output root");
        if (aCheck) {
            if (!Files.isRegularFile(locOutput) || !Files.readString(locOutput).equals(aSource.source()))
                throw new IllegalStateException("Missing/outdated generated SDO output: " + locOutput);
        } else {
            Files.createDirectories(locOutput.getParent());
            if (!Files.isRegularFile(locOutput) || !Files.readString(locOutput).equals(aSource.source()))
                Files.writeString(locOutput, aSource.source(), StandardCharsets.UTF_8);
        }
        System.out.println(locOutput);
    }
}
