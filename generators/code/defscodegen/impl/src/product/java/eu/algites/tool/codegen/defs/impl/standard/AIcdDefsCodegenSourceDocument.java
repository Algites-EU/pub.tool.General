package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AInDefsCodegenSourceInputKind;
import java.util.Map;
import java.util.Objects;

/**
 * One source document to the canonical Defs compiler pipeline. The content is
 * namespace-aware XSD XML text for XMLDEFS, or a parsed string-keyed map of JSON
 * Schema/YAML Schema fields for JSONDEFS and YAMLDEFS. The resource identifies
 * the actual input file and remains attached to all source bindings.
 *
 * @param kind explicit source technology; never inferred from filename suffix
 * @param resource source URI or original source filename, nonempty
 * @param content XSD string for XMLDEFS or a parsed Map for JSONDEFS/YAMLDEFS
 */
public record AIcdDefsCodegenSourceDocument(AInDefsCodegenSourceInputKind kind,
        String resource, Object content) {
    /**
     * Validates the source family, resource and representation before loading.
     *
     * @throws NullPointerException if kind, resource or content is null
     * @throws IllegalArgumentException if the resource or value type is inappropriate
     */
    public AIcdDefsCodegenSourceDocument {
        Objects.requireNonNull(kind, "kind");
        Objects.requireNonNull(resource, "resource");
        Objects.requireNonNull(content, "content");
        if (resource.isBlank()) throw new IllegalArgumentException("Source resource cannot be empty");
        if (kind == AInDefsCodegenSourceInputKind.XMLDEFS) {
            if (!(content instanceof String)) {
                throw new IllegalArgumentException("XMLDEFS requires XSD XML source text");
            }
        } else if (!(content instanceof Map<?, ?>)) {
            throw new IllegalArgumentException("JSONDEFS and YAMLDEFS require parsed source maps");
        }
    }
}
