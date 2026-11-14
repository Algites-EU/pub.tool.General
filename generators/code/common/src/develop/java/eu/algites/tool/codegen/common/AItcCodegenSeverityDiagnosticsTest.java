package eu.algites.tool.codegen.common;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Exercises severity grouping, per-source numbering and nonfatal diagnostics.
 *
 * @author linhart1
 */
public class AItcCodegenSeverityDiagnosticsTest {
    /** Validate the full DEBUG/INFO/WARNING/ERROR ordering without losing provenance. */
    @Test
    public void severitySectionsAndCounters() {
        var batch = new AIcCodegenValidationBatch(false);
        batch.addDiagnostic(AInCodegenDiagnosticSeverity.WARNING, "warning A1", "fix A", "a.xsd", "/one");
        batch.add(new AIxCodegenValidationException("error A1", "fix", "a.xsd", "/two"), "a.xsd");
        batch.addDiagnostic(AInCodegenDiagnosticSeverity.INFO, "info B", null, "b.json", null);
        batch.addDiagnostic(AInCodegenDiagnosticSeverity.WARNING, "warning B", null, "b.json", null);
        batch.addDiagnostic(AInCodegenDiagnosticSeverity.WARNING, "warning A2", null, "a.xsd", null);
        batch.add(new AIxCodegenValidationException("error A2", "fix", "a.xsd", "/three"), "a.xsd");
        var bytes = new ByteArrayOutputStream();
        try {
            batch.finish();
            Assert.fail("Errors must invalidate this run");
        } catch (AIxCodegenBatchValidationException failure) {
            Assert.assertTrue(AIcCodegenDiagnostics.report(failure, "Defs Codegen", null,
                    new PrintStream(bytes, true, StandardCharsets.UTF_8)));
        }
        String report = bytes.toString(StandardCharsets.UTF_8);
        Assert.assertTrue(report.indexOf("INFO - Defs Codegen") < report.indexOf("VALIDATION WARNINGS"));
        Assert.assertTrue(report.indexOf("VALIDATION WARNINGS") < report.indexOf("VALIDATION ERRORS"));
        Assert.assertTrue(report.contains("[1/3] (1/2) warning A1"));
        Assert.assertTrue(report.contains("[2/3] (1/1) warning B"));
        Assert.assertTrue(report.contains("[3/3] (2/2) warning A2"));
        Assert.assertTrue(report.contains("[1/2] (1/2) error A1"));
        Assert.assertTrue(report.contains("[2/2] (2/2) error A2"));
        Assert.assertTrue(report.contains("Location: /one"));
    }

    /** Warnings alone must not throw or publish an error section. */
    @Test
    public void warningOnlyIsSuccessful() {
        var batch = new AIcCodegenValidationBatch(false);
        batch.addDiagnostic(AInCodegenDiagnosticSeverity.WARNING, "unsupported selector",
                "Skip index generation", "schema.xsd", "/xs:key");
        batch.finish();
        var bytes = new ByteArrayOutputStream();
        batch.reportNonErrors("SDO Codegen", new PrintStream(bytes, true, StandardCharsets.UTF_8));
        String report = bytes.toString(StandardCharsets.UTF_8);
        Assert.assertTrue(report.contains("VALIDATION WARNINGS - SDO Codegen: 1 issue(s)"));
        Assert.assertFalse(report.contains("VALIDATION ERRORS"));
    }

    /** A warning preceding a sole error must still be printed before that error. */
    @Test
    public void oneErrorAndWarningUseStructuredSeverityReport() {
        var batch = new AIcCodegenValidationBatch(false);
        batch.info("read schema", "a.xsd", null);
        batch.warning("skipped optional index", null, "a.xsd", null);
        batch.add(new AIxCodegenValidationException("bad declaration", "fix schema", "a.xsd", null), "a.xsd");
        var bytes = new ByteArrayOutputStream();
        try {
            batch.finish();
            Assert.fail("Expected validation failure");
        } catch (AIxCodegenBatchValidationException error) {
            AIcCodegenDiagnostics.report(error, "Defs Codegen", null,
                    new PrintStream(bytes, true, StandardCharsets.UTF_8));
        }
        String report = bytes.toString(StandardCharsets.UTF_8);
        Assert.assertTrue(report.indexOf("INFO - Defs Codegen") < report.indexOf("VALIDATION WARNINGS"));
        Assert.assertTrue(report.indexOf("VALIDATION WARNINGS") < report.indexOf("VALIDATION ERRORS"));
        Assert.assertTrue(report.contains("[1/1] (1/1) bad declaration"));
    }

    /** Fail-fast finish filters later errors, while retaining prior warnings. */
    @Test
    public void optimizedFinishFiltersErrorsFromLaterFiles() {
        var batch = new AIcCodegenValidationBatch(true);
        batch.warning("prior warning", null, "a.xsd", null);
        batch.add(new AIxCodegenValidationException("first error", "fix", "a.xsd", null), "a.xsd");
        batch.add(new AIxCodegenValidationException("later error", "fix", "b.xsd", null), "b.xsd");
        var bytes = new ByteArrayOutputStream();
        try {
            batch.finish();
            Assert.fail("Expected validation failure");
        } catch (AIxCodegenBatchValidationException error) {
            AIcCodegenDiagnostics.report(error, "Defs Codegen", null,
                    new PrintStream(bytes, true, StandardCharsets.UTF_8));
        }
        String report = bytes.toString(StandardCharsets.UTF_8);
        Assert.assertTrue(report.contains("first error"));
        Assert.assertFalse(report.contains("later error"));
    }

    /** Early exit waits until the complete first invalid input has been examined. */
    @Test
    public void oneInputAtATimeGroupsAllErrorsWithinFirstFile() {
        var batch = new AIcCodegenValidationBatch(true);
        batch.addDiagnostic(AInCodegenDiagnosticSeverity.WARNING, "warning", null, "a.xsd", null);
        batch.finishInput("a.xsd");
        batch.add(new AIxCodegenValidationException("first", "fix", "b.xsd", null), "b.xsd");
        batch.add(new AIxCodegenValidationException("second", "fix", "b.xsd", null), "b.xsd");
        try {
            batch.finishInput("b.xsd");
            Assert.fail("Expected the first invalid source to abort");
        } catch (AIxCodegenBatchValidationException failure) {
            Assert.assertEquals(failure.issues().size(), 2);
            Assert.assertEquals(failure.diagnostics().size(), 3);
        }
    }
}
