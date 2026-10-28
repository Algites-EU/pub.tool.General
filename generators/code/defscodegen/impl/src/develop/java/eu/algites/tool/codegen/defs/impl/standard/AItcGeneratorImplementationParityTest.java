package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Comparator;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Compares independent JVM/Python generators and runs their generated native types. */
public final class AItcGeneratorImplementationParityTest {
    /** Runs the complete cross-implementation integration suite as part of the Java test phase. */
    @Test
    public void AIcIndependentGeneratorOutputsAndRuntime() throws Exception {
        String locArtifactLocation = System.getenv("MODUSTRO_ARTIFACT_DIRECTORY");
        if (locArtifactLocation == null || locArtifactLocation.isBlank()) {
            throw new IllegalStateException("Modustro must provide MODUSTRO_ARTIFACT_DIRECTORY to cross-technology tests");
        }
        Path locArtifact = Path.of(locArtifactLocation).toAbsolutePath();
        Path locSuite = locArtifact.resolve("src/develop/python/generator_implementation_parity.py");
        if (!Files.isRegularFile(locSuite)) throw new IllegalStateException("Missing artifact-local parity suite: " + locSuite);
        var locClasspath = new LinkedHashSet<String>();
        locClasspath.add(System.getProperty("java.class.path"));
        for (String locClass : new String[]{
                "eu.algites.tool.codegen.defs.impl.standard.AItcGeneratorImplementationParityTest",
                "eu.algites.tool.codegen.defs.impl.standard.AIcSchemaContractBindingsGenerator",
                "eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest",
                "eu.algites.lib.naming.convention.AIiNameConventionCatalog",
                "eu.algites.lib.naming.convention.profile.algites.AIcAlgitesNamingProfiles",
                "eu.algites.tool.codegen.defs.AInDefsNameRole",
                "eu.algites.lib.naming.convention.impl.standard.AIcNameConventionCatalog",
                "com.fasterxml.jackson.databind.ObjectMapper", "com.fasterxml.jackson.core.JsonFactory",
                "com.fasterxml.jackson.annotation.JsonCreator", "com.fasterxml.jackson.dataformat.yaml.YAMLFactory",
                "org.yaml.snakeyaml.Yaml"}) {
            locClasspath.add(Path.of(Class.forName(locClass).getProtectionDomain().getCodeSource().getLocation().toURI()).toString());
        }
        String locPython = System.getenv().getOrDefault("MODUSTRO_PYTHON_TEST_EXECUTABLE", "");
        if (locPython.isBlank()) throw new IllegalStateException("Modustro must provide a resolved Python test executable");
        Path locJavaFixtures = Files.createTempDirectory("algites-java-parity-fixtures-");
        try {
            generateJavaFixtureOutputs(locArtifact, locJavaFixtures);
            var locProcess = new ProcessBuilder(locPython, locSuite.toString(), "--java-classpath",
                    String.join(java.io.File.pathSeparator, locClasspath), "--java-fixture-directory",
                    locJavaFixtures.toString()).directory(locArtifact.toFile()).redirectErrorStream(true);
            locProcess.environment().remove("PYTHONPATH");
            String locExplicitPythonPath = System.getenv("MODUSTRO_PYTHON_TEST_PATH");
            if (locExplicitPythonPath != null && !locExplicitPythonPath.isBlank()) {
                locProcess.environment().put("PYTHONPATH", locExplicitPythonPath);
            }
            locProcess.environment().put("PYTHONPYCACHEPREFIX", locArtifact.resolve("run/pycache").toString());
            var locStarted = locProcess.start();
            String locOutput = new String(locStarted.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            int locExitCode = locStarted.waitFor();
            if (locExitCode != 0) {
                String locFailure = "Native Java/Python parity subprocess failed (exit code " + locExitCode + ")"
                        + "\nWorking directory: " + locArtifact
                        + "\nPython executable: " + locPython
                        + "\nPython test path: " + locProcess.environment().getOrDefault("PYTHONPATH", "<unset>")
                        + "\nParity suite: " + locSuite
                        + "\n--- Python output / traceback ---\n" + locOutput;
                System.err.println(locFailure);
                Assert.fail(locFailure);
            }
        } finally {
            try (var locPaths = Files.walk(locJavaFixtures)) {
                for (Path locPath : locPaths.sorted(Comparator.reverseOrder()).toList())
                    Files.deleteIfExists(locPath);
            }
        }
    }

    /**
     * Produces the native Java reference outputs for the Python/JVM parity suite.
     * All generation occurs inside this TestNG invocation; no test Java main class
     * needs to be executed as a separate JVM process.
     *
     * @param aArtifact root of the Defs implementation artifact containing schemas
     * @param aDirectory isolated directory receiving the native Java reference outputs
     * @throws Exception if schema loading, rendering, or writing a fixture fails
     */
    private static void generateJavaFixtureOutputs(Path aArtifact, Path aDirectory) throws Exception {
        for (AInDefinitionSourceKind locKind : new AInDefinitionSourceKind[] {
                AInDefinitionSourceKind.JSONDEFS,
                AInDefinitionSourceKind.YAMLDEFS,
                AInDefinitionSourceKind.XMLDEFS}) {
            String locKindName = locKind.name().toLowerCase(Locale.ROOT);
            String locExtension = locKind == AInDefinitionSourceKind.XMLDEFS
                    ? "xsd" : (locKindName.equals("jsondefs") ? "jsondef.schema.json" : "yamldef.schema.json");
            for (AInCodeGenerationTarget locTarget : AInCodeGenerationTarget.values()) {
                var locProfile = locTarget == AInCodeGenerationTarget.PYTHON
                        ? AItcConfiguredNamingProfiles.pythonProfile()
                        : AItcConfiguredNamingProfiles.javaProfile();
                for (String locStem : new String[] {
                        "parity-root", "parity-child", "parity-leaf", "parity-status", "parity-builtins"}) {
                    Path locSchema = aArtifact.resolve("src/develop")
                            .resolve(locKindName).resolve(locStem + "_1." + locExtension);
                    var locDefinition = new AIcDefaultDefsCodegenService().load(
                            AItcConfiguredNamingProfiles.load(locSchema, locKind, locProfile));
                    var locSource = new AIcSchemaContractInterfaceGenerator().generate(
                            new AIcdCodeGenerationRequest(locDefinition, locTarget, "api_parity", locProfile));
                    Path locOutput = aDirectory.resolve(locKindName)
                            .resolve(locTarget.name().toLowerCase(Locale.ROOT))
                            .resolve(locStem).resolve(locSource.relativePath());
                    Files.createDirectories(locOutput.getParent());
                    Files.writeString(locOutput, locSource.source());
                }
            }
        }
    }
}
