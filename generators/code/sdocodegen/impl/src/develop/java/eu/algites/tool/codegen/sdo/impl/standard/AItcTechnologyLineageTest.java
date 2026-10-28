package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.lib.data.dataobject.AIaDataObject;
import eu.algites.lib.data.dataobject.AIaDataObjectField;
import eu.algites.lib.data.dataobject.jsondefs.AIiJsonDataObject;
import eu.algites.lib.data.dataobject.yamldefs.AIiYamlDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField;
import eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind;
import org.testng.annotations.Test;

/**
 * Verifies source-technology-specific SDO derivation independently of scheme naming catalogs.
 * These test types deliberately have no technology-specific behavior: the contract lineage
 * itself is the guarantee for future schema-family extensions.
 */
public final class AItcTechnologyLineageTest {
    /** Simple JSON Schema contract with a stable field identifier. */
    @AIaDataObject(schemaId = "test:json", schemaVersion = 1)
    public interface AIigJson_1 extends AIiJsonDataObject {
        /** Return its optional field without altering the schema identity. */
        @AIaDataObjectField(fieldName = "key")
        String getKey();
    }

    /** Simple YAML definition contract with a stable field identifier. */
    @AIaDataObject(schemaId = "test:yaml", schemaVersion = 1)
    public interface AIigYaml_1 extends AIiYamlDataObject {
        /** Return its optional field without altering the schema identity. */
        @AIaDataObjectField(fieldName = "key")
        String getKey();
    }

    /** XML element contract whose QName is independent of its schema ID. */
    @AIaDataObject(schemaId = "test:xml", schemaVersion = 1)
    @AIaXmlDataObject(definitionKind = AInXmlObjectDefinitionKind.ELEMENT,
            namespace = "urn:example", namespaceLocalName = "entry")
    public interface AIigXml_1 extends AIiXmlDataObject {
        /** Return an XML child element with the declared wire QName. */
        @AIaDataObjectField(fieldName = "key")
        @AIaXmlDataObjectField(namespace = "urn:example", namespaceLocalName = "key")
        String getKey();
    }

    /** JSON specialization must retain the JSON runtime base, not its generated parent class. */
    @AIaDataObject(schemaId = "test:json-child", schemaVersion = 1)
    public interface AIigJsonChild_1 extends AIigJson_1 {
        /** Extra property on the specialized JSON contract. */
        @AIaDataObjectField(fieldName = "extra")
        String getExtra();
    }

    /** YAML specialization must retain the YAML runtime base, not its generated parent class. */
    @AIaDataObject(schemaId = "test:yaml-child", schemaVersion = 1)
    public interface AIigYamlChild_1 extends AIigYaml_1 {
        /** Extra property on the specialized YAML contract. */
        @AIaDataObjectField(fieldName = "extra")
        String getExtra();
    }

    /** XML element specialization must retain the XML runtime base. */
    @AIaDataObject(schemaId = "test:xml-child", schemaVersion = 1)
    @AIaXmlDataObject(definitionKind = AInXmlObjectDefinitionKind.ELEMENT,
            namespace = "urn:example", namespaceLocalName = "child")
    public interface AIigXmlChild_1 extends AIigXml_1 {
        /** Extra XML element on the specialized contract. */
        @AIaDataObjectField(fieldName = "extra")
        @AIaXmlDataObjectField(namespace = "urn:example", namespaceLocalName = "extra")
        String getExtra();
    }

    /** Check each mutable marker, concrete implementation base, and XML QName metadata. */
    @Test
    public void AIcGeneratesTechnologySpecificTypes() {
        AItcConfiguredSdoCodegenService locService = new AItcConfiguredSdoCodegenService();
        verify(locService, AIigJson_1.class, "Json");
        verify(locService, AIigYaml_1.class, "Yaml");
        verify(locService, AIigXml_1.class, "Xml");
        verifyDirectConcreteRoot(locService, AIigJsonChild_1.class, "Json");
        verifyDirectConcreteRoot(locService, AIigYamlChild_1.class, "Yaml");
        verifyDirectConcreteRoot(locService, AIigXmlChild_1.class, "Xml");
        var locXml = locService.generate(AIigXml_1.class, "d").mutableInterface().source();
        require(locXml.contains("AIaXmlDataObject("), "XML type annotation was lost");
        require(locXml.contains("namespaceLocalName = \"entry\""), "XML element QName was lost");
        require(locXml.contains("AIaXmlDataObjectField("), "XML field metadata was lost");
        require(locXml.contains("namespaceLocalName = \"key\""), "XML field QName was lost");
        require(!locXml.contains("OpenChoice"), "Removed OpenChoice API was emitted");
    }

    /**
     * Compile all three technology-specific inheritance hierarchies and verify
     * the concrete superclass by reflection rather than by string matching.
     *
     * @throws Exception if the generated Java source does not compile or load
     */
    @Test
    public void AIcCompilesAllTechnologySpecializationsWithDirectRuntimeBases() throws Exception {
        var locService = new AItcConfiguredSdoCodegenService();
        var locRoot = java.nio.file.Files.createTempDirectory("sdo-technology-concrete-");
        var locClasses = java.nio.file.Files.createDirectories(locRoot.resolve("classes"));
        var locFiles = new java.util.ArrayList<String>();
        var locChildren = new java.util.ArrayList<eu.algites.tool.codegen.sdo.AIcdSdoGenerationResult>();
        for (Class<?> locRead : java.util.List.of(AIigJson_1.class, AIigJsonChild_1.class,
                AIigYaml_1.class, AIigYamlChild_1.class, AIigXml_1.class, AIigXmlChild_1.class)) {
            var locSources = locService.generate(locRead, "d");
            if (locRead == AIigJsonChild_1.class || locRead == AIigYamlChild_1.class
                    || locRead == AIigXmlChild_1.class) locChildren.add(locSources);
            for (var locUnit : java.util.List.of(locSources.mutableInterface(), locSources.implementation())) {
                var locFile = locRoot.resolve(locUnit.relativePath());
                java.nio.file.Files.createDirectories(locFile.getParent());
                java.nio.file.Files.writeString(locFile, locUnit.source());
                locFiles.add(locFile.toString());
            }
        }
        var locArguments = new java.util.ArrayList<String>(java.util.List.of(
                "-cp", System.getProperty("java.class.path"), "-d", locClasses.toString()));
        locArguments.addAll(locFiles);
        org.testng.Assert.assertEquals(javax.tools.ToolProvider.getSystemJavaCompiler().run(
                null, null, null, locArguments.toArray(String[]::new)), 0,
                "Generated XML, YAML and JSON implementation hierarchies must compile");
        try (var locLoader = new java.net.URLClassLoader(
                new java.net.URL[] {locClasses.toUri().toURL()}, getClass().getClassLoader())) {
            String[] locExpectedBases = {
                    "eu.algites.lib.data.smartdataobject.impl.jsondefs.AIcJsonSmartDataObject",
                    "eu.algites.lib.data.smartdataobject.impl.yamldefs.AIcYamlSmartDataObject",
                    "eu.algites.lib.data.smartdataobject.impl.xmldefs.AIcXmlSmartDataObject"
            };
            for (int locIndex = 0; locIndex < locChildren.size(); locIndex++) {
                var locType = locLoader.loadClass(locChildren.get(locIndex).implementation()
                        .fullyQualifiedTypeName());
                org.testng.Assert.assertEquals(locType.getSuperclass().getName(),
                        locExpectedBases[locIndex]);
                org.testng.Assert.assertNotNull(locType.getDeclaredMethod("setKey", String.class));
            }
        }
    }

    /** Verify one schema family without depending on source naming conventions. */
    private static void verify(AItcConfiguredSdoCodegenService aService, Class<?> aRead, String aFamily) {
        var locSources = aService.generate(aRead, "d");
        require(locSources.mutableInterface().source().contains("AIi" + aFamily + "SmartDataObject"),
                "Wrong mutable marker for " + aFamily);
        require(locSources.implementation().source().contains("AIc" + aFamily + "SmartDataObject"),
                "Wrong implementation base for " + aFamily);
    }

    /** Verify inherited fields are implemented with no generated concrete superclass. */
    private static void verifyDirectConcreteRoot(AItcConfiguredSdoCodegenService aService,
            Class<?> aRead, String aFamily) {
        var locSources = aService.generate(aRead, "d");
        String locImplementation = locSources.implementation().source();
        require(locImplementation.contains(" extends eu.algites.lib.data.smartdataobject.impl."
                        + aFamily.toLowerCase(java.util.Locale.ROOT) + "defs.AIc" + aFamily + "SmartDataObject"),
                "Concrete " + aFamily + " subtype must inherit only its runtime base");
        require(!locImplementation.contains(" extends " + aRead.getPackageName() + ".AIcgd"),
                "Concrete " + aFamily + " subtype must not inherit a generated concrete type");
        require(locImplementation.contains(" getKey()"),
                "Concrete implementation must reimplement getters inherited through its interfaces");
        require(locImplementation.contains(" setKey("),
                "Concrete implementation must reimplement setters inherited through its interfaces");
    }

    /** Throw an actionable error when the generated source violates its declared lineage. */
    private static void require(boolean aCondition, String aMessage) {
        if (!aCondition) throw new AssertionError(aMessage);
    }
}
