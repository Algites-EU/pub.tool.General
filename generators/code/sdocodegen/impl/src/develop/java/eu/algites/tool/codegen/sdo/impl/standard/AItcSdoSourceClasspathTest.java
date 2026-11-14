package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verify that Java source-mode SDO compilation handles dependency paths
 * consistently with the bootstrap's materialized runtime classpath.
 *
 * @author linhart1
 */
public final class AItcSdoSourceClasspathTest {
    /**
     * Check a valid, possibly empty, classpath directory is accepted while
     * an unmaterialized dependency is reported by its own name rather than
     * as an uninformative source-tree failure.
     *
     * @throws IOException if the test cannot create its isolated source tree
     */
    @Test
    public void testExistingClasspathAndMissingDependencyDiagnostic() throws IOException {
        Path locTemp = Files.createTempDirectory("sdo-source-classpath-");
        Path locSource = Files.createDirectories(locTemp.resolve("src"));
        Path locPresent = Files.createDirectories(locTemp.resolve("compiled-resources"));
        Path locMissing = locTemp.resolve("build/resources/main");
        try {
            Files.writeString(locSource.resolve("SampleContract.java"),
                    "public interface SampleContract { String getLabel(); }\n",
                    StandardCharsets.UTF_8);
            try (var locCompiled = AIcSdoContractSourceLoader.compile(locSource, List.of(locPresent))) {
                Assert.assertEquals(locCompiled.load(locSource.resolve("SampleContract.java"))
                        .getSimpleName(), "SampleContract");
            }
            AIxCodegenValidationException locError = Assert.expectThrows(
                    AIxCodegenValidationException.class,
                    () -> AIcSdoContractSourceLoader.compile(locSource, List.of(locPresent, locMissing)));
            Assert.assertTrue(locError.getMessage().contains("Missing Java SDO dependency classpath entry"));
            Assert.assertTrue(locError.getMessage().contains(locMissing.toString()));
            Assert.assertEquals(locError.getSource(), locMissing.toString());
        } finally {
            Files.deleteIfExists(locSource.resolve("SampleContract.java"));
            Files.deleteIfExists(locPresent);
            Files.deleteIfExists(locSource);
            Files.deleteIfExists(locTemp);
        }
    }
}
