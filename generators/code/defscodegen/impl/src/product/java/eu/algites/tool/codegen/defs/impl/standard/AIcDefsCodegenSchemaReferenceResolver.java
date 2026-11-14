package eu.algites.tool.codegen.defs.impl.standard;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.StringReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Arrays;
import java.util.Objects;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.xml.sax.InputSource;

/**
 * Offline-first HTTPS schema reference resolver for the current Defs Codegen.
 * Reference URI identity is retained even when content is served locally or from
 * a bounded disk cache. A referenced schema does not become an output contract.
 * The resolver does not depend on any historical Defs Codegen implementation.
 *
 * @author linhart1
 */
public final class AIcDefsCodegenSchemaReferenceResolver {
    /** Maximum allowed downloaded or cached schema size. */
    private static final int MAX_BYTES = 4 * 1024 * 1024;
    /** Suffixes of published, explicitly supported source schema documents. */
    private static final List<String> SUFFIXES = List.of(".jsondef.schema.json", ".yamldef.schema.json", ".xsd");
    /** Locally available source checkout roots (canonical paths). */
    private final List<Path> roots;
    /** Strict, optional public URI-to-file mapping; null enables normal HTTPS resolution. */
    private final Map<String, Path> locations;
    /** Persistent download cache, which is not an output schema directory. */
    private final Path cache;
    /** Timeout of each HTTPS request. */
    private final Duration timeout;
    /** HTTP client deliberately configured to reject any redirects. */
    private final HttpClient http;
    /** JSON schema identity parser; no schema content is evaluated as code. */
    private final ObjectMapper mapper = new ObjectMapper();

    /**
     * Creates an offline-first resolver for the explicit local source roots.
     *
     * @param sourceRoots declared schema source checkout roots, never arbitrary directories
     * @param cacheDirectory persistent schema cache directory, not a generated-source root
     * @param requestTimeout maximum duration of one HTTPS request
     * @throws IOException if a source root cannot be canonicalized
     * @throws IllegalArgumentException if the timeout is not positive
     * @throws NullPointerException if any required argument is null
     */
    public AIcDefsCodegenSchemaReferenceResolver(List<Path> sourceRoots, Path cacheDirectory,
            Duration requestTimeout) throws IOException {
        this(sourceRoots, cacheDirectory, requestTimeout, null);
    }

    /**
     * Create a resolver with optional strict, explicit local URI bindings.
     * @param sourceRoots declared source directories for the unmapped mode
     * @param cacheDirectory disk cache used only when no mapping is supplied
     * @param requestTimeout maximum HTTPS request duration in unmapped mode
     * @param locationsFile UTF-8 URL=absolute-path property file, or null for
     *        ordinary source/cache/HTTPS lookup; a provided map never uses HTTPS
     * @throws IOException on a missing, malformed or unsafe mapping
     * @throws IllegalArgumentException on invalid arguments
     */
    public AIcDefsCodegenSchemaReferenceResolver(List<Path> sourceRoots, Path cacheDirectory,
            Duration requestTimeout, Path locationsFile) throws IOException {
        Objects.requireNonNull(sourceRoots, "sourceRoots");
        this.roots = sourceRoots.stream().map(root -> {
            try {
                return root.toRealPath();
            } catch (IOException error) {
                throw new IllegalArgumentException("Schema source root unavailable: " + root, error);
            }
        }).toList();
        this.cache = Objects.requireNonNull(cacheDirectory, "cacheDirectory").toAbsolutePath().normalize();
        this.locations = locationsFile == null ? null : readLocations(locationsFile);
        this.timeout = Objects.requireNonNull(requestTimeout, "requestTimeout");
        if (timeout.isZero() || timeout.isNegative()) {
            throw new IllegalArgumentException("HTTPS request timeout must be positive");
        }
        this.http = HttpClient.newBuilder().connectTimeout(timeout)
                .followRedirects(HttpClient.Redirect.NEVER).build();
    }

    /**
     * Read the documented UTF-8 properties subset with the first equals sign
     * as separator. Literal HTTPS colons remain part of the property key.
     * @param file selected property file
     * @return immutable complete URI-to-local-path lookup
     * @throws IOException if entries are malformed, duplicate or unavailable
     */
    private static Map<String, Path> readLocations(Path file) throws IOException {
        Path actual = file.toRealPath();
        Map<String, Path> found = new java.util.LinkedHashMap<>();
        int lineNumber = 0;
        for (String raw : Files.readAllLines(actual, StandardCharsets.UTF_8)) {
            lineNumber++;
            String line = raw.trim();
            if (line.isBlank() || line.startsWith("#") || line.startsWith("!")) continue;
            int delimiter = line.indexOf('=');
            if (delimiter <= 0 || delimiter == line.length() - 1)
                throw new IOException(actual + ":" + lineNumber + ": expected HTTPS_URL=absolute_local_path");
            String key = line.substring(0, delimiter).trim();
            Path value = Path.of(line.substring(delimiter + 1).trim());
            URI uri;
            try { uri = URI.create(key); }
            catch (IllegalArgumentException ex) { throw new IOException("Invalid schema URL " + key, ex); }
            if (!"https".equals(uri.getScheme()) || uri.getHost() == null ||
                    uri.getRawFragment() != null || uri.getRawQuery() != null ||
                    SUFFIXES.stream().noneMatch(suffix -> uri.getPath().endsWith(suffix)))
                throw new IOException(actual + ":" + lineNumber + ": invalid schema URL " + key);
            if (!value.isAbsolute() || Files.isSymbolicLink(value) || !Files.isRegularFile(value))
                throw new IOException(actual + ":" + lineNumber + ": missing or unsafe mapped schema " + value);
            if (found.putIfAbsent(key, value.toRealPath()) != null)
                throw new IOException(actual + ":" + lineNumber + ": duplicate schema URL " + key);
        }
        return Map.copyOf(found);
    }

    /**
     * Verified reference with original public identity and physical provenance.
     *
     * @param uri absolute, fragment-free original public HTTPS URI
     * @param content unmodified verified source bytes
     * @param origin local/cache path or remote URI from which bytes were obtained
     */
    public record ResolvedSchema(URI uri, byte[] content, String origin) {
        /**
         * Return an independent copy to avoid mutation of cache/reference bytes.
         * @return defensive copy of the verified schema bytes
         */
        @Override public byte[] content() { return content.clone(); }
        /**
         * Copy source bytes on construction.
         * @param uri public schema URI
         * @param content source bytes, not null
         * @param origin physical retrieval provenance
         * @throws NullPointerException for missing attributes
         */
        public ResolvedSchema {
            Objects.requireNonNull(uri, "uri");
            content = Objects.requireNonNull(content, "content").clone();
            Objects.requireNonNull(origin, "origin");
        }
    }

    /**
     * Resolve a schema by public HTTPS identity, checking local roots and cache
     * before a bounded remote request. No network request is made on a cache hit.
     *
     * @param uri original absolute URI, optionally including a JSON Pointer fragment
     * @param expectedNamespace expected XSD targetNamespace; null disables that check
     * @return immutable original identity, verified source bytes and retrieval origin
     * @throws IOException on inaccessible input, invalid schema identity or HTTPS failure
     * @throws IllegalArgumentException on unsupported schema URIs
     * @throws InterruptedException if the calling thread is interrupted during HTTPS
     */
    public ResolvedSchema resolve(String uri, String expectedNamespace)
            throws IOException, InterruptedException {
        URI input = URI.create(Objects.requireNonNull(uri, "uri"));
        URI document = URI.create(input.getScheme() + "://" + input.getRawAuthority() + input.getRawPath());
        if (!"https".equals(input.getScheme()) || input.getHost() == null ||
                input.getRawUserInfo() != null || input.getRawQuery() != null ||
                (input.getRawFragment() != null && !input.getRawFragment().startsWith("/")) ||
                SUFFIXES.stream().noneMatch(s -> document.getPath().endsWith(s))) {
            throw new IllegalArgumentException("Unsupported HTTPS schema reference: " + uri);
        }
        String suffix = SUFFIXES.stream().filter(s -> document.getPath().endsWith(s)).findFirst().orElseThrow();
        if (locations != null) {
            Path local = locations.get(document.toString());
            if (local == null) throw new IOException("Schema URL " + document +
                    " is absent from --schema-locations-property-file (HTTPS fallback disabled)");
            return new ResolvedSchema(document, verify(document, Files.readAllBytes(local), expectedNamespace),
                    local.toString());
        }
        // Index only published schemas. Development examples and test fixtures
        // can legitimately reuse the $id of a production schema.
        Map<String, Path> published = new HashMap<>();
        for (Path root : roots) {
            try (var candidates = Files.walk(root)) {
                for (Path path : candidates.filter(Files::isRegularFile).filter(p -> !Files.isSymbolicLink(p))
                        .filter(p -> SUFFIXES.stream().anyMatch(s -> p.getFileName().toString().endsWith(s)))
                        .sorted().toList()) {
                    String location = path.toString().replace('\\', '/');
                    if (location.contains("/.git/") || location.contains("/build/") ||
                            location.contains("/node_modules/") || location.contains("/__pycache__/")) continue;
                    String marker = suffix.equals(".xsd") ? "/src/product/xmldefs/" :
                            suffix.equals(".jsondef.schema.json") ? "/src/product/jsondefs/" :
                            "/src/product/yamldefs/";
                    // A packaged dependency (JAR/wheel) may have schema resources
                    // directly under its package name, without src/product.
                    // Never treat development fixture paths as published inputs.
                    if (location.contains("/src/develop/") || !location.endsWith(suffix)) continue;
                    if (Files.size(path) > MAX_BYTES) continue;
                    byte[] bytes = Files.readAllBytes(path);
                    String identity;
                    if (suffix.equals(".xsd")) {
                        String declared = declaredXmlNamespace(bytes);
                        if (declared.startsWith("https://") && declared.endsWith(".xsd"))
                            identity = declared;
                        else if (location.contains(marker))
                            identity = "https://defs.dev.algites.eu/api/xmldefs/" + location.split(marker, 2)[1];
                        else continue;
                    } else {
                        try {
                            identity = mapper.readTree(bytes).path("$id").asText();
                        } catch (IOException exception) {
                            continue;
                        }
                    }
                    if (!document.toString().equals(identity)) continue;
                    Path previous = published.putIfAbsent(identity, path);
                    if (previous != null && !Arrays.equals(Files.readAllBytes(previous), bytes)) {
                        throw new IOException("Conflicting published local schema declarations for " + identity +
                                ": " + previous + " and " + path);
                    }
                }
            }
        }
        if (published.containsKey(document.toString())) {
            Path source = published.get(document.toString());
            return new ResolvedSchema(document, verify(document, Files.readAllBytes(source), expectedNamespace),
                    source.toString());
        }
        Files.createDirectories(cache);
        Path location = cache.resolve(sha256(document.toString()) + suffix);
        if (Files.exists(location, LinkOption.NOFOLLOW_LINKS)) {
            if (Files.isSymbolicLink(location)) throw new IOException("Symlinked schema cache entry: " + location);
            return new ResolvedSchema(document, verify(document, Files.readAllBytes(location), expectedNamespace),
                    location.toString());
        }
        IOException failure = null;
        for (int attempt = 0; attempt < 2; attempt++) {
            try {
                var request = HttpRequest.newBuilder(document).timeout(timeout).GET().build();
                var response = http.send(request, HttpResponse.BodyHandlers.ofByteArray());
                if (response.statusCode() != 200) {
                    throw new IOException("Schema HTTPS response " + response.statusCode() + " for " + document);
                }
                var bytes = verify(document, response.body(), expectedNamespace);
                Path temporary = Files.createTempFile(cache, "schema-", ".tmp");
                try {
                    Files.write(temporary, bytes);
                    Files.move(temporary, location, StandardCopyOption.REPLACE_EXISTING);
                } finally {
                    Files.deleteIfExists(temporary);
                }
                return new ResolvedSchema(document, bytes, document.toString());
            } catch (IOException exception) {
                failure = exception;
            }
        }
        throw new IOException("Cannot resolve HTTPS schema " + document + " after two attempts", failure);
    }

    /**
     * Read an XSD target namespace from an untrusted packaged resource without
     * enabling DTD processing, XInclude, external entities or external schema
     * loading. A URL-shaped namespace is a stable offline package key.
     * @param contents exact XSD schema resource bytes
     * @return targetNamespace value, possibly empty
     * @throws IOException on a malformed or unsafe XML source
     */
    private static String declaredXmlNamespace(byte[] contents) throws IOException {
        String xml = new String(contents, StandardCharsets.UTF_8);
        if (xml.toUpperCase(java.util.Locale.ROOT).contains("<!DOCTYPE") ||
                xml.toUpperCase(java.util.Locale.ROOT).contains("<!ENTITY"))
            throw new IOException("DTD/entity is forbidden in packaged XSD dependency");
        try {
            var factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
            factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
            factory.setXIncludeAware(false);
            factory.setExpandEntityReferences(false);
            var root = factory.newDocumentBuilder().parse(new InputSource(new StringReader(xml)))
                    .getDocumentElement();
            if (!XMLConstants.W3C_XML_SCHEMA_NS_URI.equals(root.getNamespaceURI()) ||
                    !"schema".equals(root.getLocalName()))
                throw new IOException("Packaged XML resource is not an XSD schema");
            return root.getAttribute("targetNamespace");
        } catch (IOException error) {
            throw error;
        } catch (Exception error) {
            throw new IOException("Malformed packaged XSD dependency", error);
        }
    }

    /**
     * Verify the schema language and its declared identity against the URL.
     *
     * @param uri public schema URI
     * @param bytes source bytes
     * @param namespace expected XML target namespace or null
     * @return the same verified byte sequence
     * @throws IOException if schema structure, identity, or size is invalid
     */
    private byte[] verify(URI uri, byte[] bytes, String namespace) throws IOException {
        if (bytes.length == 0 || bytes.length > MAX_BYTES) throw new IOException("Invalid schema size: " + uri);
        if (uri.getPath().endsWith(".xsd")) {
            String xml = new String(bytes, StandardCharsets.UTF_8);
            if (xml.toUpperCase(java.util.Locale.ROOT).contains("<!DOCTYPE") ||
                    xml.toUpperCase(java.util.Locale.ROOT).contains("<!ENTITY")) {
                throw new IOException("DTD/entity is forbidden in schema: " + uri);
            }
            try {
                var factory = DocumentBuilderFactory.newInstance();
                factory.setNamespaceAware(true);
                factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
                factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
                factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
                factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
                factory.setXIncludeAware(false);
                factory.setExpandEntityReferences(false);
                var element = factory.newDocumentBuilder().parse(new InputSource(new StringReader(xml)))
                        .getDocumentElement();
                if (!XMLConstants.W3C_XML_SCHEMA_NS_URI.equals(element.getNamespaceURI()) ||
                        !"schema".equals(element.getLocalName())) {
                    throw new IOException("Reference is not an XSD schema: " + uri);
                }
                if (namespace != null && !namespace.equals(element.getAttribute("targetNamespace"))) {
                    throw new IOException("Wrong XSD targetNamespace: " + uri);
                }
            } catch (IOException error) {
                throw error;
            } catch (Exception error) {
                throw new IOException("Invalid referenced XSD: " + uri, error);
            }
        } else if (!uri.toString().equals(mapper.readTree(bytes).path("$id").asText())) {
            throw new IOException("Referenced schema $id does not match URI: " + uri);
        }
        return bytes;
    }

    /**
     * Compute a portable collision-resistant cache-key digest.
     * @param source public schema identity
     * @return hexadecimal SHA-256 digest
     */
    private static String sha256(String source) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(source.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("SHA-256 provider unavailable", error);
        }
    }
}
