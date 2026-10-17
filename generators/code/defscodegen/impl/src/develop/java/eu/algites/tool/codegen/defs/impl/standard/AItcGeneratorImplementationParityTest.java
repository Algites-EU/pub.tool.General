package eu.algites.tool.codegen.defs.impl.standard;


import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdGeneratedSource;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
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
                "eu.algites.tool.codegen.defs.impl.standard.AIcSchemaObjectBindingsGenerator",
                "eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest",
                "eu.algites.lib.naming.convention.AIiNameConventionCatalog",
                "eu.algites.lib.naming.convention.impl.algites.AIcAlgitesNamingProfiles_1",
                "eu.algites.tool.codegen.defs.AInDefsNameRole",
                "eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1",
                "com.fasterxml.jackson.databind.ObjectMapper", "com.fasterxml.jackson.core.JsonFactory",
                "com.fasterxml.jackson.annotation.JsonCreator", "com.fasterxml.jackson.dataformat.yaml.YAMLFactory",
                "org.yaml.snakeyaml.Yaml"}) {
            locClasspath.add(Path.of(Class.forName(locClass).getProtectionDomain().getCodeSource().getLocation().toURI()).toString());
        }
        String locPython = System.getenv().getOrDefault("MODUSTRO_PYTHON_TEST_EXECUTABLE", "");
        if (locPython.isBlank()) throw new IllegalStateException("Modustro must provide a resolved Python test executable");
        var locProcess = new ProcessBuilder(locPython, locSuite.toString(), "--java-classpath",
                String.join(java.io.File.pathSeparator, locClasspath)).directory(locArtifact.toFile()).redirectErrorStream(true);
        locProcess.environment().remove("PYTHONPATH");
        String locExplicitPythonPath = System.getenv("MODUSTRO_PYTHON_TEST_PATH");
        if (locExplicitPythonPath != null && !locExplicitPythonPath.isBlank()) {
            locProcess.environment().put("PYTHONPATH", locExplicitPythonPath);
        }
        locProcess.environment().put("PYTHONPYCACHEPREFIX", locArtifact.resolve("run/pycache").toString());
        var locStarted = locProcess.start();
        String locOutput = new String(locStarted.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        Assert.assertEquals(locStarted.waitFor(), 0, locOutput);
    }

    /** Test-only entry point used to compare the paired API across all three source frontends. */
    public static void main(String[] aArgs) throws Exception {
        if (aArgs.length != 5) throw new IllegalArgumentException("Usage: <source-kind> <target> <source> <package> <output>");
        var locTarget = AInCodeGenerationTarget.valueOf(aArgs[1]);
        var locProfile = locTarget == AInCodeGenerationTarget.PYTHON
                ? eu.algites.lib.naming.convention.impl.algites.AIcAlgitesNamingProfiles_1.pythonProfile()
                : eu.algites.lib.naming.convention.impl.algites.AIcAlgitesNamingProfiles_1.javaProfile();
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
