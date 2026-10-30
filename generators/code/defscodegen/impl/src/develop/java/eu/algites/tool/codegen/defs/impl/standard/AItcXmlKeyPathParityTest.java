package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdKeyDefinition;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies standalone Java XMLDEFS handling of typed, potentially nested XSD
 * identity fields. This regression prevents Python-driven bootstrap generation
 * from hiding divergences in the native Java frontend.
 *
 * @author linhart1
 */
public final class AItcXmlKeyPathParityTest {
    /**
     * Creates a source naming catalog that is sufficient for parsing XML
     * definitions without resolving generated structural identifiers.
     *
     * @return stateless, non-null testing catalog
     */
    private static AIiNameConventionCatalog catalog() {
        return new AIiNameConventionCatalog() {
            /** {@inheritDoc} */
            @Override public Set<String> names() { return Set.of(); }
            /** {@inheritDoc} */
            @Override public String format(String profile, String structure,
                    Map<String, String> values, String sourceConvention) { return ""; }
            /** {@inheritDoc} */
            @Override public Map<String, String> parse(String profile, String structure,
                    String name) { return Map.of(); }
            /** {@inheritDoc} */
            @Override public boolean matches(String profile, String structure,
                    String name) { return false; }
        };
    }

    /**
     * Returns an XSD that declares two independent key definitions over one
     * repeated XML item type, including a nullable intermediate element.
     *
     * @param fieldPath XPath expression of the second key field
     * @return complete example schema including the specified key expression
     */
    private static String schema(String fieldPath) {
        return """
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="urn:staff"
                targetNamespace="urn:staff" elementFormDefault="qualified">
              <xs:complexType name="staff"><xs:sequence>
                <xs:element name="Employees"><xs:complexType><xs:sequence>
                  <xs:element name="Employee" minOccurs="0" maxOccurs="unbounded">
                    <xs:complexType><xs:sequence>
                      <xs:element name="Identity" minOccurs="0"><xs:complexType><xs:sequence>
                        <xs:element name="Code" type="xs:string"/>
                      </xs:sequence></xs:complexType></xs:element>
                    </xs:sequence><xs:attribute name="Id" type="xs:integer" use="required"/>
                    </xs:complexType>
                  </xs:element>
                </xs:sequence></xs:complexType>
                  <xs:key name="ById"><xs:selector xpath="tns:Employee"/>
                    <xs:field xpath="@Id"/></xs:key>
                  <xs:key name="ByCode"><xs:selector xpath="tns:Employee"/>
                    <xs:field xpath="%s"/></xs:key>
                </xs:element>
              </xs:sequence></xs:complexType>
            </xs:schema>
            """.formatted(fieldPath);
    }

    /**
     * Ensures that both keys survive as separate unique map indexes and that
     * the nested field path is preserved for null-guarded extraction.
     *
     * @throws IOException if the temporary schema cannot be created or read
     */
    @Test
    public void readsNestedAndDirectKeys() throws IOException {
        Path directory = Files.createTempDirectory("algites-key-");
        Path source = directory.resolve("staff_1.xsd");
        try {
            Files.writeString(source, schema("tns:Identity/tns:Code"));
            var frontend = new AIcXmlDefsFrontend();
            var request = new AIcdDefinitionLoadRequest(source,
                    AInDefinitionSourceKind.XMLDEFS, catalog());
            frontend.load(request);
            var keyed = frontend.loadNamedType(request, "staffEmployees")
                    .dataType().properties().get(0).dataType();
            Assert.assertEquals(keyed.keyDefinitions(), List.of(
                    new AIcdKeyDefinition("ById", List.of("Id"), true, false),
                    new AIcdKeyDefinition("ByCode", List.of("Identity.Code"), true, false)));
            Assert.assertEquals(frontend.loadNamedType(request, "staffEmployeesEmployee")
                    .dataType().properties().size(), 2);
        } finally {
            Files.deleteIfExists(source);
            Files.deleteIfExists(directory);
        }
    }

    /**
     * Ensures an unqualified step cannot select a qualified XML element.
     *
     * @throws IOException if source creation or deletion fails
     */
    @Test
    public void rejectsUnqualifiedKeyPath() throws IOException {
        Path directory = Files.createTempDirectory("algites-key-");
        Path source = directory.resolve("staff_1.xsd");
        try {
            Files.writeString(source, schema("Identity/Code"));
            Assert.expectThrows(IOException.class, () -> new AIcXmlDefsFrontend().loadNamedType(
                    new AIcdDefinitionLoadRequest(source, AInDefinitionSourceKind.XMLDEFS, catalog()),
                    "staffEmployees"));
        } finally {
            Files.deleteIfExists(source);
            Files.deleteIfExists(directory);
        }
    }

    /**
     * Confirms that a reference constraint does not add a key index and does
     * not suppress real keys. Referential validity belongs to the XSD validator.
     *
     * @throws IOException if creating, reading or removing test sources fails
     */
    @Test
    public void ignoresKeyrefWithoutDroppingIndexes() throws IOException {
        Path directory = Files.createTempDirectory("algites-keyref-");
        Path source = directory.resolve("staff_1.xsd");
        try {
            String original = schema("tns:Identity/tns:Code");
            String keyref = "<xs:keyref name=\"RefToId\" refer=\"tns:ById\">"
                    + "<xs:selector xpath=\"tns:Employee\"/>"
                    + "<xs:field xpath=\"@Id\"/></xs:keyref>";
            String transformed = original.replaceFirst(
                    "</xs:key>(?=\\s*</xs:element>)", "</xs:key>" + keyref);
            Assert.assertEquals(transformed.equals(original), false);
            Files.writeString(source, transformed);
            var frontend = new AIcXmlDefsFrontend();
            var request = new AIcdDefinitionLoadRequest(source,
                    AInDefinitionSourceKind.XMLDEFS, catalog());
            frontend.load(request);
            var keys = frontend.loadNamedType(request, "staffEmployees")
                    .dataType().properties().get(0).dataType().keyDefinitions();
            Assert.assertEquals(keys.size(), 2);
            Assert.assertEquals(keys.get(0).name(), "ById");
            Assert.assertEquals(keys.get(1).name(), "ByCode");
        } finally {
            Files.deleteIfExists(source);
            Files.deleteIfExists(directory);
        }
    }
}
