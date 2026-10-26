package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * Binds semantic Defs output roles to externally supplied catalog identifiers.
 *
 * <p>The catalog is agnostic about the spelling or versioning of identifiers;
 * missing role bindings are rejected rather than replaced with Algites defaults.
 */
final class AIcSelectedNamingCatalog implements AIiNameConventionCatalog {
    private final AIiNameConventionCatalog catalog;
    private final Map<AInDefsNameRole, String> roles;

    /**
     * Selects naming profiles for a single schema contract family.
     * @param aCatalog fully loaded merged naming catalog
     * @param aRoles explicit target profiles keyed by semantic generated names
     */
    AIcSelectedNamingCatalog(AIiNameConventionCatalog aCatalog,
            Map<AInDefsNameRole, String> aRoles) {
        catalog = Objects.requireNonNull(aCatalog, "catalog");
        roles = Map.copyOf(Objects.requireNonNull(aRoles, "roles"));
        for (String locName : roles.values()) {
            if (!catalog.names().contains(locName))
                throw new IllegalArgumentException("Naming convention not found: " + locName);
        }
    }

    /**
     * Resolves the named role against the explicit source-to-target binding.
     * @param aRole name of the generated type or its output file
     * @return exact configured catalog ID for this role
     */
    String selected(AInDefsNameRole aRole) {
        String locName = roles.get(aRole);
        if (locName == null) throw new IllegalArgumentException("Missing configured naming role: " + aRole);
        return locName;
    }

    /** {@inheritDoc} */
    @Override public String schemaMetadataField(String aProfile, String aSide, String aKind) {
        return catalog.schemaMetadataField(aProfile, aSide, aKind);
    }
    /** {@inheritDoc} */
    @Override public Set<String> names() { return catalog.names(); }
    /** {@inheritDoc} */
    @Override public String format(String aProfile, String aStructure, Map<String, String> aValues,
            String aSourceIdentifierConvention) {
        return catalog.format(aProfile, aStructure, aValues, aSourceIdentifierConvention);
    }
    /** {@inheritDoc} */
    @Override public Map<String, String> parse(String aProfile, String aStructure, String aName) {
        return catalog.parse(aProfile, aStructure, aName);
    }
    /** {@inheritDoc} */
    @Override public boolean matches(String aProfile, String aStructure, String aName) {
        return catalog.matches(aProfile, aStructure, aName);
    }
}
