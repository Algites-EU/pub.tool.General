package eu.algites.tool.codegen.common;

import java.nio.file.Files;
import java.nio.file.Path;
import org.testng.annotations.Test;

/**
 * Regression tests for the shared Java artifact selector.
 *
 * @author linhart1
 */
public final class AItcCodegenArtifactResolverTest {
    /**
     * Confirms Maven and Modustro selections identify the same local JAR.
     *
     * @throws Exception when creating or cleaning the temporary repository fails
     */
    @Test
    public void verifyMavenAndModustroSelectors() throws Exception {
        Path locHome = Files.createTempDirectory("algites-codegen-artifacts-");
        String locPrevious = System.getProperty("user.home");
        try {
            System.setProperty("user.home", locHome.toString());
            Path locJar = locHome.resolve(".modustro/artifact-repos/java/maven/eu/algites/lib/")
                    .resolve("sample/1.1-SNAPSHOT/sample-1.1-SNAPSHOT.jar");
            Files.createDirectories(locJar.getParent());
            Files.write(locJar, new byte[] {0});
            var locMaven = AIcCodegenArtifactResolver.resolveJava(
                    "eu.algites.lib:sample:1.1-SNAPSHOT");
            var locModustro = AIcCodegenArtifactResolver.resolveJava(
                    "sample@1.1-SNAPSHOT");
            if (!locMaven.equals(locModustro) || !locMaven.equals(java.util.List.of(locJar)))
                throw new AssertionError("Maven and Modustro selectors disagree");
        } finally {
            if (locPrevious == null) System.clearProperty("user.home");
            else System.setProperty("user.home", locPrevious);
            try (var locWalk = Files.walk(locHome)) {
                for (Path locPath : locWalk.sorted(java.util.Comparator.reverseOrder()).toList())
                    Files.deleteIfExists(locPath);
            }
        }
    }
}
