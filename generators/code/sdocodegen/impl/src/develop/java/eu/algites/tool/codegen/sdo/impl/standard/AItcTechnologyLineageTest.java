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

    /** Check each mutable marker, concrete implementation base, and XML QName metadata. */
    @Test
    public void AIcGeneratesTechnologySpecificTypes() {
        AItcConfiguredSdoCodegenService locService = new AItcConfiguredSdoCodegenService();
        verify(locService, AIigJson_1.class, "Json");
        verify(locService, AIigYaml_1.class, "Yaml");
        verify(locService, AIigXml_1.class, "Xml");
        var locXml = locService.generate(AIigXml_1.class, "d").mutableInterface().source();
        require(locXml.contains("AIaXmlDataObject("), "XML type annotation was lost");
        require(locXml.contains("namespaceLocalName = \"entry\""), "XML element QName was lost");
        require(locXml.contains("AIaXmlDataObjectField("), "XML field metadata was lost");
        require(locXml.contains("namespaceLocalName = \"key\""), "XML field QName was lost");
        require(!locXml.contains("OpenChoice"), "Removed OpenChoice API was emitted");
    }

    /** Verify one schema family without depending on source naming conventions. */
    private static void verify(AItcConfiguredSdoCodegenService aService, Class<?> aRead, String aFamily) {
        var locSources = aService.generate(aRead, "d");
        require(locSources.mutableInterface().source().contains("AIi" + aFamily + "SmartDataObject"),
                "Wrong mutable marker for " + aFamily);
        require(locSources.implementation().source().contains("AIc" + aFamily + "SmartDataObject"),
                "Wrong implementation base for " + aFamily);
    }

    /** Throw an actionable error when the generated source violates its declared lineage. */
    private static void require(boolean aCondition, String aMessage) {
        if (!aCondition) throw new AssertionError(aMessage);
    }
}
