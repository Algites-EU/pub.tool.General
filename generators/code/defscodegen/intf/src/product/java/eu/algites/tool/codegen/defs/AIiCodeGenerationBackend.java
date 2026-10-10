package eu.algites.tool.codegen.defs;

/** Program-source backend for one target technology. */
public interface AIiCodeGenerationBackend {
    /**
     * Returns the target technology handled by this backend.
     *
     * @return supported code-generation target
     */
    AInCodeGenerationTarget target();

    /**
     * Generates one source artifact from a normalized canonical definition.
     *
     * @param request code-generation request
     * @return generated source artifact
     */
    AIcdGeneratedSource generate(AIcdCodeGenerationRequest request);
}
