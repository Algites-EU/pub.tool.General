package eu.algites.tool.codegen.defs;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import eu.algites.lib.naming.convention.AIcAlgitesNamingProfiles;
import eu.algites.lib.naming.convention.AIcdNamingProfile;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.net.URI;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** Contract-only generator. Owns AIig interfaces and enums but never implementation output roots. */
public final class AIcSchemaContractBindingsGenerator {
    private final ObjectMapper mapper = new ObjectMapper()
            .enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private final AIcJsonSchemaReader reader = new AIcJsonSchemaReader();
    private record AIcdUnit(String schema, String pointer, String name, JsonNode node, JsonNode document) { }

    /** Generate only read contracts/enums. Implementation generation belongs to SdoCodegen. */
    public List<Map<String, String>> generateRepository(Path repository, Path manifestFile, boolean check) throws IOException {
        repository = repository.toAbsolutePath().normalize();
        JsonNode manifest = mapper.readTree(manifestFile.toFile());
        Path intf = inside(repository, manifest.required("artifact").asText());
        Map<String, JsonNode> overrides = new LinkedHashMap<>();
        for (JsonNode entry : manifest.path("bindings")) overrides.put(entry.required("schema").asText() + "#" + entry.path("pointer").asText(), entry);
        List<AIcdUnit> units = new ArrayList<>();
        for (String kind : List.of("jsondefs", "yamldefs", "xmldefs")) {
            Path root = intf.resolve("src/product/" + kind);
            if (!Files.isDirectory(root)) continue;
            String suffix = switch (kind) {
                case "jsondefs" -> ".jsondef.schema.json";
                case "yamldefs" -> ".yamldef.schema.json";
                default -> ".xsd";
            };
            try (var paths = Files.walk(root)) {
                for (Path source : paths.filter(Files::isRegularFile).sorted().toList()) {
                    if (!source.getFileName().toString().endsWith(suffix)) continue;
                    String schema = portable(repository.relativize(source));
                    JsonNode document = kind.equals("xmldefs") ? mapper.createObjectNode() : mapper.readTree(source.toFile());
                    String base = source.getFileName().toString().substring(0, source.getFileName().toString().length() - suffix.length()).replaceFirst("_[0-9]+$", "");
                    if (kind.equals("xmldefs")) {
                        units.add(new AIcdUnit(schema, "", base, mapper.createObjectNode(), document));
                    } else collect(document, "", base, schema, document, overrides, units);
                }
            }
        }
        for (String key : overrides.keySet()) {
            if (units.stream().noneMatch(unit -> (unit.schema + "#" + unit.pointer).equals(key))) {
                throw new IllegalArgumentException("Binding override no longer identifies a schema object: " + key);
            }
        }
        Map<Path, String> pending = new TreeMap<>();
        List<Map<String, String>> result = new ArrayList<>();
        Map<String, List<AIcdCodeGenerationRequest>> requests = new LinkedHashMap<>();
        Map<String, AIcdCodeGenerationRequest> unitRequests = new LinkedHashMap<>();
        Map<String, List<AIcdUnit>> relations = new LinkedHashMap<>();
        Map<String, AIcdUnit> unitIndex = new LinkedHashMap<>();
        for (AIcdUnit unit : units) unitIndex.put(unit.schema + "#" + unit.pointer, unit);
        for (AIcdUnit unit : units) {
            Path source = inside(repository, unit.schema);
            String sourceKind = unit.schema.contains("/yamldefs/") ? "yamldefs"
                    : unit.schema.contains("/xmldefs/") ? "xmldefs" : "jsondefs";
            Path schemaRoot = intf.resolve("src/product/" + sourceKind);
            String packageName = portable(schemaRoot.relativize(source.getParent())).replace('/', '.');
            if (!packageName.matches("[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)*")) {
                throw new IllegalArgumentException("Schema must have a legal package path: " + unit.schema);
            }
            ObjectNode projection = ((ObjectNode) unit.node).deepCopy();
            if (!sourceKind.equals("xmldefs")) {
                if (unit.document.has("$defs")) projection.set("$defs", unit.document.get("$defs"));
                projection.put("x-jsondefs-id", unit.document.path("$id").asText(unit.schema)
                        + (unit.pointer.isEmpty() ? "" : "#" + unit.pointer));
                projection.put("x-jsondefs-name", unit.name);
            }
            AIcdUnit parentUnit = sourceKind.equals("xmldefs") ? null : parentUnit(unit, unitIndex, repository);
            for (JsonNode language : manifest.required("languages")) {
                String targetText = language.asText();
                AInCodeGenerationTarget target = switch (targetText) {
                    case "python" -> AInCodeGenerationTarget.PYTHON;
                    case "java" -> AInCodeGenerationTarget.JAVA;
                    default -> throw new IllegalArgumentException("Unsupported target: " + targetText);
                };
                AIcdNamingProfile profile = target == AInCodeGenerationTarget.PYTHON
                    ? AIcAlgitesNamingProfiles.pythonProfile() : AIcAlgitesNamingProfiles.javaProfile();
                var sourceType = switch (sourceKind) {
                    case "yamldefs" -> AInDefinitionSourceKind.YAMLDEFS;
                    case "xmldefs" -> AInDefinitionSourceKind.XMLDEFS;
                    default -> AInDefinitionSourceKind.JSONDEFS;
                };
                var load = new AIcdDefinitionLoadRequest(source, sourceType, profile);
                var loaded = sourceKind.equals("xmldefs") ? new AIcXmlDefsFrontend().load(load)
                        : reader.read(projection, load, load.sourceKind(), "x-jsondefs-id", "x-jsondefs-version", "x-jsondefs-name");
                var definition = new AIcdCanonicalDefinition(loaded.identity(), loaded.version(), loaded.logicalName(),
                    loaded.kind(), loaded.sourceKind(), unit.schema + (unit.pointer.isEmpty() ? "" : "#" + unit.pointer),
                    loaded.description(), loaded.properties(), loaded.enumValues());
                var request = new AIcdCodeGenerationRequest(definition, target, packageName, profile);
                var preview = new AIcSchemaContractInterfaceGenerator().generate(request);
                String outputKey = targetText + "#" + preview.relativePath();
                requests.computeIfAbsent(outputKey, key -> new ArrayList<>()).add(request);
                unitRequests.put(targetText + "#" + unit.schema + "#" + unit.pointer, request);
                relations.computeIfAbsent(outputKey, key -> new ArrayList<>()).add(parentUnit);
                result.add(Map.of("schema", unit.schema, "pointer", unit.pointer, "language", targetText, "type", preview.typeName(),
                    "path", portable(repository.relativize(intf.resolve("src/product/" + targetText + ".gen").resolve(preview.relativePath())))));
            }
        }
        for (var representations : requests.values()) {
            var first = representations.get(0);
            if (representations.stream().map(r -> r.definition().sourceKind()).distinct().count() != representations.size()) {
                throw new IllegalArgumentException("Different objects resolve to the same generated type: "
                    + representations.stream().map(r -> r.definition().sourceResource()).toList());
            }
            var merged = AIcCanonicalDefinitionMerger.AIcMerge(representations.stream().map(AIcdCodeGenerationRequest::definition).toList());
            String targetText = first.target() == AInCodeGenerationTarget.PYTHON ? "python" : "java";
            String outputKey = targetText + "#" + new AIcSchemaContractInterfaceGenerator().generate(first).relativePath();
            List<AIcdUnit> linked = relations.get(outputKey);
            var inheritedRequests = linked.stream().map(u -> u == null ? null
                : unitRequests.get(targetText + "#" + u.schema + "#" + u.pointer)).toList();
            long parentKinds = inheritedRequests.stream().map(q -> q == null ? ""
                : q.packageName() + "." + new AIcSchemaContractInterfaceGenerator().generate(q).typeName()).distinct().count();
            if (parentKinds != 1) throw new IllegalArgumentException("Conflicting inherited contracts across schema representations");
            String parentName = null, parentModule = null;
            if (inheritedRequests.get(0) != null) {
                AIcdCodeGenerationRequest inherited = inheritedRequests.get(0);
                if (merged.kind() != AInDefinitionKind.OBJECT || inherited.definition().kind() != AInDefinitionKind.OBJECT)
                    throw new IllegalArgumentException("allOf inheritance must connect object contracts");
                Map<String, AIcdPropertyDefinition> inheritedFields = new LinkedHashMap<>();
                for (var field : inherited.definition().properties()) inheritedFields.put(field.sourceName(), field);
                for (var field : merged.properties()) {
                    var previous = inheritedFields.get(field.sourceName());
                    if (previous != null && !fieldShape(previous).equals(fieldShape(field)))
                        throw new IllegalArgumentException("Conflicting inherited field: " + field.sourceName());
                }
                merged = new AIcdCanonicalDefinition(merged.identity(), merged.version(), merged.logicalName(), merged.kind(),
                    merged.sourceKind(), merged.sourceResource(), merged.description(), merged.properties().stream()
                    .filter(f -> !inheritedFields.containsKey(f.sourceName())).toList(), merged.enumValues());
                var parentSource = new AIcSchemaContractInterfaceGenerator().generate(inherited);
                parentName = parentSource.typeName();
                parentModule = inherited.packageName();
                if (first.target() == AInCodeGenerationTarget.PYTHON)
                    parentModule += "." + Path.of(parentSource.relativePath()).getFileName().toString().replaceFirst("\\.py$", "");
            }
            var pair = new AIcSchemaContractInterfaceGenerator().generate(
                new AIcdCodeGenerationRequest(merged, first.target(), first.packageName(), first.namingProfile()),
                parentName, parentModule);
            add(pending, intf.resolve("src/product/" + targetText + ".gen").resolve(pair.relativePath()), qualifyReferences(pair.source(), first, requests, true));
        }
        Path state = repository.resolve("build/run/schema-contract-bindings/generated-files.json");
        List<String> previous = Files.isRegularFile(state) ? mapper.readValue(state.toFile(), mapper.getTypeFactory().constructCollectionType(List.class, String.class)) : List.of();
        /* Only recorded files owned by this generator may be removed. */
        for (String old : previous) {
            Path stale = inside(repository, old);
            if (!hasGeneratedRoot(stale)) throw new IllegalArgumentException("Invalid ownership state: " + old);
            if (!pending.containsKey(stale) && Files.exists(stale)) {
                if (check) throw new IllegalStateException("Stale generated binding: " + old);
                Files.delete(stale);
            }
        }
        for (var entry : pending.entrySet()) {
            Path path = entry.getKey();
            if (check) {
                if (!Files.isRegularFile(path) || !Files.readString(path).equals(entry.getValue())) throw new IllegalStateException("Missing or outdated generated binding: " + path);
            } else {
                Files.createDirectories(path.getParent());
                if (!Files.isRegularFile(path) || !Files.readString(path).equals(entry.getValue())) Files.writeString(path, entry.getValue(), StandardCharsets.UTF_8);
            }
        }
        if (!check) {
            Files.createDirectories(state.getParent());
            mapper.writerWithDefaultPrettyPrinter().writeValue(state.toFile(), pending.keySet().stream().map(repository::relativize).map(AIcSchemaContractBindingsGenerator::portable).toList());
        }
        return result;
    }

    /** Keep canonical inherited field compatibility independent of documentation. */
    private static List<Object> fieldShape(AIcdPropertyDefinition aField) {
        return java.util.Arrays.asList(aField.sourceName(), aField.valueKind(), aField.required(),
            aField.nullable(), aField.itemValueKind(), aField.reference(), aField.constraints(), aField.itemConstraints());
    }

    /** Resolve exactly one local or canonical-identity allOf parent into an emitted contract. */
    private static AIcdUnit parentUnit(AIcdUnit aUnit, Map<String, AIcdUnit> aIndex, Path aRepository) {
        JsonNode locAllOf = aUnit.node.path("allOf");
        if (locAllOf.isMissingNode()) return null;
        if (!locAllOf.isArray()) throw new IllegalArgumentException("allOf must be an array");
        List<String> locReferences = new ArrayList<>();
        for (JsonNode locPart : locAllOf) if (locPart.has("$ref")) locReferences.add(locPart.path("$ref").asText());
        if (locReferences.isEmpty()) return null;
        if (locReferences.size() != 1) throw new IllegalArgumentException("Exactly one allOf parent is supported");
        String locReference = locReferences.get(0);
        URI locUri = URI.create(locReference);
        String locPointer = locUri.getRawFragment() == null ? "" : java.net.URLDecoder.decode(locUri.getRawFragment(), java.nio.charset.StandardCharsets.UTF_8);
        if (!locPointer.isEmpty() && !locPointer.startsWith("/"))
            throw new IllegalArgumentException("Unsupported allOf parent anchor: " + locReference);
        if (locUri.isAbsolute() && !locUri.getScheme().equals("file")) {
            var locCandidates = aIndex.values().stream().filter(u ->
                u.document.path("$id").asText().equals(locReference.split("#", 2)[0])
                && u.pointer.equals(locPointer)).toList();
            if (locCandidates.size() != 1) throw new IllegalArgumentException("Unresolved allOf parent: " + locReference);
            return locCandidates.get(0);
        }
        Path locSource = aRepository.resolve(aUnit.schema);
        Path locParent = (locUri.isAbsolute() ? Path.of(locUri.getPath()) : locUri.getPath().isEmpty() ? locSource
                : locSource.getParent().resolve(locUri.getPath())).toAbsolutePath().normalize();
        if (!locParent.startsWith(aRepository)) throw new IllegalArgumentException("allOf parent escapes repository: " + locReference);
        AIcdUnit locUnit = aIndex.get(portable(aRepository.relativize(locParent)) + "#" + locPointer);
        if (locUnit == null) throw new IllegalArgumentException("allOf parent is not an emitted contract: " + locReference);
        return locUnit;
    }

    private static String qualifyReferences(String source, AIcdCodeGenerationRequest request,
            Map<String, List<AIcdCodeGenerationRequest>> requests, boolean contract) {
        var names = new AIcGenerationNames();
        for (var property : request.definition().properties()) {
            var ref = property.reference();
            if (ref == null) continue;
            String resource = ref.identity().split("#", 2)[0];
            String owner = request.definition().sourceResource().split("#", 2)[0];
            String local = java.net.URI.create(resource).isAbsolute() ? null : portable(Path.of(owner).getParent().resolve(resource).normalize());
            var candidates = requests.values().stream().flatMap(List::stream).filter(candidate ->
                candidate.target() == request.target() && (candidate.definition().sourceResource().equals(local)
                    || candidate.definition().identity().equals(resource))).map(AIcdCodeGenerationRequest::packageName).distinct().toList();
            if (candidates.size() != 1) throw new IllegalArgumentException("Cannot resolve generated reference package: " + ref.identity() + " in " + owner);
            String packageName = candidates.get(0);
            if (packageName.equals(request.packageName())) continue;
            boolean isEnum = ref.targetKind() == AInDefinitionKind.ENUM;
            var typeKind = isEnum ? eu.algites.lib.naming.convention.AInOutputNameKind.ENUM_TYPE : contract
                ? eu.algites.lib.naming.convention.AInOutputNameKind.INTERFACE_TYPE : eu.algites.lib.naming.convention.AInOutputNameKind.DATA_TYPE;
            var fileKind = isEnum ? eu.algites.lib.naming.convention.AInOutputNameKind.ENUM_TYPE_FILE_STEM : contract
                ? eu.algites.lib.naming.convention.AInOutputNameKind.INTERFACE_TYPE_FILE_STEM : eu.algites.lib.naming.convention.AInOutputNameKind.DATA_TYPE_FILE_STEM;
            String type = names.referenceTypeName(ref.logicalName(), ref.version(), request.namingProfile(), typeKind);
            if (request.target() == AInCodeGenerationTarget.PYTHON) {
                String file = names.referenceTypeName(ref.logicalName(), ref.version(), request.namingProfile(), fileKind);
                source = source.replace("from ." + file + " import " + type, "from " + packageName + "." + file + " import " + type);
            } else source = source.replaceAll("(?<![A-Za-z0-9_$.])" + java.util.regex.Pattern.quote(type) + "\\b", java.util.regex.Matcher.quoteReplacement(packageName + "." + type));
        }
        return source;
    }

    private void collect(JsonNode node, String pointer, String name, String schema, JsonNode document,
                         Map<String, JsonNode> overrides, List<AIcdUnit> result) {
        if (!node.isObject()) return;
        JsonNode override = overrides.get(schema + "#" + pointer);
        if (override != null && override.path("common_one_of_fields").asBoolean()) node = commonFields(node, document);
        if (pointer.isEmpty() || node.path("type").asText().equals("object") || node.has("properties") || node.has("enum")) {
            result.add(new AIcdUnit(schema, pointer, override == null ? name : override.required("name").asText(), node, document));
        }
        /* Visit schema-bearing keywords; examples, defaults and documentation are not definitions. */
        for (String map : List.of("properties", "$defs", "definitions", "patternProperties")) {
            var entries = node.path(map).fields();
            while (entries.hasNext()) {
                var entry = entries.next();
                String token = entry.getKey().replace("~", "~0").replace("/", "~1");
                collect(entry.getValue(), pointer + "/" + map + "/" + token, name + (map.equals("$defs") || map.equals("definitions") ? "-definition-" : map.equals("patternProperties") ? "-pattern-" : "-") + kebab(entry.getKey()), schema, document, overrides, result);
            }
        }
        for (String single : List.of("items", "additionalProperties", "contains", "not", "if", "then", "else", "unevaluatedProperties")) {
            collect(node.path(single), pointer + "/" + single, name + "-" + kebab(single), schema, document, overrides, result);
        }
        for (String array : List.of("oneOf", "anyOf", "allOf", "prefixItems")) {
            JsonNode variants = node.path(array);
            for (int i = 0; i < variants.size(); i++) collect(variants.get(i), pointer + "/" + array + "/" + i, name + "-" + kebab(array) + "-" + i, schema, document, overrides, result);
        }
    }

    private ObjectNode commonFields(JsonNode node, JsonNode document) {
        List<JsonNode> variants = new ArrayList<>();
        for (JsonNode variant : node.required("oneOf")) {
            String ref = variant.required("$ref").asText();
            if (!ref.startsWith("#/")) throw new IllegalArgumentException("A shared contract requires local object variants");
            JsonNode resolved = document.at(ref.substring(1));
            if (!resolved.has("properties")) throw new IllegalArgumentException("Missing union object: " + ref);
            variants.add(resolved);
        }
        if (variants.isEmpty()) throw new IllegalArgumentException("Empty union");
        ObjectNode result = mapper.createObjectNode(); result.put("type", "object");
        ObjectNode properties = result.putObject("properties");
        var names = variants.get(0).required("properties").fieldNames();
        while (names.hasNext()) {
            String name = names.next(); JsonNode value = variants.get(0).get("properties").get(name);
            if (variants.stream().anyMatch(v -> !v.get("properties").has(name) || v.get("properties").size() != variants.get(0).get("properties").size())) throw new IllegalArgumentException("Union variants no longer have the same fields");
            if (variants.stream().allMatch(v -> value.equals(v.get("properties").get(name)))) properties.set(name, value);
            else properties.putObject(name).put("type", "string");
        }
        var required = result.putArray("required");
        for (JsonNode field : variants.get(0).path("required")) if (variants.stream().allMatch(v -> contains(v.path("required"), field))) required.add(field.asText());
        result.put("description", "Shared field contract of every value-source variant.");
        return result;
    }

    private static boolean contains(JsonNode values, JsonNode value) { for (JsonNode item : values) if (item.equals(value)) return true; return false; }
    private static String kebab(String name) { return name.replaceAll("([a-z0-9])([A-Z])", "$1-$2").replaceAll("[^A-Za-z0-9]+", "-").replaceAll("^-|-$", "").toLowerCase(java.util.Locale.ROOT); }
    private static void add(Map<Path, String> pending, Path path, String source) { if (pending.putIfAbsent(path.normalize(), source) != null) throw new IllegalArgumentException("Generated type collision: " + path); }
    private static Path inside(Path repository, String relative) { Path path = repository.resolve(relative).normalize(); if (!path.startsWith(repository) || Path.of(relative).isAbsolute()) throw new IllegalArgumentException("Path escapes repository: " + relative); return path; }
    private static String portable(Path path) { return path.toString().replace('\\', '/'); }
    private static boolean hasGeneratedRoot(Path path) { for (Path part : path) if (part.toString().endsWith(".gen")) return true; return false; }

    /** Standalone JVM entry point for local tools; Gradle calls the same generator API directly. */
    public static void main(String[] args) throws IOException {
        if (args.length < 2 || args.length > 4) throw new IllegalArgumentException("Usage: <repository> <manifest> [--check] [--json]");
        boolean check = false, json = false;
        for (int i = 2; i < args.length; i++) {
            if (args[i].equals("--check")) check = true;
            else if (args[i].equals("--json")) json = true;
            else throw new IllegalArgumentException("Unknown option: " + args[i]);
        }
        var generator = new AIcSchemaContractBindingsGenerator();
        var result = generator.generateRepository(Path.of(args[0]), Path.of(args[1]), check);
        System.out.println(json ? generator.mapper.writerWithDefaultPrettyPrinter().writeValueAsString(result)
            : (check ? "Verified " : "Generated ") + result.size() + " schema representations.");
    }
}
