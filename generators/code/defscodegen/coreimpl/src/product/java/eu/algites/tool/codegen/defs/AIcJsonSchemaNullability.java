package eu.algites.tool.codegen.defs;

import com.fasterxml.jackson.databind.JsonNode;

/** Evaluates whether JSON Schema constraints admit the actual JSON null value. */
final class AIcJsonSchemaNullability {
    private AIcJsonSchemaNullability() { }

    /** JSON Schema keywords at one location are conjunctive, except explicit composition. */
    static boolean acceptsNull(JsonNode aSchema) {
        if (aSchema == null || aSchema.isMissingNode()) return true;
        if (aSchema.isBoolean()) return aSchema.booleanValue();
        if (!aSchema.isObject()) return false;
        JsonNode locTypes = aSchema.get("type");
        if (locTypes != null) {
            if (locTypes.isTextual() && !"null".equals(locTypes.textValue())) return false;
            if (locTypes.isArray()) {
                boolean locFound = false;
                for (JsonNode locType : locTypes) if ("null".equals(locType.asText())) locFound = true;
                if (!locFound) return false;
            }
        }
        JsonNode locEnum = aSchema.get("enum");
        if (locEnum != null) {
            boolean locFound = false;
            for (JsonNode locValue : locEnum) if (locValue.isNull()) locFound = true;
            if (!locFound) return false;
        }
        JsonNode locConst = aSchema.get("const");
        if (locConst != null && !locConst.isNull()) return false;
        JsonNode locAllOf = aSchema.get("allOf");
        if (locAllOf != null && locAllOf.isArray()) {
            for (JsonNode locBranch : locAllOf) if (!acceptsNull(locBranch)) return false;
        }
        JsonNode locAnyOf = aSchema.get("anyOf");
        if (locAnyOf != null && locAnyOf.isArray()) {
            boolean locFound = false;
            for (JsonNode locBranch : locAnyOf) if (acceptsNull(locBranch)) locFound = true;
            if (!locFound) return false;
        }
        JsonNode locOneOf = aSchema.get("oneOf");
        if (locOneOf != null && locOneOf.isArray()) {
            int locMatches = 0;
            for (JsonNode locBranch : locOneOf) if (acceptsNull(locBranch)) locMatches++;
            if (locMatches != 1) return false;
        }
        JsonNode locNot = aSchema.get("not");
        if (locNot != null && acceptsNull(locNot)) return false;
        JsonNode locIf = aSchema.get("if");
        if (locIf != null) {
            JsonNode locBranch = aSchema.get(acceptsNull(locIf) ? "then" : "else");
            if (locBranch != null && !acceptsNull(locBranch)) return false;
        }
        return true;
    }
}
