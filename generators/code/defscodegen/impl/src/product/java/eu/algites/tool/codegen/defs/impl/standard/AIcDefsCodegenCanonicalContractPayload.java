package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.*;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Converts the independently parsed canonical graph into the exact field and tagged
 * choice layout of the generated {@code AIigCanonicalModel_1} schema contract.
 * This is a lossless boundary adapter: no source representation is inferred and
 * unresolved symbols are rejected instead of being silently widened to ANY.
 * The result may be validated against the published canonical JSONDEFS schema
 * before being instantiated as the generated DataObject contract.
 */
public final class AIcDefsCodegenCanonicalContractPayload {
    /** Prevents construction of a stateless serializer. */
    private AIcDefsCodegenCanonicalContractPayload() { }

    /**
     * Builds the complete canonical schema payload, checking identity collisions.
     *
     * @param types ordered, validated, reference-linked top-level declarations
     * @return mutable-container-free-by-convention JSON-compatible projection
     * @throws NullPointerException when a declaration or its required element is null
     * @throws IllegalArgumentException for duplicate IDs or unresolved references
     */
    public static Map<String, Object> emit(List<AIcdDefsCodegenType> types) {
        Objects.requireNonNull(types, "types");
        List<Object> result = new ArrayList<>();
        var identities = new java.util.HashSet<String>();
        for (var type : types) {
            Objects.requireNonNull(type, "type");
            if (!identities.add(type.identity())) {
                throw new IllegalArgumentException("Duplicate canonical TYPE identity: " + type.identity());
            }
            result.add(typeFields(type));
        }
        return Map.of("types", List.copyOf(result));
    }

    /**
     * Projects a TYPE declaration after reference resolution.
     *
     * @param type source TYPE value
     * @return source-preserving ordered map
     * @throws IllegalArgumentException when the TYPE is not resolved
     */
    private static Map<String, Object> typeFields(AIcdDefsCodegenType type) {
        if (type.resolutionState() != AInDefsCodegenResolutionState.RESOLVED) {
            throw new IllegalArgumentException("Unresolved canonical TYPE at " + type.identity()
                    + ": " + type.resolutionState() + "; resolve references before contract emission");
        }
        Map<String, Object> fields = new LinkedHashMap<>();
        fields.put("identity", type.identity());
        fields.put("name", type.name());
        fields.put("origin", type.origin().name());
        fields.put("schema_version", type.schemaVersion());
        fields.put("description", type.description());
        fields.put("path_segments", type.pathSegments());
        fields.put("inherited_from_types", type.inheritedFromTypes());
        if (!type.targetIdentity().isEmpty()) {
            fields.put("target_identity", type.targetIdentity());
        } else if (type.structure() != null) {
            fields.put("structure", structure(type.structure()));
        } else {
            throw new IllegalArgumentException("Resolved canonical TYPE has neither nested structure nor target: "
                    + type.identity());
        }
        fields.put("resolution_state", type.resolutionState().name());
        fields.put("source_bindings", bindings(type.sourceBindings()));
        return fields;
    }

    /**
     * Converts a canonical node to an explicit one-member tagged union.
     *
     * @param node one of the seven structural node types
     * @return choice variant recognized by the generated closed-choice model
     */
    /**
     * Preserves original XML selector/field paths and key-versus-unique semantics.
     *
     * @param definition original unnormalized key definition
     * @return structured generated-contract payload for a single key
     */
    private static Map<String, Object> key(AIcdDefsCodegenKeyDefinition definition) {
        return Map.of("identifier", definition.identifier(), "selector", definition.selector(),
                "source_pointer", definition.sourcePointer(), "fields", definition.fields(),
                "required", definition.required());
    }

    /**
     * Encodes an XML wire QName without inventing a namespace from the field name.
     * @param xml exact source metadata
     * @return schema-compatible wire data
     */
    private static Map<String, Object> xmlWire(AIcdDefsCodegenXmlWireName xml) {
        return Map.of("namespace_uri", xml.namespaceUri(), "local_name", xml.localName(),
                "value_kind", xml.valueKind().name());
    }

    private static Map<String, Object> structure(AIiDefsCodegenStructure node) {
        if (node instanceof AIcdDefsCodegenType type) return Map.of("Type", typeFields(type));
        if (node instanceof AIcdDefsCodegenElementList list) {
            return Map.of("ElementList", Map.of("composition", list.composition().name(),
                    "children", list.children().stream().map(AIcDefsCodegenCanonicalContractPayload::structure).toList(),
                    "min_occurs", list.minOccurs(), "max_occurs", list.maxOccurs()));
        }
        if (node instanceof AIcdDefsCodegenElement element) {
            var keys = element.keyDefinitions().stream().map(
                    AIcDefsCodegenCanonicalContractPayload::key).toList();
            Map<String, Object> fields = new LinkedHashMap<>();
            fields.put("name", element.name());
            fields.put("structure", structure(element.structure()));
            fields.put("key_definitions", keys);
            fields.put("source_bindings", bindings(element.sourceBindings()));
            fields.put("min_occurs", element.minOccurs());
            fields.put("max_occurs", element.maxOccurs());
            fields.put("description", element.description());
            if (element.xmlWire() != null) fields.put("xml_wire", xmlWire(element.xmlWire()));
            return Map.of("Element", fields);
        }
        if (node instanceof AIcdDefsCodegenList list) {
            Map<String, Object> fields = new LinkedHashMap<>();
            fields.put("name", list.name());
            fields.put("item", structure(list.item()));
            fields.put("min_occurs", list.minOccurs());
            fields.put("max_occurs", list.maxOccurs());
            fields.put("key_definitions", list.keyDefinitions().stream().map(
                    AIcDefsCodegenCanonicalContractPayload::key).toList());
            if (list.xmlWire() != null) fields.put("xml_wire", xmlWire(list.xmlWire()));
            return Map.of("List", fields);
        }
        if (node instanceof AIcdDefsCodegenMap map) {
            return Map.of("Map", Map.of("name", map.name(), "map_kind", map.mapKind().name(),
                    "key_type", structure(map.keyType()), "value_type", structure(map.valueType()),
                    "source_bindings", bindings(map.sourceBindings())));
        }
        if (node instanceof AIcdDefsCodegenScalar scalar) {
            return Map.of("Scalar", Map.of("scalar_kind", scalar.scalarKind().name(), "format", scalar.format()));
        }
        if (node instanceof AIcdDefsCodegenEnum values) {
            return Map.of("Enum", Map.of("base_scalar_type", values.baseScalarType().name(),
                    "values", values.values().stream().map(item -> Map.of(
                            "wire_value", item.wireValue(), "display_name", item.displayName())).toList()));
        }
        throw new IllegalArgumentException("Unknown canonical structure " + node.getClass());
    }

    /**
     * Preserves insertion order and repeated bindings for each source kind.
     *
     * @param input grouped source bindings
     * @return immutable per-technology source binding arrays
     */
    private static Map<String, Object> bindings(
            Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> input) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (var entry : input.entrySet()) {
            result.put(entry.getKey().name(), entry.getValue().stream().map(binding -> Map.of(
                    "source_resource", binding.sourceResource(),
                    "source_pointer", binding.sourcePointer(),
                    "representation_kind", binding.representationKind())).toList());
        }
        return result;
    }
}
