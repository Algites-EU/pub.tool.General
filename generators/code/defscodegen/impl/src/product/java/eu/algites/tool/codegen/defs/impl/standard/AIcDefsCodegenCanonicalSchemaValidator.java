package eu.algites.tool.codegen.defs.impl.standard;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Validates the schema-generated canonical payload against its own published
 * JSON Schema, without silently bypassing unknown validation keywords. The
 * supported dialect is precisely the keywords used by canonical-model_1;
 * adding new validation keywords requires extending this validator and its
 * regression tests before the Java CLI may accept the new contract.
 *
 * <p>The same schema is validated by Python's JSON Schema implementation.
 * This implementation is deliberately closed, not an all-purpose JSON Schema
 * validator and not a replacement for source-schema validation.</p>
 *
 * @author linhart1
 */
public final class AIcDefsCodegenCanonicalSchemaValidator {
    /** Core JSON Schema validator keywords supported for canonical-model_1. */
    private static final java.util.Set<String> VALIDATION = java.util.Set.of(
            "$ref", "type", "enum", "properties", "required", "additionalProperties", "items",
            "minLength", "maxLength", "minProperties", "maxProperties", "minimum", "maximum",
            "oneOf", "allOf", "anyOf", "not", "minItems", "maxItems", "pattern");
    /** Metadata-only keywords which do not affect instance validity. */
    private static final java.util.Set<String> ANNOTATIONS = java.util.Set.of(
            "$schema", "$id", "$defs", "title", "description", "x-algites-schema-id",
            "x-algites-schema-version", "x-algites-defscodegen-choice", "default", "examples", "$comment");
    /** The explicit canonical JSON Schema document. */
    private final Map<String, Object> schema;

    /**
     * Create a validator from the schema selected by the calling CLI.
     * @param schema parsed canonical-model JSON Schema mapping
     * @throws IllegalArgumentException if its validation vocabulary is unsupported
     * @throws NullPointerException when schema is missing
     */
    public AIcDefsCodegenCanonicalSchemaValidator(Map<String, Object> schema) {
        this.schema = Map.copyOf(Objects.requireNonNull(schema, "schema"));
        validateSchema(this.schema, "#");
    }

    /**
     * Validate one emitted canonical model, rejecting all schema mismatches.
     * @param payload JSON-compatible canonical object graph
     * @throws IllegalArgumentException for a schema violation with precise location
     */
    public void validate(Map<String, Object> payload) {
        if (!valid(schema, payload, "#", 0)) {
            throw new IllegalArgumentException("Generated canonical model does not satisfy schema at root");
        }
    }

    /**
     * Fail before interpreting any schema containing unknown validation keywords.
     * @param document schema definition
     * @param path location of the definition
     */
    private static void validateSchema(Object document, String path) {
        if (document instanceof Boolean) return;
        if (!(document instanceof Map<?, ?> mapping)) {
            throw new IllegalArgumentException("Expected JSON Schema definition at " + path);
        }
        for (var entry : mapping.entrySet()) {
            String keyword = String.valueOf(entry.getKey());
            if (!VALIDATION.contains(keyword) && !ANNOTATIONS.contains(keyword)) {
                throw new UnsupportedOperationException("Unsupported canonical JSON Schema keyword at "
                        + path + ": " + keyword);
            }
            if (List.of("properties", "$defs").contains(keyword)) {
                if (!(entry.getValue() instanceof Map<?, ?> props)) {
                    throw new IllegalArgumentException("Expected schema properties at " + path);
                }
                for (var child : props.entrySet()) {
                    validateSchema(child.getValue(), path + "/" + keyword + "/" + child.getKey());
                }
            } else if (List.of("additionalProperties", "items", "not").contains(keyword)) {
                validateSchema(entry.getValue(), path + "/" + keyword);
            } else if (List.of("oneOf", "anyOf", "allOf").contains(keyword)) {
                if (!(entry.getValue() instanceof List<?> children)) {
                    throw new IllegalArgumentException("Expected schema array at " + path + "/" + keyword);
                }
                for (int i = 0; i < children.size(); i++) {
                    validateSchema(children.get(i), path + "/" + keyword + "/" + i);
                }
            }
        }
    }

    /**
     * Interpret validation constraints against one instance node.
     * @param rule schema definition or boolean schema
     * @param instance instance value
     * @param path location of the instance
     * @param depth reference nesting guard
     * @return whether all constraints are satisfied
     */
    private boolean valid(Object rule, Object instance, String path, int depth) {
        if (depth > 256) throw new IllegalArgumentException("Canonical schema recursion too deep: " + path);
        if (rule instanceof Boolean allowed) return allowed;
        if (!(rule instanceof Map<?, ?> original)) throw new IllegalArgumentException("Invalid schema node " + path);
        Map<String, Object> schemaNode = cast(original);
        if (schemaNode.containsKey("$ref")) {
            String reference = String.valueOf(schemaNode.get("$ref"));
            if (!reference.startsWith("#/$defs/")) {
                throw new UnsupportedOperationException("Unsupported canonical schema reference: " + reference);
            }
            Object ref = schema.get("$defs");
            for (String part : reference.substring("#/$defs/".length()).split("/")) {
                if (!(ref instanceof Map<?, ?> mapping)) {
                    throw new IllegalArgumentException("Missing canonical definition: " + reference);
                }
                ref = mapping.get(part.replace("~1", "/").replace("~0", "~"));
            }
            if (ref == null || !valid(ref, instance, path, depth + 1)) return false;
        }
        if (schemaNode.containsKey("type") && !matchesType(instance, schemaNode.get("type"))) return false;
        if (schemaNode.containsKey("enum") && (!(schemaNode.get("enum") instanceof List<?> enums)
                || enums.stream().noneMatch(value -> Objects.equals(value, instance)))) return false;
        if (instance instanceof String text) {
            if (minimum(schemaNode, "minLength", text.codePointCount(0, text.length()))) return false;
            if (maximum(schemaNode, "maxLength", text.codePointCount(0, text.length()))) return false;
            if (schemaNode.containsKey("pattern") && !java.util.regex.Pattern.compile(
                    String.valueOf(schemaNode.get("pattern"))).matcher(text).find()) return false;
        }
        if (instance instanceof Number number) {
            if (schemaNode.containsKey("minimum") && decimal(number).compareTo(
                    decimal((Number) schemaNode.get("minimum"))) < 0) return false;
            if (schemaNode.containsKey("maximum") && decimal(number).compareTo(
                    decimal((Number) schemaNode.get("maximum"))) > 0) return false;
        }
        if (instance instanceof Map<?, ?> object) {
            if (minimum(schemaNode, "minProperties", object.size()) ||
                    maximum(schemaNode, "maxProperties", object.size())) return false;
            if (schemaNode.get("required") instanceof List<?> required &&
                    required.stream().anyMatch(field -> !object.containsKey(field))) return false;
            Map<String, Object> known = schemaNode.get("properties") instanceof Map<?, ?> map
                    ? cast(map) : Map.of();
            for (var entry : object.entrySet()) {
                String name = String.valueOf(entry.getKey());
                if (known.containsKey(name)) {
                    if (!valid(known.get(name), entry.getValue(), path + "/" + name, depth + 1)) return false;
                } else if (schemaNode.containsKey("additionalProperties") && !valid(
                        schemaNode.get("additionalProperties"), entry.getValue(), path + "/" + name, depth + 1)) {
                    return false;
                }
            }
        }
        if (instance instanceof List<?> list) {
            if (minimum(schemaNode, "minItems", list.size()) ||
                    maximum(schemaNode, "maxItems", list.size())) return false;
            if (schemaNode.containsKey("items")) {
                for (int i = 0; i < list.size(); i++) {
                    if (!valid(schemaNode.get("items"), list.get(i), path + "/" + i, depth + 1)) return false;
                }
            }
        }
        if (schemaNode.containsKey("not") && valid(schemaNode.get("not"), instance, path, depth + 1)) {
            return false;
        }
        if (schemaNode.get("allOf") instanceof List<?> all) {
            for (Object alternative : all) if (!valid(alternative, instance, path, depth + 1)) return false;
        }
        if (schemaNode.get("anyOf") instanceof List<?> any) {
            boolean one = false;
            for (Object alternative : any) one |= valid(alternative, instance, path, depth + 1);
            if (!one) return false;
        }
        if (schemaNode.get("oneOf") instanceof List<?> alternatives) {
            int matches = 0;
            for (Object alternative : alternatives) {
                if (valid(alternative, instance, path, depth + 1)) matches++;
            }
            if (matches != 1) return false;
        }
        return true;
    }

    /**
     * Check JSON Schema primitive type.
     * @param instance actual value
     * @param expected schema type token
     * @return true when the instance matches
     */
    private static boolean matchesType(Object instance, Object expected) {
        if (expected instanceof List<?> types) {
            return types.stream().anyMatch(type -> matchesType(instance, type));
        }
        return switch (String.valueOf(expected)) {
            case "object" -> instance instanceof Map<?, ?>;
            case "array" -> instance instanceof List<?>;
            case "string" -> instance instanceof String;
            case "integer" -> instance instanceof Number number &&
                    decimal(number).stripTrailingZeros().scale() <= 0;
            case "number" -> instance instanceof Number;
            case "boolean" -> instance instanceof Boolean;
            case "null" -> instance == null;
            default -> throw new IllegalArgumentException("Unknown canonical schema type " + expected);
        };
    }

    /**
     * Convert a JSON numeric node without binary floating-point assumptions.
     * @param number numeric value
     * @return precise lexical BigDecimal
     */
    private static BigDecimal decimal(Number number) {
        return new BigDecimal(number.toString());
    }

    /**
     * Check that a value is not below a minimum bound.
     * @param rule schema node
     * @param key keyword
     * @param value numeric value to check
     * @return whether the minimum is violated
     */
    private static boolean minimum(Map<String, Object> rule, String key, int value) {
        return rule.get(key) instanceof Number min && value < min.intValue();
    }

    /**
     * Check that a value does not exceed its upper bound.
     * @param rule schema node
     * @param key keyword
     * @param value numeric value to check
     * @return whether the maximum is violated
     */
    private static boolean maximum(Map<String, Object> rule, String key, int value) {
        return rule.get(key) instanceof Number max && value > max.intValue();
    }

    /**
     * Require string keys in a parsed map.
     * @param original generic parsed object
     * @return typed view over unchanged map
     */
    @SuppressWarnings("unchecked")
    private static Map<String, Object> cast(Map<?, ?> original) {
        if (original.keySet().stream().anyMatch(key -> !(key instanceof String))) {
            throw new IllegalArgumentException("Canonical object has a non-string field");
        }
        return (Map<String, Object>) original;
    }
}
