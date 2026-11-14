package eu.algites.tool.codegen.defs.impl.cli;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;

/**
 * Resolves existing, read-only Java and Python Defs contracts by their schema
 * identity and declared inheritance, independent of naming-profile prefixes.
 *
 * <p>Every XML/JSON/YAML identity of a unified read-only DataObject is indexed
 * onto that same contract. Temporary ABI seeds or packaging copies do not
 * override current generated sources. Independent competing source contracts
 * remain validation errors. Writable SDO interfaces are never candidates.</p>
 *
 * @author linhart1
 */
public final class AIcDefsCodegenExternalContractIndex {
    /** Maximum individual generated-source size accepted during indexing. */
    private static final long MAX_SOURCE_BYTES = 2_000_000;
    /** Extract the public Java interface, irrespective of naming convention. */
    private static final Pattern JAVA_TYPE = Pattern.compile("\\bpublic\\s+interface\\s+(\\w+)");
    /** Match the package in a generated Java source file. */
    private static final Pattern JAVA_PACKAGE = Pattern.compile("(?m)^package\\s+([\\w.]+)\\s*;");
    /** Recognize format-schema annotations, including deprecated equivalents.
     * Generic AIaDataObject is declared on the common interface instead. */
    private static final Pattern JAVA_ANNOTATION = Pattern.compile(
            "@(?:[\\w.]+\\.)?(?:AIaDataObjectJsonSchema|AIaDataObjectXmlSchema|"
            + "AIaJsonDataObject|AIaYamlDataObject|AIaXmlDataObject)\\s*\\(");
    /** Extract XML TYPE metadata from the Java interface annotation. */
    private static final Pattern JAVA_XML_TYPE = Pattern.compile("\\bdefinitionKind\\s*=\\s*[\\w.]+\\.TYPE\\b");
    /** Extract Python metadata-bearing classes, not module-level helper functions. */
    private static final Pattern PY_CLASS = Pattern.compile("(?m)^class\\s+(\\w+)(?:\\s*\\(([^:]*?)\\))?\\s*:", Pattern.DOTALL);
    /** Extract Python absolute imports to resolve inheritance across modules. */
    private static final Pattern PY_IMPORT = Pattern.compile("(?m)^from\\s+([\\w.]+)\\s+import\\s+(\\w+)(?:\\s+as\\s+(\\w+))?");
    /** Extract any Java/Python schema ID. */
    private static final Pattern JAVA_ID = Pattern.compile("\\bschemaId\\s*=\\s*\"([^\"]+)\"");
    /** Extract the Java URL representing a JSONDEFS/YAMLDEFS root contract. */
    private static final Pattern JAVA_URL = Pattern.compile("\\bschemaUrl\\s*=\\s*\"(https://[^\"\\s]+)\"");
    /** Extract the XML namespace independently from generic DataObject metadata. */
    private static final Pattern JAVA_XML_NAMESPACE = Pattern.compile("\\bnamespace\\s*=\\s*\"([^\"]*)\"");
    /** Extract the XML type's local name from Java annotations. */
    private static final Pattern JAVA_XML_NAME = Pattern.compile("\\bnamespaceLocalName\\s*=\\s*\"([^\"]+)\"");
    /** Extract the source schema ID from Python metadata. */
    private static final Pattern PY_ID = Pattern.compile("\\bschema_id\\s*=\\s*['\"]([^'\"]+)['\"]");
    /** Extract the JSONDEFS/YAMLDEFS schema URL from Python metadata. */
    private static final Pattern PY_URL = Pattern.compile("\\bschema_url\\s*=\\s*['\"](https://[^'\"\\s]+)['\"]");
    /** Extract Python XML namespace metadata, not a generic schema ID. */
    private static final Pattern PY_XML_NAMESPACE = Pattern.compile("\\bnamespace\\s*=\\s*['\"]([^'\"]*)['\"]");
    /** Extract an XML type's local name from Python metadata. */
    private static final Pattern PY_XML_NAME = Pattern.compile("\\bnamespace_local_name\\s*=\\s*['\"]([^'\"]+)['\"]");
    /** Identify writable Java SDO methods without depending on their type prefix. */
    private static final Pattern JAVA_MUTATION = Pattern.compile("\\b(?:set[A-Z]\\w*|_unset\\w*)\\s*\\(");
    /** Identify writable Python SDO methods without depending on their type prefix. */
    private static final Pattern PY_MUTATION = Pattern.compile("(?m)^\\s+def\\s+(?:set[A-Z]\\w*|_unset\\w*)\\s*\\(");

    /** Stateless utility; never instantiated. */
    private AIcDefsCodegenExternalContractIndex() { }

    /**
     * Fully-qualified symbols of one technology pair for an external schema.
     * Missing technology symbols remain null until both sides can be verified.
     *
     * @param javaType Java interface's fully-qualified binary source name
     * @param pythonModule absolute Python module path
     * @param pythonType Python read-only class name
     */
    public record ContractSymbols(String javaType, String pythonModule, String pythonType) { }

    /**
     * Index contracts from declared dependency source checkouts, without executing
     * source files or fetching arbitrary additional paths.
     *
     * @param roots configured local checkouts containing generated read-only contracts
     * @return schema identities mapped to unambiguous Java/Python source symbols
     * @throws IOException if a generated source file cannot be read
     * @throws IllegalArgumentException on unrelated duplicate contracts or conflicting symbols
     */
    public static Map<String, ContractSymbols> resolve(List<Path> roots) throws IOException {
        return resolve(roots, null);
    }

    /**
     * Resolve only contracts directly referenced by the current generation batch.
     * Other checkouts may contain unrelated, even ambiguous, schema projections;
     * their validation must not block an independent artifact's generation.
     *
     * @param roots declared local dependency checkouts
     * @param requiredIdentities exact referenced schema or qualified XML type IDs;
     *        null requests a complete index for standalone diagnostics
     * @return resolved source symbols for the requested identities
     * @throws IOException on unreadable input
     * @throws IllegalArgumentException on conflicting required contracts
     */
    public static Map<String, ContractSymbols> resolve(List<Path> roots,
            Set<String> requiredIdentities) throws IOException {
        if (requiredIdentities != null && requiredIdentities.isEmpty()) return Map.of();
        Map<String, Map<String, Set<String>>> java = new LinkedHashMap<>();
        Map<String, Map<String, Set<String>>> python = new LinkedHashMap<>();
        Map<String, Map<String, Path>> javaOrigins = new LinkedHashMap<>();
        Map<String, Map<String, Path>> pythonOrigins = new LinkedHashMap<>();
        for (Path root : roots) {
            if (!Files.isDirectory(root)) continue;
            try (Stream<Path> stream = Files.walk(root)) {
                for (Path file : stream.filter(Files::isRegularFile).sorted().toList()) {
                    if (Files.isSymbolicLink(file)) continue;
                    if (file.getFileName().toString().endsWith(".class")) {
                        for (var compiled : AIcDefsCodegenCompiledContractReader.readAll(file)) {
                            recordCandidate(java, javaOrigins, requiredIdentities,
                                    compiled.identity(), compiled.symbol(), compiled.parents(), file);
                        }
                        continue;
                    }
                    if (Files.size(file) > MAX_SOURCE_BYTES) continue;
                    boolean isJava = file.getFileName().toString().endsWith(".java")
                            && file.getParent().toString().replace('\\', '/').contains("/java.gen/");
                    boolean isPython = file.getFileName().toString().endsWith(".py")
                            && (file.getParent().toString().replace('\\', '/').contains("/python.gen/")
                                || file.toString().replace('\\', '/').contains("/eu/algites/"));
                    if (!isJava && !isPython) continue;
                    String content = Files.readString(file);
                    if (isJava) scanJava(content, file, java, javaOrigins, requiredIdentities);
                    else scanPython(content, file, python, pythonOrigins, requiredIdentities);
                }
            }
        }
        Map<String, ContractSymbols> result = new LinkedHashMap<>();
        Set<String> identities = new java.util.TreeSet<>(java.keySet());
        identities.addAll(python.keySet());
        for (String identity : identities) {
            if (requiredIdentities != null && !requiredIdentities.contains(identity)) continue;
            String javaSymbol = mostDerived(identity, "java", java.get(identity), javaOrigins.get(identity));
            String pythonSymbol = mostDerived(identity, "python", python.get(identity), pythonOrigins.get(identity));
            String pythonModule = null, pythonType = null;
            if (pythonSymbol != null) {
                int dot = pythonSymbol.lastIndexOf('.');
                if (dot < 1) throw new IllegalArgumentException("Invalid Python contract: " + pythonSymbol);
                pythonModule = pythonSymbol.substring(0, dot);
                pythonType = pythonSymbol.substring(dot + 1);
            }
            result.put(identity, new ContractSymbols(javaSymbol, pythonModule, pythonType));
        }
        return Map.copyOf(result);
    }

    /**
     * Inspect one Java read-only interface declaration and its parents.
     * @param source full UTF-8 compilation unit
     * @param index candidate identity map receiving the declaration
     */
    private static void scanJava(String source, Path file,
            Map<String, Map<String, Set<String>>> index,
            Map<String, Map<String, Path>> origins, Set<String> required) {
        if (!JAVA_ANNOTATION.matcher(source).find()) return;
        Matcher packageMatch = JAVA_PACKAGE.matcher(source), typeMatch = JAVA_TYPE.matcher(source);
        if (!packageMatch.find() || !typeMatch.find()) return;
        int brace = source.indexOf('{', typeMatch.end());
        if (brace < 0) return;
        String header = source.substring(typeMatch.end(), brace);
        // Never allow a writable API to supersede the read-only Defs interface.
        if (header.contains("AIiSmartDataObject") || JAVA_MUTATION.matcher(source.substring(brace)).find()) return;
        Set<String> identities = schemaIdentities(source, true);
        if (identities.isEmpty()) return;
        String pack = packageMatch.group(1);
        Map<String, String> imports = new HashMap<>();
        Matcher importMatch = Pattern.compile("(?m)^import\\s+([\\w.]+)\\s*;").matcher(source);
        while (importMatch.find()) {
            String imported = importMatch.group(1);
            imports.put(imported.substring(imported.lastIndexOf('.') + 1), imported);
        }
        Set<String> parents = new HashSet<>();
        Matcher extendsMatch = Pattern.compile("\\bextends\\s+(.+)", Pattern.DOTALL).matcher(header);
        if (extendsMatch.find()) {
            String flat = withoutGenericArguments(extendsMatch.group(1));
            for (String part : flat.split(",")) {
                String base = part.trim();
                if (base.isEmpty()) continue;
                base = base.split("\\s+", 2)[0];
                parents.add(base.contains(".") ? base : imports.getOrDefault(base, pack + "." + base));
            }
        }
        for (String identity : identities) {
            recordCandidate(index, origins, required, identity, pack + "." + typeMatch.group(1),
                    parents, file);
        }
    }

    /**
     * Inspect Python read-only DataObject classes and their directly declared bases.
     * @param source complete generated module text
     * @param file source path within a python.gen tree
     * @param index candidate identity map receiving the declaration
     */
    private static void scanPython(String source, Path file,
            Map<String, Map<String, Set<String>>> index,
            Map<String, Map<String, Path>> origins, Set<String> required) {
        if (source.contains("Generated mutable contract") ||
                source.contains("Generated SmartDataObject implementation")) return;
        String path = file.toString().replace('\\', '/');
        int marker = path.lastIndexOf("/python.gen/");
        String module;
        if (marker < 0) {
            int packageStart = path.indexOf("/eu/algites/");
            if (packageStart < 0) return;
            module = path.substring(packageStart + 1).replace('/', '.').replaceAll("\\.py$", "");
        } else {
            module = path.substring(marker + "/python.gen/".length())
                    .replace('/', '.').replaceAll("\\.py$", "");
        }
        Map<String, String> imports = new HashMap<>();
        Matcher importMatch = PY_IMPORT.matcher(source);
        while (importMatch.find()) {
            String alias = importMatch.group(3) == null ? importMatch.group(2) : importMatch.group(3);
            imports.put(alias, importMatch.group(1) + "." + importMatch.group(2));
        }
        Matcher typeMatch = PY_CLASS.matcher(source);
        List<int[]> declarations = new ArrayList<>();
        while (typeMatch.find()) declarations.add(new int[]{typeMatch.start(), typeMatch.end()});
        for (int i = 0; i < declarations.size(); i++) {
            int start = declarations.get(i)[0];
            int end = i + 1 < declarations.size() ? declarations.get(i + 1)[0] : source.length();
            String block = source.substring(start, end);
            Matcher declaration = PY_CLASS.matcher(block);
            if (!declaration.find() ||
                    !(block.contains("__json_schema__") || block.contains("__xml_schema__")
                      || block.contains("__json_data_object__")
                      || block.contains("__yaml_data_object__")
                      || block.contains("__xml_data_object__")) ||
                    PY_MUTATION.matcher(block).find() || block.contains("AIiSmartDataObject")) continue;
            Set<String> identities = schemaIdentities(block, false);
            if (identities.isEmpty()) continue;
            Set<String> parents = new HashSet<>();
            for (String raw : withoutGenericArguments(declaration.group(2) == null ? "" : declaration.group(2)).split(",")) {
                String base = raw.trim();
                if (base.isEmpty()) continue;
                parents.add(imports.getOrDefault(base, module + "." + base));
            }
            for (String identity : identities) {
                recordCandidate(index, origins, required, identity,
                        module + "." + declaration.group(1), parents, file);
            }
        }
    }

    /**
     * Collect independent format-specific schema identities from one unified
     * read-only declaration. No equality is required between XML, JSON and YAML
     * IDs or versions. Transitional annotations for one format are deduplicated.
     *
     * @param source one Java compilation unit or Python class source block
     * @param java true for Java annotation syntax, false for Python metadata
     * @return unique qualified XML type and JSON/YAML public URLs
     */
    private static Set<String> schemaIdentities(String source, boolean java) {
        Map<String, String> attributes = new LinkedHashMap<>();
        Pattern annotation = java
                ? Pattern.compile("@(?:[\\w.]+\\.)?(AIaDataObjectJsonSchema|AIaDataObjectXmlSchema|"
                        + "AIaJsonDataObject|AIaYamlDataObject|AIaXmlDataObject)\\s*\\(([^)]*)\\)")
                : Pattern.compile("__(xml_schema|json_schema|xml_data_object|json_data_object|"
                        + "yaml_data_object)__\\s*=\\s*AIa\\w+\\s*\\(([^)]*)\\)");
        Matcher matches = annotation.matcher(source);
        while (matches.find()) attributes.put(matches.group(1), matches.group(2));
        String xml = java ? attributes.getOrDefault("AIaDataObjectXmlSchema",
                attributes.get("AIaXmlDataObject")) : attributes.getOrDefault("xml_schema",
                attributes.get("xml_data_object"));
        String json = java ? attributes.getOrDefault("AIaDataObjectJsonSchema",
                attributes.get("AIaJsonDataObject")) : attributes.getOrDefault("json_schema",
                attributes.get("json_data_object"));
        String yaml = java ? attributes.get("AIaYamlDataObject") : attributes.get("yaml_data_object");
        Set<String> result = new HashSet<>();
        if (xml != null && (java ? JAVA_XML_TYPE : Pattern.compile(
                "\\bdefinition_kind\\s*=\\s*[\\w.]+\\.TYPE\\b")).matcher(xml).find()) {
            Matcher namespace = (java ? JAVA_XML_NAMESPACE : PY_XML_NAMESPACE).matcher(xml);
            Matcher name = (java ? JAVA_XML_NAME : PY_XML_NAME).matcher(xml);
            if (namespace.find() && name.find()) result.add("{" + namespace.group(1) + "}" + name.group(1));
        }
        for (String metadata : new String[] {json, yaml}) {
            if (metadata == null) continue;
            Matcher id = (java ? JAVA_ID : PY_ID).matcher(metadata);
            Matcher uri = (java ? JAVA_URL : PY_URL).matcher(metadata);
            if (id.find() && !id.group(1).contains("#") && uri.find()) result.add(uri.group(1));
        }
        return result;
    }

    /**
     * Remove nested generic arguments so comma separators represent parent types.
     * @param source Java/Python base-type declaration
     * @return declaration without generic argument groups
     */
    private static String withoutGenericArguments(String source) {
        StringBuilder result = new StringBuilder();
        int depth = 0;
        for (int i = 0; i < source.length(); i++) {
            char item = source.charAt(i);
            if (item == '<' || item == '[') { depth++; continue; }
            if (item == '>' || item == ']') { if (depth > 0) depth--; continue; }
            if (depth == 0) result.append(item);
        }
        return result.toString();
    }

    /**
     * Add a candidate and reject contradictory metadata for one symbol.
     * @param index schema identity candidate index
     * @param identity exact schema or QName identity
     * @param symbol fully qualified generated interface symbol
     * @param parents direct superclass/interface symbols
     */
    private static void recordCandidate(Map<String, Map<String, Set<String>>> index,
            Map<String, Map<String, Path>> origins, Set<String> required,
            String identity, String symbol, Set<String> parents, Path source) {
        // Unrelated contracts must not block the artifact being generated.
        if (required != null && !required.contains(identity)) return;
        Map<String, Set<String>> group = index.computeIfAbsent(identity, ignored -> new LinkedHashMap<>());
        Set<String> previous = group.putIfAbsent(symbol, Set.copyOf(parents));
        Map<String, Path> locations = origins.computeIfAbsent(identity, ignored -> new LinkedHashMap<>());
        if (previous != null && !previous.equals(parents)) {
            throw new IllegalArgumentException("Conflicting generated contract: " + identity
                    + " (" + symbol + "); " + locations.get(symbol) + ": parents=" + previous
                    + "; " + source + ": parents=" + parents);
        }
        if (previous == null) locations.put(symbol, source);
    }

    /**
     * Select the unique interface inheriting all other same-identity candidates.
     * @param identity schema identity for diagnostics
     * @param technology technology label for diagnostics
     * @param group candidates mapped to immediate parent symbols
     * @return fully qualified selected symbol; null when no candidate exists
     */
    private static String mostDerived(String identity, String technology,
            Map<String, Set<String>> group, Map<String, Path> origins) {
        if (group == null || group.isEmpty()) return null;
        // Current generated product contracts supersede temporary compiler
        // ABI seeds, staged build/lib copies and compiled shadows of the same
        // schema identity. Genuine competing product sources stay ambiguous.
        String generatedRoot = technology.equals("java") ? "java.gen" : "python.gen";
        boolean hasSource = group.keySet().stream().anyMatch(symbol ->
                origins.get(symbol) != null
                        && origins.get(symbol).toString().replace('\\', '/').contains("/" + generatedRoot + "/"));
        if (hasSource) {
            Map<String, Set<String>> live = new LinkedHashMap<>();
            for (var entry : group.entrySet()) {
                Path origin = origins.get(entry.getKey());
                String path = origin == null ? "" : origin.toString().replace('\\', '/');
                if (path.contains("/" + generatedRoot + "/")
                        || (!path.contains(".extgen/") && !path.contains("/build/lib/")
                            && !path.endsWith(".class"))) {
                    live.put(entry.getKey(), entry.getValue());
                }
            }
            group = live;
        }
        List<String> winners = new ArrayList<>();
        for (String candidate : group.keySet()) {
            Set<String> ancestors = new HashSet<>();
            var pending = new ArrayDeque<>(group.get(candidate));
            while (!pending.isEmpty()) {
                String parent = pending.pop();
                if (ancestors.add(parent)) pending.addAll(group.getOrDefault(parent, Set.of()));
            }
            if (group.keySet().stream().allMatch(other -> other.equals(candidate) || ancestors.contains(other))) {
                winners.add(candidate);
            }
        }
        if (winners.size() != 1) {
            List<String> descriptions = new ArrayList<>();
            for (String symbol : group.keySet()) {
                descriptions.add(symbol + " [" + origins.get(symbol) + "]");
            }
            throw new IllegalArgumentException("Ambiguous existing generated contract " + identity
                    + " (" + technology + "): unrelated candidates " + String.join(", ", descriptions));
        }
        return winners.get(0);
    }
}
