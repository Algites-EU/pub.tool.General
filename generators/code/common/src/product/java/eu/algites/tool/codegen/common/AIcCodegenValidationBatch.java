package eu.algites.tool.codegen.common;

import java.util.ArrayList;
import java.util.List;

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

    /**
     * Create a collector preserving fail-fast semantics unless requested otherwise.
     *
     * @param aFailFast true to throw at the first input error, false to collect
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
     * Read a validated, inherited bootstrap policy, defaulting to legacy fail-fast.
     *
     * @return true when only the first failing input is to be reported
     * @throws AIxCodegenValidationException when the environment value is malformed
     */
    public static boolean defaultPolicy() {
        return parseBoolean(System.getenv().getOrDefault(ENVIRONMENT, "true"));
    }

    /**
     * Add a source-specific failure or throw it immediately in fail-fast mode.
     *
     * @param aError typed input validation failure
     * @param aSource current input source if not already supplied by the validator
     */
    public void add(AIxCodegenValidationException aError, String aSource) {
        AIxCodegenValidationException enriched = new AIxCodegenValidationException(
                aError.getMessage(), aError.getHint(),
                aError.getSource() != null ? aError.getSource() : aSource,
                aError.getLocation(), aError);
        if (failFast) throw enriched;
        errors.add(enriched);
    }

    /**
     * Abort after all input validation is finished if any input was invalid.
     *
     * @throws AIxCodegenBatchValidationException for accumulated errors
     */
    public void finish() {
        if (!errors.isEmpty()) throw new AIxCodegenBatchValidationException(errors);
    }
}
