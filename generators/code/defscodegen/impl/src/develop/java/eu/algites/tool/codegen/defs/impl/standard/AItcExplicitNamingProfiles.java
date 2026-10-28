package eu.algites.tool.codegen.defs.impl.standard;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;

/**
 * Configures legacy integration fixtures with explicit semantic naming roles.
 *
 * <p>Production Codegen must never choose these profiles automatically. Tests
 * opt in through their own manifest before invoking a native generator.
 */
final class AItcExplicitNamingProfiles {
    private AItcExplicitNamingProfiles() { }

    /**
     * Add the Algites naming catalogs and selected source/output roles to a
     * fixture manifest, leaving its existing schema inputs and bindings intact.
     *
     * @param manifest path of the test-owned manifest JSON file
     * @throws IOException when the manifest cannot be parsed or written
     */
    static void enrich(Path manifest) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        ObjectNode root = (ObjectNode) mapper.readTree(manifest.toFile());
        ObjectNode outputs = root.putObject("technology_outputs");
        outputs.put("java", "intf/src/product/java.gen");
        outputs.put("python", "intf/src/product/python.gen");
        ObjectNode source = root.putObject("schema_input_naming_conventions");
        source.put("jsondefs", "algites-jsondef-schema-versioned_1");
        source.put("yamldefs", "algites-yamldef-schema-versioned_1");
        source.put("xmldefs", "algites-xmldef-schema-versioned_1");
        ObjectNode roles = root.putObject("technology_output_naming_conventions");
        for (String language : new String[] {"java", "python"}) {
            ObjectNode role = roles.putObject(language);
            role.put("common", "algites-" + language + "-gen-intf-versioned_1");
            role.put("jsondefs", "algites-" + language + "-gen-json-intf-versioned_1");
            role.put("yamldefs", "algites-" + language + "-gen-yaml-intf-versioned_1");
            role.put("xmldefs_type", "algites-" + language + "-gen-xml-type-intf-versioned_1");
            role.put("xmldefs_element", "algites-" + language + "-gen-xml-element-intf-versioned_1");
            role.put("xmldefs_namespace", "algites-" + language + "-gen-xml-namespace-intf_1");
        }
        ObjectNode enums = root.putObject("technology_enum_output_naming_conventions");
        enums.put("java", "algites-java-gen-enum-versioned_1");
        enums.put("python", "algites-python-gen-enum-versioned_1");
        var catalogs = root.putArray("naming_convention_files");
        for (String name : new String[] {"algites-java-name-conventions.yml",
                "algites-python-name-conventions.yml", "algites-jsondef-name-conventions.yml",
                "algites-yamldef-name-conventions.yml", "algites-xmldef-name-conventions.yml"}) {
            catalogs.add("resource:" + name);
        }
        mapper.writerWithDefaultPrettyPrinter().writeValue(manifest.toFile(), root);
    }
}
