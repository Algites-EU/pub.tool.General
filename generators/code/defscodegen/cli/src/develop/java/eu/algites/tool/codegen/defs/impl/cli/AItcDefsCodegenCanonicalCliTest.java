package eu.algites.tool.codegen.defs.impl.cli;

import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Regression checks for the independent Java native Defs CLI argument contract.
 * The Python CLI uses the same manifest and check option spelling.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenCanonicalCliTest {
    /** Rejects an invocation without any generation manifest. */
    @Test
    public void AIcJavaCanonicalCliRequiresManifest() throws Exception {
        try {
            AIcDefsCodegenCanonicalCli.run(List.of());
            Assert.fail("Empty manifest list was accepted");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("--manifest"));
        }
    }

    /** Rejects an old or misspelled parameter rather than silently interpreting it. */
    @Test
    public void AIcJavaCanonicalCliRejectsUnknownArguments() throws Exception {
        try {
            AIcDefsCodegenCanonicalCli.run(List.of("--unexpected"));
            Assert.fail("Unknown CLI parameter was accepted");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("--unexpected"));
        }
    }
}
