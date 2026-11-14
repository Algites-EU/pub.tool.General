package eu.algites.tool.codegen.common;

import java.util.Objects;

/**
 * Immutable diagnostic with severity and optional source provenance.
 * The message is kept separate from the remediation hint and location.
 *
 * @param severity ordered diagnostic severity; must not be null
 * @param message nonblank explanation of the observed condition
 * @param hint suggested correction; required for errors, optional otherwise
 * @param source source path or artifact identifier, or null if unknown
 * @param location XPath/JSON Pointer/declaration, or null if unknown
 * @author linhart1
 */
public record AIcdCodegenDiagnostic(AInCodegenDiagnosticSeverity severity, String message,
        String hint, String source, String location) {
    /**
     * Validates a structured diagnostic without altering its original message.
     *
     * @throws NullPointerException if severity or message is null
     * @throws IllegalArgumentException if message is blank, or an error has no hint
     */
    public AIcdCodegenDiagnostic {
        Objects.requireNonNull(severity, "severity");
        Objects.requireNonNull(message, "message");
        if (message.isBlank()) throw new IllegalArgumentException("Diagnostic message must not be blank");
        if (severity == AInCodegenDiagnosticSeverity.ERROR && (hint == null || hint.isBlank()))
            throw new IllegalArgumentException("Error diagnostics require an actionable hint");
    }

    /**
     * Convert an existing validation exception without changing its semantics.
     *
     * @param error nonnull validation exception with source and hint
     * @return severity ERROR diagnostic retaining the original text
     * @throws NullPointerException if error is null
     */
    public static AIcdCodegenDiagnostic fromError(AIxCodegenValidationException error) {
        Objects.requireNonNull(error, "error");
        return new AIcdCodegenDiagnostic(AInCodegenDiagnosticSeverity.ERROR,
                error.getMessage(), error.getHint(), error.getSource(), error.getLocation());
    }
}
