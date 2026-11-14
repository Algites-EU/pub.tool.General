package eu.algites.tool.codegen.common;

import java.util.List;
import java.util.Objects;

/**
 * Aggregated input validation failures from a single independent Codegen run.
 * No generated output may be published after this exception is thrown.
 *
 * @author linhart1
 */
public final class AIxCodegenBatchValidationException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    private final List<AIxCodegenValidationException> issues;
    private final List<AIcdCodegenDiagnostic> diagnostics;

    /**
     * Constructs an ordered report.
     *
     * @param errors nonempty input errors with source provenance
     * @throws IllegalArgumentException when no failures are supplied
     * @throws NullPointerException when the list is null
     */
    public AIxCodegenBatchValidationException(List<AIxCodegenValidationException> errors) {
        this(errors, Objects.requireNonNull(errors, "errors").stream()
                .map(AIcdCodegenDiagnostic::fromError).toList());
    }

    /**
     * Constructs a report retaining nonfatal messages before the errors.
     *
     * @param errors nonempty input errors with source provenance
     * @param allDiagnostics ordered diagnostics containing the errors and any preceding messages
     * @throws IllegalArgumentException when there are no failures
     * @throws NullPointerException when either list is null or contains null
     */
    public AIxCodegenBatchValidationException(List<AIxCodegenValidationException> errors,
            List<AIcdCodegenDiagnostic> allDiagnostics) {
        super(Objects.requireNonNull(errors, "errors").size() + " input validation error(s)");
        if (errors.isEmpty()) throw new IllegalArgumentException("An empty validation report is not a failure");
        this.issues = List.copyOf(errors);
        this.diagnostics = List.copyOf(Objects.requireNonNull(allDiagnostics, "allDiagnostics"));
    }

    /** @return ordered, immutable list of all reported input failures */
    public List<AIxCodegenValidationException> issues() { return issues; }

    /** @return ordered immutable diagnostics, including warnings and errors */
    public List<AIcdCodegenDiagnostic> diagnostics() { return diagnostics; }
}
