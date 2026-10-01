package eu.algites.tool.codegen.defs;

import java.io.IOException;

/** Reusable programmatic defs-codegen entry point. */
public interface AIiDefsCodegenService {
    /**
     * Loads one source definition into the normalized canonical-definition model.
     *
     * @param request definition load request
     * @return normalized canonical definition
     * @throws IOException if the selected frontend cannot load the source
     */
    AIcdCanonicalDefinition load(AIcdDefinitionLoadRequest request) throws IOException;

    /**
     * Generates one source artifact from a normalized canonical definition.
     *
     * @param request code-generation request
     * @return generated source artifact
     */
    AIcdGeneratedSource generate(AIcdCodeGenerationRequest request);
}
