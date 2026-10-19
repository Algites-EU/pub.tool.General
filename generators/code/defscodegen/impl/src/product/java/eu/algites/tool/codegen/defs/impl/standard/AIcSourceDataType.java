package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdDefinitionReference;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import java.util.List;
import java.util.Objects;

/**
 * Converts source-format reader hints to a recursive canonical type before creating a definition.
 * Parsing hints are intentionally internal to Defs Codegen and never part of the canonical API.
 */
final class AIcSourceDataType {
    private AIcSourceDataType() { }

    /**
     * Translate a schema reader's primitive kind, optional array item and reference
     * into a single recursive node before a canonical member is constructed.
     * These source hints are never retained as parallel canonical fields.
     */
    static AIcdDataType fromSourceHints(AInDataTypeKind aKind, AInDataTypeKind aItemKind,
            AIcdDefinitionReference aReference, AIcdValueConstraints aConstraints,
            AIcdValueConstraints aItemConstraints) {
        if (aKind == AInDataTypeKind.ARRAY) {
            AIcdDataType locItem = aReference == null
                    ? AIcdDataType.atom(aItemKind == null ? AInDataTypeKind.ANY : aItemKind, aItemConstraints)
                    : AIcdDataType.reference(aReference);
            return new AIcdDataType(AInDataTypeKind.ARRAY, locItem, List.of(), List.of(), null, aConstraints);
        }
        if (aKind == AInDataTypeKind.REFERENCE) return AIcdDataType.reference(Objects.requireNonNull(aReference));
        if (aKind == AInDataTypeKind.OBJECT) return AIcdDataType.object(List.of());
        return AIcdDataType.atom(aKind == null ? AInDataTypeKind.ANY : aKind, aConstraints);
    }

}
