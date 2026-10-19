package eu.algites.tool.codegen.defs.impl.standard;







import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdDefinitionReference;
import eu.algites.tool.codegen.defs.AIcdEnumValueDefinition;
import eu.algites.tool.codegen.defs.AIcdParsedVersionedName;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
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
        /* Algites logical SchemaId must never be reconstructed from JSON Schema $id,
         * which is a URI resource identifier and may be the published SchemaUrl. */
        String identity = text(root, "x-algites-schema-id");
        if (identity == null || identity.isBlank()) identity = text(root, idExtension);
        if (identity == null || identity.isBlank()) identity = text(root, "$id");
        if (identity == null || identity.isBlank()) identity = parsed.logicalName();
        Integer version = explicitVersion != null ? explicitVersion : parsed.version();
        String description = text(root, "description");
        String title = text(root, "title");
        root = structural(root, request, new HashSet<>());
        List<AIcdEnumValueDefinition> enumValues = enumValues(root);
        if (!enumValues.isEmpty()) {
            return new AIcdCanonicalDefinition(identity, version, logicalName, sourceKind, request.path().toString(), description, AIcdDataType.atom(AInDataTypeKind.ENUM, AIcdValueConstraints.empty()), enumValues, title);
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
            return new AIcdCanonicalDefinition(identity, version, logicalName, sourceKind, request.path().toString(), description, recursiveType(root, request), List.of(), title);
        }
        return new AIcdCanonicalDefinition(identity, version, logicalName, sourceKind, request.path().toString(), description, recursiveType(root, request), List.of(), title);
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
            AIcdDataType locCanonicalType = recursiveType(node, request);
            boolean locNamed = locCanonicalType.kind() == AInDataTypeKind.REFERENCE;
            return new AIcdPropertyDefinition(name, locNamed ? locCanonicalType : normalized.dataType(), ((required) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), nullable && normalized.nullable(), text(node, "description") == null ? normalized.description() : text(node, "description"), text(node, "title") == null ? normalized.title() : text(node, "title"), null);
        }
        if (ref != null) {
            String resource = ref.split("#", 2)[0];
            Path referencedPath = referencePath(resource, request);
            String stem = AIcDefinitionIdentityResolver.stripDefinitionExtensions(referencedPath.getFileName().toString());
            AIcdParsedVersionedName parsed = AIcDefinitionIdentityResolver.parseVersionedStem(stem, null);
            AInDataTypeKind targetKind = detectReferencedKind(referencedPath);
            JsonNode locReferencedSchema;
            try {
                locReferencedSchema = jsonMapper.readTree(referencedPath.toFile());
            } catch (IOException ex) {
                throw new IllegalArgumentException("Cannot resolve schema reference '" + ref + "' in " + request.path(), ex);
            }
            nullable = nullable && AIcJsonSchemaNullability.acceptsNull(locReferencedSchema);
            return new AIcdPropertyDefinition(name, AIcSourceDataType.fromSourceHints(AInDataTypeKind.REFERENCE, null, new AIcdDefinitionReference(ref, parsed.version(), parsed.logicalName(), targetKind == null ? null : AIcdDataType.atom(targetKind, null)), AIcdValueConstraints.empty(), AIcdValueConstraints.empty()), ((required) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), nullable, text(node, "description"), text(node, "title"), null);
        }
        AInDataTypeKind kind = type == null && (!enumValues(node).isEmpty() || node.has("const"))
                ? kindFromValue(node) : kind(type);
        AIcdPropertyDefinition item = kind == AInDataTypeKind.ARRAY && node.get("items") != null
                ? property(name, node.get("items"), true, request, new HashSet<>(visited)) : null;
        return new AIcdPropertyDefinition(name, recursiveType(node, request), ((required) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), nullable, text(node, "description"), text(node, "title"), null);
    }

    /** Build the recursive structural model without truncating nested array or choice types. */
    private AIcdDataType recursiveType(JsonNode aSchema, AIcdDefinitionLoadRequest aRequest) {
        if (aSchema == null || aSchema.isNull() || !aSchema.isObject())
            return AIcdDataType.atom(AInDataTypeKind.ANY, AIcdValueConstraints.empty());
        /* A typed scalar enum may use oneOf only for per-value descriptions.
         * It remains a scalar when all const branches exactly enumerate the
         * declared enum without introducing additional structural restrictions. */
        JsonNode locEnum = aSchema.get("enum");
        JsonNode locOneOf = aSchema.get("oneOf");
        String locDeclaredType = text(aSchema, "type");
        if (locEnum != null && locEnum.isArray() && !locEnum.isEmpty()
                && locOneOf != null && locOneOf.isArray() && locOneOf.size() == locEnum.size()
                && List.of("string", "integer", "number", "boolean").contains(locDeclaredType)) {
            Set<String> locValues = new HashSet<>();
            locEnum.forEach(aValue -> locValues.add(aValue.toString()));
            Set<String> locBranchValues = new HashSet<>();
            boolean locPureDocumentation = true;
            for (JsonNode locBranch : locOneOf) {
                if (!locBranch.isObject() || !locBranch.has("const")) {
                    locPureDocumentation = false;
                    break;
                }
                for (java.util.Iterator<String> locNames = locBranch.fieldNames(); locNames.hasNext();) {
                    if (!Set.of("const", "title", "description").contains(locNames.next())) {
                        locPureDocumentation = false;
                        break;
                    }
                }
                locBranchValues.add(locBranch.path("const").toString());
            }
            if (locPureDocumentation && locBranchValues.size() == locOneOf.size()
                    && locBranchValues.equals(locValues)) {
                AInDataTypeKind locScalarKind = kind(locDeclaredType);
                return AIcdDataType.atom(locScalarKind,
                        AIcScalarConstraints.json(aSchema, locScalarKind));
            }
        }
        for (String locKey : List.of("oneOf", "anyOf")) {
            JsonNode locBranches = aSchema.get(locKey);
            if (locBranches != null && locBranches.isArray() && !locBranches.isEmpty()) {
                List<AIcdDataType> locAlternatives = new ArrayList<>();
                for (JsonNode locBranch : locBranches) locAlternatives.add(recursiveType(locBranch, aRequest));
                return AIcdDataType.choice(locKey.equals("oneOf")
                        ? AInDataTypeKind.ONE_OF : AInDataTypeKind.ANY_OF, locAlternatives);
            }
        }
        String locRef = text(aSchema, "$ref");
        if (locRef != null) {
            String locResource = locRef.split("#", 2)[0];
            String locFragment = URI.create(locRef).getFragment();
            if (locFragment == null || locFragment.isEmpty())
                return property("reference", aSchema, false, aRequest).dataType();
            Path locTarget = referencePath(locResource, aRequest);
            try {
                String locName = locTarget.getFileName().toString().toLowerCase();
                JsonNode locDocument = (locName.endsWith(".yaml") || locName.endsWith(".yml"))
                        ? yamlMapper.readTree(locTarget.toFile()) : jsonMapper.readTree(locTarget.toFile());
                JsonNode locResolved = locFragment.startsWith("/") ? locDocument.at(locFragment)
                        : anchor(locDocument, locFragment);
                if (locResolved == null || locResolved.isMissingNode())
                    throw new IllegalArgumentException("Undefined schema reference '" + locRef + "'");
                String[] locTokens = locFragment.startsWith("/") ? locFragment.substring(1).split("/") : new String[0];
                if (locTokens.length == 2 && (locTokens[0].equals("$defs") || locTokens[0].equals("definitions"))
                        && (locResolved.has("properties") || "object".equals(text(locResolved, "type"))
                            || locResolved.has("enum") || locResolved.has("oneOf") || locResolved.has("anyOf"))) {
                    String locStem = AIcDefinitionIdentityResolver.stripDefinitionExtensions(locTarget.getFileName().toString());
                    AIcdParsedVersionedName locParsed = AIcDefinitionIdentityResolver.parseVersionedStem(locStem, null);
                    String locToken = locTokens[1].replace("~1", "/").replace("~0", "~");
                    String locKebab = locToken.replaceAll("([a-z0-9])([A-Z])", "$1-$2")
                            .replaceAll("[^a-zA-Z0-9]+", "-").replaceAll("^-|-$", "")
                            .toLowerCase(java.util.Locale.ROOT);
                    AInDataTypeKind locKind = locResolved.has("enum") ? AInDataTypeKind.ENUM : AInDataTypeKind.OBJECT;
                    return AIcdDataType.reference(new AIcdDefinitionReference(locRef, locParsed.version(),
                            locParsed.logicalName() + "-definition-" + locKebab, AIcdDataType.atom(locKind, null)));
                }
                return recursiveType(locResolved, new AIcdDefinitionLoadRequest(locTarget,
                        aRequest.sourceKind(), aRequest.namingProfile()));
            } catch (IOException locError) {
                throw new IllegalArgumentException("Cannot read nested schema reference '" + locRef + "'", locError);
            }
        }
        String locType = text(aSchema, "type");
        if (aSchema.path("type").isArray()) {
            for (JsonNode locItem : aSchema.path("type"))
                if (!locItem.asText().equals("null")) { locType = locItem.asText(); break; }
        }
        if ("array".equals(locType) || aSchema.has("items"))
            return new AIcdDataType(AInDataTypeKind.ARRAY,
                    recursiveType(aSchema.get("items"), aRequest), List.of(), List.of(), null,
                    AIcScalarConstraints.json(aSchema, AInDataTypeKind.ARRAY));
        if ("object".equals(locType) || aSchema.has("properties")) {
            Set<String> locRequired = new HashSet<>();
            if (aSchema.path("required").isArray())
                aSchema.path("required").forEach(aItem -> locRequired.add(aItem.asText()));
            List<AIcdPropertyDefinition> locProperties = new ArrayList<>();
            JsonNode locObject = aSchema.path("properties");
            if (locObject.isObject()) locObject.fields().forEachRemaining(aEntry ->
                    locProperties.add(property(aEntry.getKey(), aEntry.getValue(),
                            locRequired.contains(aEntry.getKey()), aRequest)));
            return AIcdDataType.object(locProperties);
        }
        if (aSchema.has("enum") || aSchema.has("const"))
            return AIcdDataType.atom(locType == null ? kindFromValue(aSchema) : kind(locType),
                    AIcScalarConstraints.json(aSchema, kindFromValue(aSchema)));
        AInDataTypeKind locKind = kind(locType);
        return AIcdDataType.atom(locKind, AIcScalarConstraints.json(aSchema, locKind));
    }

    /** Walks owned source roots without visiting transient build outputs or generated-source copies. */
    private static Stream<Path> AIcCanonicalReferenceFiles(Path aRoot) throws IOException {
        List<Path> locFiles = new ArrayList<>();
        boolean locRepository = Files.isRegularFile(aRoot.resolve("modustro-source-repository.yml"));
        Files.walkFileTree(aRoot, new SimpleFileVisitor<Path>() {
            /** {@inheritDoc} */
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

            /** {@inheritDoc} */
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
            if (branch.has("properties")) {
                JsonNode locBranchProperties = branch.get("properties");
                if (!locBranchProperties.isObject())
                    throw new IllegalArgumentException("allOf properties must be a schema object in " + request.path());
                var locEntries = locBranchProperties.fields();
                while (locEntries.hasNext()) {
                    var locEntry = locEntries.next();
                    JsonNode locPrevious = properties.get(locEntry.getKey());
                    if (locPrevious != null && !locPrevious.equals(locEntry.getValue()))
                        throw new IllegalArgumentException("Conflicting allOf property schema '"
                                + locEntry.getKey() + "' in " + request.path());
                    properties.set(locEntry.getKey(), locEntry.getValue());
                }
            }
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

    private AInDataTypeKind detectReferencedKind(Path path) {
        if (!Files.isRegularFile(path)) return null;
        try {
            String fileName = path.getFileName().toString().toLowerCase();
            JsonNode root = (fileName.endsWith(".yaml") || fileName.endsWith(".yml"))
                    ? yamlMapper.readTree(path.toFile()) : jsonMapper.readTree(path.toFile());
            if (root != null && !enumValues(root).isEmpty()) return AInDataTypeKind.ENUM;
            if (root != null && ("object".equals(text(root, "type")) || root.has("properties")
                    || root.has("oneOf") || root.has("anyOf"))) return AInDataTypeKind.OBJECT;
            return AInDataTypeKind.ANY;
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
        java.util.Map<String, String> titles = new java.util.LinkedHashMap<>();
        List<AIcdEnumValueDefinition> oneOfValues = new ArrayList<>();
        JsonNode oneOf = root.get("oneOf");
        if (oneOf != null && oneOf.isArray()) {
            for (JsonNode branch : oneOf) {
                JsonNode constant = branch.get("const");
                if (constant == null || constant.isContainerNode() || constant.isNull()) continue;
                String value = constant.asText();
                String valueDescription = text(branch, "description");
                descriptions.put(value, valueDescription);
                titles.put(value, text(branch, "title"));
                oneOfValues.add(new AIcdEnumValueDefinition(value, valueDescription, text(branch, "title")));
            }
        }
        JsonNode enumNode = root.get("enum");
        if (enumNode != null && enumNode.isArray()) {
            List<AIcdEnumValueDefinition> result = new ArrayList<>();
            enumNode.forEach(value -> {
                /* JSON null is represented by nullable data, never a string enum member. */
                if (!value.isNull()) result.add(new AIcdEnumValueDefinition(value.asText(), descriptions.get(value.asText()), titles.get(value.asText())));
            });
            return result;
        }
        return oneOfValues;
    }

    /** Infer the non-null primitive type of an untyped enum or constant. */
    private static AInDataTypeKind kindFromValue(JsonNode aNode) {
        JsonNode locValues = aNode.get("enum");
        JsonNode locFirst = null;
        if (locValues != null && locValues.isArray()) {
            for (JsonNode locValue : locValues) {
                if (!locValue.isNull()) { locFirst = locValue; break; }
            }
        }
        if (locFirst == null) locFirst = aNode.get("const");
        if (locFirst == null || locFirst.isNull()) return AInDataTypeKind.ANY;
        if (locFirst.isBoolean()) return AInDataTypeKind.BOOLEAN;
        if (locFirst.isIntegralNumber()) return AInDataTypeKind.INTEGER;
        if (locFirst.isNumber()) return AInDataTypeKind.NUMBER;
        return locFirst.isTextual() ? AInDataTypeKind.STRING : AInDataTypeKind.ANY;
    }

    private static AInDataTypeKind kind(String type) {
        if (type == null) return AInDataTypeKind.ANY;
        return switch (type) {
            case "string" -> AInDataTypeKind.STRING;
            case "integer" -> AInDataTypeKind.INTEGER;
            case "number" -> AInDataTypeKind.NUMBER;
            case "boolean" -> AInDataTypeKind.BOOLEAN;
            case "array" -> AInDataTypeKind.ARRAY;
            case "object" -> AInDataTypeKind.OBJECT;
            default -> AInDataTypeKind.ANY;
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
