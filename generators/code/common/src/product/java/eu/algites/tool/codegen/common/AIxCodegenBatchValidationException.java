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

    /**
     * Constructs an ordered report.
     *
     * @param errors nonempty input errors with source provenance
     * @throws IllegalArgumentException when no failures are supplied
     * @throws NullPointerException when the list is null
     */
    public AIxCodegenBatchValidationException(List<AIxCodegenValidationException> errors) {
        super(Objects.requireNonNull(errors, "errors").size() + " input validation error(s)");
        if (errors.isEmpty()) throw new IllegalArgumentException("An empty validation report is not a failure");
        this.issues = List.copyOf(errors);
    }

    /** @return ordered, immutable list of all reported input failures */
    public List<AIxCodegenValidationException> issues() { return issues; }
}
