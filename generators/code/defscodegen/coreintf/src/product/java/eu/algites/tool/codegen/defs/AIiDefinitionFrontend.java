package eu.algites.tool.codegen.defs;

import java.io.IOException;

/** Source-format frontend that maps one definition family to the normalized model. */
public interface AIiDefinitionFrontend {
    /**
     * Returns the definition source family handled by this frontend.
     *
     * @return supported definition source kind
     */
    AInDefinitionSourceKind sourceKind();

    /**
     * Loads one source definition into the normalized canonical-definition model.
     *
     * @param request definition load request
     * @return normalized canonical definition
     * @throws IOException if the source cannot be loaded
     */
    AIcdCanonicalDefinition load(AIcdDefinitionLoadRequest request) throws IOException;
}
