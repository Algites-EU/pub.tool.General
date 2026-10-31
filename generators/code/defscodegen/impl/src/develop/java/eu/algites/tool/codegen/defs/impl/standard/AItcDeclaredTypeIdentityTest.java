package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Tests that the JVM implementation applies the same declared-type identity
 * contract as the Python implementation for each supported source family.
 *
 * @author linhart1
 */
public final class AItcDeclaredTypeIdentityTest {
    /**
     * Verify explicit XSD, JSON Schema and YAML Schema type declarations resolve
     * to the same local canonical name while retaining the source's own identity.
     *
     * @throws IllegalArgumentException if a configured naming profile is invalid
     */
    @Test
    public void canonicalDeclaredTypeNamesAgreeAcrossSourceLanguages() {
        AIiNameConventionCatalog catalog = AItcConfiguredNamingProfiles.javaProfile();
        for (String source : new String[]{"jsondef", "yamldef", "xmldef"}) {
            String profile = "algites-" + source + "-schema-versioned_1";
            Assert.assertEquals(AIcDeclaredTypeIdentity.canonicalTypeIdentifier(
                    catalog, profile, "IdentifierConventions"), "identifier-conventions");
            Assert.assertEquals(AIcDeclaredTypeIdentity.canonicalTypeIdentifier(
                    catalog, profile, "VersionConventions"), "version-conventions");
            Assert.expectThrows(IllegalArgumentException.class,
                    () -> AIcDeclaredTypeIdentity.canonicalTypeIdentifier(
                            catalog, profile, "identifier-conventions"));
        }
    }
}
