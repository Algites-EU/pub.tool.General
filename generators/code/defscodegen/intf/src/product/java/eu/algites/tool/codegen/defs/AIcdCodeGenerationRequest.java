package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;


import java.util.Objects;

/**
 * Request to render one normalized definition into program source.
 *
 * @param definition normalized canonical definition
 * @param target target programming technology
 * @param packageName target package or module namespace
 * @param namingProfile input/output naming and version profile
 * @param xmlTypeQName expanded QName of the declared named XSD type, or {@code null}
 *                     when the definition does not represent an XSD named type
 */
public record AIcdCodeGenerationRequest(
        AIcdCanonicalDefinition definition,
        AInCodeGenerationTarget target,
        String packageName,
        AIiNameConventionCatalog namingProfile,
        String xmlTypeQName) {
    /**
     * Creates a code generation request without explicit XSD type identity.
     * The four-argument form remains appropriate for JSON/YAML definitions and
     * standalone canonical types that do not have a source XSD declaration.
     *
     * @param definition format-neutral definition to render
     * @param target native language of the generated source
     * @param packageName destination business package
     * @param namingProfile naming convention used for all generated declarations
     */
    public AIcdCodeGenerationRequest(AIcdCanonicalDefinition definition,
            AInCodeGenerationTarget target, String packageName,
            AIiNameConventionCatalog namingProfile) {
        this(definition, target, packageName, namingProfile, null);
    }

    /** Validates and normalizes the supplied data-object components. */
    public AIcdCodeGenerationRequest {
        Objects.requireNonNull(definition, "definition");
        Objects.requireNonNull(target, "target");
        Objects.requireNonNull(packageName, "packageName");
        Objects.requireNonNull(namingProfile, "namingProfile");
        if (xmlTypeQName != null && (definition.sourceKind() != AInDefinitionSourceKind.XMLDEFS
                || !xmlTypeQName.startsWith("{") || xmlTypeQName.indexOf('}') <= 0
                || xmlTypeQName.endsWith("}")))
            throw new IllegalArgumentException("XML type QName must be an expanded XSD named type: " + xmlTypeQName);
    }
}
