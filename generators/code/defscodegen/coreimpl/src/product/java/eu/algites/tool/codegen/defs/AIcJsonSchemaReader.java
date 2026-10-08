package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.conversion.AIcDefaultNameConverter;
import eu.algites.lib.naming.convention.AIcdInputVersionPolicy;
import eu.algites.lib.naming.conversion.AIcdParsedVersionedName;
import eu.algites.lib.naming.convention.AInVersionSource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.FileVisitResult;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.stream.Stream;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

/** Shared structural JSON-Schema mapping used by distinct jsondefs and yamldefs frontends. */
final class AIcJsonSchemaReader {
    private final AIcDefinitionIdentityResolver identities = new AIcDefinitionIdentityResolver();
    private final ObjectMapper jsonMapper = new ObjectMapper().enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private final ObjectMapper yamlMapper = new ObjectMapper(new YAMLFactory()).enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);

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
        root = structural(root, request, new HashSet<>());
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
        return new AIcdCanonicalDefinition(identity, version, logicalName, AInDefinitionKind.SCALAR, sourceKind, request.path().toString(), description, List.of(property("value", root, true, request)), List.of());
    }

    private AIcdPropertyDefinition property(String name, JsonNode node, boolean required, AIcdDefinitionLoadRequest request) {
        return property(name, node, required, request, new HashSet<>());
    }

    private AIcdPropertyDefinition property(String name, JsonNode node, boolean required, AIcdDefinitionLoadRequest request, Set<String> visited) {
        boolean nullable = AIcJsonSchemaNullability.acceptsNull(node);
        String type = text(node, "type");
        JsonNode typeNode = node.get("type");
        if (typeNode != null && typeNode.isArray()) {
            List<String> types = new ArrayList<>();
            typeNode.forEach(item -> types.add(item.asText()));
            type = types.stream().filter(item -> !"null".equals(item)).findFirst().orElse(null);
        }
        String ref = text(node, "$ref");
        if (ref != null && URI.create(ref).getFragment() != null && !URI.create(ref).getFragment().isEmpty()) {
            String resource = ref.split("#", 2)[0];
            Path target = referencePath(resource, request);
            JsonNode document;
            try {
                String fileName = target.getFileName().toString().toLowerCase();
                document = (fileName.endsWith(".yaml") || fileName.endsWith(".yml"))
                        ? yamlMapper.readTree(target.toFile()) : jsonMapper.readTree(target.toFile());
            } catch (IOException ex) {
                throw new IllegalArgumentException("Cannot resolve schema reference '" + ref + "' in " + request.path(), ex);
            }
            String fragment = URI.create(ref).getFragment();
            JsonNode referenced = fragment.startsWith("/") ? document.at(fragment) : anchor(document, fragment);
            if (referenced == null || referenced.isMissingNode()) {
                throw new IllegalArgumentException("Undefined schema reference '" + ref + "' in " + request.path());
            }
            String referenceKey = target.toAbsolutePath().normalize() + "#" + fragment;
            if (!visited.add(referenceKey)) {
                throw new IllegalArgumentException("Circular schema reference '" + ref + "' in " + request.path());
            }
            AIcdPropertyDefinition normalized = property(name, referenced.has("allOf")
                    ? structural(referenced, new AIcdDefinitionLoadRequest(target, request.sourceKind(), request.namingProfile()), new HashSet<>()) : referenced, required,
                    new AIcdDefinitionLoadRequest(target, request.sourceKind(), request.namingProfile()), visited);
            return new AIcdPropertyDefinition(name, normalized.valueKind(), required, nullable && normalized.nullable(),
                    normalized.itemValueKind(), normalized.reference(),
                    text(node, "description") == null ? normalized.description() : text(node, "description"), normalized.constraints(), normalized.itemConstraints());
        }
        if (ref != null) {
            String resource = ref.split("#", 2)[0];
            Path referencedPath = referencePath(resource, request);
            String stem = AIcDefinitionIdentityResolver.stripDefinitionExtensions(referencedPath.getFileName().toString());
            AIcdParsedVersionedName parsed = new AIcDefaultNameConverter().parseVersionedName(
                    stem, null, new AIcdInputVersionPolicy(AInVersionSource.FILE_NAME_SUFFIX, "_", true, false));
            AInDefinitionKind targetKind = detectReferencedKind(referencedPath);
            JsonNode locReferencedSchema;
            try {
                locReferencedSchema = jsonMapper.readTree(referencedPath.toFile());
            } catch (IOException ex) {
                throw new IllegalArgumentException("Cannot resolve schema reference '" + ref + "' in " + request.path(), ex);
            }
            nullable = nullable && AIcJsonSchemaNullability.acceptsNull(locReferencedSchema);
            return new AIcdPropertyDefinition(name, AInValueKind.REFERENCE, required, nullable, null,
                    new AIcdDefinitionReference(ref, parsed.version(), parsed.logicalName(), targetKind), text(node, "description"));
        }
        AInValueKind kind = type == null && (!enumValues(node).isEmpty() || node.has("const"))
                ? kindFromValue(node) : kind(type);
        AIcdPropertyDefinition item = kind == AInValueKind.ARRAY && node.get("items") != null
                ? property(name, node.get("items"), true, request, new HashSet<>(visited)) : null;
        return new AIcdPropertyDefinition(name, kind, required, nullable,
                item == null ? null : item.valueKind(), item == null ? null : item.reference(), text(node, "description"),
                AIcScalarConstraints.json(node, kind), item == null ? AIcdValueConstraints.empty() : item.constraints());
    }

    /** Walks owned source roots without visiting transient build outputs or generated-source copies. */
    private static Stream<Path> AIcCanonicalReferenceFiles(Path aRoot) throws IOException {
        List<Path> locFiles = new ArrayList<>();
        boolean locRepository = Files.isRegularFile(aRoot.resolve("modustro-source-repository.yml"));
        Files.walkFileTree(aRoot, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult preVisitDirectory(Path aDirectory, BasicFileAttributes aAttributes) {
                if (aDirectory.equals(aRoot)) return FileVisitResult.CONTINUE;
                String locName = aDirectory.getFileName().toString();
                if (locName.startsWith(".") || locName.equals("__pycache__")
                    || locName.endsWith(".gen") || locName.endsWith(".extgen")) {
                    return FileVisitResult.SKIP_SUBTREE;
                }
                if (locRepository && (locName.equals("build") || locName.equals("run"))
                    && (aDirectory.getParent().equals(aRoot)
                        || Files.isRegularFile(aDirectory.getParent().resolve("modustro-artifact.yml")))) {
                    return FileVisitResult.SKIP_SUBTREE;
                }
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFile(Path aFile, BasicFileAttributes aAttributes) {
                if (aAttributes.isRegularFile()) locFiles.add(aFile);
                return FileVisitResult.CONTINUE;
            }
        });
        return locFiles.stream();
    }

    /** Resolves canonical URLs from the checked-out definition roots without network downloads. */
    private static Path referencePath(String resource, AIcdDefinitionLoadRequest request) {
        if (resource.isEmpty()) return request.path();
        URI uri = URI.create(resource);
        if (!uri.isAbsolute()) return request.path().toAbsolutePath().getParent().resolve(resource).normalize();
        if ("file".equals(uri.getScheme())) return Path.of(uri);
        for (String sourceKind : List.of("yamldefs", "jsondefs")) {
            String marker = "/" + sourceKind + "/";
            String uriPath = uri.getPath();
            int index = uriPath == null ? -1 : uriPath.indexOf(marker);
            if (index < 0) continue;
            for (Path ancestor = request.path().toAbsolutePath().getParent(); ancestor != null; ancestor = ancestor.getParent()) {
                if (ancestor.getFileName() == null || !ancestor.getFileName().toString().equals(sourceKind)) continue;
                Path candidate = ancestor.resolve(uriPath.substring(index + marker.length())).normalize();
                if (candidate.startsWith(ancestor) && Files.isRegularFile(candidate)) return candidate;
            }
            for (Path ancestor = request.path().toAbsolutePath().getParent(); ancestor != null; ancestor = ancestor.getParent()) {
                if (!Files.isRegularFile(ancestor.resolve("modustro-source-repository.yml"))) continue;
                String suffix = "/src/product/" + sourceKind + "/" + uriPath.substring(index + marker.length());
                try (var files = AIcCanonicalReferenceFiles(ancestor)) {
                    List<Path> matches = files.filter(Files::isRegularFile)
                            .filter(path -> path.toString().replace('\\', '/').endsWith(suffix)).toList();
                    if (matches.size() == 1) return matches.get(0);
                    if (matches.size() > 1) throw new IllegalArgumentException("Ambiguous local schema reference '" + resource + "'.");
                } catch (IOException ex) { throw new IllegalArgumentException("Cannot discover local schema reference '" + resource + "'.", ex); }
                break;
            }
        }
        for (Path ancestor = request.path().toAbsolutePath().getParent(); ancestor != null; ancestor = ancestor.getParent()) {
            boolean definitions = ancestor.getFileName() != null && Set.of("yamldefs", "jsondefs").contains(ancestor.getFileName().toString());
            boolean repository = Files.isRegularFile(ancestor.resolve("modustro-source-repository.yml"));
            if (!definitions && !repository) continue;
            List<Path> matches = new ArrayList<>();
            try (var files = AIcCanonicalReferenceFiles(ancestor)) {
                for (Path file : files.filter(Files::isRegularFile).filter(path -> path.toString().endsWith(".schema.json")
                        || path.toString().endsWith(".yaml") || path.toString().endsWith(".yml")).toList()) {
                    if (repository && !file.toString().replace('\\', '/').contains("/src/product/")) continue;
                    JsonNode document = file.toString().endsWith(".json") ? new ObjectMapper().readTree(file.toFile())
                            : new ObjectMapper(new YAMLFactory()).readTree(file.toFile());
                    if (resource.equals(text(document, "$id")) || resource.equals(text(document, "x-yamldefs-id"))
                            || resource.equals(text(document, "x-jsondefs-id"))) matches.add(file);
                }
            } catch (IOException ex) { throw new IllegalArgumentException("Cannot discover schema identity '" + resource + "'.", ex); }
            if (matches.size() == 1) return matches.get(0);
            if (matches.size() > 1) throw new IllegalArgumentException("Ambiguous local schema identity '" + resource + "'.");
            if (repository) break;
        }
        throw new IllegalArgumentException("Schema reference '" + resource + "' has no local canonical definition for " + request.path());
    }

    /** Extracts the structural contract of allOf compositions, including referenced root documents. */
    private JsonNode structural(JsonNode node, AIcdDefinitionLoadRequest request, Set<String> visited) {
        ObjectNode result = node.deepCopy();
        String ref = text(node, "$ref");
        List<JsonNode> branches = new ArrayList<>();
        if (ref != null) {
            String resource = ref.split("#", 2)[0];
            String fragment = URI.create(ref).getFragment();
            Path target = referencePath(resource, request);
            String key = target.toAbsolutePath().normalize() + "#" + (fragment == null ? "" : fragment);
            if (!visited.add(key)) throw new IllegalArgumentException("Circular schema composition '" + ref + "' in " + request.path());
            try {
                String name = target.getFileName().toString().toLowerCase();
                JsonNode document = (name.endsWith(".yaml") || name.endsWith(".yml")) ? yamlMapper.readTree(target.toFile()) : jsonMapper.readTree(target.toFile());
                JsonNode referenced = fragment == null || fragment.isEmpty() ? document : fragment.startsWith("/") ? document.at(fragment) : anchor(document, fragment);
                if (referenced == null || referenced.isMissingNode()) throw new IllegalArgumentException("Undefined schema reference '" + ref + "' in " + request.path());
                branches.add(structural(referenced, new AIcdDefinitionLoadRequest(target, request.sourceKind(), request.namingProfile()), visited));
            } catch (IOException ex) { throw new IllegalArgumentException("Cannot read schema composition '" + ref + "'.", ex); }
            visited.remove(key);
        }
        JsonNode allOf = node.get("allOf");
        if (allOf != null && allOf.isArray()) for (JsonNode branch : allOf) branches.add(structural(branch, request, visited));
        ObjectNode properties = jsonMapper.createObjectNode();
        Set<String> required = new java.util.LinkedHashSet<>();
        branches.add(node);
        for (JsonNode branch : branches) {
            if (branch.has("properties")) properties.setAll((ObjectNode) branch.get("properties"));
            if (branch.has("required")) branch.get("required").forEach(value -> required.add(value.asText()));
            if (branch.has("type") && !result.has("type")) result.set("type", branch.get("type"));
        }
        if (!properties.isEmpty()) result.set("properties", properties);
        if (!required.isEmpty()) { var array = result.putArray("required"); required.forEach(array::add); }
        return result;
    }

    /** Finds a named JSON Schema anchor without treating it as a versioned file name. */
    private static JsonNode anchor(JsonNode node, String name) {
        if (name.equals(text(node, "$anchor"))) return node;
        if (node != null && node.isContainerNode()) {
            for (JsonNode child : node) {
                JsonNode match = anchor(child, name);
                if (match != null) return match;
            }
        }
        return null;
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
            enumNode.forEach(value -> {
                /* JSON null is represented by nullable data, never a string enum member. */
                if (!value.isNull()) result.add(new AIcdEnumValueDefinition(value.asText(), descriptions.get(value.asText())));
            });
            return result;
        }
        return oneOfValues;
    }

    /** Infer the non-null primitive type of an untyped enum or constant. */
    private static AInValueKind kindFromValue(JsonNode aNode) {
        JsonNode locValues = aNode.get("enum");
        JsonNode locFirst = null;
        if (locValues != null && locValues.isArray()) {
            for (JsonNode locValue : locValues) {
                if (!locValue.isNull()) { locFirst = locValue; break; }
            }
        }
        if (locFirst == null) locFirst = aNode.get("const");
        if (locFirst == null || locFirst.isNull()) return AInValueKind.ANY;
        if (locFirst.isBoolean()) return AInValueKind.BOOLEAN;
        if (locFirst.isIntegralNumber()) return AInValueKind.INTEGER;
        if (locFirst.isNumber()) return AInValueKind.NUMBER;
        return locFirst.isTextual() ? AInValueKind.STRING : AInValueKind.ANY;
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
