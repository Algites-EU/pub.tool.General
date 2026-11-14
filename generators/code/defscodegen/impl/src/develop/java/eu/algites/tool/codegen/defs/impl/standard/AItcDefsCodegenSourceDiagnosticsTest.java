package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies that the native Java frontend preserves the input filename in its errors.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenSourceDiagnosticsTest {
    /**
     * Rejects a malformed named-definitions container with its original resource.
     */
    @Test
    public void AIcInvalidDefinitionsReportTheirResource() {
        var profile = new AIcCodegenNamingProfileResolver.Profile("test",
                Map.of("standard_getter", "unused", "standard_setter", "unused"),
                Map.of(), Map.of(), Map.of(), 1, Map.of());
        var pipeline = new AIcDefsCodegenCanonicalPipeline(profile, ignored -> { });
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            String resource = "schemas/broken-" + kind + ".json";
            try {
                pipeline.process(List.of(new AIcdDefsCodegenSourceDocument(
                        kind, resource, Map.of("$defs", List.of("wrong")))));
                Assert.fail("Malformed named definitions must be rejected");
            } catch (IllegalArgumentException expected) {
                Assert.assertTrue(expected.getMessage().contains(resource),
                        expected.getMessage());
            }
        }
    }
}
