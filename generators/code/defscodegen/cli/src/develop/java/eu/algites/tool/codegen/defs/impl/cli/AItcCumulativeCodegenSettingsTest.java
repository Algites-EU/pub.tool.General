package eu.algites.tool.codegen.defs.impl.cli;

import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

import org.testng.annotations.Test;

/** Regression of layered settings from two independent classpath roots. */
public final class AItcCumulativeCodegenSettingsTest {
    /**
     * Checks cross-resource accumulation and highest-priority invocation options.
     *
     * @throws Exception if the isolated classpath resources cannot be read
     */
    @Test
    public void verifyCumulativeSettings() throws Exception {
        Path locRoot = Files.createTempDirectory("algites-cumulative-settings-");
        Path locFirst = locRoot.resolve("first");
        Path locSecond = locRoot.resolve("second");
        String locSubpath = "eu/algites/tool/codegen/defs/defscodegen-java.settings";
        Files.createDirectories(locFirst.resolve(locSubpath).getParent());
        Files.createDirectories(locSecond.resolve(locSubpath).getParent());
        Files.writeString(locSecond.resolve(locSubpath),
                "--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER\n"
                + "--naming-conventions-file:second=classpath:second.yml\n");
        Files.writeString(locFirst.resolve(locSubpath),
                "--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER\n"
                + "--naming-conventions-file:first=classpath:first.yml\n");
        ClassLoader locPrevious = Thread.currentThread().getContextClassLoader();
        try (URLClassLoader locLoader = new URLClassLoader(new URL[] {
                locFirst.toUri().toURL(), locSecond.toUri().toURL()}, locPrevious)) {
            Thread.currentThread().setContextClassLoader(locLoader);
            List<String> locMerged = Arrays.asList(AIcLayeredCodegenSettings.expand(
                    new String[0], "defscodegen", "java", "defs"));
            if (!locMerged.contains("--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER")
                    || !locMerged.contains("--naming-conventions-file=classpath:first.yml")
                    || !locMerged.contains("--naming-conventions-file=classpath:second.yml"))
                throw new AssertionError("Not all classpath settings were merged: " + locMerged);
            Path locExplicit = locRoot.resolve("invocation.settings");
            Files.writeString(locExplicit, "--naming-conventions-file:second=\n"
                    + "--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER\n");
            locMerged = Arrays.asList(AIcLayeredCodegenSettings.expand(new String[] {
                    "--settings-file=" + locExplicit,
                    "--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER"},
                    "defscodegen", "java", "defs"));
            if (locMerged.contains("--naming-conventions-file=classpath:second.yml")
                    || !locMerged.contains("--naming-conventions-file=classpath:first.yml")
                    || !locMerged.contains("--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER"))
                throw new AssertionError("Explicit settings/CLI precedence failed: " + locMerged);
        } finally {
            Thread.currentThread().setContextClassLoader(locPrevious);
            try (var locFiles = Files.walk(locRoot)) {
                for (Path locFile : locFiles.sorted(java.util.Comparator.reverseOrder()).toList())
                    Files.deleteIfExists(locFile);
            }
        }
    }
}
