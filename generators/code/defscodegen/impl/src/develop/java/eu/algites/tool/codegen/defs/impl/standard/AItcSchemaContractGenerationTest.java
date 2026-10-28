package eu.algites.tool.codegen.defs.impl.standard;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import javax.tools.ToolProvider;
import org.testng.Assert;
import org.testng.annotations.Test;

/** The first code-generation stage only owns annotated read contracts. */
public final class AItcSchemaContractGenerationTest {
    /**
     * A locally named XSD complex type must retain a nominal reference just as
     * an equivalent JSON Schema definition does; an opaque map would destroy
     * typed accessors and covariance with common schema contracts.
     */
    @Test
    public void AIcLocalNamedComplexTypeUsesTypedReference() throws Exception {
        Path locSource = Files.createTempDirectory("algites-typed-local-").resolve("typed-local_1.xsd");
        Files.writeString(locSource, """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                  xmlns:tns="urn:typed" targetNamespace="urn:typed" version="1">
                  <xs:complexType name="ItemType"><xs:sequence>
                    <xs:element name="code" type="xs:string"/>
                  </xs:sequence></xs:complexType>
                  <xs:complexType name="RootType"><xs:sequence>
                    <xs:element name="bindings" type="tns:ItemType" maxOccurs="unbounded"/>
                  </xs:sequence></xs:complexType>
                  <xs:element name="root" type="tns:RootType"/>
                </xs:schema>
                """);
        var locDefinition = new AIcXmlDefsFrontend().load(
                new eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest(locSource,
                        eu.algites.tool.codegen.defs.AInDefinitionSourceKind.XMLDEFS,
                        eu.algites.lib.naming.convention.profile.algites.AIcAlgitesNamingProfiles.javaProfile()));
        var locField = locDefinition.dataType().properties().stream()
                .filter(aProperty -> aProperty.sourceName().equals("bindings"))
                .findFirst().orElseThrow();
        Assert.assertEquals(locField.dataType().kind(),
                eu.algites.tool.codegen.defs.AInDataTypeKind.ARRAY);
        Assert.assertEquals(locField.dataType().elementType().kind(),
                eu.algites.tool.codegen.defs.AInDataTypeKind.REFERENCE);
        Assert.assertEquals(locField.dataType().elementType().reference().identity(), "#@type/ItemType");
        Assert.assertEquals(locField.dataType().elementType().reference().targetDataType().kind(),
                eu.algites.tool.codegen.defs.AInDataTypeKind.OBJECT);
    }

    /** Runs independent native Python generation through the same Gradle verification stage. */
    @Test
    public void AIcNativePythonContractGeneration() throws Exception {
        String locArtifactDirectory = System.getenv("MODUSTRO_ARTIFACT_DIRECTORY");
        if (locArtifactDirectory == null || locArtifactDirectory.isBlank()) {
            throw new IllegalStateException("Missing Modustro artifact directory for Python contract verification");
        }
        Path locArtifact = Path.of(locArtifactDirectory).toAbsolutePath();
        Path locSuite = locArtifact.resolve("src/develop/python/test_contract_only_generation.py");
        if (!Files.isRegularFile(locSuite)) throw new IllegalStateException("Missing native contract test: " + locSuite);
        String locPython = System.getenv("MODUSTRO_PYTHON_TEST_EXECUTABLE");
        if (locPython == null || locPython.isBlank()) {
            throw new IllegalStateException("Missing Modustro Python test executable");
        }
        var locProcess = new ProcessBuilder(locPython, "-m", "pytest", "-q", locSuite.toString())
                .directory(locArtifact.toFile()).redirectErrorStream(true);
        locProcess.environment().remove("PYTHONPATH");
        String locPythonTestPath = System.getenv("MODUSTRO_PYTHON_TEST_PATH");
        if (locPythonTestPath != null && !locPythonTestPath.isBlank()) {
            locProcess.environment().put("PYTHONPATH", locPythonTestPath);
        }
        locProcess.environment().put("PYTHONPYCACHEPREFIX", locArtifact.resolve("run/pycache").toString());
        var locStarted = locProcess.start();
        String locOutput = new String(locStarted.getInputStream().readAllBytes(),
                java.nio.charset.StandardCharsets.UTF_8);
        int locExitCode = locStarted.waitFor();
        if (locExitCode != 0) {
            String locFailure = "Native Python contract generation tests failed (exit code " + locExitCode + ")"
                    + "\nWorking directory: " + locArtifact
                    + "\nPython executable: " + locPython
                    + "\nPython test path: " + locProcess.environment().getOrDefault("PYTHONPATH", "<unset>")
                    + "\nTest suite: " + locSuite
                    + "\n--- Python output / traceback ---\n" + locOutput;
            System.err.println(locFailure);
            Assert.fail(locFailure);
        }
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
        AItcExplicitNamingProfiles.enrich(locManifest);
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        var locGenerated = locGenerator.generateRepository(locRoot, locManifest, false);
        Assert.assertEquals(locGenerated.size(), 8,
                "Both technologies must emit the named XML content type, global element, and namespace contract");
        for (String locLanguage : java.util.List.of("java", "python")) {
            var locEntries = locGenerated.stream()
                    .filter(aEntry -> locLanguage.equals(aEntry.get("language"))).toList();
            Assert.assertEquals(locEntries.size(), 4,
                    "Common, XML type, element, and namespace contracts must all be emitted");
            Assert.assertEquals(locEntries.stream()
                    .filter(aEntry -> "@element/example".equals(aEntry.get("pointer"))).count(), 1L);
            Assert.assertEquals(locEntries.stream()
                    .filter(aEntry -> "@namespace/urn:example:xml:1".equals(aEntry.get("pointer"))).count(), 1L);
            for (var locEntry : locEntries) {
                Path locOutput = locRoot.resolve(locEntry.get("path"));
                Assert.assertTrue(Files.isRegularFile(locOutput), locOutput.toString());
                if ("@element/example".equals(locEntry.get("pointer"))) {
                    Assert.assertTrue(Files.readString(locOutput).contains("AInXmlObjectDefinitionKind.ELEMENT"),
                            "The XML element contract must retain its nominal identity: " + locOutput);
                } else if ("@namespace/urn:example:xml:1".equals(locEntry.get("pointer"))) {
                    String locSource = Files.readString(locOutput);
                    Assert.assertTrue(locSource.contains("AIig_xnXmlDataObjectUrnExampleXml1"),
                            "The XML namespace contract must use its selected naming convention: " + locOutput);
                    Assert.assertTrue(locSource.contains("urn:example:xml:1"),
                            "The namespace annotation must preserve its exact URI: " + locOutput);
                    Assert.assertTrue(locSource.contains("AIiXmlDataObjectNamespace"),
                            "The namespace marker must extend the XML namespace base interface: " + locOutput);
                }
            }
        }
        Path locJava = locRoot.resolve("intf/src/product/java.gen/example/contracts/AIigExample_1.java");
        Path locPython = locRoot.resolve("intf/src/product/python.gen/example/contracts/aiig_example_1.py");
        Assert.assertTrue(Files.readString(locJava).contains("AIaDataObjectField"));
        Assert.assertTrue(Files.readString(locJava).contains(" getName()"));
        Assert.assertTrue(Files.readString(locJava).contains(" getCount()"));
        Assert.assertTrue(Files.readString(locPython).contains("@AIaDataObjectField"));
        Assert.assertTrue(Files.readString(locPython).contains("def getName"));
        Assert.assertFalse(Files.exists(locRoot.resolve("impl")));
        locGenerator.generateRepository(locRoot, locManifest, true);
    }

    /** Root XSD attributes are ordinary typed canonical fields, never silently dropped. */
    @Test
    public void AIcXsdRootAttributeProjection() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-xsd-attributes-");
        Path locSource = locRoot.resolve("example_1.xsd");
        Files.writeString(locSource, """
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
              <xs:complexType name="ExampleType">
                <xs:sequence><xs:element name="Value" type="xs:string"/></xs:sequence>
                <xs:attribute name="Code" type="xs:int" use="required">
                  <xs:annotation><xs:documentation>Numeric attribute code.</xs:documentation></xs:annotation>
                </xs:attribute>
                <xs:attribute name="Optional" type="xs:string"/>
              </xs:complexType>
            </xs:schema>
            """);
        var locDefinition = new AIcXmlDefsFrontend().load(
                new eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest(
                        locSource, eu.algites.tool.codegen.defs.AInDefinitionSourceKind.XMLDEFS,
                        eu.algites.lib.naming.convention.profile.algites.AIcAlgitesNamingProfiles.javaProfile()));
        Assert.assertEquals(locDefinition.dataType().properties().size(), 3);
        Assert.assertEquals(locDefinition.dataType().properties().get(1).sourceName(), "Code");
        Assert.assertEquals(locDefinition.dataType().properties().get(1).dataType().kind(),
                eu.algites.tool.codegen.defs.AInDataTypeKind.INTEGER);
        Assert.assertTrue(locDefinition.dataType().properties().get(1).presence() == eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED);
        Assert.assertEquals(locDefinition.dataType().properties().get(1).description(), "Numeric attribute code.");
        Assert.assertEquals(locDefinition.dataType().properties().get(2).sourceName(), "Optional");
        Assert.assertFalse(locDefinition.dataType().properties().get(2).presence() == eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED);
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
        AItcExplicitNamingProfiles.enrich(locManifest);
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        Assert.assertTrue(locGenerator.generateRepository(locRoot, locManifest, false).size() >= 4);
        Path locJavaRoot = locRoot.resolve("intf/src/product/java.gen/example/contracts/");
        String locChild = Files.readString(locJavaRoot.resolve("AIigChild_1.java"));
        Assert.assertTrue(locChild.contains("extends example.contracts.AIigParent_1"));
        Assert.assertFalse(locChild.contains(" getName()"));
        Assert.assertTrue(locChild.contains(" getCount()"));
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

    /** Inherited Python contracts replace the actual role-specific base rather than assuming a format base. */
    @Test
    public void AIcPythonInheritanceRespectsContractRole() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-inheritance-role-");
        Path locSchema = locRoot.resolve("child_1.jsondef.schema.json");
        Files.writeString(locSchema, """
            {"$id":"urn:child:1","type":"object","properties":{"Count":{"type":"integer"}}}
            """);
        var locProfile = AItcConfiguredNamingProfiles.pythonProfile();
        var locDefinition = new AIcJsonDefsFrontend().load(AItcConfiguredNamingProfiles.load(
                locSchema, eu.algites.tool.codegen.defs.AInDefinitionSourceKind.JSONDEFS, locProfile));
        var locGenerator = new AIcSchemaContractInterfaceGenerator();
        for (String locRole : java.util.List.of("common", "jsondefs")) {
            var locRequest = new eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest(
                    locDefinition, eu.algites.tool.codegen.defs.AInCodeGenerationTarget.PYTHON,
                    "example.contracts", locProfile, null, "", locRole);
            var locDirect = locGenerator.generate(locRequest);
            String locBaseType = locRole.equals("common") ? "AIiDataObject" : "AIiJsonDataObject";
            Assert.assertTrue(locDirect.source().contains("class " + locDirect.typeName()
                    + "(" + locBaseType + ", ABC):"), locRole);
            var locInherited = locGenerator.generate(locRequest, "AIigParent_1",
                    "example.contracts.aiig_parent_1");
            Assert.assertTrue(locInherited.source().contains("class " + locDirect.typeName()
                    + "(AIigParent_1):"), locRole);
            Assert.assertTrue(locInherited.source().contains(
                    "from example.contracts.aiig_parent_1 import AIigParent_1"), locRole);
            Assert.assertFalse(locInherited.source().contains("class " + locDirect.typeName()
                    + "(" + locBaseType + ", ABC):"), locRole);
        }
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
        AItcExplicitNamingProfiles.enrich(locManifest);
        var locGenerator = new AIcSchemaContractBindingsGenerator();
        Assert.assertEquals(locGenerator.generateRepository(locRoot, locManifest, false).size(), 4);
        Path locJava = locRoot.resolve("intf/src/product/java.gen/example/contracts/AIigExample_1.java");
        Path locPython = locRoot.resolve("intf/src/product/python.gen/example/contracts/aiig_example_1.py");
        String locJavaText = Files.readString(locJava);
        String locPythonText = Files.readString(locPython);
        Assert.assertTrue(locJavaText.contains("@eu.algites.lib.data.dataobject.AIaDataObject("));
        Assert.assertTrue(locJavaText.contains("@eu.algites.lib.data.dataobject.AIaDataObjectField("));
        Assert.assertTrue(locPythonText.contains("@AIaDataObjectField("));
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
