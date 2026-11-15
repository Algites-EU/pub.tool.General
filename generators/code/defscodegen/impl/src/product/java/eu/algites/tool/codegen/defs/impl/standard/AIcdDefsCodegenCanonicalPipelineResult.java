package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Finalized canonical graph together with its schema-compatible generated contract
 * payload. Both fields have already passed reference linking, merge validation,
 * and unnormalized-contract schema validation in that order.
 *
 * @param types linked and normalized declarations in stable input order
 * @param payload JSON-compatible generated-contract representation for downstream codegen
 */
public record AIcdDefsCodegenCanonicalPipelineResult(List<AIcDefsCanonicalType> types,
        Map<String, Object> payload) {
    /**
     * Requires complete non-null results and copies the outer declaration list.
     *
     * @throws NullPointerException if types or payload is null
     */
    public AIcdDefsCodegenCanonicalPipelineResult {
        types = List.copyOf(Objects.requireNonNull(types, "types"));
        payload = Map.copyOf(Objects.requireNonNull(payload, "payload"));
    }
}
