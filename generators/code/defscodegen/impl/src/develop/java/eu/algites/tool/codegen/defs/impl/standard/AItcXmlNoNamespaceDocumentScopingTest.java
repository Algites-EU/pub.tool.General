package eu.algites.tool.codegen.defs.impl.standard;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Regression coverage for independently valid XSD documents with no target
 * namespace and the same global type/element names, as encountered in Builder
 * capability configuration definitions.
 */
public final class AItcXmlNoNamespaceDocumentScopingTest {
    /**
     * Build one XSD resource with a globally declared content type and element.
     * The two documents deliberately have incompatible property sets: they
     * cannot share either one generated type or the same Java output file.
     *
     * @param root temporary repository root
     * @param stem versioned XSD filename stem without the version
     * @param property property unique to this schema
     * @throws Exception when fixture creation fails
     */
    private static void schema(Path root, String stem, String property) throws Exception {
        Path folder = root.resolve("src/product/xmldefs/example/modustro");
        Files.createDirectories(folder);
        Files.writeString(folder.resolve(stem + "_1.xsd"), """
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
              <xs:complexType name="DocumentContentType"><xs:sequence>
                <xs:element name="Enabled" type="xs:boolean"/>
                <xs:element name="%s" type="xs:string"/>
              </xs:sequence></xs:complexType>
              <xs:element name="CapabilityConfiguration" type="DocumentContentType"/>
            </xs:schema>
            """.formatted(property));
    }

    /**
     * Generate a configured two-language manifest using the same XML naming
     * conventions as a real 1.1 source-generation invocation.
     *
     * @return fully configured manifest for the temporary repository
     */
    private static com.fasterxml.jackson.databind.JsonNode manifest() {
        var mapper = new ObjectMapper();
        var manifest = mapper.createObjectNode();
        manifest.put("artifact", ".");
        manifest.putArray("languages").add("java").add("python");
        manifest.putArray("schema_inputs").addObject().put("kind", "xmldefs")
                .put("directory", "src/product/xmldefs");
        manifest.putObject("schema_input_naming_conventions")
                .put("xmldefs", "algites-xmldef-schema-versioned_1");
        var outputs = manifest.putObject("technology_outputs");
        var profiles = manifest.putObject("technology_output_naming_conventions");
        for (String technology : new String[] {"java", "python"}) {
            outputs.put(technology, "src/product/" + technology + ".gen");
            var role = profiles.putObject(technology);
            role.put("common", "algites-" + technology + "-gen-intf-versioned_1");
            role.put("xmldefs_type", "algites-" + technology + "-gen-xml-type-intf-versioned_1");
            role.put("xmldefs_element", "algites-" + technology + "-gen-xml-element-intf-versioned_1");
            role.put("xmldefs_namespace", "algites-" + technology + "-gen-xml-namespace-intf_1");
        }
        var naming = manifest.putArray("naming_convention_files");
        for (String name : new String[] {"algites-java-name-conventions.yml",
                "algites-python-name-conventions.yml", "algites-xmldef-name-conventions.yml"})
            naming.add("resource:" + name);
        return manifest;
    }

    /**
     * A repeated empty-namespace QName is document-local. It must not merge
     * content types, resolve elements to an unrelated content type or create
     * Java/Python source collisions. The check phase must reproduce the same
     * stable paths without changing the already generated files.
     *
     * @throws Exception when generation or the generated-file checks fail
     */
    @Test
    public void AIcIndependentAnonymousXmlTypesAndElements() throws Exception {
        Path root = Files.createTempDirectory("defs-empty-namespace-");
        Map<String, String> fields = new LinkedHashMap<>();
        fields.put("docs-site-content", "Javadoc");
        fields.put("publication-of-docs-site", "PublicationDestinations");
        fields.put("publication-of-global-schemas", "SourceKinds");
        for (var item : fields.entrySet()) schema(root, item.getKey(), item.getValue());
        var generator = new AIcSchemaContractBindingsGenerator();
        var options = manifest();
        var generated = generator.generateManifest(root, options, false);
        Assert.assertEquals(generated.stream().filter(item ->
                item.get("pointer").startsWith("@element/")).count(), 6L);
        for (var item : fields.entrySet()) {
            String packagePath = "example/modustro/xmlschema_" + item.getKey().replace('-', '_') + "_1";
            for (String technology : new String[] {"java", "python"}) {
                Path output = root.resolve("src/product/" + technology + ".gen/" + packagePath);
                Assert.assertTrue(Files.isDirectory(output), "Missing " + output);
                Path element = output.resolve(technology.equals("java")
                        ? "AIig_xeCapabilityConfiguration_1.java"
                        : "aiig__xe_capability_configuration_1.py");
                Assert.assertTrue(Files.isRegularFile(element), "Missing " + element);
                if (technology.equals("java")) {
                    Assert.assertTrue(Files.readString(element).contains("AIig_xnXmlDataObjectLocal"),
                            "XML element must implement its own namespace marker");
                    Path type = output.resolve("AIig_x" + java.util.Arrays.stream(item.getKey().split("-"))
                            .map(part -> part.substring(0, 1).toUpperCase(java.util.Locale.ROOT)
                                    + part.substring(1))
                            .collect(java.util.stream.Collectors.joining()) + "_1.java");
                    Assert.assertTrue(Files.isRegularFile(type), "Missing specialized XML type " + type);
                    Assert.assertTrue(Files.readString(type).contains("AIig_xnXmlDataObjectLocal"),
                            "XML type must implement its own namespace marker");
                }
                try (var paths = Files.walk(output)) {
                    String sources = paths.filter(Files::isRegularFile).map(path -> {
                        try { return Files.readString(path); }
                        catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
                    }).reduce("", (left, right) -> left + "\n" + right);
                    Assert.assertTrue(sources.contains(item.getValue()), "Missing own field");
                    for (String other : fields.values())
                        if (!other.equals(item.getValue()))
                            Assert.assertFalse(sources.contains(other), "Foreign field in " + output);
                }
            }
        }
        Assert.assertEquals(generator.generateManifest(root, options, true), generated);
    }

    /**
     * The package of an XML schema without QName collisions remains unchanged.
     *
     * @throws Exception when the isolated schema cannot be processed
     */
    @Test
    public void AIcUniqueAnonymousXmlTypeRetainsPackage() throws Exception {
        Path root = Files.createTempDirectory("defs-unique-empty-namespace-");
        schema(root, "docs-site-content", "Javadoc");
        new AIcSchemaContractBindingsGenerator().generateManifest(root, manifest(), false);
        Assert.assertTrue(Files.isRegularFile(root.resolve(
                "src/product/java.gen/example/modustro/AIig_xeCapabilityConfiguration_1.java")));
    }
}
