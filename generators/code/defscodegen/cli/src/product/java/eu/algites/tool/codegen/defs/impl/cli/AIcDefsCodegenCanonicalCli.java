package eu.algites.tool.codegen.defs.impl.cli;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.common.AIcCodegenWorkspace;
import eu.algites.lib.naming.convention.impl.standard.AIcNameConventionCatalog;
import eu.algites.tool.codegen.defs.model.AIngSourceInputKind_1;
import eu.algites.tool.codegen.defs.impl.standard.AIcDefsCodegenCanonicalCompiler;
import eu.algites.tool.codegen.defs.impl.standard.AIcDefsCodegenCanonicalSourceEmitter;
import eu.algites.tool.codegen.defs.impl.standard.AIcDefsCodegenCanonicalSchemaValidator;
import eu.algites.tool.codegen.defs.impl.standard.AIcDefsCodegenSchemaReferenceResolver;
import eu.algites.tool.codegen.defs.impl.standard.AIcdDefsCodegenSourceDocument;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.InputSource;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * Native Java entry point for canonical Defs Codegen. The public CLI accepts
 * only documented technology-qualified Defs input/dependency and naming
 * parameters. Any private batch manifests are created and consumed entirely
 * within this generator, never by bootstrap or a public caller.
 *
 * <p>The Java compiler generates Java and Python from one canonical graph.
 * A remotely resolved schema does not by itself prove a compiled external
 * parent contract exists.</p>
 *
 * @author linhart1
 */
public final class AIcDefsCodegenCanonicalCli {
    /** UTF-8 JSON parser for manifest documents and canonical source schemas. */
    private static final ObjectMapper JSON = new ObjectMapper();
    /** YAML parser for naming catalogs and YAMLDEFS source documents. */
    private static final ObjectMapper YAML = new ObjectMapper(new YAMLFactory());

    /**
     * One manifest's staged source outputs and source-neutral canonical graph.
     * @param outputs generated repository-relative source files
     * @param common source-neutral types requiring batch coalescing
     */
    private record ManifestOutput(Map<String, String> outputs,
            Map<String, AIcDefsCodegenCanonicalSourceEmitter.CommonProjection> common) { }

    /** Prevent instantiation of a stateless CLI. */
    private AIcDefsCodegenCanonicalCli() { }

    /**
     * Command line entry point.
     * @param args qualified public Defs CLI arguments, including source selectors
     * @throws Exception on parsing, schema validation, missing dependencies or publishing failures
     */
    public static void main(String[] args) throws Exception {
        run(List.of(args));
    }

    /**
     * Compile and publish sources selected by the standard qualified CLI.
     * @param args command-line arguments identical to the Python native CLI
     * @return zero after successful completion
     * @throws Exception for invalid input, unsupported constructs or I/O failures
     */
    public static int run(List<String> args) throws Exception {
        Objects.requireNonNull(args, "args");
        return AIcDefsCodegenStandardCli.run(args);
    }

    /**
     * Consume compiler-private batch files created in a UUID workspace by
     * {@link AIcDefsCodegenStandardCli}. Not part of the public CLI protocol.
     * @param args internal batch paths and optional verification switch
     * @return zero on successful internal compilation
     * @throws Exception for invalid or inconsistent canonical definitions
     */
    static int runInternalBatches(List<String> args) throws Exception {
        var manifests = new ArrayList<Path>();
        boolean check = false;
        boolean cleanup = false;
        for (int index = 0; index < args.size(); index++) {
            switch (args.get(index)) {
                case "--manifest" -> {
                    if (++index >= args.size()) throw new IllegalArgumentException("Missing --manifest value");
                    manifests.add(Path.of(args.get(index)).toRealPath());
                }
                case "--check" -> check = true;
                case "--cleanup-output-folder-before-generation" -> cleanup = true;
                default -> throw new IllegalArgumentException("Unknown native Defs CLI argument: " + args.get(index));
            }
        }
        if (check && cleanup) throw new IllegalArgumentException("--check and cleanup conflict");
        if (manifests.isEmpty()) throw new IllegalArgumentException("At least one --manifest is required");
        Path repository = null;
        Map<String, String> pending = new LinkedHashMap<>();
        Map<String, List<AIcDefsCodegenCanonicalSourceEmitter.CommonProjection>> commonGroups =
                new LinkedHashMap<>();
        for (Path manifest : manifests) {
            Map<String, Object> document = read(manifest);
            Path root = absolute(manifest, string(document, "repository_root"));
            if (!Files.isDirectory(root)) throw new IOException("Missing repository " + root);
            if (repository != null && !repository.equals(root)) {
                throw new IllegalArgumentException("All Defs manifests must share a repository root");
            }
            repository = root;
            ManifestOutput produced = compile(manifest, document, root);
            for (var entry : produced.common().entrySet()) {
                commonGroups.computeIfAbsent(entry.getKey(), ignored -> new ArrayList<>())
                        .add(entry.getValue());
            }
            for (var output : produced.outputs().entrySet()) {
                if (produced.common().containsKey(output.getKey())) continue;
                String previous = pending.putIfAbsent(output.getKey(), output.getValue());
                if (previous != null) {
                    pending.put(output.getKey(), coalesceEquivalentEnum(
                            output.getKey(), previous, output.getValue()));
                }
            }
        }
        for (var entry : commonGroups.entrySet()) {
            String path = entry.getKey();
            if (pending.containsKey(path)) {
                throw new IllegalArgumentException("Common/specific source collision at " + path);
            }
            pending.put(path, AIcDefsCodegenCanonicalSourceEmitter.mergeCommon(path, entry.getValue()));
        }
        publish(Objects.requireNonNull(repository), pending, check, cleanup);
        pending.keySet().forEach(System.out::println);
        return 0;
    }

    /**
     * Coalesce equivalent ENUMs published by several wire representations.
     * This only merges the canonical-identity documentation when their entire
     * executable Java API is otherwise identical; all other collisions fail.
     *
     * @param path common destination of two compilation units
     * @param existing already staged source
     * @param next another source with the same generated path
     * @return first source with all equivalent identities documented
     */
    private static String coalesceEquivalentEnum(String path, String existing, String next) {
        return AIcDefsCodegenEnumCoalescer.merge(path, existing, next);
    }

    /**
     * Parse one manifest and compile its complete schema and naming context.
     * @param manifest manifest filename used for relative configuration paths
     * @param options validated manifest mapping
     * @param root canonical root of the output repository
     * @return repository-relative generated paths and complete source strings
     * @throws Exception on unsupported input or invalid schema provenance
     */
    private static ManifestOutput compile(Path manifest, Map<String, Object> options, Path root) throws Exception {
        var documents = new ArrayList<AIcdDefsCodegenSourceDocument>();
        Map<String, Object> inputNaming = mapping(options.get("input_naming"), "input_naming");
        var inputCatalogs = new LinkedHashMap<String, AIcNameConventionCatalog>();
        for (Object raw : array(options, "inputs")) {
            Map<String, Object> input = mapping(raw, "input");
            String kind = string(input, "kind").toUpperCase(java.util.Locale.ROOT);
            var sourceKind = AIngSourceInputKind_1.valueOf(kind);
            String relative = string(input, "path");
            Path file = inside(root, relative, false);
            Object content = sourceKind == AIngSourceInputKind_1.XMLDEFS
                    ? Files.readString(file) : read(file);
            String family = kind.toLowerCase(java.util.Locale.ROOT);
            Map<String, Object> selected = mapping(inputNaming.get(family), "input_naming/" + family);
            String catalogPath = string(selected, "catalog");
            String sourceProfile = string(selected, "profile");
            var catalog = inputCatalogs.get(catalogPath);
            if (catalog == null) {
                catalog = AIcNameConventionCatalog.load(absolute(manifest, catalogPath));
                inputCatalogs.put(catalogPath, catalog);
            }
            var matched = catalog.recognizeFilename(file.getFileName().toString(), Set.of(sourceProfile));
            if (matched == null || !matched.variables().containsKey("identifier")
                    || !matched.variables().containsKey("version")) {
                throw new IllegalArgumentException(file + ": filename does not match "
                        + sourceProfile + " with identifier and version");
            }
            String identifierRule = catalog.identifierConvention(sourceProfile, "file_name_stem");
            String rootName = catalog.format(sourceProfile, "type_name", matched.variables(), identifierRule);
            String sourceVersion = matched.variables().get("version");
            if (content instanceof Map<?, ?> source && source.get("x-algites-schema-version") != null
                    && !sourceVersion.equals(String.valueOf(source.get("x-algites-schema-version")))) {
                throw new IllegalArgumentException(file + ": #/x-algites-schema-version "
                        + source.get("x-algites-schema-version") + " does not match filename version " + sourceVersion);
            }
            documents.add(new AIcdDefsCodegenSourceDocument(sourceKind, relative, content,
                    rootName, sourceVersion));
        }
        if (documents.isEmpty()) throw new IllegalArgumentException("No Defs input documents");
        Path canonical = absolute(manifest, string(options, "canonical_schema"));
        Map<String, Object> canonicalSchema = read(canonical);
        if (!canonicalSchema.containsKey("$defs") || !canonicalSchema.containsKey("$id")) {
            throw new IllegalArgumentException("Missing or incomplete generated canonical schema: " + canonical);
        }
        Map<String, Object> profiles = mapping(options.get("profiles"), "profiles");
        Map<String, Object> compositions = mapping(options.get("output_compositions"), "output compositions");
        var javaNaming = profile(manifest, mapping(profiles.containsKey("java")
                ? profiles.get("java") : profiles.get("python"), "java profile"));
        var pythonNaming = profile(manifest, mapping(profiles.containsKey("python")
                ? profiles.get("python") : profiles.get("java"), "python profile"));
        Map<String, String> versions = stringMap(options.getOrDefault("versions", Map.of()), "versions");
        String packageName = string(options, "package_name");
        // The Java adapter validates the same published canonical-model schema
        // as the Python native pipeline; unknown schema keywords fail closed.
        var schemaValidator = new AIcDefsCodegenCanonicalSchemaValidator(canonicalSchema);
        var compiler = new AIcDefsCodegenCanonicalCompiler(javaNaming, pythonNaming,
                schemaValidator::validate,
                stringMap(mapping(compositions.containsKey("java") ? compositions.get("java")
                        : compositions.get("python"), "java output compositions"), "java"),
                stringMap(mapping(compositions.containsKey("python") ? compositions.get("python")
                        : compositions.get("java"), "python output compositions"), "python"),
                versions, packageName);
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> external = new LinkedHashMap<>();
        Map<String, Object> declarations = mapping(options.getOrDefault("external_contracts", Map.of()),
                "external_contracts");
        var roots = new ArrayList<Path>();
        for (Object raw : arrayOrEmpty(options, "reference_roots")) {
            Path path = absolute(manifest, String.valueOf(raw));
            if (Files.isDirectory(path)) roots.add(path);
        }
        Path cache = options.containsKey("schema_cache")
                ? absolute(manifest, string(options, "schema_cache"))
                : Path.of(System.getProperty("user.home"), ".modustro/cache/defs-schemas");
        var resolver = new AIcDefsCodegenSchemaReferenceResolver(roots, cache,
                Duration.ofSeconds(20), options.containsKey("schema_locations_property_file")
                        ? absolute(manifest, string(options, "schema_locations_property_file")) : null);
        var discovered = existingContracts(roots, requiredExternalContracts(documents));
        for (var entry : declarations.entrySet()) {
            var binding = mapping(entry.getValue(), "external contract " + entry.getKey());
            if (!entry.getKey().startsWith("https://")) {
                throw new IllegalArgumentException("External contract must have HTTPS schema identity: " + entry.getKey());
            }
            resolver.resolve(entry.getKey(), null);
            external.put(entry.getKey(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    string(binding, "java"), string(binding, "python_type"),
                    string(binding, "python_module")));
        }
        // Resolve the parent schema, then bind it to the previously generated
        // compiled interface. Availability of HTTPS content alone is not enough.
        var importedXsdTypes = new java.util.LinkedHashSet<String>();
        for (var input : documents) {
            if (input.kind() == AIngSourceInputKind_1.XMLDEFS) {
                for (var imported : xsdImports((String) input.content(), input.resource(), root,
                        resolver, discovered, external)) {
                    importedXsdTypes.add(imported);
                }
                continue;
            }
            Map<String, Object> schema = mapping(input.content(), "schema");
            var needed = new java.util.LinkedHashSet<String>();
            for (Object reference : arrayOrEmpty(schema, "x-algites-defscodegen-extends")) {
                needed.add(String.valueOf(reference));
            }
            for (Object inherited : arrayOrEmpty(schema, "allOf")) {
                if (inherited instanceof Map<?, ?> item && item.get("$ref") instanceof String ref) {
                    needed.add(ref);
                }
            }
            for (String identity : needed) {
                if (identity.startsWith("#")) continue;
                if (!identity.startsWith("https://")) continue;
                resolver.resolve(identity, null);
                if (!external.containsKey(identity)) {
                    var compiled = discovered.get(identity.split("#", 2)[0]);
                    if (compiled == null) {
                        throw new IllegalArgumentException("External schema exists, but the compiled "
                                + "Java/Python parent is absent or ambiguous: " + identity);
                    }
                    external.put(identity, compiled);
                }
            }
        }
        var compiled = compiler.compileWithCommon(documents, external, Set.copyOf(importedXsdTypes));
        Map<String, Object> dirs = mapping(options.get("output_dirs"), "output_dirs");
        Map<String, String> result = new LinkedHashMap<>();
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.CommonProjection> shared = new LinkedHashMap<>();
        for (var item : compiled.outputs()) {
            if (!dirs.containsKey(item.language())) continue;
            Path dir = inside(root, string(dirs, item.language()), true);
            Path destination = dir.resolve(item.relativePath()).normalize();
            if (!destination.startsWith(dir)) {
                throw new IllegalArgumentException("Generated path escapes output directory: " + destination);
            }
            String relative = root.relativize(destination).toString().replace('\\', '/');
            if (result.putIfAbsent(relative, item.sourceText()) != null) {
                throw new IllegalArgumentException("Duplicate Java native output: " + relative);
            }
            var common = compiled.shared().get(item.relativePath());
            if (common != null) shared.put(relative, common);
        }
        return new ManifestOutput(Map.copyOf(result), Map.copyOf(shared));
    }

    /**
     * Determine which external compiled contracts are referenced by this batch.
     * Importing an XML schema alone does not mean that every named type in
     * that document is an API parent.  The selected type is identified through
     * the qualified QName actually used by a type/base reference.
     *
     * @param documents typed source declarations of the generation batch
     * @return exact public JSON schema IDs and imported XSD QNames
     * @throws Exception when XML is malformed or cannot be inspected securely
     */
    private static Set<String> requiredExternalContracts(
            List<AIcdDefsCodegenSourceDocument> documents) throws Exception {
        Set<String> needed = new java.util.LinkedHashSet<>();
        var factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        factory.setXIncludeAware(false);
        for (var source : documents) {
            if (source.kind() != AIngSourceInputKind_1.XMLDEFS) {
                Map<String, Object> schema = mapping(source.content(), "schema");
                var references = new java.util.ArrayList<Object>(
                        arrayOrEmpty(schema, "x-algites-defscodegen-extends"));
                for (Object inherited : arrayOrEmpty(schema, "allOf")) {
                    if (inherited instanceof Map<?, ?> item && item.get("$ref") instanceof String ref) {
                        references.add(ref);
                    }
                }
                for (Object reference : references) {
                    String id = String.valueOf(reference);
                    if (id.startsWith("https://")) needed.add(id.split("#", 2)[0]);
                }
                continue;
            }
            Element document = factory.newDocumentBuilder().parse(
                    new InputSource(new StringReader((String) source.content()))).getDocumentElement();
            Set<String> namespaces = new java.util.HashSet<>();
            for (int i = 0; i < document.getChildNodes().getLength(); i++) {
                Node child = document.getChildNodes().item(i);
                if (child instanceof Element element
                        && XMLConstants.W3C_XML_SCHEMA_NS_URI.equals(element.getNamespaceURI())
                        && "import".equals(element.getLocalName())) {
                    namespaces.add(element.getAttribute("namespace"));
                }
            }
            var pending = new java.util.ArrayDeque<Element>();
            pending.add(document);
            for (Element element; (element = pending.poll()) != null;) {
                for (String attribute : List.of("base", "type", "ref", "itemType",
                        "memberTypes", "substitutionGroup")) {
                    for (String qname : element.getAttribute(attribute).trim().split("\\s+")) {
                        int colon = qname.indexOf(':');
                        if (colon < 1 || colon == qname.length() - 1) continue;
                        String namespace = element.lookupNamespaceURI(qname.substring(0, colon));
                        if (namespace != null && namespaces.contains(namespace)) {
                            needed.add("{" + namespace + "}" + qname.substring(colon + 1));
                        }
                    }
                }
                for (int i = 0; i < element.getChildNodes().getLength(); i++) {
                    Node child = element.getChildNodes().item(i);
                    if (child instanceof Element nested) pending.add(nested);
                }
            }
        }
        return Set.copyOf(needed);
    }

    /**
     * Inspect verified generated DataObject contracts from declared dependency
     * checkouts. Only schema IDs/URLs and declaration identities are read; no
     * external Python or Java code is imported or executed.
     * @param roots declared source checkouts containing already generated contracts
     * @return public URI/QName to both compiled technology names
     * @throws IOException on unreadable declared source roots
     */
    private static Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> existingContracts(
            List<Path> roots, Set<String> required) throws IOException {
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> result = new LinkedHashMap<>();
        for (var entry : AIcDefsCodegenExternalContractIndex.resolve(roots, required).entrySet()) {
            var symbols = entry.getValue();
            if (symbols.javaType() == null || symbols.pythonModule() == null ||
                    symbols.pythonType() == null) continue;
            result.put(entry.getKey(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    symbols.javaType(), symbols.pythonType(), symbols.pythonModule()));
        }
        return result;
    }

    /**
     * Verify XSD import namespaces without converting helper type imports
     * into duplicate parent DataObject contracts.
     * @param source XSD document text
     * @param resource original source resource, used for local import resolution
     * @param root repository root
     * @param resolver approved HTTPS/local schema resolver
     * @param discovered already compiled schema contracts
     * @param external output map of needed typed external parent contracts
     * @return externally verified QNames of XSD declarations
     * @throws Exception on invalid XML, missing schema or wrong namespace
     */
    private static Set<String> xsdImports(String source, String resource, Path root,
            AIcDefsCodegenSchemaReferenceResolver resolver,
            Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> discovered,
            Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> external) throws Exception {
        var factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        factory.setXIncludeAware(false);
        var rootXml = factory.newDocumentBuilder().parse(new InputSource(new StringReader(source))).getDocumentElement();
        var result = new java.util.LinkedHashSet<String>();
        for (int i = 0; i < rootXml.getChildNodes().getLength(); i++) {
            Node node = rootXml.getChildNodes().item(i);
            if (!(node instanceof Element element) ||
                    !XMLConstants.W3C_XML_SCHEMA_NS_URI.equals(element.getNamespaceURI()) ||
                    !"import".equals(element.getLocalName())) continue;
            String location = element.getAttribute("schemaLocation");
            String namespace = element.getAttribute("namespace");
            if (location.isBlank()) throw new IllegalArgumentException("XSD import requires schemaLocation");
            String content;
            if (location.startsWith("https://")) {
                content = new String(resolver.resolve(location, namespace).content(), StandardCharsets.UTF_8);
            } else {
                Path parent = inside(root, resource, false).getParent();
                Path local = parent.resolve(location).normalize();
                if (!local.startsWith(root)) throw new IllegalArgumentException("XSD import escapes repository");
                content = Files.readString(local);
            }
            var imported = factory.newDocumentBuilder().parse(
                    new InputSource(new StringReader(content))).getDocumentElement();
            if (!namespace.equals(imported.getAttribute("targetNamespace"))) {
                throw new IllegalArgumentException("XSD import namespace mismatch: " + location);
            }
            for (int n = 0; n < imported.getChildNodes().getLength(); n++) {
                Node child = imported.getChildNodes().item(n);
                if (!(child instanceof Element declaration) ||
                        !XMLConstants.W3C_XML_SCHEMA_NS_URI.equals(declaration.getNamespaceURI()) ||
                        !Set.of("complexType", "simpleType").contains(declaration.getLocalName()) ||
                        declaration.getAttribute("name").isBlank()) continue;
                String key = "{" + namespace + "}" + declaration.getAttribute("name");
                result.add(key);
                if (discovered.containsKey(key)) external.put(key, discovered.get(key));
            }
        }
        return result;
    }

    /**
     * Resolve validated Common/Defs naming profiles from manifest-selected catalogs.
     * @param manifest manifest path for resolving referenced catalogs
     * @param settings selected profile identifiers and filenames
     * @return fully resolved catalog without hardcoded Algites naming prefixes
     * @throws IOException on unreadable catalog
     */
    private static AIcCodegenNamingProfileResolver.Profile profile(Path manifest,
            Map<String, Object> settings) throws IOException {
        var common = read(absolute(manifest, string(settings, "common_file")));
        var defs = read(absolute(manifest, string(settings, "defs_file")));
        var catalog = read(absolute(manifest, string(settings, "sourcecode_catalog")));
        return AIcCodegenNamingProfileResolver.withExternalSourcecodeConventions(
                AIcCodegenNamingProfileResolver.resolve(common, string(settings, "common_id"),
                        defs, string(settings, "defs_id"), null, null), catalog);
    }

    /**
     * Verify previous publication ownership, stage replacements and publish
     * atomically per path with rollback on failure.
     * @param root repository root
     * @param outputs expected owned files
     * @param check true to verify without modification
     * @throws IOException when the existing files are stale, unowned or inaccessible
     */
    private static void publish(Path root, Map<String, String> outputs, boolean check,
            boolean cleanup) throws IOException {
        Map<Path, Map<Path, String>> groups = new LinkedHashMap<>();
        for (var entry : outputs.entrySet()) {
            Path destination = inside(root, entry.getKey(), true);
            Path artifact = AIcCodegenWorkspace.artifactRoot(root, destination);
            groups.computeIfAbsent(artifact, ignored -> new LinkedHashMap<>())
                    .put(destination, entry.getValue());
        }
        for (var entry : groups.entrySet()) {
            try (var workspace = new AIcCodegenWorkspace(root, entry.getKey(), "defscodegen")) {
                workspace.publish(entry.getValue(), check, cleanup);
            }
        }
    }

    /**
     * Read a JSON or YAML mapping from a validated path.
     * @param file source file
     * @return string-keyed map
     * @throws IOException for invalid JSON/YAML syntax or unreadable source
     */
    private static Map<String, Object> read(Path file) throws IOException {
        ObjectMapper parser = file.getFileName().toString().endsWith(".json") ? JSON : YAML;
        return mapping(parser.readValue(Files.readAllBytes(file), Map.class), file.toString());
    }

    /**
     * Verify and resolve manifest-relative paths without changing URI identity.
     * @param manifest referencing manifest
     * @param raw configured path
     * @return absolute normalized path
     */
    private static Path absolute(Path manifest, String raw) {
        Path configured = Path.of(raw);
        return (configured.isAbsolute() ? configured : manifest.getParent().resolve(configured))
                .toAbsolutePath().normalize();
    }

    /**
     * Require generated destination paths to be within the repository and
     * explicitly named *.gen, which distinguishes them from tracked *.extgen.
     * @param root repository root
     * @param relative repository-relative path
     * @param generated whether to enforce generated-root ownership
     * @return normalized path
     * @throws IllegalArgumentException on an escape or non-generated destination
     */
    private static Path inside(Path root, String relative, boolean generated) {
        Path path = root.resolve(relative).normalize();
        if (!path.startsWith(root) || Files.isSymbolicLink(path)) {
            throw new IllegalArgumentException("Path escapes repository or is a symlink: " + relative);
        }
        boolean generatedRoot = false;
        for (Path part : root.relativize(path)) {
            if (part.toString().endsWith(".gen")) generatedRoot = true;
        }
        if (generated && !generatedRoot) {
            throw new IllegalArgumentException("Not an owned generated-source path: " + relative);
        }
        return path;
    }

    /**
     * Safely interpret a parsed JSON/YAML mapping.
     * @param raw untyped parsed value
     * @param name diagnostic name
     * @return string-keyed map
     * @throws IllegalArgumentException for missing or malformed object
     */
    @SuppressWarnings("unchecked")
    private static Map<String, Object> mapping(Object raw, String name) {
        if (!(raw instanceof Map<?, ?> map) || map.keySet().stream().anyMatch(k -> !(k instanceof String))) {
            throw new IllegalArgumentException("Expected string-keyed mapping: " + name);
        }
        return (Map<String, Object>) map;
    }

    /**
     * Select required string member.
     * @param object mapping
     * @param key required field
     * @return nonempty value
     */
    private static String string(Map<String, Object> object, String key) {
        Object value = object.get(key);
        if (!(value instanceof String result) || result.isBlank()) {
            throw new IllegalArgumentException("Expected nonempty string field: " + key);
        }
        return result;
    }

    /**
     * Convert an object of string values; reject implicit string coercion.
     * @param raw mapping
     * @param name diagnostic name
     * @return immutable typed values
     */
    private static Map<String, String> stringMap(Object raw, String name) {
        Map<String, Object> values = mapping(raw, name);
        Map<String, String> result = new LinkedHashMap<>();
        for (var entry : values.entrySet()) {
            if (!(entry.getValue() instanceof String value)) {
                throw new IllegalArgumentException("Non-string value in " + name + ": " + entry.getKey());
            }
            result.put(entry.getKey(), value);
        }
        return Map.copyOf(result);
    }

    /**
     * Require array member from JSON/YAML configuration.
     * @param object mapping
     * @param key required key
     * @return ordered array
     */
    private static List<?> array(Map<String, Object> object, String key) {
        if (!(object.get(key) instanceof List<?> list)) {
            throw new IllegalArgumentException("Expected array field: " + key);
        }
        return list;
    }

    /**
     * Read optional array as an empty list when absent.
     * @param object mapping
     * @param key optional key
     * @return ordered array or empty
     */
    private static List<?> arrayOrEmpty(Map<String, Object> object, String key) {
        return object.containsKey(key) ? array(object, key) : List.of();
    }

    /**
     * Ordered set union for deterministic file publishing checks.
     * @param first set of current files
     * @param second set of desired files
     * @return union preserving first-seen order
     */
    private static Set<String> union(Set<String> first, Set<String> second) {
        var result = new java.util.LinkedHashSet<String>(first);
        result.addAll(second);
        return result;
    }

    /**
     * Digest one UTF-8 source string for ownership validation.
     * @param source full source text
     * @return lowercase SHA-256 hex
     */
    private static String sha256(String source) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(source.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException impossible) {
            throw new IllegalStateException("SHA-256 unavailable", impossible);
        }
    }
}
