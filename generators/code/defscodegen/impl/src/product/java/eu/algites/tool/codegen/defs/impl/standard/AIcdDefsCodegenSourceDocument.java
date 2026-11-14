package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
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
 * @param rootName type-local identifier extracted by the selected source filename naming convention
 * @param sourceVersion version extracted by the selected source filename naming convention
 * @author linhart1
 */
public record AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1 kind,
        String resource, Object content, String rootName, String sourceVersion) {
    /**
     * Create a source document for a direct frontend caller without a selected filename profile.
     * CLI production callers supply both parsed naming values explicitly.
     * @param kind source technology
     * @param resource exact source path
     * @param content typed schema content
     */
    public AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1 kind, String resource, Object content) {
        this(kind, resource, content, "", "");
    }

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
        Objects.requireNonNull(rootName, "rootName");
        Objects.requireNonNull(sourceVersion, "sourceVersion");
        if (resource.isBlank()) throw new IllegalArgumentException("Source resource cannot be empty");
        if (kind == AIngSourceInputKind_1.XMLDEFS) {
            if (!(content instanceof String)) {
                throw new IllegalArgumentException("XMLDEFS requires XSD XML source text");
            }
        } else if (!(content instanceof Map<?, ?>)) {
            throw new IllegalArgumentException("JSONDEFS and YAMLDEFS require parsed source maps");
        }
    }
}
