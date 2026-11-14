package eu.algites.tool.codegen.common;

import java.io.PrintStream;
import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

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
        Throwable batch = error;
        while (batch != null && !(batch instanceof AIxCodegenBatchValidationException))
            batch = batch.getCause();
        if (batch instanceof AIxCodegenBatchValidationException report) {
            reportDiagnostics(report.diagnostics(), generator, output);
            return true;
        }
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
     * Write collected diagnostics in severity order, with counters local to each
     * section and to each source file. Debug is suppressed unless explicitly enabled.
     * Unknown sources are not grouped together as a fictitious common file.
     *
     * @param diagnostics possibly empty structured messages from one generator run
     * @param generator generator name for the header
     * @param output stream receiving the text
     * @return true when at least one visible message was printed
     * @throws NullPointerException if diagnostics or output is null
     */
    public static boolean reportDiagnostics(List<AIcdCodegenDiagnostic> diagnostics,
            String generator, PrintStream output) {
        java.util.Objects.requireNonNull(diagnostics, "diagnostics");
        java.util.Objects.requireNonNull(output, "output");
        boolean printed = false;
        for (AInCodegenDiagnosticSeverity level : AInCodegenDiagnosticSeverity.values()) {
            if (level == AInCodegenDiagnosticSeverity.DEBUG && !debugEnabled()) continue;
            List<AIcdCodegenDiagnostic> issues = new ArrayList<>();
            for (AIcdCodegenDiagnostic issue : diagnostics)
                if (issue.severity() == level) issues.add(issue);
            if (issues.isEmpty()) continue;
            printed = true;
            String title = switch (level) {
                case DEBUG -> "DEBUG";
                case INFO -> "INFO";
                case WARNING -> "VALIDATION WARNINGS";
                case ERROR -> "VALIDATION ERRORS";
            };
            String unit = level == AInCodegenDiagnosticSeverity.DEBUG
                    || level == AInCodegenDiagnosticSeverity.INFO ? "message(s)" : "issue(s)";
            output.println("\n  " + title + " - " + generator + ": " + issues.size() + " " + unit);
            Map<String, Integer> totalBySource = new HashMap<>();
            for (AIcdCodegenDiagnostic issue : issues)
                if (issue.source() != null && !issue.source().isBlank())
                    totalBySource.merge(issue.source(), 1, Integer::sum);
            Map<String, Integer> seenBySource = new HashMap<>();
            int index = 0;
            for (AIcdCodegenDiagnostic issue : issues) {
                int position = 1;
                int sourceTotal = 1;
                if (issue.source() != null && !issue.source().isBlank()) {
                    position = seenBySource.merge(issue.source(), 1, Integer::sum);
                    sourceTotal = totalBySource.get(issue.source());
                }
                output.println("\n  [" + (++index) + "/" + issues.size() + "] (" + position
                        + "/" + sourceTotal + ") " + issue.message());
                if (issue.source() != null) output.println("  Source: " + issue.source());
                if (issue.location() != null) output.println("  Location: " + issue.location());
                if (issue.hint() != null && !issue.hint().isBlank())
                    output.println("  Hint: " + issue.hint());
            }
        }
        if (printed) output.println();
        return printed;
    }

    /** @return whether developer debug diagnostics were enabled explicitly */
    private static boolean debugEnabled() {
        String value = System.getenv("ALGITES_CODEGEN_DEBUG");
        return "1".equals(value) || "true".equalsIgnoreCase(value)
                || "yes".equalsIgnoreCase(value) || "on".equalsIgnoreCase(value);
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
