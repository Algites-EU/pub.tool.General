package eu.algites.tool.codegen.defs.impl.standard;

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
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        var locOutput = locGenerator.generateRepository(locRoot, locManifest, false);
        Assert.assertEquals(locOutput.size(), 2);
        Assert.assertTrue(Files.isRegularFile(locRoot.resolve("intf/src/product/java.gen/example/contracts/AIigExample_1.java")));
        Assert.assertTrue(Files.isRegularFile(locRoot.resolve("intf/src/product/python.gen/example/contracts/aiig_example_1.py")));
        Assert.assertFalse(Files.exists(locRoot.resolve("impl")));
        Assert.assertEquals(locGenerator.generateRepository(locRoot, locManifest, true), locOutput);
    }
}
