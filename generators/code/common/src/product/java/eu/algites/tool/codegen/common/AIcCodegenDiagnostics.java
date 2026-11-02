package eu.algites.tool.codegen.common;

import java.io.PrintStream;

/**
 * Plain-text reporting of explicitly hinted validation exceptions raised by
 * either Codegen. Unexpected implementation exceptions are never disguised.
 *
 * @author linhart1
 */
public final class AIcCodegenDiagnostics {
    private AIcCodegenDiagnostics() { }

    /**
     * Renders an expected validation exception without changing its message.
     *
     * @param error failure raised during generation, possibly wrapped by a CLI
     * @param generator tool name shown in the output
     * @param source fallback source file or artifact, or null when unavailable
     * @param output stream receiving the report
     * @return true only if an explicit validation exception was found
     */
    public static boolean report(Throwable error, String generator, String source, PrintStream output) {
        Throwable current = error;
        while (current != null && !(current instanceof AIxCodegenValidationException)) {
            current = current.getCause();
        }
        if (!(current instanceof AIxCodegenValidationException diagnostic)) return false;
        output.println();
        output.println("  VALIDATION ERROR - " + generator);
        output.println();
        output.println("  Message: " + diagnostic.getMessage());
        String actualSource = diagnostic.getSource() == null ? source : diagnostic.getSource();
        if (actualSource != null) output.println("  Source: " + actualSource);
        if (diagnostic.getLocation() != null) output.println("  Location: " + diagnostic.getLocation());
        output.println();
        output.println("  Hint: " + diagnostic.getHint());
        output.println();
        String debug = System.getenv("ALGITES_CODEGEN_DEBUG");
        if ("1".equals(debug) || "true".equalsIgnoreCase(debug)) error.printStackTrace(output);
        return true;
    }

    /**
     * Reports a validation failure at the standalone CLI boundary and exits
     * with status 2. Unexpected failures are rethrown unchanged.
     *
     * @param failure original failure
     * @param generator tool name
     * @throws Exception when the failure is not an explicit validation failure
     */
    public static void exitOnExpectedError(Exception failure, String generator) throws Exception {
        if (!report(failure, generator, null, System.err)) throw failure;
        System.exit(2);
    }
}
