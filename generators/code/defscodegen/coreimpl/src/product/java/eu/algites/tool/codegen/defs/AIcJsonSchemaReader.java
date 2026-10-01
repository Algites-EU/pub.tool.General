package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.conversion.AIcDefaultNameConverter;
import eu.algites.lib.naming.convention.AIcdInputVersionPolicy;
import eu.algites.lib.naming.conversion.AIcdParsedVersionedName;
import eu.algites.lib.naming.convention.AInVersionSource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

/** Shared structural JSON-Schema mapping used by distinct jsondefs and yamldefs frontends. */
final class AIcJsonSchemaReader {
    private final AIcDefinitionIdentityResolver identities = new AIcDefinitionIdentityResolver();
    private final ObjectMapper jsonMapper = new ObjectMapper();
    private final ObjectMapper yamlMapper = new ObjectMapper(new YAMLFactory());

    AIcdCanonicalDefinition read(JsonNode root, AIcdDefinitionLoadRequest request, AInDefinitionSourceKind sourceKind, String idExtension, String versionExtension, String nameExtension) {
        Integer explicitVersion = integer(root, versionExtension);
        AIcdParsedVersionedName parsed = identities.fromFileName(request, explicitVersion);
        String logicalName = text(root, nameExtension);
        if (logicalName == null || logicalName.isBlank()) logicalName = parsed.logicalName();
        String identity = text(root, idExtension);
        if (identity == null || identity.isBlank()) identity = text(root, "$id");
        if (identity == null || identity.isBlank()) identity = parsed.logicalName();
        Integer version = explicitVersion != null ? explicitVersion : parsed.version();
        String description = text(root, "description");
        List<AIcdEnumValueDefinition> enumValues = enumValues(root);
        if (!enumValues.isEmpty()) {
            return new AIcdCanonicalDefinition(identity, version, logicalName, AInDefinitionKind.ENUM, sourceKind, request.path().toString(), description, List.of(), enumValues);
        }
        String type = text(root, "type");
        if ("object".equals(type) || root.has("properties")) {
            Set<String> required = new HashSet<>();
            JsonNode requiredNode = root.get("required");
            if (requiredNode != null && requiredNode.isArray()) requiredNode.forEach(value -> required.add(value.asText()));
            List<AIcdPropertyDefinition> properties = new ArrayList<>();
            JsonNode props = root.get("properties");
            if (props != null && props.isObject()) {
                Iterator<String> names = props.fieldNames();
                while (names.hasNext()) {
                    String name = names.next();
                    properties.add(property(name, props.get(name), required.contains(name), request));
                }
            }
            return new AIcdCanonicalDefinition(identity, version, logicalName, AInDefinitionKind.OBJECT, sourceKind, request.path().toString(), description, properties, List.of());
        }
        return new AIcdCanonicalDefinition(identity, version, logicalName, AInDefinitionKind.SCALAR, sourceKind, request.path().toString(), description, List.of(), List.of());
    }

    private AIcdPropertyDefinition property(String name, JsonNode node, boolean required, AIcdDefinitionLoadRequest request) {
        boolean nullable = false;
        String type = text(node, "type");
        JsonNode typeNode = node.get("type");
        if (typeNode != null && typeNode.isArray()) {
            List<String> types = new ArrayList<>();
            typeNode.forEach(item -> types.add(item.asText()));
            nullable = types.contains("null");
            type = types.stream().filter(item -> !"null".equals(item)).findFirst().orElse(null);
        }
        String ref = text(node, "$ref");
        if (ref != null) {
            String resource = ref.split("#", 2)[0];
            String stem = AIcDefinitionIdentityResolver.stripDefinitionExtensions(resource.substring(resource.lastIndexOf('/') + 1));
            AIcdParsedVersionedName parsed = new AIcDefaultNameConverter().parseVersionedName(
                    stem, null, new AIcdInputVersionPolicy(AInVersionSource.FILE_NAME_SUFFIX, "_", true, false));
            Path referencedPath = request.path().getParent() == null ? Path.of(resource) : request.path().getParent().resolve(resource).normalize();
            AInDefinitionKind targetKind = detectReferencedKind(referencedPath);
            return new AIcdPropertyDefinition(name, AInValueKind.REFERENCE, required, nullable, null,
                    new AIcdDefinitionReference(ref, parsed.version(), parsed.logicalName(), targetKind), text(node, "description"));
        }
        AInValueKind kind = kind(type);
        AInValueKind itemKind = null;
        if (kind == AInValueKind.ARRAY && node.get("items") != null) itemKind = kind(text(node.get("items"), "type"));
        return new AIcdPropertyDefinition(name, kind, required, nullable, itemKind, null, text(node, "description"));
    }

    private AInDefinitionKind detectReferencedKind(Path path) {
        if (!Files.isRegularFile(path)) return null;
        try {
            String fileName = path.getFileName().toString().toLowerCase();
            JsonNode root = (fileName.endsWith(".yaml") || fileName.endsWith(".yml"))
                    ? yamlMapper.readTree(path.toFile()) : jsonMapper.readTree(path.toFile());
            if (root != null && !enumValues(root).isEmpty()) return AInDefinitionKind.ENUM;
            if (root != null && ("object".equals(text(root, "type")) || root.has("properties"))) return AInDefinitionKind.OBJECT;
            return AInDefinitionKind.SCALAR;
        } catch (IOException ex) {
            return null;
        }
    }

    /**
     * Normalizes enum values and optional per-value descriptions from JSON-Schema-shaped definitions.
     *
     * <p>Descriptions are read from {@code oneOf} branches containing {@code const} and
     * {@code description}. A plain {@code enum} array remains supported; matching {@code oneOf}
     * branches enrich those values without changing their wire representation.</p>
     *
     * @param root source definition root
     * @return canonical enum values in declared order
     */
    private static List<AIcdEnumValueDefinition> enumValues(JsonNode root) {
        if (root == null) return List.of();
        java.util.Map<String, String> descriptions = new java.util.LinkedHashMap<>();
        List<AIcdEnumValueDefinition> oneOfValues = new ArrayList<>();
        JsonNode oneOf = root.get("oneOf");
        if (oneOf != null && oneOf.isArray()) {
            for (JsonNode branch : oneOf) {
                JsonNode constant = branch.get("const");
                if (constant == null || constant.isContainerNode() || constant.isNull()) continue;
                String value = constant.asText();
                String valueDescription = text(branch, "description");
                descriptions.put(value, valueDescription);
                oneOfValues.add(new AIcdEnumValueDefinition(value, valueDescription));
            }
        }
        JsonNode enumNode = root.get("enum");
        if (enumNode != null && enumNode.isArray()) {
            List<AIcdEnumValueDefinition> result = new ArrayList<>();
            enumNode.forEach(value -> result.add(new AIcdEnumValueDefinition(value.asText(), descriptions.get(value.asText()))));
            return result;
        }
        return oneOfValues;
    }

    private static AInValueKind kind(String type) {
        if (type == null) return AInValueKind.ANY;
        return switch (type) {
            case "string" -> AInValueKind.STRING;
            case "integer" -> AInValueKind.INTEGER;
            case "number" -> AInValueKind.NUMBER;
            case "boolean" -> AInValueKind.BOOLEAN;
            case "array" -> AInValueKind.ARRAY;
            case "object" -> AInValueKind.OBJECT;
            default -> AInValueKind.ANY;
        };
    }

    private static String text(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        return value == null || value.isNull() ? null : value.asText();
    }

    private static Integer integer(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        return value == null || !value.isIntegralNumber() ? null : value.intValue();
    }
}
