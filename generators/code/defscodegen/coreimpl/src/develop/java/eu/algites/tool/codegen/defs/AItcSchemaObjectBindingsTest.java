package eu.algites.tool.codegen.defs;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import javax.tools.ToolProvider;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Verifies generation from a checkout without pre-existing .gen directories. */
public final class AItcSchemaObjectBindingsTest {
    private record AIcdFixture(Path root, Path schema, Path manifest) { }

    private AIcdFixture fixture() throws Exception {
        Path root = Files.createTempDirectory("schema-bindings-");
        Path schema = root.resolve("coreintf/src/product/jsondefs/example/contracts/example_1.jsondef.schema.json");
        Files.createDirectories(schema.getParent());
        Files.writeString(schema, """
            {"$id":"https://example.test/example_1", "type":"object", "properties":{
              "Name":{"type":"string","description":"Display name."},
              "Items":{"type":"array","items":{"type":"object","properties":{"Id":{"type":"integer"}},"required":["Id"]}},
              "State":{"type":"string","enum":["open","closed"]}},"required":["Name"]}
            """);
        Path manifest = root.resolve("bindings.json");
        Files.writeString(manifest, """
            {"artifact":"coreintf","implementation_artifact":"coreimpl","languages":["python","java"],"bindings":[]}
            """);
        return new AIcdFixture(root, schema, manifest);
    }

    /** Native interfaces/ABCs and their implementations compile and support actual serialization. */
    @Test
    public void AIcContractsAndImplementations() throws Exception {
        var fixture = fixture();
        var result = new AIcSchemaObjectBindingsGenerator().generateRepository(fixture.root, fixture.manifest, false);
        Assert.assertEquals(result.size(), 6); // root, item object, enum, each for Java/Python
        for (var output : result) Assert.assertTrue(output.get("path").contains("/example/contracts/"));
        Path intf = fixture.root.resolve("coreintf/src/product/python.gen");
        Path impl = fixture.root.resolve("coreimpl/src/product/python.gen");
        var process = new ProcessBuilder("python3", "-c", """
            import inspect, dataclasses
            from example.contracts.aiig_example_1 import AIigExample_1
            from example.contracts.aicgd_example_1 import AIcgdExample_1
            from example.contracts.aiig_example_items_items_1 import AIigExampleItemsItems_1
            from example.contracts.aing_example_state_1 import AIngExampleState_1
            assert inspect.isabstract(AIigExample_1)
            assert not inspect.isabstract(AIcgdExample_1)
            assert 'items' in AIigExample_1.__annotations__
            assert AIigExampleItemsItems_1.SCHEMA_FIELD_NAME__ID == 'Id'
            value = AIcgdExample_1.from_mapping({'Name':'Example','Items':[{'Id':7}]})
            assert isinstance(value, AIigExample_1)
            assert value.to_mapping() == {'Name':'Example','Items':[{'Id':7}]}
            assert not hasattr(value, '__dict__')
            assert all(not f.name.startswith('SCHEMA_FIELD_NAME__') for f in dataclasses.fields(value))
            assert AIngExampleState_1.OPEN.value == 'open'
            try: AIigExample_1()
            except TypeError: pass
            else: raise AssertionError('Abstract contract is constructible')
            """).inheritIO();
        process.environment().put("PYTHONPATH", intf + java.io.File.pathSeparator + impl);
        process.environment().put("PYTHONPYCACHEPREFIX", fixture.root.resolve("build/pycache").toString());
        Assert.assertEquals(process.start().waitFor(), 0);
        var compilerArguments = new ArrayList<String>();
        compilerArguments.add("-d"); compilerArguments.add(fixture.root.resolve("build/classes").toString());
        for (String artifact : java.util.List.of("coreintf", "coreimpl")) {
            try (var files = Files.walk(fixture.root.resolve(artifact + "/src/product/java.gen"))) {
                compilerArguments.addAll(files.filter(p -> p.toString().endsWith(".java")).map(Path::toString).toList());
            }
        }
        Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null, compilerArguments.toArray(String[]::new)), 0);
    }

    /** Stale pruning is limited to recorded ownership, while check mode never recreates missing files. */
    @Test
    public void AIcOwnedOutputsAndMissingGeneration() throws Exception {
        var fixture = fixture(); var generator = new AIcSchemaObjectBindingsGenerator();
        generator.generateRepository(fixture.root, fixture.manifest, false);
        Path root = fixture.root.resolve("coreintf/src/product/python.gen/example/contracts");
        Path other = root.resolve("other_generator.py"); Files.writeString(other, "# independently owned\n");
        Path contract = root.resolve("aiig_example_1.py"); Files.delete(contract);
        Assert.expectThrows(IllegalStateException.class, () -> generator.generateRepository(fixture.root, fixture.manifest, true));
        Assert.assertFalse(Files.exists(contract));
        Files.writeString(fixture.schema, "{\"type\":\"object\",\"properties\":{\"Name\":{\"type\":\"string\"}}}");
        generator.generateRepository(fixture.root, fixture.manifest, false);
        Assert.assertTrue(Files.exists(contract)); Assert.assertTrue(Files.exists(other));
        Assert.assertFalse(Files.exists(root.resolve("aiig_example_items_items_1.py")));
        generator.generateRepository(fixture.root, fixture.manifest, true);
    }

    /** Compatible representations share one type; incompatible ones fail before changing prior outputs. */
    @Test
    public void AIcRepresentationCompatibility() throws Exception {
        var fixture = fixture(); var generator = new AIcSchemaObjectBindingsGenerator();
        Path yaml = fixture.root.resolve("coreintf/src/product/yamldefs/example/contracts/example_1.yamldef.schema.json");
        Files.createDirectories(yaml.getParent()); Files.copy(fixture.schema, yaml);
        generator.generateRepository(fixture.root, fixture.manifest, false);
        Path contract = fixture.root.resolve("coreintf/src/product/python.gen/example/contracts/aiig_example_1.py");
        String before = Files.readString(contract);
        Files.writeString(yaml, "{\"type\":\"object\",\"properties\":{\"Name\":{\"type\":\"integer\"}}}");
        Assert.expectThrows(IllegalArgumentException.class, () -> generator.generateRepository(fixture.root, fixture.manifest, false));
        Assert.assertEquals(Files.readString(contract), before);
        Files.writeString(fixture.manifest, "{\"artifact\":\"../../escape\",\"implementation_artifact\":\"coreimpl\",\"languages\":[\"python\"]}");
        Assert.expectThrows(IllegalArgumentException.class, () -> generator.generateRepository(fixture.root, fixture.manifest, false));
    }

    /** A property object and a named definition with the same label remain separate schema objects. */
    @Test
    public void AIcDistinctObjectsHaveDistinctTypes() throws Exception {
        var fixture = fixture();
        Files.writeString(fixture.schema, """
            {"type":"object","properties":{"Thing":{"type":"object","properties":{"A":{"type":"string"}}}},
             "$defs":{"Thing":{"type":"object","properties":{"B":{"type":"integer"}}}}}
            """);
        var result = new AIcSchemaObjectBindingsGenerator().generateRepository(fixture.root, fixture.manifest, false);
        Assert.assertEquals(result.size(), 6);
        Path root = fixture.root.resolve("coreintf/src/product/python.gen/example/contracts");
        Assert.assertTrue(Files.readString(root.resolve("aiig_example_thing_1.py")).contains("SCHEMA_FIELD_NAME__A"));
        Assert.assertTrue(Files.readString(root.resolve("aiig_example_definition_thing_1.py")).contains("SCHEMA_FIELD_NAME__B"));
    }
}
