package eu.algites.tool.codegen.common;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
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
