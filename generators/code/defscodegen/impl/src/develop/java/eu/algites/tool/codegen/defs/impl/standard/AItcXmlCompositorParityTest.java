package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.data.dataobject.AInFieldPresenceKind;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies that supported XML {@code xs:all} and {@code xs:sequence} particles
 * share the same canonical ordered-property representation, including simple
 * content-model restrictions. This does not substitute for strict XSD validation
 * of serialized documents: an XML Schema sequence remains order-sensitive when
 * validated by an independent XML Schema validator.
 */
public final class AItcXmlCompositorParityTest {
    /**
     * Projects both compositor names to identical field declarations and
     * preserves a deterministic declaration order for XML serialization.
     *
     * @throws Exception if temporary XML fixtures cannot be written or parsed
     */
    @Test
    public void AIcCanonicalAllAndSequenceEquivalence() throws Exception {
        var locSequence = load("sequence", null, "Base");
        var locAll = load("all", null, "Base");
        Assert.assertEquals(locSequence.dataType(), locAll.dataType());
        Assert.assertEquals(locAll.dataType().properties().get(0).sourceName(), "first");
        Assert.assertEquals(locAll.dataType().properties().get(1).sourceName(), "second");
    }

    /**
     * Exercises all four possible pairs of base and restricted compositor
     * names. Omitted optional XML elements remain canonically forbidden.
     *
     * @throws Exception if temporary XML fixtures cannot be written or parsed
     */
    @Test
    public void AIcAllowEquivalentFlatAllAndSequenceRestrictions() throws Exception {
        for (String locBase : new String[] {"sequence", "all"}) {
            for (String locRestricted : new String[] {"sequence", "all"}) {
                String locRestriction = "<xs:complexType name='Derived'><xs:complexContent>"
                        + "<xs:restriction base='tns:Base'><xs:" + locRestricted + ">"
                        + "<xs:element name='first' type='xs:string'/>"
                        + "</xs:" + locRestricted + "></xs:restriction>"
                        + "</xs:complexContent></xs:complexType>";
                var locDefinition = load(locBase, locRestriction, "Derived");
                Assert.assertEquals(locDefinition.dataType().properties().size(), 2);
                Assert.assertEquals(locDefinition.dataType().properties().get(1).presence(),
                        AInFieldPresenceKind.FORBIDDEN);
            }
        }
    }

    /**
     * Loads one generated test schema with an inert naming catalog. This tests
     * source normalization without coupling to published naming configurations.
     *
     * @param aCompositorName either supported XML compositor name
     * @param aRestriction optional XML complex type restriction declaration
     * @param aTypeName named type to project
     * @return the selected canonical definition
     * @throws Exception if the temporary schema cannot be written or loaded
     */
    private static eu.algites.tool.codegen.defs.AIcdCanonicalDefinition load(
            String aCompositorName, String aRestriction, String aTypeName) throws Exception {
        Path locFolder = Files.createTempDirectory("algites-xml-compositor-");
        Path locFile = locFolder.resolve("compositor_1.xsd");
        try {
            Files.writeString(locFile, "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' "
                    + "xmlns:tns='urn:compositors' targetNamespace='urn:compositors' "
                    + "elementFormDefault='qualified' version='1'>"
                    + "<xs:complexType name='Base'><xs:" + aCompositorName + ">"
                    + "<xs:element name='first' type='xs:string'/>"
                    + "<xs:element name='second' type='xs:int' minOccurs='0'/>"
                    + "</xs:" + aCompositorName + "></xs:complexType>"
                    + (aRestriction == null ? "" : aRestriction) + "</xs:schema>");
            AIiNameConventionCatalog locNaming = new AIiNameConventionCatalog() {
                /** The XML frontend does not enumerate naming conventions. */
                @Override public Set<String> names() { return Set.of(); }
                /** Unused by XML input parsing. */
                @Override public String format(String aProfile, String aStructure,
                        Map<String, String> aValues, String aSourceIdentifierConvention) {
                    throw new UnsupportedOperationException();
                }
                /** Unused by XML input parsing. */
                @Override public Map<String, String> parse(String aProfile, String aStructure, String aName) {
                    throw new UnsupportedOperationException();
                }
                /** Unused by XML input parsing. */
                @Override public boolean matches(String aProfile, String aStructure, String aName) {
                    return false;
                }
            };
            var locRequest = new AIcdDefinitionLoadRequest(locFile, AInDefinitionSourceKind.XMLDEFS, locNaming);
            return new AIcXmlDefsFrontend().loadNamedType(locRequest, aTypeName);
        } finally {
            Files.deleteIfExists(locFile);
            Files.deleteIfExists(locFolder);
        }
    }
}
