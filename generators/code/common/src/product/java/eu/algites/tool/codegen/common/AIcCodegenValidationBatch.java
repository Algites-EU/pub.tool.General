package eu.algites.tool.codegen.common;

import java.util.ArrayList;
import java.util.List;
import java.io.PrintStream;

/**
 * Validation policy shared by both Java generators without coupling them.
 *
 * @author linhart1
 */
public final class AIcCodegenValidationBatch {
    /** Qualified CLI key for the validation mode. */
    public static final String OPTION = "codegen-validate-one-input-at-a-time-only";
    /** Environment variable inherited from the universal bootstrap. */
    public static final String ENVIRONMENT = "MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY";
    private final boolean failFast;
    private final List<AIxCodegenValidationException> errors = new ArrayList<>();
    private final List<AIcdCodegenDiagnostic> diagnostics = new ArrayList<>();

    /**
     * Create a collector preserving fail-fast semantics unless requested otherwise.
     *
     * @param aFailFast true to stop after the first invalid input has been checked, false to collect
     */
    public AIcCodegenValidationBatch(boolean aFailFast) { this.failFast = aFailFast; }

    /**
     * Parse the exact Boolean syntax used in settings and bootstrap.
     *
     * @param aValue textual true/false, in lowercase
     * @return parsed mode
     * @throws AIxCodegenValidationException for invalid values
     */
    public static boolean parseBoolean(String aValue) {
        if ("true".equals(aValue)) return true;
        if ("false".equals(aValue)) return false;
        throw new AIxCodegenValidationException("--" + OPTION + " expects true or false: " + aValue,
                "Use --codegen-validate-one-input-at-a-time-only=true or =false.", null, "--" + OPTION);
    }

    /**
     * Read a validated, inherited bootstrap policy, defaulting to exhaustive validation.
     *
     * @return true when only the first failing input is to be reported
     * @throws AIxCodegenValidationException when the environment value is malformed
     */
    public static boolean defaultPolicy() {
        return parseBoolean(System.getenv().getOrDefault(ENVIRONMENT, "false"));
    }

    /**
     * Record a source-specific failure until the current input is fully checked.
     *
     * @param aError typed input validation failure
     * @param aSource current input source if not already supplied by the validator
     */
    public void add(AIxCodegenValidationException aError, String aSource) {
        AIxCodegenValidationException enriched = new AIxCodegenValidationException(
                aError.getMessage(), aError.getHint(),
                aError.getSource() != null ? aError.getSource() : aSource,
                aError.getLocation(), aError);
        errors.add(enriched);
        diagnostics.add(AIcdCodegenDiagnostic.fromError(enriched));
    }

    /**
     * Record a nonfatal diagnostic, or an ERROR through typed validation.
     *
     * @param severity one of DEBUG/INFO/WARNING/ERROR
     * @param message nonblank message
     * @param hint corrective advice (required for ERROR)
     * @param source input file or artifact, or null
     * @param location field or pointer, or null
     * @throws IllegalArgumentException if message/hint is invalid
     * @throws NullPointerException if severity or message is null
     */
    public void addDiagnostic(AInCodegenDiagnosticSeverity severity, String message,
            String hint, String source, String location) {
        var diagnostic = new AIcdCodegenDiagnostic(severity, message, hint, source, location);
        if (severity == AInCodegenDiagnosticSeverity.ERROR)
            add(new AIxCodegenValidationException(message, hint, source, location), source);
        else diagnostics.add(diagnostic);
    }

    /**
     * Record a DEBUG event, displayed only with diagnostic mode enabled.
     *
     * @param message nonblank explanation
     * @param source source filename, or null
     * @param location source location, or null
     */
    public void debug(String message, String source, String location) {
        addDiagnostic(AInCodegenDiagnosticSeverity.DEBUG, message, null, source, location);
    }

    /**
     * Record an informational message without invalidating the input.
     *
     * @param message nonblank explanation
     * @param source source filename, or null
     * @param location source location, or null
     */
    public void info(String message, String source, String location) {
        addDiagnostic(AInCodegenDiagnosticSeverity.INFO, message, null, source, location);
    }

    /**
     * Record a nonfatal warning with optional corrective advice.
     *
     * @param message nonblank explanation
     * @param hint optional corrective advice, or null
     * @param source source filename, or null
     * @param location source location, or null
     */
    public void warning(String message, String hint, String source, String location) {
        addDiagnostic(AInCodegenDiagnosticSeverity.WARNING, message, hint, source, location);
    }

    /**
     * Emit collected informational and warning diagnostics on a successful run.
     *
     * @param generator label for the reporting tool
     * @param output destination stream, which must not be null
     * @throws NullPointerException if output is null
     */
    public void reportNonErrors(String generator, PrintStream output) {
        AIcCodegenDiagnostics.reportDiagnostics(diagnostics.stream()
                .filter(aDiagnostic -> aDiagnostic.severity() != AInCodegenDiagnosticSeverity.ERROR)
                .toList(), generator, output);
    }

    /**
     * Complete the independent checks of a single input before optional early exit.
     *
     * @param aSource fully qualified source path used when adding input errors
     * @throws AIxCodegenValidationException if this input has exactly one issue
     * @throws AIxCodegenBatchValidationException if this input has multiple issues
     */
    public void finishInput(String aSource) {
        if (!failFast) return;
        List<AIxCodegenValidationException> locMatches = errors.stream()
                .filter(aError -> java.util.Objects.equals(aError.getSource(), aSource)).toList();
        if (!locMatches.isEmpty()) {
            List<AIcdCodegenDiagnostic> locIncluded = diagnostics.stream()
                    .filter(aDiagnostic -> aDiagnostic.severity() != AInCodegenDiagnosticSeverity.ERROR
                            || java.util.Objects.equals(aDiagnostic.source(), aSource)).toList();
            if (locMatches.size() == 1 && locIncluded.size() == 1) throw locMatches.get(0);
            throw new AIxCodegenBatchValidationException(locMatches, locIncluded);
        }
    }

    /**
     * Abort after all input validation is finished if any input was invalid.
     *
     * @throws AIxCodegenValidationException for exactly one issue
     * @throws AIxCodegenBatchValidationException for multiple issues
     */
    public void finish() {
        if (errors.isEmpty()) return;
        List<AIxCodegenValidationException> locReported = failFast
                ? errors.stream().filter(aError -> java.util.Objects.equals(
                        aError.getSource(), errors.get(0).getSource())).toList()
                : errors;
        List<AIcdCodegenDiagnostic> locIncluded = failFast
                ? diagnostics.stream().filter(aDiagnostic ->
                        aDiagnostic.severity() != AInCodegenDiagnosticSeverity.ERROR
                        || java.util.Objects.equals(aDiagnostic.source(), errors.get(0).getSource())).toList()
                : diagnostics;
        if (locReported.size() == 1 && locIncluded.size() == 1) throw locReported.get(0);
        throw new AIxCodegenBatchValidationException(locReported, locIncluded);
    }
}
