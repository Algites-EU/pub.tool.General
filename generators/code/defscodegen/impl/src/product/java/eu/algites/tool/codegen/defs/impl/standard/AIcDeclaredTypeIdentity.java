package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import java.util.Map;
import java.util.Objects;

/**
 * Converts declared XML, JSON, and YAML source type identifiers into the same
 * canonical local identifier without discarding the owning schema identity.
 * The input must first satisfy the selected source naming convention; no
 * punctuation- or case-based recovery of malformed declarations is permitted.
 *
 * <p>The schema URI, JSON Pointer, or XML QName remains the nominal identity.
 * This conversion changes only the local identifier used for generated names.</p>
 *
 * @author linhart1
 */
final class AIcDeclaredTypeIdentity {
    /** Prevents instances of a stateless conversion utility. */
    private AIcDeclaredTypeIdentity() { }

    /**
     * Validate and convert a declared local type identifier reversibly.
     *
     * @param catalog exact configured naming catalog for this schema family
     * @param profile source schema profile selected from the generator manifest
     * @param name unmodified type name from a global XSD type or a named $defs entry
     * @return canonical lower-kebab-case local identifier, not a qualified type identity
     * @throws NullPointerException if any input is null
     * @throws IllegalArgumentException if the source type naming rule is missing,
     *         the name violates it, or converting to the canonical form loses data
     */
    static String canonicalTypeIdentifier(AIiNameConventionCatalog catalog, String profile, String name) {
        Objects.requireNonNull(catalog, "catalog");
        Objects.requireNonNull(profile, "profile");
        Objects.requireNonNull(name, "name");
        Map<String, String> parsed = catalog.parse(profile, "type_name", name);
        String lexical = catalog.identifierConvention(profile, "type_name");
        if (lexical == null || lexical.isBlank())
            throw new IllegalArgumentException("Source type naming profile has no identifier convention: " + profile);
        String identifier = parsed.get("identifier");
        if (identifier == null || identifier.isBlank())
            throw new IllegalArgumentException("Source type naming profile does not capture identifier: " + profile);
        String canonical = catalog.convertIdentifierByDeclaredStyle(identifier, lexical, "lower_kebab_case_1");
        String restored = catalog.convertIdentifierByDeclaredStyle(canonical, "lower_kebab_case_1", lexical);
        if (!restored.equals(identifier))
            throw new IllegalArgumentException("Non-round-trippable declared type name: " + name + " -> " + restored);
        return canonical;
    }
}
