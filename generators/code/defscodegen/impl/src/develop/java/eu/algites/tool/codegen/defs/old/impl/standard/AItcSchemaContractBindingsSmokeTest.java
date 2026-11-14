package eu.algites.tool.codegen.defs.old.impl.standard;

import java.nio.file.Files;
import java.nio.file.Path;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Verify that Defs emits only interface-artifact sources on a clean checkout. */
public final class AItcSchemaContractBindingsSmokeTest {
    @Test
    public void AIcContractOnlyRepositoryGeneration() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-contract-only-");
        Path locSchema = locRoot.resolve("intf/src/product/jsondefs/example/contracts/example_1.jsondef.schema.json");
        Files.createDirectories(locSchema.getParent());
        Files.writeString(locSchema, """
            {"$id":"https://example.test/example_1","type":"object",
             "title":"Example","properties":{"Name":{"type":"string","title":"Name"}},"required":["Name"]}
            """);
        Path locManifest = locRoot.resolve("bindings.json");
        Files.writeString(locManifest, """
            {"artifact":"intf","languages":["python","java"],"bindings":[]}
            """);
        AItcExplicitNamingProfiles.enrich(locManifest);
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        var locOutput = locGenerator.generateRepository(locRoot, locManifest, false);
        Assert.assertEquals(locOutput.size(), 4);
        Assert.assertTrue(Files.isRegularFile(locRoot.resolve("intf/src/product/java.gen/example/contracts/AIigExample_1.java")));
        Assert.assertTrue(Files.isRegularFile(locRoot.resolve("intf/src/product/python.gen/example/contracts/aiig_example_1.py")));
        Assert.assertFalse(Files.exists(locRoot.resolve("impl")));
        Assert.assertEquals(locGenerator.generateRepository(locRoot, locManifest, true), locOutput);
    }

    /**
     * JSON/YAML dynamic map entries must preserve their role-neutral read
     * parent even when the value schema is an array rather than an object.
     * The same fixture asserts Java and Python emission by the Java Defs
     * generator, so Java-only fixes cannot silently diverge from Python.
     *
     * @throws Exception if a schema fixture or generated file cannot be read
     */
    @Test
    public void AIcSyntheticArrayMapEntryExtendsCommonInBothLanguages() throws Exception {
        Path locBuild = Path.of("build", "test", "defs-canonical-map").toAbsolutePath();
        Files.createDirectories(locBuild);
        Path locRoot = Files.createTempDirectory(locBuild, "array-entry-");
        Path locSchema = locRoot.resolve("intf/src/product/jsondefs/example/contracts/"
                + "source-bindings_1.jsondef.schema.json");
        Files.createDirectories(locSchema.getParent());
        Files.writeString(locSchema, """
            {"$id":"https://example.test/source-bindings_1","type":"object",
             "title":"Source bindings","additionalProperties":{
                 "type":"array","items":{"type":"string"}}}
            """);
        Path locManifest = locRoot.resolve("bindings.json");
        Files.writeString(locManifest, """
            {"artifact":"intf","languages":["java","python"],"bindings":[]}
            """);
        AItcExplicitNamingProfiles.enrich(locManifest);
        new AIcSchemaContractBindingsGenerator().generateRepository(locRoot, locManifest, false);
        Path locJavaCommon = locRoot.resolve("intf/src/product/java.gen/example/contracts/"
                + "AIigSourceBindingsAdditionalProperties_1.java");
        Path locJavaJson = locRoot.resolve("intf/src/product/java.gen/example/contracts/"
                + "AIig_jSourceBindingsAdditionalProperties_1.java");
        Path locPythonCommon = locRoot.resolve("intf/src/product/python.gen/example/contracts/"
                + "aiig_source_bindings_additional_properties_1.py");
        Path locPythonJson = locRoot.resolve("intf/src/product/python.gen/example/contracts/"
                + "aiig__j_source_bindings_additional_properties_1.py");
        for (Path locGenerated : new Path[] {
                locJavaCommon, locJavaJson, locPythonCommon, locPythonJson}) {
            Assert.assertTrue(Files.isRegularFile(locGenerated), "Missing output " + locGenerated);
        }
        Assert.assertFalse(Files.readString(locJavaCommon).contains(
                "extends example.contracts.AIigSourceBindingsAdditionalProperties_1"),
                "The role-neutral Java interface may not inherit itself");
        Assert.assertTrue(Files.readString(locJavaJson).contains(
                "extends example.contracts.AIigSourceBindingsAdditionalProperties_1"),
                "The JSON array-valued map entry must extend its neutral Java contract");
        Assert.assertFalse(Files.readString(locPythonCommon).contains(
                "class AIigSourceBindingsAdditionalProperties_1(AIigSourceBindingsAdditionalProperties_1"),
                "The role-neutral Python class may not inherit itself");
        Assert.assertTrue(Files.readString(locPythonJson).contains(
                "class AIig_jSourceBindingsAdditionalProperties_1(AIigSourceBindingsAdditionalProperties_1"),
                "The JSON array-valued map entry must extend its neutral Python contract");
    }
}
