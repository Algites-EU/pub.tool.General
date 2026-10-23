package eu.algites.tool.codegen.sdo.impl.cli;

import org.testng.annotations.Test;

/**
 * TestNG regression for classpath and legacy catalog selectors.
 *
 * <p>Runs in the Gradle TestNG test task with the compiled generator dependencies.
 */
public final class AItcNamingCatalogSourceTest {
    /**
     * Verifies the portable classpath spelling and backward compatibility.
     */
    @Test
    public void verifyNamingCatalogSources() {
        if (!"resource:catalog.yml".equals(AIcNamingCatalogSource.normalize("classpath:catalog.yml")))
            throw new AssertionError("Classpath naming catalog was not normalized");
        if (!"resource:catalog.yml".equals(AIcNamingCatalogSource.normalize("resource:catalog.yml")))
            throw new AssertionError("Legacy resource naming catalog changed");
        if (!"/tmp/catalog.yml".equals(AIcNamingCatalogSource.normalize("/tmp/catalog.yml")))
            throw new AssertionError("Filesystem catalog was modified");
    }
}
