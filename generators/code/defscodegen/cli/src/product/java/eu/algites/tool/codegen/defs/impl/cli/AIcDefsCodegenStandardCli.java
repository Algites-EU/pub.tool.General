package eu.algites.tool.codegen.defs.impl.cli;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import eu.algites.tool.codegen.common.AIcCodegenArtifactResolver;
import eu.algites.tool.codegen.common.AIcCodegenWorkspace;
import eu.algites.tool.codegen.common.AIcCodegenRunLog;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.zip.ZipFile;

/**
 * Converts the standard qualified Defs options into private canonical batches.
 * No caller or bootstrap script is required to construct JSON manifests.
 * Input selectors trigger generation; dependency selectors only resolve imports.
 *
 * @author linhart1
 */
public final class AIcDefsCodegenStandardCli {
    /** JSON writer for private, per-invocation canonical batch files. */
    private static final ObjectMapper JSON = new ObjectMapper();
    /** YAML reader for public naming convention compositions. */
    private static final ObjectMapper YAML = new ObjectMapper(new YAMLFactory());
    /** Recognized source technology directories and file suffixes. */
    private static final Map<String, String> KINDS = Map.of(
            "xmldefs", ".xsd", "jsondefs", ".jsondef.schema.json",
            "yamldefs", ".yamldef.schema.json");
    /** Independently accumulating selectors. */
    private static final Set<String> LISTS = Set.of(
            "defs-input-paths", "defs-input-artifacts", "defs-dependency-paths",
            "defs-dependency-artifacts");

    /** Utility class; not instantiable. */
    private AIcDefsCodegenStandardCli() { }

    /**
     * Run native Defs generation using only public qualified CLI options.
     * @param aArguments layered settings and explicit CLI arguments
     * @return zero on success
     * @throws Exception on invalid inputs, catalogs, compilation, or publication
     */
    public static int run(List<String> aArguments) throws Exception {
        Map<String, String> options = options(aArguments);
        Path repository = Path.of(options.getOrDefault("repository-root", ".")).toRealPath();
        Map<String, String> outputs = new LinkedHashMap<>();
        for (String language : List.of("java", "python")) {
            String root = options.get("technology-dointf-output-dir:" + language);
            if (root != null) outputs.put(language, root);
        }
        if (outputs.isEmpty()) throw new IllegalArgumentException("Missing Defs output technology");
        Set<Path> artifacts = new LinkedHashSet<>();
        for (String root : outputs.values()) artifacts.add(AIcCodegenWorkspace.artifactRoot(
                repository, repository.resolve(root)));
        if (artifacts.size() != 1) throw new IllegalArgumentException(
                "One Defs CLI invocation must target exactly one artifact");
        Path artifact = artifacts.iterator().next();
        var timing = new ArrayList<AIcCodegenRunLog>();
        try {
            for (String language : outputs.keySet())
                timing.add(new AIcCodegenRunLog("Defs Codegen", language, repository, artifact));
        boolean cleanup = parseBoolean(options.getOrDefault(
                "cleanup-output-folder-before-generation", "false"));
        if ("true".equals(options.get("check")) && cleanup)
            throw new IllegalArgumentException(
                    "--check conflicts with --cleanup-output-folder-before-generation=true");
        if ("true".equals(options.get("check")) && "true".equals(options.get("clean-only")))
            throw new IllegalArgumentException("--check conflicts with --clean-only");
        if ("true".equals(options.get("clean-only"))) {
            try (var cleaner = new AIcCodegenWorkspace(repository, artifact, "defscodegen")) {
                cleaner.publish(Map.of(), false, true);
            }
            AIcCodegenWorkspace.cleanupInactive(repository, artifact, "defscodegen");
            return 0;
        }
        try (var workspace = new AIcCodegenWorkspace(repository, artifact, "defscodegen")) {
            Path batch = workspace.workDir().resolve("tmp/standard");
            Files.createDirectories(batch);
            try {
                Map<String, Path> catalogs = catalogs(options, batch);
                Map<String, Map<String, Object>> profiles = new LinkedHashMap<>();
                Map<String, Map<String, String>> compositions = new LinkedHashMap<>();
                for (String language : outputs.keySet()) {
                    String common = require(options, "common-codegen-naming-convention:" + language);
                    String defs = require(options, "defs-codegen-naming-convention:" + language);
                    String commonInterface = require(options, "dointf-naming-convention:" + language);
                    String enumProfile = require(options, "output-enum-technology-naming-convention:" + language);
                    Path sourcecode = catalog(catalogs, language);
                    profiles.put(language, Map.of(
                            "common_file", catalog(catalogs, "codegen_common_" + language,
                                    "codegen_common").toString(),
                            "common_id", common,
                            "defs_file", catalog(catalogs, "codegen_defs_" + language,
                                    "codegen_defs").toString(),
                            "defs_id", defs,
                            "sourcecode_catalog", sourcecode.toString()));
                    compositions.put(language, Map.of(
                            "common_interface", commonInterface,
                            "common_interface_file", filenameRule(sourcecode, commonInterface),
                            "enum", enumProfile,
                            "enum_file", filenameRule(sourcecode, enumProfile)));
                }
                List<Source> sources = new ArrayList<>();
                Set<Path> selected = new LinkedHashSet<>();
                List<Path> dependencies = new ArrayList<>();
                for (String purpose : List.of("input", "dependency")) {
                    for (String language : List.of("java", "python")) {
                        List<Path> paths = new ArrayList<>();
                        for (String raw : split(options.get("defs-" + purpose + "-paths:" + language)))
                            paths.add(repository.resolve(raw).toAbsolutePath().normalize());
                        String coordinates = options.get("defs-" + purpose + "-artifacts:" + language);
                        if (coordinates != null) {
                            if (language.equals("java"))
                                paths.addAll(AIcCodegenArtifactResolver.resolveJava(coordinates));
                            else
                                paths.addAll(pythonWheels(coordinates));
                        }
                        int index = 0;
                        for (Path path : paths) {
                            if (!Files.exists(path)) throw new IOException("Selected Defs " + purpose
                                    + " missing: " + path);
                            if (Files.isRegularFile(path) && (path.toString().endsWith(".jar")
                                    || path.toString().endsWith(".whl")
                                    || path.toString().endsWith(".zip"))) {
                                Path archiveRoot = batch.resolve(purpose).resolve(language)
                                        .resolve(Integer.toString(index++));
                                unpack(path, archiveRoot);
                                path = archiveRoot;
                            }
                            if (purpose.equals("input") && !path.toAbsolutePath().normalize().startsWith(repository))
                                path = stageExternalInput(path, repository, batch, language, index++);
                            if (purpose.equals("dependency")) {
                                if (!dependencies.contains(path)) dependencies.add(path);
                            } else {
                                try (var walk = Files.isDirectory(path) ? Files.walk(path) : java.util.stream.Stream.of(path)) {
                                    for (Path file : walk.filter(Files::isRegularFile).sorted().toList()) {
                                        if (Files.isSymbolicLink(file))
                                            throw new IOException("Symlinked schema input " + file);
                                        if (!selected.add(file)) continue;
                                        String kind = kind(file.getFileName().toString());
                                        if (kind != null) sources.add(new Source(kind, file,
                                                packageName(file, kind)));
                                    }
                                }
                            }
                        }
                    }
                }
                if (sources.isEmpty()) throw new IllegalArgumentException(
                        "No Defs schemas in explicit --defs-input-* selections");
                Path schema = canonicalSchema(repository);
                var grouped = new LinkedHashMap<String, List<Source>>();
                for (Source source : sources)
                    grouped.computeIfAbsent(source.kind() + "/" + source.packageName(),
                            ignored -> new ArrayList<>()).add(source);
                List<String> arguments = new ArrayList<>();
                int count = 0;
                for (List<Source> group : grouped.values()) {
                    Source first = group.get(0);
                    String kind = first.kind();
                    Map<String, String> input = Map.of(
                            "catalog", catalog(catalogs, kind).toString(),
                            "profile", require(options, "input-schema-naming-convention:" + kind));
                    Map<String, Object> configs = new LinkedHashMap<>();
                    configs.put("repository_root", repository.toString());
                    List<Map<String, String>> files = new ArrayList<>();
                    for (Source source : group) files.add(Map.of("kind", source.kind(),
                            "path", repository.relativize(source.path()).toString().replace('\\', '/')));
                    configs.put("inputs", files);
                    configs.put("input_naming", Map.of(kind, input));
                    configs.put("canonical_schema", schema.toString());
                    configs.put("profiles", profiles);
                    Map<String, Map<String, String>> roleCompositions = new LinkedHashMap<>();
                    for (String language : outputs.keySet()) {
                        String name = require(options, "dointf-naming-convention:" + language);
                        var settings = new LinkedHashMap<>(compositions.get(language));
                        settings.put("interface", name);
                        settings.put("interface_file", filenameRule(catalog(catalogs, language), name));
                        roleCompositions.put(language, settings);
                    }
                    configs.put("output_compositions", roleCompositions);
                    configs.put("package_name", first.packageName());
                    configs.put("versions", Map.of());
                    configs.put("reference_roots", dependencies.stream().map(Path::toString).toList());
                    if (options.containsKey("schema-locations-property-file")) {
                        configs.put("schema_locations_property_file", repository.resolve(
                                options.get("schema-locations-property-file")).normalize().toString());
                    }
                    configs.put("output_dirs", outputs);
                    Path manifest = batch.resolve("canonical-" + count++ + ".json");
                    JSON.writerWithDefaultPrettyPrinter().writeValue(manifest.toFile(), configs);
                    arguments.add("--manifest");
                    arguments.add(manifest.toString());
                }
                if ("true".equals(options.get("check"))) arguments.add("--check");
                if (cleanup) arguments.add("--cleanup-output-folder-before-generation");
                return AIcDefsCodegenCanonicalCli.runInternalBatches(arguments);
            } finally {
                deleteTree(batch);
            }
        }
        } finally {
            for (int index = timing.size() - 1; index >= 0; index--) timing.get(index).close();
        }
    }

    /** One selected source schema with its physical path and logical package. */
    private record Source(String kind, Path path, String packageName) { }

    /**
     * Parse layered settings, preserving repeated list-valued selectors.
     * @param arguments CLI tokens
     * @return complete qualified options
     * @throws IOException on invalid settings
     */
    private static Map<String, String> options(List<String> arguments) throws IOException {
        var values = new LinkedHashMap<String, String>();
        Path settingsFile = null;
        for (String value : arguments) if (value.startsWith("--settings-file=")) {
            if (settingsFile != null) throw new IllegalArgumentException("Only one --settings-file allowed");
            settingsFile = Path.of(value.substring("--settings-file=".length()));
        }
        if (settingsFile != null) for (String line : Files.readAllLines(settingsFile))
            put(values, line.strip(), true);
        for (String arg : arguments) if (!arg.startsWith("--settings-file="))
            put(values, arg, false);
        return values;
    }

    /**
     * Add one option while merging list values and overriding scalar settings.
     * @param values effective options
     * @param token one option or settings line
     * @param fromFile if true, allow blank/comments
     */
    private static boolean parseBoolean(String value) {
        if (!value.equals("true") && !value.equals("false"))
            throw new IllegalArgumentException("Expected boolean true/false for "
                    + "--cleanup-output-folder-before-generation: " + value);
        return Boolean.parseBoolean(value);
    }

    private static void put(Map<String, String> values, String token, boolean fromFile) {
        if (fromFile && (token.isBlank() || token.startsWith("#"))) return;
        if (token.equals("--check") || token.equals("--clean-only")) token += "=true";
        if (!token.startsWith("--") || !token.contains("="))
            throw new IllegalArgumentException("Invalid Defs setting " + token);
        String[] parts = token.substring(2).split("=", 2);
        String key = parts[0];
        String name = key.split(":", 2)[0];
        if (LISTS.contains(name)) {
            if (!key.matches("defs-(input|dependency)-(paths|artifacts):(java|python)"))
                throw new IllegalArgumentException("Missing :technology on " + token);
            values.merge(key, parts[1], (previous, next) -> previous + ";" + next);
        } else values.put(key, parts[1]);
    }

    /**
     * Resolve a configured catalog by its entry identity.
     * @param catalogs materialized catalog entries
     * @param names preferred identities, in order
     * @return catalog physical path
     */
    private static Path catalog(Map<String, Path> catalogs, String... names) {
        for (String name : names) if (catalogs.containsKey(name)) return catalogs.get(name);
        throw new IllegalArgumentException("Missing naming catalog " + java.util.Arrays.toString(names));
    }

    /**
     * Materialize installed classpath/catalog resources in the private work area.
     * @param options naming catalog qualified settings
     * @param batch work area
     * @return stable entry-id/path mapping
     * @throws IOException on unavailable or conflicting resources
     */
    private static Map<String, Path> catalogs(Map<String, String> options, Path batch) throws IOException {
        Map<String, Path> result = new LinkedHashMap<>();
        Path catalogDir = batch.resolve("catalogs");
        Files.createDirectories(catalogDir);
        for (var entry : options.entrySet()) {
            if (!entry.getKey().startsWith("naming-conventions-file:")) continue;
            String name = entry.getKey().substring("naming-conventions-file:".length());
            String location = entry.getValue();
            Path file;
            if (location.startsWith("classpath:") || location.startsWith("resource:")) {
                String resource = location.substring(location.indexOf(':') + 1);
                file = catalogDir.resolve(name).resolve(resource);
                Files.createDirectories(file.getParent());
                copyResource(resource, file);
                // Referenced common standards are published separately.
                String text = Files.readString(file);
                var matcher = java.util.regex.Pattern.compile(
                        "(?m)^\\s*StandardConventionsFile:\\s*['\\\"]?([A-Za-z0-9_.-]+\\.yml)")
                        .matcher(text);
                if (matcher.find()) copyResource(matcher.group(1), file.getParent().resolve(matcher.group(1)));
            } else file = Path.of(location).toAbsolutePath().normalize();
            if (!Files.isRegularFile(file)) throw new IOException("Missing naming catalog: " + file);
            result.put(name, file);
        }
        return result;
    }

    /**
     * Copy a classpath resource by published file name, never by a vendor profile.
     * @param name catalog resource file name
     * @param destination private extracted file
     * @throws IOException when missing
     */
    private static void copyResource(String name, Path destination) throws IOException {
        for (String prefix : List.of("", "eu/algites/lib/naming/convention/",
                "eu/algites/lib/naming/convention/sourcecode/",
                "eu/algites/tool/codegen/")) {
            try (InputStream stream = AIcDefsCodegenStandardCli.class.getClassLoader()
                    .getResourceAsStream(prefix + name)) {
                if (stream != null) {
                    Files.copy(stream, destination, StandardCopyOption.REPLACE_EXISTING);
                    return;
                }
            }
        }
        throw new IOException("Missing Codegen naming resource on classpath: " + name);
    }

    /**
     * Resolve the file naming composition from its declared public catalog.
     * @param catalog selected sourcecode naming catalog
     * @param identity selected naming convention ID
     * @return name of the file stem composition
     * @throws IOException on invalid catalog
     */
    private static String filenameRule(Path catalog, String identity) throws IOException {
        @SuppressWarnings("unchecked")
        Map<String, Object> yaml = YAML.readValue(Files.readAllBytes(catalog), Map.class);
        if (!(yaml.get("SourceStructureNameConventions") instanceof Map<?, ?> naming))
            throw new IOException(catalog + ": missing SourceStructureNameConventions");
        if (!(naming.get("NameConventions") instanceof Map<?, ?> container)
                || !(container.get("NameConvention") instanceof List<?> entries))
            throw new IOException(catalog + ": expected NameConventions/NameConvention list");
        Map<?, ?> selected = null;
        java.util.Set<String> seenProfiles = new java.util.HashSet<>();
        for (Object raw : entries) {
            if (!(raw instanceof Map<?, ?> entry)
                    || !(entry.get("name") instanceof String name) || name.isBlank())
                throw new IOException(catalog + ": invalid NameConventions/NameConvention entry");
            if (!seenProfiles.add(name))
                throw new IOException(catalog + ": duplicate NameConvention name " + name);
            if (name.equals(identity)) selected = entry;
        }
        if (selected == null) throw new IOException(catalog + ": no naming convention " + identity);
        if (!(selected.get("StructureNaming") instanceof Map<?, ?> namingRules)
                || !(namingRules.get("Rule") instanceof List<?> rules))
            throw new IOException(catalog + ": missing StructureNaming/Rule for " + identity);
        String stem = null;
        java.util.Set<String> seenKinds = new java.util.HashSet<>();
        for (Object raw : rules) {
            if (!(raw instanceof Map<?, ?> rule)
                    || !(rule.get("kind") instanceof String kind) || kind.isBlank())
                throw new IOException(catalog + ": invalid StructureNaming/Rule for " + identity);
            if (!seenKinds.add(kind))
                throw new IOException(catalog + ": duplicate StructureNaming kind " + kind);
            if (kind.equals("file_name_stem")) {
                if (!(rule.get("Value") instanceof String text) || text.isBlank())
                    throw new IOException(catalog + ": invalid file_name_stem for " + identity);
                stem = text;
            }
        }
        if (stem == null) throw new IOException(catalog + ": missing file_name_stem for " + identity);
        return stem;
    }

    /**
     * Identify source technology by filename suffix.
     * @param name filename
     * @return schema technology or null
     */
    private static String kind(String name) {
        for (var entry : KINDS.entrySet()) if (name.endsWith(entry.getValue())) return entry.getKey();
        return null;
    }

    /**
     * Derive a package from segments below a technology source directory.
     * @param source schema path
     * @param kind technology directory name
     * @return package name
     */
    private static String packageName(Path source, String kind) {
        int position = -1;
        for (int i = 0; i < source.getNameCount() - 1; i++)
            if (source.getName(i).toString().equals(kind)) position = i;
        if (position < 0 || position == source.getNameCount() - 2)
            throw new IllegalArgumentException(source + ": missing package under " + kind);
        var names = new ArrayList<String>();
        for (int i = position + 1; i < source.getNameCount() - 1; i++) {
            String name = source.getName(i).toString();
            if (!name.matches("[A-Za-z_$][A-Za-z0-9_$]*"))
                throw new IllegalArgumentException(source + ": invalid package component " + name);
            names.add(name);
        }
        return String.join(".", names);
    }

    /**
     * Materialize one explicitly selected archive, preserving no links.
     * @param archive JAR/wheel/ZIP path
     * @param destination work directory
     * @throws IOException on malformed archive or escaping paths
     */
    private static void unpack(Path archive, Path destination) throws IOException {
        Files.createDirectories(destination);
        try (var zip = new ZipFile(archive.toFile())) {
            var entries = zip.entries();
            while (entries.hasMoreElements()) {
                var entry = entries.nextElement();
                Path path = destination.resolve(entry.getName()).normalize();
                if (!path.startsWith(destination)) throw new IOException("Unsafe archive entry " + entry.getName());
                if (entry.isDirectory()) continue;
                Files.createDirectories(path.getParent());
                try (var input = zip.getInputStream(entry)) { Files.copy(input, path); }
            }
        }
    }

    /**
     * Stage external local schemas within this invocation, preserving relative imports.
     * A single-file selection stays single-file; neighboring schemas are copied
     * only to make relative schema imports resolvable, never to expand generation.
     * @param path explicitly selected external source
     * @param repository current repository root
     * @param batch private invocation work directory
     * @param language selected output technology
     * @param index unique selector ordinal
     * @return repository-internal source path suitable for canonical provenance
     * @throws IOException for unsafe links, invalid technologies, or copy errors
     */
    private static Path stageExternalInput(Path path, Path repository, Path batch,
            String language, int index) throws IOException {
        if (path.startsWith(repository)) return path;
        Path technology = path;
        while (technology != null && technology.getFileName() != null
                && !KINDS.containsKey(technology.getFileName().toString()))
            technology = technology.getParent();
        if (Files.isRegularFile(path) && (technology == null || technology.getFileName() == null))
            throw new IOException("External Defs schema is not under"
                    + " an xmldefs/jsondefs/yamldefs directory: " + path);
        Path source = technology != null && technology.getFileName() != null ? technology : path;
        if (!Files.isDirectory(source)) throw new IOException("Not an external schema input: " + path);
        Path destination = batch.resolve("external-input").resolve(language)
                .resolve(Integer.toString(index)).resolve(source.getFileName());
        try (var walk = Files.walk(source)) {
            for (Path current : walk.sorted().toList()) {
                if (Files.isSymbolicLink(current))
                    throw new IOException("External Defs schema input contains symlink: " + current);
                Path copied = destination.resolve(source.relativize(current));
                if (Files.isDirectory(current)) Files.createDirectories(copied);
                else if (Files.isRegularFile(current)) {
                    Files.createDirectories(copied.getParent());
                    Files.copy(current, copied, StandardCopyOption.COPY_ATTRIBUTES);
                } else throw new IOException("Unsupported external Defs resource: " + current);
            }
        }
        return destination.resolve(source.relativize(path));
    }

    /**
     * Locate the published canonical model schema relative to a source checkout.
     * @param repository selected repository
     * @return existing schema file
     * @throws IOException if the codegen model resource is missing
     */
    private static Path canonicalSchema(Path repository) throws IOException {
        Path suffix = Path.of("generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/"
                + "codegen/defs/model/canonical-model_1.jsondef.schema.json");
        for (Path parent : List.of(repository, repository.getParent())) {
            if (parent == null) continue;
            Path file = parent.resolve(suffix);
            if (Files.isRegularFile(file)) return file;
            try (var siblings = Files.list(parent)) {
                for (Path sibling : siblings.toList()) {
                    file = sibling.resolve(suffix);
                    if (Files.isRegularFile(file)) return file;
                }
            }
        }
        throw new IOException("Missing installed canonical-model_1.jsondef.schema.json");
    }

    /**
     * Find locally published Python dependency wheels by their exact distribution.
     * @param coordinates semicolon-delimited Python requirements
     * @return validated wheel paths
     * @throws IOException when local wheels cannot be selected unambiguously
     */
    private static List<Path> pythonWheels(String coordinates) throws IOException {
        Path store = Path.of(System.getProperty("user.home"), ".modustro/artifact-repos/python");
        List<Path> result = new ArrayList<>();
        for (String spec : split(coordinates)) {
            String name = spec.split("[<>=!~@]", 2)[0].replace('-', '_').toLowerCase();
            List<Path> matches;
            if (!Files.isDirectory(store)) matches = List.of();
            else try (var walk = Files.walk(store)) {
                matches = walk.filter(path -> Files.isRegularFile(path) &&
                        path.toString().endsWith(".whl") && path.getFileName().toString()
                        .toLowerCase().startsWith(name + "-")).toList();
            }
            if (matches.size() != 1) throw new IOException("Expected exactly one Python wheel for " + spec
                    + ", found " + matches);
            result.add(matches.get(0));
        }
        return result;
    }

    /**
     * Split semicolon-separated values with empty entries rejected.
     * @param value configured list or null
     * @return ordered nonempty entries
     */
    private static List<String> split(String value) {
        if (value == null || value.isBlank()) return List.of();
        var parts = new ArrayList<String>();
        for (String part : value.split(";")) if (!part.isBlank()) parts.add(part.strip());
        return parts;
    }

    /**
     * Demand an explicit naming setting; never infer a class prefix or version.
     * @param options selected settings
     * @param key fully qualified setting name
     * @return configured value
     */
    private static String require(Map<String, String> options, String key) {
        String value = options.get(key);
        if (value == null || value.isBlank())
            throw new IllegalArgumentException("Missing Defs Codegen option --" + key);
        return value;
    }

    /**
     * Delete private batch files without traversing symlinks.
     * @param tree temporary directory
     * @throws IOException when filesystem cleanup fails
     */
    private static void deleteTree(Path tree) throws IOException {
        if (!Files.exists(tree)) return;
        try (var walk = Files.walk(tree)) {
            for (Path path : walk.sorted(Comparator.reverseOrder()).toList()) Files.deleteIfExists(path);
        }
    }
}
