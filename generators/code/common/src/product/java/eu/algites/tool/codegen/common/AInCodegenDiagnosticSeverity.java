package eu.algites.tool.codegen.common;

/**
 * Increasing levels of source-located Codegen diagnostics.
 * Only {@link #ERROR} invalidates a Codegen run; debug output is opt-in.
 *
 * @author linhart1
 */
public enum AInCodegenDiagnosticSeverity {
    /** Developer-only details, shown when ALGITES_CODEGEN_DEBUG is enabled. */
    DEBUG,
    /** Progress or explanatory information without a validation failure. */
    INFO,
    /** Recoverable issue that does not prevent generation. */
    WARNING,
    /** Input/configuration failure that prevents publishing generated output. */
    ERROR
}
