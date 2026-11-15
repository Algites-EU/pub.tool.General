package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.model.AIngSourceInputKind_1;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Consumer;

/**
 * Coordinates the native Java canonical Defs compiler frontends, provenance-safe
 * merging, reference linking, schema-contract validation, and final normalization.
 * The old generator is intentionally not called or imported by this pipeline.
 */
public final class AIcDefsCodegenCanonicalPipeline {
    /** Source-schema parser configured by the explicit Common+Defs naming profile. */
    private final AIcDefsCodegenCanonicalSchemaFrontend frontend;
    /** Required validator supplied by the compiler's JSON Schema implementation. */
    private final Consumer<Map<String, Object>> validateContract;

    /**
     * Creates a new native compiler pipeline whose callback checks the actual
     * generated canonical-model schema before normalization takes place.
     *
     * @param naming validated Common/Defs synthetic-type naming profile
     * @param validateContract mandatory schema validation callback; errors propagate
     * @throws NullPointerException when naming or validation callback is missing
     */
    public AIcDefsCodegenCanonicalPipeline(AIcCodegenNamingProfileResolver.Profile naming,
            Consumer<Map<String, Object>> validateContract) {
        this(naming, validateContract, java.util.Set.of());
    }

    /**
     * Prepare a native schema frontend with externally verified XSD QName names.
     * @param naming selected Common and Defs naming profile
     * @param validateContract canonical-model validation callback
     * @param importedXsdTypes QNames returned by a trusted schema resolver
     * @throws NullPointerException on missing parameters
     */
    public AIcDefsCodegenCanonicalPipeline(AIcCodegenNamingProfileResolver.Profile naming,
            Consumer<Map<String, Object>> validateContract, java.util.Set<String> importedXsdTypes) {
        this(naming, validateContract, importedXsdTypes, Map.of());
    }

    /**
     * Initialize a canonical pipeline with verified imported XSD documents.
     * @param naming resolved naming profile
     * @param validateContract contract validator
     * @param importedXsdTypes imported type identities
     * @param importedXsdDocuments source URI to verified XSD text
     */
    public AIcDefsCodegenCanonicalPipeline(AIcCodegenNamingProfileResolver.Profile naming,
            Consumer<Map<String, Object>> validateContract, java.util.Set<String> importedXsdTypes,
            Map<String, String> importedXsdDocuments) {
        this.frontend = new AIcDefsCodegenCanonicalSchemaFrontend(
                Objects.requireNonNull(naming, "naming"), Objects.requireNonNull(importedXsdTypes, "importedXsdTypes"),
                Objects.requireNonNull(importedXsdDocuments, "importedXsdDocuments"));
        this.validateContract = Objects.requireNonNull(validateContract, "validateContract");
    }

    /**
     * Processes a heterogeneous, ordered batch of source documents. Input-format
     * frontends retain their individual source bindings; equivalent logical IDs
     * are merged and validated before the graph is normalized for code generation.
     *
     * @param documents typed source documents with parsed JSON/YAML or XSD text
     * @return normalized and reference-linked graph plus a schema-compatible payload
     * @throws NullPointerException for null input
     * @throws IllegalArgumentException for empty batches, unsupported source documents,
     *         incompatible models, cyclic inheritance, or unresolved type references
     */
    public AIcdDefsCodegenCanonicalPipelineResult process(List<AIcdDefsCodegenSourceDocument> documents) {
        return process(documents, java.util.Set.of());
    }

    /**
     * Compile a batch with explicitly verified, existing parent identities.
     * @param documents schema inputs to generate, excluding reference-only parents
     * @param externalParentIds accepted parent identities, not source declarations
     * @return validated, linked canonical model without emitting external contracts
     * @throws IllegalArgumentException on missing parent references
     * @throws NullPointerException for null inputs
     */
    public AIcdDefsCodegenCanonicalPipelineResult process(List<AIcdDefsCodegenSourceDocument> documents,
            java.util.Set<String> externalParentIds) {
        Objects.requireNonNull(documents, "documents");
        Objects.requireNonNull(externalParentIds, "externalParentIds");
        List<AIcDefsCanonicalType> sourceTypes = new ArrayList<>();
        Map<String, String> documentUris = new java.util.LinkedHashMap<>();
        for (AIcdDefsCodegenSourceDocument document : documents) {
            Objects.requireNonNull(document, "source document");
            try {
                if (document.kind() == AIngSourceInputKind_1.XMLDEFS) {
                    sourceTypes.addAll(frontend.loadXsd((String) document.content(), document.resource(), document.sourceVersion()));
                } else {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> schema = (Map<String, Object>) document.content();
                    if (schema.get("$id") instanceof String uri && !uri.isBlank()) {
                        documentUris.put(document.resource(), uri);
                    }
                    sourceTypes.addAll(frontend.loadJsonOrYamlTypes(schema, document.resource(), document.kind(),
                            document.rootName(), document.sourceVersion()));
                }
            } catch (IllegalArgumentException | ClassCastException | UnsupportedOperationException exception) {
                // Frontend messages retain their JSON Pointer or XML location;
                // prepend the originating file when processing multi-source batches.
                throw new IllegalArgumentException(document.resource() + ": "
                        + exception.getMessage(), exception);
            }
        }
        if (sourceTypes.isEmpty()) {
            throw new IllegalArgumentException("No canonical TYPE declarations found in source documents");
        }
        var merged = AIcDefsCodegenCanonicalModelMerger.merge(sourceTypes);
        var linked = AIcDefsCodegenCanonicalModelLinker.link(
                merged, validateContract, externalParentIds, documentUris);
        return new AIcdDefsCodegenCanonicalPipelineResult(linked,
                AIcDefsCodegenCanonicalContractPayload.emit(linked));
    }
}
