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
        locDocument.put("$id", "https://schemas.example.test/" + aBranch + "/customer_1.yamldef.schema.json");
        locDocument.put("$x-algites-schema-id", aIdentity);
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
        var locOutputs = locManifest.putObject("technology_outputs");
        locOutputs.put("java", "src/product/java.gen");
        locManifest.putObject("schema_input_naming_conventions")
                .put("yamldefs", "algites-yamldef-schema-versioned_1");
        locManifest.putObject("technology_output_naming_conventions")
                .putObject("java").put("common", "algites-java-gen-intf-versioned_1");
        locManifest.putObject("technology_enum_output_naming_conventions")
                .put("java", "algites-java-gen-enum-versioned_1");
        var locCatalogs = locManifest.putArray("naming_convention_files");
        for (String locCatalog : new String[] {"algites-java-name-conventions.yml",
                "algites-yamldef-name-conventions.yml"})
            locCatalogs.add("resource:" + locCatalog);
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

    /**
     * Distinct JSON Schema publication URLs do not imply distinct semantic schema IDs.
     * When the configured logical-ID source property is absent, the contract identity
     * comes from the source name and version in both input files.
     */
    @Test
    public void AIcDistinctPublicationUrlsRemainOneImplicitIdentity() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-published-url-aliases-");
        Path locFirst = schema(locRoot, "first", "urn:example:customer:1", "string");
        Path locSecond = schema(locRoot, "second", "urn:other:customer:1", "string");
        ObjectMapper locMapper = new ObjectMapper();
        for (Path locSource : new Path[] {locFirst, locSecond}) {
            ObjectNode locDocument = (ObjectNode) locMapper.readTree(locSource.toFile());
            locDocument.remove("$x-algites-schema-id");
            Files.writeString(locSource, locDocument.toString());
        }
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        Assert.assertEquals(locGenerator.generateManifest(locRoot, manifest(locRoot, locFirst, locSecond), false).size(), 2);
        Assert.assertTrue(Files.isRegularFile(locRoot.resolve("src/product/java.gen/example/AIigCustomer_1.java")));
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
