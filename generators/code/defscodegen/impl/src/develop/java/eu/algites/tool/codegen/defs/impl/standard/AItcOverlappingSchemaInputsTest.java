package eu.algites.tool.codegen.defs.impl.standard;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Regression coverage for merging independently located schema representations. */
public final class AItcOverlappingSchemaInputsTest {
    private static Path schema(Path aRoot, String aBranch, String aIdentity, String aFieldType) throws Exception {
        Path locFolder = aRoot.resolve("schemas/" + aBranch + "/yamldefs/example");
        Files.createDirectories(locFolder);
        Path locSource = locFolder.resolve("customer_1.yamldef.schema.json");
        ObjectNode locDocument = new ObjectMapper().createObjectNode();
        locDocument.put("$id", aIdentity);
        locDocument.put("type", "object");
        locDocument.putObject("properties").putObject("Name").put("type", aFieldType);
        locDocument.putArray("required").add("Name");
        Files.writeString(locSource, locDocument.toString());
        return locSource;
    }

    private static com.fasterxml.jackson.databind.JsonNode manifest(Path aRoot, Path... aSources) {
        ObjectNode locManifest = new ObjectMapper().createObjectNode();
        locManifest.put("artifact", ".");
        locManifest.putArray("languages").add("java");
        var locInputs = locManifest.putArray("schema_inputs");
        for (Path locSource : aSources) {
            var locEntry = locInputs.addObject();
            locEntry.put("kind", "yamldefs");
            locEntry.put("directory", aRoot.relativize(locSource.getParent().getParent()).toString());
        }
        return locManifest;
    }

    /** Same format can be represented by multiple roots with one canonical identity. */
    @Test
    public void AIcMergeEquivalentSameFormatRoots() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-duplicate-roots-");
        Path locFirst = schema(locRoot, "first", "urn:example:customer:1", "string");
        Path locSecond = schema(locRoot, "second", "urn:example:customer:1", "string");
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        Assert.assertEquals(locGenerator.generateManifest(locRoot, manifest(locRoot, locFirst, locSecond), false).size(), 2);
        Assert.assertTrue(Files.isRegularFile(locRoot.resolve("src/product/java.gen/example/AIigCustomer_1.java")));
    }

    /** Matching output paths must not merge unrelated canonical identities. */
    @Test
    public void AIcRejectUnrelatedCanonicalIdentity() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-id-collision-");
        Path locFirst = schema(locRoot, "first", "urn:example:customer:1", "string");
        Path locSecond = schema(locRoot, "second", "urn:other:customer:1", "string");
        Assert.expectThrows(IllegalArgumentException.class, () -> new AIcSchemaContractBindingsGenerator()
                .generateManifest(locRoot, manifest(locRoot, locFirst, locSecond), false));
    }

    /** Equal identity with incompatible field types is a structural conflict. */
    @Test
    public void AIcRejectDifferentShapeWithEqualIdentity() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-shape-collision-");
        Path locFirst = schema(locRoot, "first", "urn:example:customer:1", "string");
        Path locSecond = schema(locRoot, "second", "urn:example:customer:1", "integer");
        Assert.expectThrows(IllegalArgumentException.class, () -> new AIcSchemaContractBindingsGenerator()
                .generateManifest(locRoot, manifest(locRoot, locFirst, locSecond), false));
    }
}
