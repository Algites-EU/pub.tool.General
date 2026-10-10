package eu.algites.tool.codegen.defs;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import javax.tools.ToolProvider;
import org.testng.Assert;
import org.testng.annotations.Test;

/** The first code-generation stage only owns annotated read contracts. */
public final class AItcSchemaContractGenerationTest {
    /** Runs independent native Python generation through the same Gradle verification stage. */
    @Test
    public void AIcNativePythonContractGeneration() throws Exception {
        Path locRoot = Path.of("").toAbsolutePath();
        String locRelative = "generators/code/defscodegen/impl/src/develop/python/test_contract_only_generation.py";
        while (locRoot != null && !Files.isRegularFile(locRoot.resolve(locRelative))) {
            locRoot = locRoot.getParent();
        }
        if (locRoot == null) throw new IllegalStateException("Missing native contract test");
        String locPython = System.getenv().getOrDefault("ALGITES_PYTHON_EXECUTABLE", "python3");
        var locProcess = new ProcessBuilder(locPython, "-m", "pytest", "-q",
                locRoot.resolve(locRelative).toString()).directory(locRoot.toFile()).redirectErrorStream(true);
        var locPythonPath = new java.util.ArrayList<String>();
        for (String locArtifact : java.util.List.of("intf", "impl")) {
            locPythonPath.add(locRoot.resolve("generators/code/defscodegen/" + locArtifact + "/src/product/python").toString());
        }
        String locDependencies = System.getenv("MODUSTRO_GENERATOR_PARITY_PYTHON_DEPENDENCIES");
        if (locDependencies != null && !locDependencies.isBlank()) locPythonPath.add(locDependencies);
        String locPrevious = System.getenv("PYTHONPATH");
        if (locPrevious != null && !locPrevious.isBlank()) locPythonPath.add(locPrevious);
        locProcess.environment().put("PYTHONPATH", String.join(java.io.File.pathSeparator, locPythonPath));
        locProcess.environment().put("PYTHONPYCACHEPREFIX", locRoot.resolve("build/run/defs-contracts/pycache").toString());
        var locStarted = locProcess.start();
        String locOutput = new String(locStarted.getInputStream().readAllBytes(),
                java.nio.charset.StandardCharsets.UTF_8);
        Assert.assertEquals(locStarted.waitFor(), 0, locOutput);
    }

    /** Manifest enumeration includes XSD and preserves Java/Python equivalence of field contracts. */
    @Test
    public void AIcXsdManifestContractParity() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-xsd-");
        Path locDefinitions = locRoot.resolve("intf/src/product/xmldefs/example/contracts");
        Files.createDirectories(locDefinitions);
        Files.writeString(locDefinitions.resolve("example_1.xsd"), """
            <?xml version="1.0" encoding="UTF-8"?>
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:example:xml:1" version="1">
                <xs:element name="example" type="ExampleType" />
                <xs:complexType name="ExampleType"><xs:sequence>
                    <xs:element name="Name" type="xs:string" />
                    <xs:element name="Count" type="xs:int" minOccurs="0" />
                </xs:sequence></xs:complexType>
            </xs:schema>
            """);
        Path locManifest = locRoot.resolve("bindings.json");
        Files.writeString(locManifest, """
            {"artifact":"intf","languages":["java","python"],"bindings":[]}
            """);
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        Assert.assertEquals(locGenerator.generateRepository(locRoot, locManifest, false).size(), 2);
        Path locJava = locRoot.resolve("intf/src/product/java.gen/example/contracts/AIigExample_1.java");
        Path locPython = locRoot.resolve("intf/src/product/python.gen/example/contracts/aiig_example_1.py");
        Assert.assertTrue(Files.readString(locJava).contains("AIaDataObjectField"));
        Assert.assertTrue(Files.readString(locJava).contains("name()"));
        Assert.assertTrue(Files.readString(locPython).contains("AIcdDataObjectField"));
        Assert.assertTrue(Files.readString(locPython).contains("def getName"));
        Assert.assertFalse(Files.exists(locRoot.resolve("impl")));
        locGenerator.generateRepository(locRoot, locManifest, true);
    }

    /** Local allOf inheritance becomes real Java/Python interface inheritance. */
    @Test
    public void AIcGeneratesSchemaInheritance() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-inheritance-");
        Path locDefinitions = locRoot.resolve("intf/src/product/jsondefs/example/contracts");
        Files.createDirectories(locDefinitions);
        Files.writeString(locDefinitions.resolve("parent_1.jsondef.schema.json"), """
            {"$id":"urn:parent:1","type":"object","properties":{"Name":{"type":"string"}},"required":["Name"]}
            """);
        Files.writeString(locDefinitions.resolve("child_1.jsondef.schema.json"), """
            {"$id":"urn:child:1","allOf":[{"$ref":"parent_1.jsondef.schema.json"},
              {"type":"object","properties":{"Count":{"type":"integer"}}}]}
            """);
        Path locManifest = locRoot.resolve("bindings.json");
        Files.writeString(locManifest, """
            {"artifact":"intf","languages":["java","python"],"bindings":[]}
            """);
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        Assert.assertTrue(locGenerator.generateRepository(locRoot, locManifest, false).size() >= 4);
        Path locJavaRoot = locRoot.resolve("intf/src/product/java.gen/example/contracts/");
        String locChild = Files.readString(locJavaRoot.resolve("AIigChild_1.java"));
        Assert.assertTrue(locChild.contains("extends example.contracts.AIigParent_1"));
        Assert.assertFalse(locChild.contains(" name()"));
        Assert.assertTrue(locChild.contains(" count()"));
        String locPyChild = Files.readString(locRoot.resolve("intf/src/product/python.gen/example/contracts/aiig_child_1.py"));
        Assert.assertTrue(locPyChild.contains("class AIigChild_1(AIigParent_1):"));
        var locArgs = new ArrayList<String>(java.util.List.of(
                "-cp", System.getProperty("java.class.path"), "-d",
                Files.createDirectory(locRoot.resolve("classes")).toString()));
        locArgs.add(locJavaRoot.resolve("AIigParent_1.java").toString());
        locArgs.add(locJavaRoot.resolve("AIigChild_1.java").toString());
        Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                locArgs.toArray(String[]::new)), 0);
        locGenerator.generateRepository(locRoot, locManifest, true);
    }

    /** Both Java and Python contracts preserve canonical field annotations without producing DTOs. */
    @Test
    public void AIcContractsForBothTechnologies() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-contracts-");
        Path locDefinitions = locRoot.resolve("intf/src/product/jsondefs/example/contracts");
        Files.createDirectories(locDefinitions);
        Files.writeString(locDefinitions.resolve("example_1.jsondef.schema.json"), """
            {"$id":"urn:test:example:1","type":"object","properties":{
              "Name":{"type":"string"},"Count":{"type":"integer"}},"required":["Name"]}
            """);
        Path locManifest = locRoot.resolve("bindings.json");
        Files.writeString(locManifest, """
            {"artifact":"intf","languages":["java","python"],"bindings":[]}
            """);
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        Assert.assertEquals(locGenerator.generateRepository(locRoot, locManifest, false).size(), 2);
        Path locJava = locRoot.resolve("intf/src/product/java.gen/example/contracts/AIigExample_1.java");
        Path locPython = locRoot.resolve("intf/src/product/python.gen/example/contracts/aiig_example_1.py");
        String locJavaText = Files.readString(locJava);
        String locPythonText = Files.readString(locPython);
        Assert.assertTrue(locJavaText.contains("@eu.algites.lib.data.dataobject.AIaDataObject("));
        Assert.assertTrue(locJavaText.contains("@eu.algites.lib.data.dataobject.AIaDataObjectField("));
        Assert.assertTrue(locPythonText.contains("AIcdDataObjectField("));
        Assert.assertTrue(locPythonText.contains("@abstractmethod\n    def getName"));
        Assert.assertFalse(locPythonText.contains("def to_mapping("));
        Assert.assertFalse(locPythonText.contains("def to_mapping("));
        Assert.assertFalse(Files.exists(locRoot.resolve("impl")));
        var locArgs = new ArrayList<String>();
        locArgs.add("-cp"); locArgs.add(System.getProperty("java.class.path"));
        locArgs.add("-d");locArgs.add(Files.createDirectory(locRoot.resolve("classes")).toString());
        locArgs.add(locJava.toString());
        Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                locArgs.toArray(String[]::new)), 0);
        locGenerator.generateRepository(locRoot, locManifest, true);
    }
}
