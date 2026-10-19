package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import org.testng.annotations.Test;

/** Validates exact one-element compositor cardinality in the Java XML frontend. */
public final class AItcXmlSingleLeafRepeatedGroupTest {
    /**
     * One repeated compositor with one mandatory member maps to a repeated QName
     * without introducing artificial group identity or dropping occurrence limits.
     *
     * @throws Exception if the frontend or schema fixture cannot be executed
     */
    @Test
    public void AIcSingleLeafCompositorRetainsBounds() throws Exception {
        var locFile = Files.createTempFile("algites-xsd-group-", ".xsd");
        try {
            Files.writeString(locFile, "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" " +
                    "targetNamespace=\"urn:group\"><xs:complexType name=\"Root\">" +
                    "<xs:all minOccurs=\"2\" maxOccurs=\"4\">" +
                    "<xs:element name=\"Code\" type=\"xs:string\"/>" +
                    "</xs:all></xs:complexType></xs:schema>");
            AIiNameConventionCatalog locCatalog = (AIiNameConventionCatalog) Proxy.newProxyInstance(
                    AIiNameConventionCatalog.class.getClassLoader(),
                    new Class<?>[]{AIiNameConventionCatalog.class}, (aProxy, aMethod, aArgs) -> null);
            var locDefinition = new AIcXmlDefsFrontend().load(new AIcdDefinitionLoadRequest(
                    locFile, AInDefinitionSourceKind.XMLDEFS, locCatalog));
            var locField = locDefinition.dataType().properties().get(0);
            if (locField.dataType().kind() != AInDataTypeKind.ARRAY
                    || locField.dataType().constraints().minItems() != 2
                    || locField.dataType().constraints().maxItems() != 4
                    || locField.dataType().elementType().kind() != AInDataTypeKind.STRING)
                throw new AssertionError("One-element repeating XSD group lost its occurrence bounds");
        } finally {
            Files.deleteIfExists(locFile);
        }
    }

    /**
     * Repeated correlated fields cannot be mapped into independent arrays.
     *
     * @throws Exception if the frontend or schema fixture cannot be executed
     */
    @Test
    public void AIcCorrelatedRepeatedGroupFailsClosed() throws Exception {
        var locFile = Files.createTempFile("algites-xsd-group-", ".xsd");
        try {
            Files.writeString(locFile, "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">" +
                    "<xs:complexType name=\"Root\"><xs:sequence maxOccurs=\"3\">" +
                    "<xs:element name=\"A\" type=\"xs:string\"/>" +
                    "<xs:element name=\"B\" type=\"xs:string\"/>" +
                    "</xs:sequence></xs:complexType></xs:schema>");
            AIiNameConventionCatalog locCatalog = (AIiNameConventionCatalog) Proxy.newProxyInstance(
                    AIiNameConventionCatalog.class.getClassLoader(),
                    new Class<?>[]{AIiNameConventionCatalog.class}, (aProxy, aMethod, aArgs) -> null);
            try {
                new AIcXmlDefsFrontend().load(new AIcdDefinitionLoadRequest(
                        locFile, AInDefinitionSourceKind.XMLDEFS, locCatalog));
                throw new AssertionError("Repeated correlated XSD fields were incorrectly flattened");
            } catch (java.io.IOException locExpected) {
                if (!locExpected.getMessage().contains("group cardinality")) throw locExpected;
            }
        } finally {
            Files.deleteIfExists(locFile);
        }
    }
}
