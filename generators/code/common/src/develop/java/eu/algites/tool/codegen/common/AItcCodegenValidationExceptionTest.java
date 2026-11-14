package eu.algites.tool.codegen.common;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Validates the explicit message-plus-hint contract shared by Java generators.
 *
 * @author linhart1
 */
public class AItcCodegenValidationExceptionTest {
    /** Assert that the inherited message is unchanged and hint is independently available. */
    @Test
    public void messageAndHintAreSeparateFields() {
        String original = "Incompatible KEYED_VALUES declarations: credentials";
        String hint = "Align the XML collection and JSON/YAML map in their source schemas.";
        AIxCodegenValidationException error = new AIxCodegenValidationException(
                original, hint, "credentials_1.xsd", "/Credentials/Profile");
        Assert.assertEquals(error.getMessage(), original);
        Assert.assertEquals(error.getHint(), hint);
        Assert.assertEquals(error.getSource(), "credentials_1.xsd");
        Assert.assertEquals(error.getLocation(), "/Credentials/Profile");
        Assert.assertTrue(error instanceof IllegalArgumentException);
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        Assert.assertTrue(AIcCodegenDiagnostics.report(error, "Defs Codegen", null,
                new PrintStream(bytes, true, StandardCharsets.UTF_8)));
        String rendered = bytes.toString(StandardCharsets.UTF_8);
        Assert.assertTrue(rendered.contains("Message: " + original));
        Assert.assertTrue(rendered.contains("Hint: " + hint));
        Assert.assertFalse(rendered.contains("at eu.algites."), "Validation is not an unhandled stack trace");
    }

    /** Count each file's issues independently even when the report interleaves files. */
    @Test
    public void batchDiagnosticsIncludeGlobalAndPerFileCounters() {
        List<AIxCodegenValidationException> issues = List.of(
                new AIxCodegenValidationException("first-A", "fix A", "a.xsd", "/one"),
                new AIxCodegenValidationException("only-B", "fix B", "b.xsd", null),
                new AIxCodegenValidationException("second-A", "fix A", "a.xsd", "/two"),
                new AIxCodegenValidationException("unknown", "inspect input"),
                new AIxCodegenValidationException("third-A", "fix A", "a.xsd", null),
                new AIxCodegenValidationException("unknown-2", "inspect input"));
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        boolean handled = AIcCodegenDiagnostics.report(
                new AIxCodegenBatchValidationException(issues), "SDO Codegen", null,
                new PrintStream(bytes, true, StandardCharsets.UTF_8));
        Assert.assertTrue(handled);
        String rendered = bytes.toString(StandardCharsets.UTF_8);
        Assert.assertTrue(rendered.contains("[1/6] (1/3) first-A"));
        Assert.assertTrue(rendered.contains("[2/6] (1/1) only-B"));
        Assert.assertTrue(rendered.contains("[3/6] (2/3) second-A"));
        Assert.assertTrue(rendered.contains("[4/6] (1/1) unknown"));
        Assert.assertTrue(rendered.contains("[5/6] (3/3) third-A"));
        Assert.assertTrue(rendered.contains("[6/6] (1/1) unknown-2"));
        Assert.assertTrue(rendered.contains("Source: a.xsd"));
        Assert.assertTrue(rendered.contains("Location: /two"));
    }

    /** Assert that stack traces for unexpected failures remain possible. */
    @Test
    public void unexpectedFailuresAreNotRenderedAsUserErrors() {
        Assert.assertFalse(AIcCodegenDiagnostics.report(new NullPointerException("internal defect"),
                "SDO Codegen", null, System.err));
    }

    /** Assert that the original cause is retained without altering the text. */
    @Test
    public void causeAndMessageStayAvailable() {
        Throwable cause = new IllegalStateException("nested failure");
        AIxCodegenValidationException error = new AIxCodegenValidationException(
                "missing input", "Correct the selected input artifact.", null, null, cause);
        Assert.assertSame(error.getCause(), cause);
        Assert.assertEquals(error.getMessage(), "missing input");
    }
}
