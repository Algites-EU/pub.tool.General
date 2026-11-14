package eu.algites.tool.codegen.common;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Resolves the new independent Common, Defs, and SDO naming catalogs after
 * the input documents have been parsed by the configured YAML/JSON loader.
 * The old mixed naming catalog is deliberately not changed by this API.
 * Roles, metadata dependencies and common-profile references are validated
 * identically to the Python implementation.
 */
public final class AIcCodegenNamingProfileResolver {
    /** All shared method naming roles, with no SDO-only or Defs-only entries. */
    public static final Set<String> COMMON_ROLES = Set.of("standard_getter", "standard_setter", "list_getter",
            "multi_mapped_list_key_synthetic_getter", "multi_mapped_list_value_synthetic_getter",
            "positional_item_synthetic_getter", "const_container_interface");
    /** Only Defs generation and synthetic type naming roles. */
    public static final Set<String> DEFS_ROLES = Set.of("synthetic_property_type", "synthetic_inline_enum_type", "synthetic_list_item_type",
            "synthetic_map_value_type", "synthetic_positional_item_type", "synthetic_choice_variant_type",
            "synthetic_group_type", "string_enum_item", "non_string_enum_item");
    /** Only SDO runtime-accessor naming roles. */
    public static final Set<String> SDO_ROLES = Set.of("raw_getter", "raw_presence_checker_method", "raw_unsetter", "raw_empty_setter", "raw_empty_checker_method");
    /** Schema metadata names common to the Defs and SDO naming profiles. */
    public static final Set<String> METADATA_ROLES = Set.of("schema_source_schema_url", "schema_source_schema_identifier",
            "schema_source_schema_version", "data_source_schema_url", "data_source_schema_identifier",
            "data_source_schema_version");

    /** Prevents instantiation of the stateless resolver. */
    private AIcCodegenNamingProfileResolver() { }

    /**
     * A validated and immutable set of domain-specific names and compositions.
     * All role values reference naming compositions except the literal map key/value getters.
     *
     * @param commonProfileId identity that specialized profiles must reference
     * @param commonRoles shared method roles and composition identifiers
     * @param defsRoles Defs-specific role values, possibly empty
     * @param sdoRoles SDO-specific role values, possibly empty
     * @param schemaMetadata shared source and serialized-document metadata mapping
     * @param indexesStartingFrom first generated positional suffix, never a data index
     * @param nameCompositions merged named composition definitions, including custom segments
     */
    public record Profile(String commonProfileId,
            Map<String, String> commonRoles, Map<String, String> defsRoles, Map<String, String> sdoRoles,
            Map<String, String> schemaMetadata, int indexesStartingFrom,
            Map<String, Map<String, Object>> nameCompositions) {
        /** Copies all maps so parsed mutable YAML documents can no longer change a resolved profile. */
        public Profile {
            Objects.requireNonNull(commonProfileId, "commonProfileId");
            commonRoles = Map.copyOf(commonRoles);
            defsRoles = Map.copyOf(defsRoles);
            sdoRoles = Map.copyOf(sdoRoles);
            schemaMetadata = Map.copyOf(schemaMetadata);
            nameCompositions = Map.copyOf(nameCompositions);
            if (indexesStartingFrom < 0) throw new IllegalArgumentException("IndexesStartingFrom must be non-negative");
        }

        /**
         * Converts a zero-based source position to the configured displayed suffix.
         *
         * @param zeroBasedIndex index in a tuple or source group, starting from zero
         * @return configured position label, potentially starting from zero or one
         * @throws IllegalArgumentException for negative indexes
         * @throws ArithmeticException if the resulting suffix overflows an integer
         */
        public int positionalNumber(int zeroBasedIndex) {
            if (zeroBasedIndex < 0) throw new IllegalArgumentException("Position must not be negative");
            return Math.addExact(zeroBasedIndex, indexesStartingFrom);
        }

        /**
         * Renders one typed naming role with its configured helper words and segments.
         * For externally supplied compositions, load the standard naming catalog first.
         *
         * @param role known Common, Defs or SDO naming role
         * @param identifier source identifier supplied to its identifier segment
         * @param variables named context values used by variable/version segments
         * @return resolved method/type name or literal synthetic key/value getter
         * @throws IllegalArgumentException for absent/unknown roles or missing compositions
         */
        public String render(String role, String identifier, Map<String, String> variables) {
            Objects.requireNonNull(role, "role");
            Objects.requireNonNull(identifier, "identifier");
            Objects.requireNonNull(variables, "variables");
            String name = COMMON_ROLES.contains(role) ? commonRoles.get(role)
                    : DEFS_ROLES.contains(role) ? defsRoles.get(role)
                    : SDO_ROLES.contains(role) ? sdoRoles.get(role) : null;
            if (name == null) throw new IllegalArgumentException("Unknown or unconfigured naming role " + role);
            if (role.equals("multi_mapped_list_key_synthetic_getter") ||
                    role.equals("multi_mapped_list_value_synthetic_getter")) return name;
            return renderComposition(name, identifier, variables, Set.of());
        }

        /**
         * Renders an explicitly selected type or filename composition from the
         * resolved source-code catalog. The caller chooses the correct domain
         * (generated interface, enum, representation and versioned filename).
         *
         * @param compositionId configured source-code composition identifier
         * @param identifier original logical type name before formatting
         * @param variables version and additional required naming variables
         * @return formatted source-code name
         * @throws IllegalArgumentException for unknown compositions or variables
         */
        public String composedName(String compositionId, String identifier, Map<String, String> variables) {
            Objects.requireNonNull(compositionId, "compositionId");
            Objects.requireNonNull(identifier, "identifier");
            Objects.requireNonNull(variables, "variables");
            return renderComposition(compositionId, identifier, variables, Set.of());
        }

        /**
         * Renders a generated synthetic type name based on semantic path components.
         * The optional position is translated using IndexesStartingFrom.
         *
         * @param role one of the synthetic Defs type roles
         * @param ownerType name of the owning canonical type before lexical formatting
         * @param identifier original field or alternative identifier
         * @param zeroBasedIndex optional source ordinal, or null if non-positional
         * @return formatted type name
         */
        public String syntheticTypeName(String role, String ownerType, String identifier, Integer zeroBasedIndex) {
            if (!DEFS_ROLES.contains(role) || !role.startsWith("synthetic_")) {
                throw new IllegalArgumentException("Expected a synthetic Defs type role");
            }
            Map<String, String> variables = new HashMap<>();
            variables.put("owner_type", Objects.requireNonNull(ownerType, "ownerType"));
            if (zeroBasedIndex != null) variables.put("position", Integer.toString(positionalNumber(zeroBasedIndex)));
            return render(role, identifier, variables);
        }

        @SuppressWarnings("unchecked")
        private String renderComposition(String id, String identifier, Map<String, String> variables,
                Set<String> visited) {
            if (visited.contains(id)) throw new IllegalArgumentException("Circular composition reference " + id);
            Map<String, Object> composition = nameCompositions.get(id);
            if (composition == null) throw new IllegalArgumentException("Missing or external composition " + id);
            Object segments = composition.get("Segments");
            if (!(segments instanceof List<?> list)) throw new IllegalArgumentException("Expected Segments in " + id);
            var result = new StringBuilder();
            var path = new java.util.HashSet<>(visited);
            path.add(id);
            for (var raw : list) {
                Map<String, Object> segment = asMap(raw, "segment");
                if (segment.containsKey("Ref")) {
                    result.append(renderComposition(String.valueOf(segment.get("Ref")), identifier, variables, path));
                    continue;
                }
                Map<String, Object> value = asMap(segment.get("NameFragmentsSegmentValue"), "segment value");
                if (value.containsKey("Content")) {
                    if (value.size() != 2 || !value.containsKey("Kind"))
                        throw new IllegalArgumentException("Inline naming segment requires Kind and Content");
                    Map<String, Object> content = asMap(value.get("Content"), "segment Content");
                    if (content.size() != 1)
                        throw new IllegalArgumentException("Inline naming Content requires exactly one alternative");
                    var selected = content.entrySet().iterator().next();
                    Map<String, Object> normalized = new HashMap<>();
                    normalized.put("Kind", value.get("Kind"));
                    if ("NameRegexp".equals(selected.getKey())) {
                        Map<String, Object> pair = asMap(selected.getValue(), "NameRegexp");
                        if (pair.size() != 2 || !pair.containsKey("Name") || !pair.containsKey("Regexp"))
                            throw new IllegalArgumentException("NameRegexp must contain Name and Regexp");
                        normalized.putAll(pair);
                    } else if (Set.of("Value", "Convention", "CustomConventionRegexp").contains(selected.getKey())) {
                        normalized.put(selected.getKey(), selected.getValue());
                    } else {
                        throw new IllegalArgumentException("Unsupported naming Content alternative " + selected.getKey());
                    }
                    value = normalized;
                }
                String kind = String.valueOf(value.get("Kind"));
                switch (kind) {
                    case "constant_string" -> result.append(value.get("Value"));
                    case "identifier" -> result.append(formatIdentifier(identifier, String.valueOf(value.get("Convention"))));
                    case "variable" -> {
                        String variableName = String.valueOf(value.get("Name"));
                        String text = variables.get(variableName);
                        if (text == null || !Pattern.compile(String.valueOf(value.get("Regexp"))).matcher(text).matches()) {
                            throw new IllegalArgumentException("Missing or invalid naming variable " + variableName);
                        }
                        result.append(text);
                    }
                    case "version" -> {
                        if (!variables.containsKey("version")) throw new IllegalArgumentException("Missing version segment");
                        result.append(variables.get("version"));
                    }
                    default -> throw new IllegalArgumentException("Unknown composition segment " + kind);
                }
            }
            return result.toString();
        }
    }

    /**
     * Resolves three parsed documents by stable profile IDs, requiring specialized
     * profiles to reference the supplied common one.
     *
     * @param commonDoc parsed common profile document
     * @param commonId selected common profile identifier
     * @param defsDoc parsed Defs profile document, or null to omit this specialization
     * @param defsId selected Defs profile identifier when supplied
     * @param sdoDoc parsed SDO profile document, or null to omit this specialization
     * @param sdoId selected SDO profile identifier when supplied
     * @return validated resolved naming profile
     * @throws IllegalArgumentException if roles, profile references, metadata or indexes are invalid
     */
    public static Profile resolve(Map<String, Object> commonDoc, String commonId,
            Map<String, Object> defsDoc, String defsId,
            Map<String, Object> sdoDoc, String sdoId) {
        Objects.requireNonNull(commonDoc, "commonDoc");
        Objects.requireNonNull(commonId, "commonId");
        var commonProfile = select(commonDoc, "CommonCodegenNameConventions", commonId);
        var commonRoles = roles(commonProfile, COMMON_ROLES, "Common");
        if (!commonRoles.containsKey("standard_getter") || !commonRoles.containsKey("standard_setter")
                || !commonRoles.containsKey("list_getter")) {
            throw new IllegalArgumentException("Common getter/setter/list getter compositions required");
        }
        var metadata = namingRules(commonProfile.getOrDefault("SchemaMetadataNaming", Map.of()), "SchemaMetadataNaming");
        if (!METADATA_ROLES.containsAll(metadata.keySet())) throw new IllegalArgumentException("Foreign metadata role");
        for (String suffix : List.of("url", "identifier", "version")) {
            if (!metadata.getOrDefault("data_source_schema_" + suffix, "").isBlank() &&
                    metadata.getOrDefault("schema_source_schema_" + suffix, "").isBlank()) {
                throw new IllegalArgumentException("Missing source metadata mapping for " + suffix);
            }
        }
        Object indexValue = commonProfile.getOrDefault("IndexesStartingFrom", 1);
        if (!(indexValue instanceof Integer index) || index < 0) {
            throw new IllegalArgumentException("IndexesStartingFrom must be a non-negative integer");
        }
        Map<String, String> defs = Map.of();
        Map<String, String> sdo = Map.of();
        Map<String, Map<String, Object>> compositions = new LinkedHashMap<>();
        collectCompositions(commonDoc, compositions);
        if (defsDoc != null) {
            var profile = select(defsDoc, "DefsCodegenNameConventions", Objects.requireNonNull(defsId, "defsId"));
            if (!commonId.equals(profile.get("CommonNamingConvention"))) {
                throw new IllegalArgumentException("Defs must reference the selected common profile");
            }
            defs = roles(profile, DEFS_ROLES, "Defs");
            collectCompositions(defsDoc, compositions);
        }
        if (sdoDoc != null) {
            var profile = select(sdoDoc, "SdoCodegenNameConventions", Objects.requireNonNull(sdoId, "sdoId"));
            if (!commonId.equals(profile.get("CommonNamingConvention"))) {
                throw new IllegalArgumentException("SDO must reference the selected common profile");
            }
            sdo = roles(profile, SDO_ROLES, "SDO");
            collectCompositions(sdoDoc, compositions);
        }
        return new Profile(commonId, commonRoles, defs, sdo, metadata, index, compositions);
    }

    /** Index the XSD-shaped named array used by JSONDEFS and YAMLDEFS. */
    private static Map<String, Object> namedEntries(Object source, String label, String field, String path) {
        Map<String, Object> envelope = asMap(source, path);
        if (!envelope.containsKey(label)) return envelope; // Already indexed in-memory.
        if (envelope.size() != 1 || !(envelope.get(label) instanceof List<?> list))
            throw new IllegalArgumentException(path + "/" + label + ": expected an array");
        Map<String, Object> result = new LinkedHashMap<>();
        int index = 0;
        for (Object raw : list) {
            String location = path + "/" + label + "[" + index++ + "]";
            Map<String, Object> entry = asMap(raw, location);
            Object key = entry.get(field);
            if (!(key instanceof String name) || name.isBlank())
                throw new IllegalArgumentException(location + ": missing " + field);
            Map<String, Object> body = new LinkedHashMap<>(entry);
            body.remove(field);
            if (result.putIfAbsent(name, body) != null)
                throw new IllegalArgumentException(location + ": duplicate " + field + " " + name);
        }
        return result;
    }

    private static Map<String, String> namingRules(Object source, String path) {
        Map<String, Object> entries = namedEntries(source, "Rule", "kind", path);
        Map<String, String> result = new LinkedHashMap<>();
        entries.forEach((kind, raw) -> {
            if (raw instanceof String value) result.put(kind, value);
            else {
                Map<String, Object> item = asMap(raw, path + "/" + kind);
                if (item.size() != 1 || !(item.get("Value") instanceof String value))
                    throw new IllegalArgumentException(path + "/" + kind + ": expected string Value");
                result.put(kind, value);
            }
        });
        return result;
    }

    private static Map<String, Object> select(Map<String, Object> doc, String root, String id) {
        Map<String, Object> container = asMap(doc.get(root), root);
        Map<String, Object> profiles = namedEntries(container.get("NameConventions"), "NameConvention", "name", "NameConventions");
        return asMap(profiles.get(id), "profile " + id);
    }

    private static Map<String, String> roles(Map<String, Object> profile, Set<String> allowed, String domain) {
        var result = namingRules(profile.get("StructureNaming"), domain + "/StructureNaming");
        if (!allowed.containsAll(result.keySet()) || result.values().stream().anyMatch(String::isBlank)) {
            throw new IllegalArgumentException("Unknown or empty naming role in " + domain);
        }
        return result;
    }

    private static Map<String, String> asStringMap(Object object) {
        var map = asMap(object, "naming roles");
        Map<String, String> result = new LinkedHashMap<>();
        for (var entry : map.entrySet()) {
            if (entry.getValue() != null && !(entry.getValue() instanceof String)) {
                throw new IllegalArgumentException("Non-string role value " + entry.getKey());
            }
            result.put(entry.getKey(), entry.getValue() == null ? "" : (String) entry.getValue());
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> asMap(Object object, String location) {
        if (!(object instanceof Map<?, ?> map)) throw new IllegalArgumentException("Missing or invalid " + location);
        for (Object key : map.keySet()) {
            if (!(key instanceof String)) throw new IllegalArgumentException("Non-string map key in " + location);
        }
        return (Map<String, Object>) map;
    }

    private static void collectCompositions(Map<String, Object> doc, Map<String, Map<String, Object>> result) {
        Map<String, Object> values = namedEntries(doc.getOrDefault("NameCompositions", Map.of()), "NameComposition", "name", "NameCompositions");
        for (var entry : values.entrySet()) {
            var value = asMap(entry.getValue(), entry.getKey());
            var old = result.putIfAbsent(entry.getKey(), value);
            if (old != null && !old.equals(value)) throw new IllegalArgumentException("Conflicting naming composition " + entry.getKey());
        }
    }

    /**
     * Adds source-code naming fragments from the explicitly selected external
     * library catalog to a validated Common/Defs/SDO naming profile. External
     * compositions supply getter/setter lexical rules that do not belong in
     * Defs-specific configuration. Existing composition IDs must agree exactly.
     *
     * @param profile already validated Common/Defs/SDO naming profile
     * @param sourceCatalog parsed external source-code catalog with NameFragments
     *        and NameCompositions collections
     * @return new immutable profile with all referenced fragments available
     * @throws IllegalArgumentException for incompatible duplicate composition IDs
     *         or malformed fragment/reference definitions
     */
    public static Profile withExternalSourcecodeConventions(Profile profile,
            Map<String, Object> sourceCatalog) {
        Objects.requireNonNull(profile, "profile");
        Objects.requireNonNull(sourceCatalog, "sourceCatalog");
        Map<String, Map<String, Object>> merged = new LinkedHashMap<>(profile.nameCompositions());
        for (String collection : List.of("NameFragments", "NameCompositions")) {
            Map<String, Object> definitions = namedEntries(sourceCatalog.getOrDefault(collection, Map.of()),
                    collection.equals("NameFragments") ? "NameFragment" : "NameComposition", "name", collection);
            for (var entry : definitions.entrySet()) {
                Map<String, Object> definition = asMap(entry.getValue(), entry.getKey());
                Object rawSegments = definition.get("Segments");
                if (!(rawSegments instanceof List<?> segments)) {
                    throw new IllegalArgumentException("Invalid source-code composition " + entry.getKey());
                }
                List<Map<String, Object>> normalized = new ArrayList<>();
                for (Object raw : segments) {
                    Map<String, Object> segment = asMap(raw, "segment in " + entry.getKey());
                    if (segment.containsKey("NameFragmentsSegmentReference")) {
                        Map<String, Object> ref = asMap(segment.get("NameFragmentsSegmentReference"), "reference");
                        Object reference = ref.get("Ref");
                        if (!(reference instanceof String identifier)) {
                            throw new IllegalArgumentException("Invalid source-code naming reference " + reference);
                        }
                        normalized.add(Map.of("Ref", identifier));
                    } else if (segment.containsKey("Ref")) {
                        normalized.add(Map.of("Ref", segment.get("Ref")));
                    } else if (segment.containsKey("NameFragmentsSegmentValue")) {
                        normalized.add(Map.of("NameFragmentsSegmentValue",
                                asMap(segment.get("NameFragmentsSegmentValue"), "value")));
                    } else {
                        throw new IllegalArgumentException("Invalid source-code naming segment " + segment);
                    }
                }
                Map<String, Object> canonical = Map.of("Segments", List.copyOf(normalized));
                Map<String, Object> previous = merged.putIfAbsent(entry.getKey(), canonical);
                if (previous != null && !previous.equals(canonical)) {
                    throw new IllegalArgumentException("Conflicting source-code composition " + entry.getKey());
                }
            }
        }
        return new Profile(profile.commonProfileId(), profile.commonRoles(), profile.defsRoles(),
                profile.sdoRoles(), profile.schemaMetadata(), profile.indexesStartingFrom(), merged);
    }

    private static String formatIdentifier(String original, String convention) {
        String text = original.replaceAll("([a-z0-9])([A-Z])", "$1 $2")
                .replaceAll("([A-Z])([A-Z][a-z])", "$1 $2");
        String[] parts = text.split("[^A-Za-z0-9]+");
        List<String> words = new ArrayList<>();
        for (String part : parts) if (!part.isBlank()) words.add(part);
        if (words.isEmpty()) throw new IllegalArgumentException("Empty identifier");
        boolean upperCamel = convention.contains("upper_camel") || convention.contains("upper-camel");
        boolean lowerCamel = convention.contains("lower_camel") || convention.contains("lower-camel");
        if (upperCamel || lowerCamel) {
            StringBuilder result = new StringBuilder();
            for (int i = 0; i < words.size(); i++) {
                String word = words.get(i).toLowerCase(java.util.Locale.ROOT);
                if (!lowerCamel || i > 0) word = Character.toUpperCase(word.charAt(0)) + word.substring(1);
                result.append(word);
            }
            return result.toString();
        }
        String separator;
        if (convention.contains("snake")) separator = "_";
        else if (convention.contains("kebab")) separator = "-";
        else if (convention.contains("flat")) separator = "";
        else throw new IllegalArgumentException("Unknown lexical conversion " + convention);
        String joined = String.join(separator, words);
        return convention.startsWith("upper_") ? joined.toUpperCase(java.util.Locale.ROOT)
                : joined.toLowerCase(java.util.Locale.ROOT);
    }
}
