package eu.algites.tool.codegen.sdo.impl.cli;

import java.util.Arrays;
import java.util.List;

import org.testng.annotations.Test;

/**
 * TestNG regression of qualified, inherited Java sdocodegen settings.
 *
 * <p>Runs in the Gradle TestNG test task and verifies the configured defaults.
 */
public final class AItcLayeredCodegenSettingsTest {
    /**
     * Verify default inheritance, explicit replacement and removal.
     *
     * @throws Exception if packaged settings are unavailable or invalid
     */
    @Test
    public void verifyLayeredSettings() throws Exception {
        List<String> locSettings = Arrays.asList(AIcLayeredCodegenSettings.expand(
                new String[] { "--naming-conventions-file:xmldefs=",
                        "--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER",
                        "--check=true", "--check=false" },
                "sdocodegen", "java", "sdo"));
        if (!locSettings.contains("--setter-inheritance-policy=INHERIT_AS_FIXED_PARAMETER"))
            throw new AssertionError("Invocation layer failed: " + locSettings);
        if (locSettings.contains("--check"))
            throw new AssertionError("Boolean override failed: " + locSettings);
        if (locSettings.stream().anyMatch(aValue ->
                aValue.endsWith("classpath:algites-xmldef-name-conventions.yml")))
            throw new AssertionError("Removing an inherited naming catalog failed: " + locSettings);
        if (locSettings.stream().noneMatch(aValue ->
                aValue.endsWith("classpath:standard-conventions.yml")))
            throw new AssertionError("Unmodified naming catalog was lost: " + locSettings);
        if (!locSettings.contains("--output-technology-naming-convention=java:yamldefs:sdointf=algites-java-gen-data-yaml-intf-versioned_1")
                || !locSettings.contains("--output-technology-naming-convention=java:yamldefs:sdoclass=algites-java-gen-data-yaml-class-versioned_1"))
            throw new AssertionError("Independent SDO naming roles were not preserved: " + locSettings);
    }
}
