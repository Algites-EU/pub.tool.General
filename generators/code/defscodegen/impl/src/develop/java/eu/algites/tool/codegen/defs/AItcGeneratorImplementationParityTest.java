package eu.algites.tool.codegen.defs;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashSet;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Compares independent JVM/Python generators and runs their generated native types. */
public final class AItcGeneratorImplementationParityTest {
    /** Runs the complete cross-implementation integration suite as part of the Java test phase. */
    @Test
    public void AIcIndependentGeneratorOutputsAndRuntime() throws Exception {
        Path locRoot = Path.of("").toAbsolutePath();
        String locRelative = "generators/code/defscodegen/impl/src/develop/python/generator_implementation_parity.py";
        while (locRoot != null && !Files.isRegularFile(locRoot.resolve(locRelative))) locRoot = locRoot.getParent();
        if (locRoot == null) throw new IllegalStateException("Cannot find generator implementation parity suite in checkout");
        var locClasspath = new LinkedHashSet<String>();
        locClasspath.add(System.getProperty("java.class.path"));
        for (String locClass : new String[]{
                "eu.algites.tool.codegen.defs.AItcGeneratorImplementationParityTest",
                "eu.algites.tool.codegen.defs.AIcSchemaObjectBindingsGenerator",
                "eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest",
                "eu.algites.lib.naming.convention.AIcdNamingProfile",
                "eu.algites.lib.naming.convention.AIcAlgitesNamingProfiles",
                "eu.algites.lib.naming.conversion.AIiNameConverter",
                "eu.algites.lib.naming.conversion.AIcDefaultNameConverter",
                "com.fasterxml.jackson.databind.ObjectMapper", "com.fasterxml.jackson.core.JsonFactory",
                "com.fasterxml.jackson.annotation.JsonCreator", "com.fasterxml.jackson.dataformat.yaml.YAMLFactory",
                "org.yaml.snakeyaml.Yaml"}) {
            locClasspath.add(Path.of(Class.forName(locClass).getProtectionDomain().getCodeSource().getLocation().toURI()).toString());
        }
        String locPython = System.getenv().getOrDefault("ALGITES_PYTHON_EXECUTABLE", "python3");
        var locProcess = new ProcessBuilder(locPython, locRoot.resolve(locRelative).toString(), "--java-classpath",
                String.join(java.io.File.pathSeparator, locClasspath)).directory(locRoot.toFile()).redirectErrorStream(true);
        String locExistingPythonPath = System.getenv().getOrDefault("PYTHONPATH", "");
        var locPythonPaths = new java.util.ArrayList<String>();
        for (String locArtifact : java.util.List.of("intf", "impl")) {
            locPythonPaths.add(locRoot.resolve("generators/code/defscodegen/" + locArtifact + "/src/product/python").toString());
        }
        String locPreparedDependencies = System.getenv("MODUSTRO_GENERATOR_PARITY_PYTHON_DEPENDENCIES");
        if (locPreparedDependencies != null && !locPreparedDependencies.isBlank()) locPythonPaths.add(locPreparedDependencies);
        if (!locExistingPythonPath.isEmpty()) locPythonPaths.add(locExistingPythonPath);
        locProcess.environment().put("PYTHONPATH", String.join(java.io.File.pathSeparator, locPythonPaths));
        locProcess.environment().put("PYTHONPYCACHEPREFIX", locRoot.resolve("build/run/generator-parity/pycache").toString());
        var locStarted = locProcess.start();
        String locOutput = new String(locStarted.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        Assert.assertEquals(locStarted.waitFor(), 0, locOutput);
    }

    /** Test-only entry point used to compare the paired API across all three source frontends. */
    public static void main(String[] aArgs) throws Exception {
        if (aArgs.length != 5) throw new IllegalArgumentException("Usage: <source-kind> <target> <source> <package> <output>");
        var locTarget = AInCodeGenerationTarget.valueOf(aArgs[1]);
        var locProfile = locTarget == AInCodeGenerationTarget.PYTHON
                ? eu.algites.lib.naming.convention.AIcAlgitesNamingProfiles.pythonProfile()
                : eu.algites.lib.naming.convention.AIcAlgitesNamingProfiles.javaProfile();
        var locDefinition = new AIcDefaultDefsCodegenService().load(new AIcdDefinitionLoadRequest(
                Path.of(aArgs[2]), AInDefinitionSourceKind.valueOf(aArgs[0]), locProfile));
        var locPair = new AIcSchemaInterfaceGenerator().generate(new AIcdCodeGenerationRequest(
                locDefinition, locTarget, aArgs[3], locProfile));
        for (var locSource : new AIcdGeneratedSource[]{locPair.contract(), locPair.implementation()}) {
            if (locSource == null) continue;
            Path locPath = Path.of(aArgs[4]).resolve(locSource.relativePath());
            Files.createDirectories(locPath.getParent());
            Files.writeString(locPath, locSource.source());
        }
    }
}
