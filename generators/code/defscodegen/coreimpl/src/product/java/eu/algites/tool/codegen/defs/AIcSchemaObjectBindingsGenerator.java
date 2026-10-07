package eu.algites.tool.codegen.defs;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import eu.algites.lib.naming.convention.AIcAlgitesNamingProfiles;
import eu.algites.lib.naming.convention.AIcdNamingProfile;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** Repository-aware generator: one source unit per schema object, in the owning schema's package. */
public final class AIcSchemaObjectBindingsGenerator {
    private final ObjectMapper mapper = new ObjectMapper();
    private final AIcJsonSchemaReader reader = new AIcJsonSchemaReader();
    private record AIcdUnit(String schema, String pointer, String name, JsonNode node, JsonNode document) { }

    /** Generate all contracts/enums into intf and concrete types into impl. A check never modifies outputs. */
    public List<Map<String, String>> generateRepository(Path repository, Path manifestFile, boolean check) throws IOException {
        repository = repository.toAbsolutePath().normalize();
        JsonNode manifest = mapper.readTree(manifestFile.toFile());
        Path intf = inside(repository, manifest.required("artifact").asText());
        Path impl = inside(repository, manifest.required("implementation_artifact").asText());
        if (intf.equals(impl)) throw new IllegalArgumentException("Interface and implementation artifacts must differ");
        Map<String, JsonNode> overrides = new LinkedHashMap<>();
        for (JsonNode entry : manifest.path("bindings")) overrides.put(entry.required("schema").asText() + "#" + entry.path("pointer").asText(), entry);
        List<AIcdUnit> units = new ArrayList<>();
        for (String kind : List.of("jsondefs", "yamldefs")) {
            Path root = intf.resolve("src/product/" + kind);
            if (!Files.isDirectory(root)) continue;
            String suffix = kind.equals("jsondefs") ? ".jsondef.schema.json" : ".yamldef.schema.json";
            try (var paths = Files.walk(root)) {
                for (Path source : paths.filter(Files::isRegularFile).sorted().toList()) {
                    if (!source.getFileName().toString().endsWith(suffix)) continue;
                    String schema = portable(repository.relativize(source));
                    JsonNode document = mapper.readTree(source.toFile());
                    String base = source.getFileName().toString().substring(0, source.getFileName().toString().length() - suffix.length()).replaceFirst("_[0-9]+$", "");
                    collect(document, "", base, schema, document, overrides, units);
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
        for (AIcdUnit unit : units) {
            Path source = inside(repository, unit.schema);
            String sourceKind = unit.schema.contains("/yamldefs/") ? "yamldefs" : "jsondefs";
            Path schemaRoot = intf.resolve("src/product/" + sourceKind);
            String packageName = portable(schemaRoot.relativize(source.getParent())).replace('/', '.');
            if (!packageName.matches("[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)*")) {
                throw new IllegalArgumentException("Schema must have a legal package path: " + unit.schema);
            }
            ObjectNode projection = ((ObjectNode) unit.node).deepCopy();
            if (unit.document.has("$defs")) projection.set("$defs", unit.document.get("$defs"));
            projection.put("x-jsondefs-id", unit.document.path("$id").asText(unit.schema) + (unit.pointer.isEmpty() ? "" : "#" + unit.pointer));
            projection.put("x-jsondefs-name", unit.name);
            for (JsonNode language : manifest.required("languages")) {
                String targetText = language.asText();
                AInCodeGenerationTarget target = switch (targetText) {
                    case "python" -> AInCodeGenerationTarget.PYTHON;
                    case "java" -> AInCodeGenerationTarget.JAVA;
                    default -> throw new IllegalArgumentException("Unsupported target: " + targetText);
                };
                AIcdNamingProfile profile = target == AInCodeGenerationTarget.PYTHON ? AIcAlgitesNamingProfiles.pythonProfile() : AIcAlgitesNamingProfiles.javaProfile();
                var load = new AIcdDefinitionLoadRequest(source, sourceKind.equals("jsondefs") ? AInDefinitionSourceKind.JSONDEFS : AInDefinitionSourceKind.YAMLDEFS, profile);
                var loaded = reader.read(projection, load, load.sourceKind(), "x-jsondefs-id", "x-jsondefs-version", "x-jsondefs-name");
                var definition = new AIcdCanonicalDefinition(loaded.identity(), loaded.version(), loaded.logicalName(), loaded.kind(), loaded.sourceKind(),
                    unit.schema + (unit.pointer.isEmpty() ? "" : "#" + unit.pointer), loaded.description(), loaded.properties(), loaded.enumValues());
                var request = new AIcdCodeGenerationRequest(definition, target, packageName, profile);
                var preview = new AIcSchemaInterfaceGenerator().generate(request);
                requests.computeIfAbsent(targetText + "#" + preview.contract().relativePath(), key -> new ArrayList<>()).add(request);
                result.add(Map.of("schema", unit.schema, "pointer", unit.pointer, "language", targetText, "type", preview.contract().typeName(),
                    "path", portable(repository.relativize(intf.resolve("src/product/" + targetText + ".gen").resolve(preview.contract().relativePath())))));
            }
        }
        for (var representations : requests.values()) {
            var first = representations.get(0);
            if (representations.stream().map(r -> r.definition().sourceKind()).distinct().count() != representations.size()) {
                throw new IllegalArgumentException("Different objects resolve to the same generated type: "
                    + representations.stream().map(r -> r.definition().sourceResource()).toList());
            }
            var merged = AIcCanonicalDefinitionMerger.AIcMerge(representations.stream().map(AIcdCodeGenerationRequest::definition).toList());
            var pair = new AIcSchemaInterfaceGenerator().generate(new AIcdCodeGenerationRequest(merged, first.target(), first.packageName(), first.namingProfile()));
            String targetText = first.target() == AInCodeGenerationTarget.PYTHON ? "python" : "java";
            add(pending, intf.resolve("src/product/" + targetText + ".gen").resolve(pair.contract().relativePath()), qualifyReferences(pair.contract().source(), first, requests, true));
            if (pair.implementation() != null) add(pending, impl.resolve("src/product/" + targetText + ".gen").resolve(pair.implementation().relativePath()), qualifyReferences(pair.implementation().source(), first, requests, false));
        }
        Path state = repository.resolve("build/run/schema-bindings/generated-files.json");
        List<String> previous = Files.isRegularFile(state) ? mapper.readValue(state.toFile(), mapper.getTypeFactory().constructCollectionType(List.class, String.class)) : List.of();
        // Only this generator's recorded files may be removed. Never clear a shared .gen directory.
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
            mapper.writerWithDefaultPrettyPrinter().writeValue(state.toFile(), pending.keySet().stream().map(repository::relativize).map(AIcSchemaObjectBindingsGenerator::portable).toList());
        }
        return result;
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
            } else source = source.replaceAll("\\b" + java.util.regex.Pattern.quote(type) + "\\b", java.util.regex.Matcher.quoteReplacement(packageName + "." + type));
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
        // Visit only schema-bearing keywords: never generate DTOs for examples, defaults or property documentation.
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
        var generator = new AIcSchemaObjectBindingsGenerator();
        var result = generator.generateRepository(Path.of(args[0]), Path.of(args[1]), check);
        System.out.println(json ? generator.mapper.writerWithDefaultPrettyPrinter().writeValueAsString(result)
            : (check ? "Verified " : "Generated ") + result.size() + " schema representations.");
    }
}
