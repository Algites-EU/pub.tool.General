package eu.algites.tool.codegen.defs;

import java.util.List;
import java.util.Objects;

/**
 * Generated source unit with explicit importable type identities.
 *
 * @param typeName name of the primary generated source type
 * @param relativePath path relative to the generated source root
 * @param source generated native source text
 * @param generatedTypes importable public types declared in the source
 */
public record AIcdGeneratedSource(
        String typeName, String relativePath, String source,
        List<AIcdGeneratedTypeIdentity> generatedTypes) {

    /** Validates and defensively copies the source metadata. */
    public AIcdGeneratedSource {
        Objects.requireNonNull(typeName, "typeName");
        Objects.requireNonNull(relativePath, "relativePath");
        Objects.requireNonNull(source, "source");
        generatedTypes = List.copyOf(Objects.requireNonNull(generatedTypes, "generatedTypes"));
    }

    /** Compatibility constructor for legacy consumers and non-type source units. */
    public AIcdGeneratedSource(String aTypeName, String aRelativePath, String aSource) {
        this(aTypeName, aRelativePath, aSource, List.of());
    }

    /** Resolves the primary generated type without parsing source text. */
    public AIcdGeneratedTypeIdentity primaryType() {
        return generatedTypes.stream().filter(aType -> aType.typeName().equals(typeName))
                .findFirst().orElseThrow(() -> new IllegalStateException("Primary generated type identity missing: " + typeName));
    }
}
