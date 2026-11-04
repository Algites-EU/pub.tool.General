package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenType;
import eu.algites.tool.codegen.defs.AInDefsCodegenSourceInputKind;
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
        this.frontend = new AIcDefsCodegenCanonicalSchemaFrontend(
                Objects.requireNonNull(naming, "naming"));
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
        Objects.requireNonNull(documents, "documents");
        List<AIcdDefsCodegenType> sourceTypes = new ArrayList<>();
        for (AIcdDefsCodegenSourceDocument document : documents) {
            Objects.requireNonNull(document, "source document");
            if (document.kind() == AInDefsCodegenSourceInputKind.XMLDEFS) {
                sourceTypes.addAll(frontend.loadXsd((String) document.content(), document.resource()));
            } else {
                @SuppressWarnings("unchecked")
                Map<String, Object> schema = (Map<String, Object>) document.content();
                sourceTypes.addAll(frontend.loadJsonOrYamlTypes(schema, document.resource(), document.kind()));
            }
        }
        if (sourceTypes.isEmpty()) {
            throw new IllegalArgumentException("No canonical TYPE declarations found in source documents");
        }
        var merged = AIcDefsCodegenCanonicalModelMerger.merge(sourceTypes);
        var linked = AIcDefsCodegenCanonicalModelLinker.link(merged, validateContract);
        return new AIcdDefsCodegenCanonicalPipelineResult(linked,
                AIcDefsCodegenCanonicalContractPayload.emit(linked));
    }
}
