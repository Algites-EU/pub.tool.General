package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Checks that XSD features outside the canonical particle model fail explicitly. */
public final class AItcXmlNoSilentContentLossTest {
    /** Validate an unsupported content-model construct independently of naming. */
    private static void reject(String aBody, String aExpected) throws Exception {
        Path locDirectory = Files.createTempDirectory("algites-xsd-no-loss-");
        Path locSchema = locDirectory.resolve("guard_1.xsd");
        try {
            Files.writeString(locSchema, "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" "
                    + "version=\"1\" targetNamespace=\"urn:guard\"><xs:complexType name=\"Guard\">"
                    + aBody + "</xs:complexType></xs:schema>");
            AIiNameConventionCatalog locCatalog = (AIiNameConventionCatalog) Proxy.newProxyInstance(
                    AIiNameConventionCatalog.class.getClassLoader(),
                    new Class<?>[]{AIiNameConventionCatalog.class}, (aProxy, aMethod, aArgs) -> null);
            try {
                new AIcXmlDefsFrontend().load(new AIcdDefinitionLoadRequest(
                        locSchema, AInDefinitionSourceKind.XMLDEFS, locCatalog));
                throw new AssertionError("Unsupported XSD content model was silently accepted");
            } catch (IOException locExpected) {
                Assert.assertEquals(locExpected.getMessage().contains(aExpected), true);
            }
        } finally {
            Files.deleteIfExists(locSchema);
            Files.deleteIfExists(locDirectory);
        }
    }

    /** Unsupported assertions must not disappear from canonical contracts. */
    @Test
    public void AIcRejectUnsupportedSchemaAssertion() throws Exception {
        reject("<xs:assert test=\"true()\"/>", "Unsupported XSD content model child");
    }

    /** Unsupported wildcard content models must never generate partial contracts. */
    @Test
    public void AIcRejectUnsupportedOpenContent() throws Exception {
        reject("<xs:openContent mode=\"interleave\"><xs:any/></xs:openContent>",
                "Unsupported XSD content model child");
    }
}
