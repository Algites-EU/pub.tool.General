package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * Exact input provenance of one canonical node. Source locations are not converted
 * to generated identifiers and are preserved through normalization.
 *
 * @param sourceResource original source resource path or URL
 * @param sourcePointer exact path within the source, such as JSON Pointer or XPath
 * @param representationKind the original construct, for example properties, items, or xs:element
 */
public record AIcdDefsCodegenSourceBinding(String sourceResource, String sourcePointer, String representationKind) {
    /** Validates the binding's exact location and keeps the original representation label. */
    public AIcdDefsCodegenSourceBinding {
        Objects.requireNonNull(sourceResource, "sourceResource");
        Objects.requireNonNull(sourcePointer, "sourcePointer");
        Objects.requireNonNull(representationKind, "representationKind");
        if (sourceResource.isBlank()) {
            throw new IllegalArgumentException("sourceResource must not be blank");
        }
    }
}

