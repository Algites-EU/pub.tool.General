package eu.algites.tool.codegen.common;

/**
 * An expected validation failure in a Defs or SDO generator.
 *
 * <p>The inherited message preserves the original failure text without adding
 * formatting or advice. The separately available hint explains how the caller
 * can correct the input. The optional source and location identify the failing
 * declaration without changing the message. This exception intentionally
 * extends {@link IllegalArgumentException} to preserve callers' existing
 * exception handling contracts.</p>
 *
 * @author linhart1
 */
public final class AIxCodegenValidationException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    private final String hint;
    private final String source;
    private final String location;

    /**
     * Creates a validation failure with an explicit remediation hint.
     *
     * @param message unchanged original validation message; must not be null
     * @param hint actionable correction for the problem; must not be blank
     * @throws NullPointerException if message or hint is null
     * @throws IllegalArgumentException if hint is blank
     */
    public AIxCodegenValidationException(String message, String hint) {
        this(message, hint, null, null, null);
    }

    /**
     * Creates a validation failure tied to a particular source and location.
     *
     * @param message unchanged original validation message
     * @param hint actionable correction for the problem
     * @param source schema, settings file, or artifact name, or null if unknown
     * @param location XPath, JSON Pointer, field, or option, or null if unknown
     * @throws NullPointerException if message or hint is null
     * @throws IllegalArgumentException if hint is blank
     */
    public AIxCodegenValidationException(String message, String hint, String source, String location) {
        this(message, hint, source, location, null);
    }

    /**
     * Creates a validation failure while retaining its original cause.
     *
     * @param message unchanged original validation message
     * @param hint actionable correction for the problem
     * @param source schema, settings file, or artifact name, or null if unknown
     * @param location XPath, JSON Pointer, field, or option, or null if unknown
     * @param cause original failure, or null when no cause exists
     * @throws NullPointerException if message or hint is null
     * @throws IllegalArgumentException if hint is blank
     */
    public AIxCodegenValidationException(String message, String hint, String source,
            String location, Throwable cause) {
        super(java.util.Objects.requireNonNull(message, "message"), cause);
        this.hint = java.util.Objects.requireNonNull(hint, "hint");
        if (hint.isBlank()) throw new IllegalArgumentException("Validation hint must not be blank");
        this.source = source;
        this.location = location;
    }

    /** @return explicit remediation instructions for this validation failure */
    public String getHint() { return hint; }

    /** @return source artifact or file, or null if it is unknown */
    public String getSource() { return source; }

    /** @return source declaration, field, or path, or null if it is unknown */
    public String getLocation() { return location; }
}
