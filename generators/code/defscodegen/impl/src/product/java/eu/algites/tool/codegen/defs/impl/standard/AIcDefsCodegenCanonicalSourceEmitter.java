package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenElement;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenElementList;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenEnum;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenList;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenMap;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenScalar;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenType;
import eu.algites.tool.codegen.defs.AIiDefsCodegenStructure;
import eu.algites.tool.codegen.defs.AInDefsCodegenComposition;
import eu.algites.tool.codegen.defs.AInDefsCodegenMapKind;
import eu.algites.tool.codegen.defs.AInDefsCodegenResolutionState;
import eu.algites.tool.codegen.defs.AInDefsCodegenScalarKind;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Native Java source renderer for a losslessly supported subset of the canonical
 * Defs graph. The implementation does not depend on the deprecated generator.
 * Names must be produced by the configured source-code naming catalog; this
 * renderer does not invent type names or reinterpret schema source identities.
 *
 * <p>Output is an immutable ordered set of complete Java and Python source files.
 * Unsupported semantic constructs fail the complete render before publication.
 * The repository and CLI layer owns atomic publishing and generated-file state.</p>
 */
public final class AIcDefsCodegenCanonicalSourceEmitter {
    /** Valid identifier characters for the Java compilation unit and package. */
    private static final Pattern JAVA_ID = Pattern.compile("[A-Za-z_$][A-Za-z0-9_$]*");
    /** Valid identifier characters for Python modules and definitions. */
    private static final Pattern PYTHON_ID = Pattern.compile("[A-Za-z_][A-Za-z0-9_]*");
    /** Java keywords and contextual declarations forbidden as generated identifiers. */
    private static final Set<String> JAVA_RESERVED = Set.of(
            "class", "interface", "record", "enum", "extends", "implements", "import", "package", "public",
            "private", "protected", "static", "final", "void", "new", "this", "super", "true", "false", "null",
            "if", "else", "for", "while", "switch", "case", "default", "break", "continue", "return",
            "try", "catch", "finally", "throw", "throws", "sealed", "permits", "var", "yield", "int",
            "long", "double", "float", "char", "byte", "short", "boolean", "abstract", "assert", "do",
            "instanceof", "native", "strictfp", "synchronized", "transient", "volatile", "const", "goto");
    /** Python keywords and reserved class identifiers. */
    private static final Set<String> PYTHON_RESERVED = Set.of(
            "and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif",
            "else", "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "True", "try", "while", "with", "yield", "None");
    /** Selected Common + Defs naming role definitions and compositions. */
    private final AIcCodegenNamingProfileResolver.Profile naming;
    /** Canonical identity to Java type, Python type, and Python module names. */
    private final Map<String, Names> outputNames;
    /** Validated target package shared by both output technologies. */
    private final String packageName;

    /**
     * Fully resolved output names of one canonical TYPE declaration.
     *
     * @param javaType Java class/interface name selected by the naming catalog
     * @param pythonType Python class name selected by the naming catalog
     * @param pythonModule filename stem for the Python source file
     */
    public record Names(String javaType, String pythonType, String pythonModule) { }

    /**
     * One rendered compilation unit, before committing to a generated source root.
     *
     * @param language target language ({@code java} or {@code python})
     * @param relativePath package-relative output path for generated source roots
     * @param sourceText complete UTF-8 source text
     * @param typeIdentity exact canonical identity of the owning declaration
     */
    public record Output(String language, String relativePath, String sourceText, String typeIdentity) { }

    /**
     * Creates a fail-closed, pure output renderer.
     *
     * @param naming explicit Common + Defs naming context with resolved method compositions
     * @param outputNames catalog-derived names for every canonical declaration
     * @param packageName required target Java package, also used as Python module path
     * @throws IllegalArgumentException if the package name is not a legal Java package
     */
    public AIcDefsCodegenCanonicalSourceEmitter(AIcCodegenNamingProfileResolver.Profile naming,
            Map<String, Names> outputNames, String packageName) {
        this.naming = Objects.requireNonNull(naming, "naming");
        this.outputNames = Map.copyOf(Objects.requireNonNull(outputNames, "outputNames"));
        this.packageName = Objects.requireNonNull(packageName, "packageName");
        for (var part : packageName.split("\\.", -1)) identifier(part, true);
    }

    /**
     * Validates and emits every supported declaration for both language targets.
     * No files are written until the caller receives the complete output list.
     *
     * @param roots normalized and reference-resolved declarations from the pipeline
     * @return immutable, reproducibly ordered list of Java and Python compilation units
     * @throws IllegalArgumentException for missing/duplicate names or unknown type links
     * @throws UnsupportedOperationException when a shape would lose semantics in emission
     */
    public List<Output> render(List<AIcdDefsCodegenType> roots) {
        Objects.requireNonNull(roots, "roots");
        Map<String, AIcdDefsCodegenType> types = new LinkedHashMap<>();
        for (var root : roots) collect(root, types);
        if (types.isEmpty()) throw new IllegalArgumentException("No canonical source types to emit");
        if (!types.keySet().equals(outputNames.keySet())) {
            throw new IllegalArgumentException("Output names do not exactly cover canonical identities: "
                    + types.keySet() + " versus " + outputNames.keySet());
        }
        Set<String> paths = new HashSet<>();
        for (var type : types.values()) {
            var names = outputNames.get(type.identity());
            identifier(names.javaType(), true);
            identifier(names.pythonType(), false);
            identifier(names.pythonModule(), false);
            if (!paths.add("java:" + names.javaType().toLowerCase(java.util.Locale.ROOT)) ||
                    !paths.add("python:" + names.pythonModule().toLowerCase(java.util.Locale.ROOT))) {
                throw new IllegalArgumentException("Generated output path collision at " + type.identity());
            }
            for (String parent : type.inheritedFromTypes()) {
                if (!types.containsKey(parent)) throw new IllegalArgumentException("Unresolved parent " + parent);
            }
        }
        Map<String, String> choiceParents = choiceParents(types);
        List<Output> result = new ArrayList<>();
        String folder = packageName.replace('.', '/') + '/';
        for (var type : types.values()) {
            var names = outputNames.get(type.identity());
            result.add(new Output("java", folder + names.javaType() + ".java", javaSource(type, types, choiceParents), type.identity()));
            result.add(new Output("python", folder + names.pythonModule() + ".py", pythonSource(type, types, choiceParents), type.identity()));
        }
        return List.copyOf(result);
    }

    /**
     * Exposes every ordered output declaration, including embedded synthetic
     * variants, for the external catalog naming phase. This method never
     * invents class identifiers or modifies the canonical graph.
     *
     * @param roots normalized, reference-linked top-level type declarations
     * @return unmodifiable ordered set of output TYPE definitions
     * @throws IllegalArgumentException when a nested canonical identity conflicts
     */
    public static List<AIcdDefsCodegenType> declarations(List<AIcdDefsCodegenType> roots) {
        Objects.requireNonNull(roots, "roots");
        Map<String, AIcdDefsCodegenType> registry = new LinkedHashMap<>();
        for (var type : roots) collect(type, registry);
        return List.copyOf(registry.values());
    }

    /**
     * Collects an embedded synthetic type exactly once and detects inconsistent aliases.
     *
     * @param node canonical node under traversal
     * @param result mutable insertion-order identity registry
     */
    private static void collect(AIiDefsCodegenStructure node, Map<String, AIcdDefsCodegenType> result) {
        if (node instanceof AIcdDefsCodegenType type) {
            if (type.resolutionState() != AInDefsCodegenResolutionState.RESOLVED) {
                throw new IllegalArgumentException("Unresolved canonical TYPE " + type.identity());
            }
            if (!type.targetIdentity().isBlank()) return;
            var previous = result.putIfAbsent(type.identity(), type);
            if (previous != null) {
                if (!previous.equals(type)) throw new IllegalArgumentException("Conflicting canonical identity " + type.identity());
                return;
            }
            collect(type.structure(), result);
        } else if (node instanceof AIcdDefsCodegenElementList group) {
            for (var child : group.children()) collect(child, result);
        } else if (node instanceof AIcdDefsCodegenElement member) {
            collect(member.structure(), result);
        } else if (node instanceof AIcdDefsCodegenList list) {
            collect(list.item(), result);
        } else if (node instanceof AIcdDefsCodegenMap map) {
            collect(map.keyType(), result);
            collect(map.valueType(), result);
        } else if (!(node instanceof AIcdDefsCodegenScalar) && !(node instanceof AIcdDefsCodegenEnum)) {
            throw new IllegalArgumentException("Unsupported canonical structure " + node);
        }
    }

    /**
     * Computes ownership of first-class closed variants and validates
     * every exclusive choice before generating any target-language source.
     *
     * @param types ordered registry of explicit and embedded synthetic types
     * @return canonical variant ID to its sealed parent type ID
     * @throws UnsupportedOperationException for unsupported nested choice structures
     * @throws IllegalArgumentException for ambiguous or dangling variant ownership
     */
    private static Map<String, String> choiceParents(Map<String, AIcdDefsCodegenType> types) {
        Map<String, String> result = new LinkedHashMap<>();
        for (var owner : types.values()) {
            if (!(owner.structure() instanceof AIcdDefsCodegenElementList group) ||
                    group.composition() != AInDefsCodegenComposition.CHOICE) continue;
            if (group.minOccurs() != 1 || group.maxOccurs() != 1 || !owner.inheritedFromTypes().isEmpty()) {
                throw new UnsupportedOperationException("CHOICE group occurrences/inheritance unsupported: " + owner.identity());
            }
            if (group.children().isEmpty()) throw new IllegalArgumentException("Empty CHOICE " + owner.identity());
            for (var child : group.children()) {
                if (!(child instanceof AIcdDefsCodegenElement element) ||
                        !(element.structure() instanceof AIcdDefsCodegenType variant) ||
                        !variant.targetIdentity().isEmpty() || element.minOccurs() != 0 || element.maxOccurs() != 1) {
                    throw new UnsupportedOperationException("CHOICE requires named exclusive variants: " + owner.identity());
                }
                if (!(variant.structure() instanceof AIcdDefsCodegenScalar) &&
                        !(variant.structure() instanceof AIcdDefsCodegenElementList object &&
                        (object.composition() == AInDefsCodegenComposition.SEQUENCE ||
                         object.composition() == AInDefsCodegenComposition.ALL))) {
                    throw new UnsupportedOperationException("Unsupported CHOICE variant " + variant.identity());
                }
                if (!variant.inheritedFromTypes().isEmpty() || !types.containsKey(variant.identity())) {
                    throw new IllegalArgumentException("Invalid CHOICE variant " + variant.identity());
                }
                if (result.putIfAbsent(variant.identity(), owner.identity()) != null) {
                    throw new IllegalArgumentException("CHOICE variant has multiple owners " + variant.identity());
                }
            }
        }
        return Map.copyOf(result);
    }

    /**
     * One source key translated into runtime semantic paths (not arbitrary XPath).
     *
     * @param name identity of the XSD key or unique constraint
     * @param fields source-ordered semantic paths for runtime field extraction
     * @param required whether incomplete composite keys are forbidden
     */
    private record IndexKey(String name, List<String> fields, boolean required) { }

    /**
     * Converts the safe direct-child XPath subset to the SDO's field path format.
     * Descendant selectors, namespaces and predicates need a namespace-aware
     * resolver and are rejected rather than silently converted incorrectly.
     *
     * @param list directly indexed canonical LIST
     * @param types resolved declared and synthetic model types
     * @return runtime key definitions in source order
     * @throws UnsupportedOperationException if any XPath cannot be resolved safely
     * @throws IllegalArgumentException if a definition lacks fields
     */
    private static List<IndexKey> indexKeys(AIcdDefsCodegenList list,
            Map<String, AIcdDefsCodegenType> types) {
        if (list.keyDefinitions().isEmpty()) return List.of();
        if (list.minOccurs() != 0 || list.maxOccurs() != -1) {
            throw new UnsupportedOperationException("Indexed LIST cardinality unsupported: " + list.name());
        }
        if (!(list.item() instanceof AIcdDefsCodegenType)) {
            throw new UnsupportedOperationException("Indexed LIST requires named TYPE elements: " + list.name());
        }
        List<IndexKey> keys = new ArrayList<>();
        for (var key : list.keyDefinitions()) {
            String selector = key.selector().startsWith("./")
                    ? key.selector().substring(2) : key.selector();
            if (!selector.equals(list.name())) {
                throw new UnsupportedOperationException("Indexed LIST selector must name its direct child: " + key.selector());
            }
            if (key.fields().isEmpty()) throw new IllegalArgumentException("Indexed LIST key requires fields: " + key.identifier());
            List<String> fields = new ArrayList<>();
            for (var xpath : key.fields()) {
                String relative = xpath.startsWith("./") ? xpath.substring(2) : xpath;
                String[] segments = relative.split("/", -1);
                List<String> names = new ArrayList<>();
                for (int i = 0; i < segments.length; i++) {
                    String segment = segments[i];
                    if (segment.startsWith("@")) {
                        /* XML attributes are not retained by this frontend.
                         * Treating them as same-named elements would be lossy. */
                        throw new UnsupportedOperationException("Attribute XPath needs an attribute-aware model: " + xpath);
                    }
                    if (!segment.matches("[A-Za-z_][A-Za-z0-9_-]*")) {
                        throw new UnsupportedOperationException("Namespace/predicate/axis in indexed LIST XPath needs a resolver: " + xpath);
                    }
                    names.add(segment);
                }
                String normalized = String.join(".", names);
                validateIndexPath(list.item(), normalized, types);
                fields.add(normalized);
            }
            if (new HashSet<>(fields).size() != fields.size()) {
                throw new IllegalArgumentException("Duplicate normalized index key fields: " + key.identifier());
            }
            keys.add(new IndexKey(key.identifier(), List.copyOf(fields), key.required()));
        }
        return List.copyOf(keys);
    }

    /**
     * Resolves named canonical references without traversing object recursion.
     *
     * @param node nested structure or TYPE reference
     * @param types known declared and synthetic types
     * @return effective structure of this one TYPE
     */
    private static AIiDefsCodegenStructure indexStructure(AIiDefsCodegenStructure node,
            Map<String, AIcdDefsCodegenType> types) {
        Set<String> seen = new HashSet<>();
        while (node instanceof AIcdDefsCodegenType type) {
            if (!type.targetIdentity().isEmpty()) {
                if (!seen.add(type.targetIdentity()) || !types.containsKey(type.targetIdentity())) {
                    throw new IllegalArgumentException("Unresolved indexed LIST target " + type.targetIdentity());
                }
                node = types.get(type.targetIdentity()).structure();
            } else {
                node = type.structure();
            }
        }
        return node;
    }

    /**
     * Ensures a translated index path refers to an actual scalar member chain.
     *
     * @param item indexed list element
     * @param path semantic dot-separated field path
     * @param types named TYPE registry for reference resolution
     * @throws IllegalArgumentException for missing or ambiguous members
     * @throws UnsupportedOperationException for complex or untyped key values
     */
    private static void validateIndexPath(AIiDefsCodegenStructure item, String path,
            Map<String, AIcdDefsCodegenType> types) {
        String[] components = path.split("\\.", -1);
        AIiDefsCodegenStructure node = item;
        for (int index = 0; index < components.length; index++) {
            node = indexStructure(node, types);
            if (!(node instanceof AIcdDefsCodegenElementList group) ||
                    group.composition() == AInDefsCodegenComposition.CHOICE) {
                throw new UnsupportedOperationException("Indexed LIST path crosses a non-object: " + path);
            }
            AIcdDefsCodegenElement match = null;
            for (var child : group.children()) {
                if (child instanceof AIcdDefsCodegenElement element &&
                        element.name().equals(components[index])) {
                    if (match != null) throw new IllegalArgumentException("Ambiguous indexed field: " + path);
                    match = element;
                }
            }
            if (match == null) throw new IllegalArgumentException("Unresolved indexed LIST field: " + path);
            node = match.structure();
            if (index == components.length - 1) {
                node = indexStructure(node, types);
                if (!(node instanceof AIcdDefsCodegenScalar) && !(node instanceof AIcdDefsCodegenEnum)) {
                    throw new UnsupportedOperationException("Index must resolve to a typed scalar: " + path);
                }
                if (node instanceof AIcdDefsCodegenScalar scalar &&
                        (scalar.scalarKind() == AInDefsCodegenScalarKind.ANY ||
                         scalar.scalarKind() == AInDefsCodegenScalarKind.NULL)) {
                    throw new UnsupportedOperationException("Unindexable scalar kind at " + path);
                }
            }
        }
    }

    /**
     * Finds source LIST metadata for a contract member without inventing a wrapper.
     *
     * @param type owning TYPE
     * @param member source member name
     * @return source LIST, or null when this field is not a direct LIST
     */
    private static AIcdDefsCodegenList directList(AIcdDefsCodegenType type, String member) {
        if (!(type.structure() instanceof AIcdDefsCodegenElementList group)) return null;
        for (var entry : group.children()) {
            if (entry instanceof AIcdDefsCodegenList list && list.name().equals(member)) return list;
        }
        return null;
    }

    /**
     * Canonicalizes a member/key pair into an unambiguous Java constant identifier.
     * This helper is intentionally identical in meaning to the Python emitter.
     *
     * @param field XML repeated child element name
     * @param key local XSD identity constraint name
     * @return member-scoped KEY_ constant identifier
     * @throws IllegalArgumentException when either name has no usable lexical words
     */
    private static String keyConstant(String field, String key) {
        return identifier("KEY_" + keyWords(field) + "_" + keyWords(key), true);
    }

    /**
     * Converts camel-cased and separator-delimited names to upper snake case.
     *
     * @param value XML local identifier
     * @return upper snake words without external source punctuation
     * @throws IllegalArgumentException if no words remain
     */
    private static String keyWords(String value) {
        String segments = value.replaceAll("([a-z0-9])([A-Z])", "$1_$2")
                .replaceAll("([A-Z])([A-Z][a-z])", "$1_$2");
        String[] words = segments.split("[^A-Za-z0-9]+", -1);
        List<String> result = new ArrayList<>();
        for (String word : words) if (!word.isEmpty()) result.add(word.toUpperCase(java.util.Locale.ROOT));
        if (result.isEmpty()) throw new IllegalArgumentException("Empty key constant name: " + value);
        return String.join("_", result);
    }

    /**
     * Plans every key constant before rendering in either target technology.
     *
     * @param type owning canonical object type
     * @param types resolved canonical type registry
     * @return source-ordered scoped symbol to original XSD key identity
     * @throws IllegalArgumentException on normalized naming collisions
     */
    private static Map<String, String> keyConstants(AIcdDefsCodegenType type,
            Map<String, AIcdDefsCodegenType> types) {
        Map<String, String> result = new LinkedHashMap<>();
        if (!(type.structure() instanceof AIcdDefsCodegenElementList group)) return result;
        for (var member : group.children()) {
            if (!(member instanceof AIcdDefsCodegenList list) || list.keyDefinitions().isEmpty()) continue;
            for (var key : indexKeys(list, types)) {
                String symbol = keyConstant(list.name(), key.name());
                if (result.putIfAbsent(symbol, key.name()) != null) {
                    throw new IllegalArgumentException("Conflicting XSD key constant in " + type.identity() + ": " + symbol);
                }
            }
        }
        return result;
    }

    /**
     * An output member with resolved methods and parameter types.
     *
     * @param sourceName original schema field name
     * @param getter configured getter method name
     * @param setter configured setter method name
     * @param type target-specific member type
     * @param minimum minimum occurrences
     * @param maximum maximum occurrences
     * @param description source documentation
     */
    private record Member(String sourceName, String getter, String setter, String type,
            int minimum, int maximum, String description) { }

    /**
     * Converts a supported source structure into the corresponding typed method contracts.
     *
     * @param type owning type
     * @param types all available resolved canonical symbols
     * @param javaTarget whether the requested syntax is Java rather than Python
     * @return source-ordered members with lossless type signatures
     */
    private List<Member> members(AIcdDefsCodegenType type, Map<String, AIcdDefsCodegenType> types, boolean javaTarget) {
        if (!(type.structure() instanceof AIcdDefsCodegenElementList group)) {
            throw new UnsupportedOperationException("Only object and top-level enum supported: " + type.identity());
        }
        if ((group.composition() != AInDefsCodegenComposition.SEQUENCE &&
                group.composition() != AInDefsCodegenComposition.ALL) ||
                group.minOccurs() != 1 || group.maxOccurs() != 1) {
            throw new UnsupportedOperationException("CHOICE/group-cardinality emission needs a dedicated backend: " + type.identity());
        }
        List<Member> result = new ArrayList<>();
        Set<String> methods = new HashSet<>();
        for (var entry : group.children()) {
            String field;
            AIiDefsCodegenStructure structure;
            int minimum;
            int maximum;
            String description;
            if (entry instanceof AIcdDefsCodegenElement element) {
                if (!element.keyDefinitions().isEmpty() || element.maxOccurs() != 1) {
                    throw new UnsupportedOperationException("Identity/repeated-field emission needs extended backend: "
                            + type.identity() + '/' + element.name());
                }
                field = element.name();
                structure = element.structure();
                minimum = element.minOccurs();
                maximum = element.maxOccurs();
                description = element.description();
            } else if (entry instanceof AIcdDefsCodegenList list) {
                /* A direct XSD repeated particle is LIST, not ELEMENT(LIST).
                 * Keep the collection's original bounds; typed() rejects all
                 * bounds which the current emitter cannot represent safely. */
                if (list.name().isBlank()) {
                    throw new IllegalArgumentException("Unnamed direct LIST inside " + type.identity());
                }
                field = list.name();
                structure = list;
                minimum = list.minOccurs();
                maximum = list.maxOccurs();
                description = "";
            } else if (entry instanceof AIcdDefsCodegenMap map &&
                    map.mapKind() == AInDefsCodegenMapKind.INTEGRATED_PROPERTY_MAP) {
                field = map.name();
                structure = map;
                minimum = 0;
                maximum = -1;
                description = "";
            } else {
                throw new UnsupportedOperationException("Unsupported object child " + entry.kind());
            }
            String getter = identifier(naming.render("standard_getter", field, Map.of()), javaTarget);
            String setter = identifier(naming.render("standard_setter", field, Map.of()), javaTarget);
            if (getter.equals(setter) || !methods.add(getter) || !methods.add(setter)) {
                throw new IllegalArgumentException("Duplicate getter/setter in " + type.identity() + '/' + field);
            }
            result.add(new Member(field, getter, setter, typed(structure, types, javaTarget,
                    type.identity() + '/' + field), minimum, maximum, description));
        }
        return List.copyOf(result);
    }

    /**
     * Resolves one nested field type without coercing unsupported semantics to {@code ANY}.
     *
     * @param node canonical source value
     * @param types valid identity references
     * @param javaTarget whether to use Java rather than Python syntax
     * @param context full semantic path for diagnostics
     * @return Java/Python type expression
     */
    private String typed(AIiDefsCodegenStructure node, Map<String, AIcdDefsCodegenType> types,
            boolean javaTarget, String context) {
        if (node instanceof AIcdDefsCodegenType reference) {
            String key = reference.targetIdentity().isEmpty() ? reference.identity() : reference.targetIdentity();
            if (!types.containsKey(key)) throw new IllegalArgumentException("Unknown referenced TYPE " + key + " at " + context);
            var names = outputNames.get(key);
            return javaTarget ? names.javaType() : names.pythonType();
        }
        if (node instanceof AIcdDefsCodegenScalar scalar) {
            if (!scalar.format().isEmpty()) {
                throw new UnsupportedOperationException("Unsupported scalar format " + scalar.format() + " at " + context);
            }
            return switch (scalar.scalarKind()) {
                case STRING -> javaTarget ? "String" : "str";
                case INTEGER -> javaTarget ? "Long" : "int";
                case NUMBER -> javaTarget ? "Double" : "float";
                case BOOLEAN -> javaTarget ? "Boolean" : "bool";
                default -> throw new UnsupportedOperationException("Unrepresentable scalar " + scalar.scalarKind() + " at " + context);
            };
        }
        if (node instanceof AIcdDefsCodegenList list) {
            indexKeys(list, types);
            if (list.minOccurs() != 0 || list.maxOccurs() != -1) {
                throw new UnsupportedOperationException("Bounded LIST requires a cardinality-aware emitter: " + context);
            }
            String value = typed(list.item(), types, javaTarget, context + "/items");
            if (!list.keyDefinitions().isEmpty()) {
                return javaTarget ? "eu.algites.lib.common.list.AIiMultiMappedList<" + value + ">"
                        : "AIiMultiMappedList[" + value + "]";
            }
            return javaTarget ? "java.util.List<" + value + ">" : "list[" + value + "]";
        }
        if (node instanceof AIcdDefsCodegenMap map) {
            String key = typed(map.keyType(), types, javaTarget, context + "/key");
            String value = typed(map.valueType(), types, javaTarget, context + "/value");
            return javaTarget ? "java.util.Map<" + key + ", " + value + ">" : "dict[" + key + ", " + value + "]";
        }
        throw new UnsupportedOperationException("Inline " + node.kind() + " requires named TYPE at " + context);
    }

    /**
     * Renders the native Java contract of one declaration.
     *
     * @param type linked canonical type
     * @param types complete identity registry
     * @return full Java source file
     */
    private String javaSource(AIcdDefsCodegenType type, Map<String, AIcdDefsCodegenType> types,
            Map<String, String> choiceParents) {
        String name = outputNames.get(type.identity()).javaType();
        StringBuilder result = new StringBuilder("package ").append(packageName).append(";\n\n")
                .append("/**\n * ").append(javaDoc(type.description().isEmpty() ? "Contract for " + type.name() : type.description()))
                .append("\n *\n * <p>Canonical identity: ").append(javaDoc(type.identity())).append("; version: ")
                .append(javaDoc(type.schemaVersion())).append(".</p>\n */\n");
        if (type.structure() instanceof AIcdDefsCodegenElementList choice &&
                choice.composition() == AInDefsCodegenComposition.CHOICE) {
            result.append("public sealed interface ").append(name).append(" permits ");
            String separator = "";
            for (var child : choice.children()) {
                var variant = (AIcdDefsCodegenType) ((AIcdDefsCodegenElement) child).structure();
                result.append(separator).append(outputNames.get(variant.identity()).javaType());
                separator = ", ";
            }
            return result.append(" {\n}\n").toString();
        }
        if (choiceParents.containsKey(type.identity())) {
            if (!type.inheritedFromTypes().isEmpty()) {
                throw new UnsupportedOperationException("CHOICE variant inheritance unsupported: " + type.identity());
            }
            String parent = outputNames.get(choiceParents.get(type.identity())).javaType();
            if (type.structure() instanceof AIcdDefsCodegenScalar) {
                String scalarType = typed(type.structure(), types, true, type.identity() + "/value");
                String getter = identifier(naming.render("standard_getter", "value", Map.of()), true);
                return result.append("public record ").append(name).append('(').append(scalarType)
                        .append(" value) implements ").append(parent).append(" {\n")
                        .append("    /** @return exact typed value of this exclusive alternative */\n")
                        .append("    public ").append(scalarType).append(' ').append(getter)
                        .append("() { return value; }\n}\n").toString();
            }
            var fields = members(type, types, true);
            Set<String> components = new HashSet<>();
            for (int i = 0; i < fields.size(); i++) components.add("field" + (i + 1));
            for (var field : fields) {
                if (components.contains(field.getter())) {
                    throw new IllegalArgumentException("CHOICE getter conflicts with record component: " + type.identity());
                }
            }
            int index = 0;
            for (var field : fields) {
                result.insert(result.length() - 4, " * @param field" + (++index) + " " +
                        javaDoc(field.description().isBlank() ? "Schema field " + field.sourceName() : field.description()) + "\n");
            }
            result.append("public record ").append(name).append('(');
            index = 0;
            for (var field : fields) {
                if (index++ > 0) result.append(", ");
                result.append(field.type()).append(" field").append(index);
            }
            result.append(") implements ").append(parent).append(" {\n");
            if (fields.stream().anyMatch(field -> field.minimum() > 0)) {
                result.append("    /** Validate required fields on construction. */\n")
                        .append("    public ").append(name).append(" {\n");
                index = 0;
                for (var field : fields) {
                    index++;
                    if (field.minimum() > 0) {
                        result.append("        java.util.Objects.requireNonNull(field")
                                .append(index).append(", ").append(javaString(field.sourceName()))
                                .append(");\n");
                    }
                }
                result.append("    }\n\n");
            }
            index = 0;
            for (var field : fields) {
                String doc = javaDoc(field.description().isBlank()
                        ? "Value of " + field.sourceName() : field.description());
                result.append("    /** @return ").append(doc)
                        .append(field.minimum() > 0 ? " (required)" : " (optional)")
                        .append(" */\n    public ").append(field.type()).append(' ')
                        .append(field.getter()).append("() { return field")
                        .append(++index).append("; }\n");
            }
            return result.append("}\n").toString();
        }
        if (type.structure() instanceof AIcdDefsCodegenEnum enumeration) {
            if (!type.inheritedFromTypes().isEmpty()) {
                throw new UnsupportedOperationException("Enum inheritance unsupported at " + type.identity());
            }
            String codeType = switch (enumeration.baseScalarType()) {
                case STRING -> "String";
                case INTEGER -> "java.math.BigInteger";
                case BOOLEAN -> "Boolean";
                default -> throw new UnsupportedOperationException(
                        "Exact decimal enum representation unsupported at " + type.identity());
            };
            result.append("public enum ").append(name).append(" {\n");
            Set<String> values = new HashSet<>();
            int index = 0;
            for (var value : enumeration.values()) {
                if (!values.add(value.wireValue())) {
                    throw new IllegalArgumentException("Duplicate enum wire code at " + type.identity());
                }
                if (index > 0) result.append(",\n");
                result.append("    /** Exact source code ").append(javaDoc(value.wireValue()))
                        .append(". */\n    VALUE_").append(++index).append('(')
                        .append(enumLiteral(value.wireValue(), enumeration.baseScalarType(), true)).append(')');
            }
            return result.append(";\n\n    private final ").append(codeType).append(" wireCode;\n\n")
                    .append("    /** @param aWireCode original typed schema code */\n")
                    .append("    ").append(name).append('(').append(codeType)
                    .append(" aWireCode) { wireCode = aWireCode; }\n\n")
                    .append("    /** @return exact typed schema wire code */\n")
                    .append("    public ").append(codeType).append(" code() { return wireCode; }\n}\n").toString();
        }
        var members = members(type, types, true);
        result.append("public interface ").append(name);
        if (!type.inheritedFromTypes().isEmpty()) {
            result.append(" extends ");
            var separator = "";
            for (var parent : type.inheritedFromTypes()) {
                result.append(separator).append(outputNames.get(parent).javaType());
                separator = ", ";
            }
        }
        result.append(" {\n");
        Map<String, String> constValues = keyConstants(type, types);
        String constContainer = constValues.isEmpty() ? "" :
                identifier(naming.render("const_container_interface", type.name(), Map.of()), true);
        if (!constValues.isEmpty()) {
            if (members.stream().anyMatch(member -> member.getter().equals(constContainer)
                    || member.setter().equals(constContainer))) {
                throw new IllegalArgumentException("CONST container collides with a method in " + type.identity());
            }
            result.append("    /** Canonical identifiers of the XML identity constraints for this TYPE. */\n")
                    .append("    interface ").append(constContainer).append(" {\n");
            for (var entry : constValues.entrySet()) {
                result.append("        /** XSD key or unique constraint ")
                        .append(javaDoc(entry.getValue())).append(". */\n")
                        .append("        String ").append(entry.getKey()).append(" = ")
                        .append(javaString(entry.getValue())).append(";\n");
            }
            result.append("    }\n\n");
        }
        for (int position = 0; position < members.size(); position++) {
            var field = members.get(position);
            var xmlWire = type.structure() instanceof AIcdDefsCodegenElementList group
                    ? group.children().stream().filter(child ->
                            child instanceof AIcdDefsCodegenElement element && element.name().equals(field.sourceName())
                            || child instanceof AIcdDefsCodegenList collection && collection.name().equals(field.sourceName()))
                            .findFirst().map(child -> child instanceof AIcdDefsCodegenElement element
                                    ? element.xmlWire() : ((AIcdDefsCodegenList) child).xmlWire()).orElse(null)
                    : null;
            if (xmlWire != null) {
                result.append("    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField(namespace = ")
                        .append(javaString(xmlWire.namespaceUri()))
                        .append(", namespaceLocalName = ").append(javaString(xmlWire.localName()))
                        .append(", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.")
                        .append(xmlWire.valueKind().name())
                        .append(", order = ").append(position)
                        .append(", minOccurs = ").append(field.minimum())
                        .append(", maxOccurs = ").append(field.maximum()).append(")\n");
            }
            var list = directList(type, field.sourceName());
            if (list != null) {
                for (var key : indexKeys(list, types)) {
                    result.append("    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlKeyDefinition(name = ")
                            .append(constContainer).append('.').append(keyConstant(list.name(), key.name()))
                            .append(", fields = {");
                    String separator = "";
                    for (var path : key.fields()) {
                        result.append(separator).append(javaString(path));
                        separator = ", ";
                    }
                    result.append("}, required = ").append(key.required()).append(")\n");
                }
            }
            String doc = javaDoc(field.description().isBlank()
                    ? "Value of schema field " + field.sourceName() : field.description());
            String required = field.minimum() == 0 ? "optional" : "required";
            result.append("    /** ").append(doc).append(" Field is ").append(required)
                    .append("; cardinality ").append(field.minimum()).append("..").append(field.maximum())
                    .append(".\n     * @return canonical field value\n     */\n    ")
                    .append(field.type()).append(' ').append(field.getter()).append("();\n\n")
                    .append("    /** Set ").append(doc).append("\n     * @param aValue schema value (")
                    .append(required).append(")\n     */\n    void ").append(field.setter()).append('(')
                    .append(field.type()).append(" aValue);\n\n");
        }
        return result.append("}\n").toString();
    }

    /**
     * Renders the native Python contract of one declaration with typed accessors.
     *
     * @param type linked canonical type
     * @param types complete identity registry
     * @return full Python source file
     */
    private String pythonSource(AIcdDefsCodegenType type, Map<String, AIcdDefsCodegenType> types,
            Map<String, String> choiceParents) {
        String name = outputNames.get(type.identity()).pythonType();
        StringBuilder result = new StringBuilder("from __future__ import annotations\n\n");
        if (type.structure() instanceof AIcdDefsCodegenElementList choice &&
                choice.composition() == AInDefsCodegenComposition.CHOICE) {
            return result.append("from abc import ABC\n\n\nclass ").append(name).append("(ABC):\n")
                    .append("    \"\"\"").append(pyDoc(type.description().isEmpty()
                            ? "Exclusive canonical choice" : type.description()))
                    .append("\"\"\"\n    pass\n").toString();
        }
        if (choiceParents.containsKey(type.identity())) {
            if (!type.inheritedFromTypes().isEmpty()) {
                throw new UnsupportedOperationException("CHOICE variant inheritance unsupported: " + type.identity());
            }
            var parent = outputNames.get(choiceParents.get(type.identity()));
            result.append("from dataclasses import dataclass\nfrom typing import final\n")
                    .append("from .").append(parent.pythonModule()).append(" import ")
                    .append(parent.pythonType()).append("\n\n\n@final\n@dataclass(frozen=True)\nclass ")
                    .append(name).append('(').append(parent.pythonType()).append("):\n")
                    .append("    \"\"\"").append(pyDoc(type.description().isEmpty()
                            ? "Exclusive canonical variant" : type.description()))
                    .append("\"\"\"\n");
            if (type.structure() instanceof AIcdDefsCodegenScalar) {
                String scalarType = typed(type.structure(), types, false, type.identity() + "/value");
                String getter = identifier(naming.render("standard_getter", "value", Map.of()), false);
                return result.append("    value: ").append(scalarType).append("\n\n")
                        .append("    def ").append(getter).append("(self) -> ").append(scalarType)
                        .append(":\n        \"\"\"Return the exact typed alternative value.\"\"\"\n")
                        .append("        return self.value\n").toString();
            }
            var fields = members(type, types, false);
            Set<String> components = new HashSet<>();
            for (int i = 0; i < fields.size(); i++) components.add("field" + (i + 1));
            for (var field : fields) {
                if (components.contains(field.getter())) {
                    throw new IllegalArgumentException("CHOICE getter conflicts with dataclass component: " + type.identity());
                }
            }
            if (fields.isEmpty()) result.append("    pass\n");
            int index = 0;
            for (var field : fields) {
                String annotation = field.type() + (field.minimum() == 0 ? " | None" : "");
                result.append("    field").append(++index).append(": ").append(annotation).append('\n');
            }
            if (fields.stream().anyMatch(field -> field.minimum() > 0)) {
                result.append("\n    def __post_init__(self) -> None:\n")
                        .append("        \"\"\"Validate required fields of this exact alternative.\"\"\"\n");
                index = 0;
                for (var field : fields) {
                    index++;
                    if (field.minimum() > 0) {
                        result.append("        if self.field").append(index).append(" is None:\n")
                                .append("            raise ValueError(").append(pyString(field.sourceName() + " is required"))
                                .append(")\n");
                    }
                }
            }
            index = 0;
            for (var field : fields) {
                String annotation = field.type() + (field.minimum() == 0 ? " | None" : "");
                String doc = pyDoc(field.description().isBlank()
                        ? "field " + field.sourceName() : field.description());
                result.append("\n    def ").append(field.getter()).append("(self) -> ").append(annotation)
                        .append(":\n        \"\"\"Return ").append(doc)
                        .append(".\"\"\"\n        return self.field")
                        .append(++index).append('\n');
            }
            return result.toString();
        }
        if (type.structure() instanceof AIcdDefsCodegenEnum enumeration) {
            if (!type.inheritedFromTypes().isEmpty()) {
                throw new UnsupportedOperationException("Enum inheritance unsupported at " + type.identity());
            }
            String base = switch (enumeration.baseScalarType()) {
                case STRING -> "str, Enum";
                case INTEGER -> "int, Enum";
                case BOOLEAN -> "Enum";
                default -> throw new UnsupportedOperationException(
                        "Exact decimal enum representation unsupported at " + type.identity());
            };
            String returnType = switch (enumeration.baseScalarType()) {
                case STRING -> "str";
                case INTEGER -> "int";
                case BOOLEAN -> "bool";
                default -> throw new UnsupportedOperationException("Unrepresentable enum");
            };
            result.append("from enum import Enum\n\n\nclass ").append(name).append('(').append(base).append("):\n")
                    .append("    \"\"\"").append(pyDoc(type.description().isEmpty() ? "Schema enum" : type.description()))
                    .append("\"\"\"\n\n");
            Set<String> values = new HashSet<>();
            int index = 0;
            for (var value : enumeration.values()) {
                if (!values.add(value.wireValue())) throw new IllegalArgumentException("Duplicate enum wire code at " + type.identity());
                result.append("    VALUE_").append(++index).append(" = ")
                        .append(enumLiteral(value.wireValue(), enumeration.baseScalarType(), false)).append('\n');
            }
            return result.append("\n    def code(self) -> ").append(returnType).append(":\n")
                    .append("        \"\"\"Return the exact typed wire code.\"\"\"\n")
                    .append("        return self.value\n").toString();
        }
        var fields = members(type, types, false);
        result.append("from abc import ABC, abstractmethod\nfrom typing import TYPE_CHECKING\n");
        boolean hasIndexedList = fields.stream().anyMatch(field -> {
            var list = directList(type, field.sourceName());
            return list != null && !list.keyDefinitions().isEmpty();
        });
        if (hasIndexedList) {
            result.append("from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList\n");
        }
        boolean hasXmlWires = type.structure() instanceof AIcdDefsCodegenElementList group
                && group.children().stream().anyMatch(child ->
                        child instanceof AIcdDefsCodegenElement element && element.xmlWire() != null
                        || child instanceof AIcdDefsCodegenList list && list.xmlWire() != null);
        if (hasXmlWires) {
            result.append("from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field "
                    + "import AIaXmlDataObjectField\n")
                    .append("from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind "
                    + "import AInXmlValueKind\n");
        }
        for (String parent : type.inheritedFromTypes()) {
            var names = outputNames.get(parent);
            result.append("from .").append(names.pythonModule()).append(" import ").append(names.pythonType()).append('\n');
        }
        var imported = new HashSet<>(type.inheritedFromTypes());
        var typingImports = new StringBuilder();
        for (var field : fields) {
            for (var entry : outputNames.entrySet()) {
                String identity = entry.getKey();
                String symbol = entry.getValue().pythonType();
                if (!identity.equals(type.identity()) && !imported.contains(identity)
                        && Pattern.compile("\\b" + Pattern.quote(symbol) + "\\b").matcher(field.type()).find()) {
                    typingImports.append("    from .").append(entry.getValue().pythonModule()).append(" import ")
                            .append(symbol).append('\n');
                    imported.add(identity);
                }
            }
        }
        if (!typingImports.isEmpty()) result.append("\nif TYPE_CHECKING:\n").append(typingImports);
        result.append("\n\nclass ").append(name).append('(');
        String separator = "";
        for (var parent : type.inheritedFromTypes()) {
            result.append(separator).append(outputNames.get(parent).pythonType());
            separator = ", ";
        }
        if (separator.isEmpty()) result.append("ABC");
        result.append("):\n    \"\"\"").append(pyDoc(type.description().isEmpty() ? "Contract for " + type.name() : type.description()))
                .append("\"\"\"\n\n");
        if (hasXmlWires && type.structure() instanceof AIcdDefsCodegenElementList group) {
            result.append("    __xml_data_object_fields__ = {\n");
            for (int position = 0; position < group.children().size(); position++) {
                var child = group.children().get(position);
                var wire = child instanceof AIcdDefsCodegenElement element ? element.xmlWire()
                        : child instanceof AIcdDefsCodegenList collection ? collection.xmlWire() : null;
                if (wire == null) continue;
                var fieldName = child instanceof AIcdDefsCodegenElement element ? element.name()
                        : ((AIcdDefsCodegenList) child).name();
                int minimum = child instanceof AIcdDefsCodegenElement element ? element.minOccurs()
                        : ((AIcdDefsCodegenList) child).minOccurs();
                int maximum = child instanceof AIcdDefsCodegenElement element ? element.maxOccurs()
                        : ((AIcdDefsCodegenList) child).maxOccurs();
                result.append("        ").append(pyString(fieldName))
                        .append(": AIaXmlDataObjectField(namespace=").append(pyString(wire.namespaceUri()))
                        .append(", namespace_local_name=").append(pyString(wire.localName()))
                        .append(", value_kind=AInXmlValueKind.").append(wire.valueKind().name())
                        .append(", order=").append(position).append(", min_occurs=").append(minimum)
                        .append(", max_occurs=").append(maximum).append("),\n");
            }
            result.append("    }\n\n");
            result.append("    __xml_repeated_fields__ = (");
            for (var child : group.children()) {
                if (child instanceof AIcdDefsCodegenList list) result.append(pyString(list.name())).append(", ");
            }
            result.append(")\n\n");
        }
        Map<String, String> pythonConstValues = keyConstants(type, types);
        String pythonConstContainer = pythonConstValues.isEmpty() ? "" :
                identifier(naming.render("const_container_interface", type.name(), Map.of()), false);
        if (!pythonConstValues.isEmpty()) {
            if (fields.stream().anyMatch(member -> member.getter().equals(pythonConstContainer)
                    || member.setter().equals(pythonConstContainer))) {
                throw new IllegalArgumentException("CONST container collides with a method in " + type.identity());
            }
            result.append("    class ").append(pythonConstContainer).append(":\n")
                    .append("        \"\"\"Stable XML identity constraint identifiers for this type.\"\"\"\n");
            for (var entry : pythonConstValues.entrySet()) {
                result.append("        ").append(entry.getKey()).append(" = ")
                        .append(pyString(entry.getValue())).append('\n');
            }
            result.append('\n');
        }
        if (hasIndexedList) {
            result.append("    __xml_key_definitions__ = {\n");
            for (var field : fields) {
                var list = directList(type, field.sourceName());
                if (list == null || list.keyDefinitions().isEmpty()) continue;
                result.append("        ").append(pyString(field.sourceName())).append(": (");
                for (var key : indexKeys(list, types)) {
                    result.append('(').append(pythonConstContainer).append('.')
                            .append(keyConstant(list.name(), key.name())).append(", (");
                    for (var path : key.fields()) result.append(pyString(path)).append(", ");
                    result.append("), ").append(key.required() ? "True" : "False").append("), ");
                }
                result.append("),\n");
            }
            result.append("    }\n\n");
        }
        if (fields.isEmpty()) result.append("    pass\n");
        for (var field : fields) {
            String required = field.minimum() == 0 ? "optional" : "required";
            String doc = pyDoc(field.description().isBlank() ? "Canonical field " + field.sourceName() : field.description());
            result.append("    @abstractmethod\n    def ").append(field.getter()).append("(self) -> ")
                    .append(field.type()).append(":\n        \"\"\"Return ")
                    .append(doc).append(" (").append(required).append(", cardinality ")
                    .append(field.minimum()).append("..").append(field.maximum())
                    .append(").\"\"\"\n        raise NotImplementedError\n\n")
                    .append("    @abstractmethod\n    def ").append(field.setter()).append("(self, value: ")
                    .append(field.type()).append(") -> None:\n        \"\"\"Set ")
                    .append(doc).append(" (").append(required).append(").\"\"\"\n")
                    .append("        raise NotImplementedError\n\n");
        }
        return result.toString();
    }

    /**
     * Validates a resolved lexical identifier against the target language keywords.
     *
     * @param value resolved naming-catalog token
     * @param javaTarget whether the output syntax is Java
     * @return unchanged validated identifier
     */
    private static String identifier(String value, boolean javaTarget) {
        Objects.requireNonNull(value, "identifier");
        if (!(javaTarget ? JAVA_ID : PYTHON_ID).matcher(value).matches() ||
                (javaTarget ? JAVA_RESERVED : PYTHON_RESERVED).contains(value)) {
            throw new IllegalArgumentException("Invalid " + (javaTarget ? "Java" : "Python")
                    + " naming-catalog identifier " + value);
        }
        return value;
    }

    /**
     * Escapes a source string for safe HTML/Javadoc inclusion.
     *
     * @param value arbitrary source text
     * @return literal-text-safe Javadoc payload
     */
    private static String javaDoc(String value) {
        var escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("*/", "* /").replace('\n', ' ').replace('\r', ' ');
        StringBuilder result = new StringBuilder();
        for (int position = 0; position < escaped.length(); position++) {
            char current = escaped.charAt(position);
            if (current < 32 && current != '\t') {
                result.append(String.format("[U+%04X]", (int) current));
            } else {
                result.append(current);
            }
        }
        return result.toString();
    }

    /**
     * Escapes a source string for a Python triple-quoted documentation literal.
     *
     * @param value arbitrary source documentation
     * @return source-safe docstring payload
     */
    private static String pyDoc(String value) {
        return value.replace("\\", "\\\\").replace("\"\"\"", "\\\"\\\"\\\"")
                .replace('\n', ' ').replace('\r', ' ');
    }

    /**
     * Quotes any lexical code as a Java string literal, retaining control characters.
     *
     * @param value original enum code
     * @return escaped Java string literal
     */
    private static String javaString(String value) {
        StringBuilder result = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"' -> result.append("\\\"");
                case '\\' -> result.append("\\\\");
                case '\n' -> result.append("\\n");
                case '\r' -> result.append("\\r");
                case '\t' -> result.append("\\t");
                default -> {
                    if (c < 32) result.append(String.format("\\%03o", (int) c));
                    else result.append(c);
                }
            }
        }
        return result.append('"').toString();
    }

    /**
     * Converts a validated scalar wire code into an exact Java/Python literal.
     * Arbitrary-precision integer values are supported without rounding; a
     * decimal {@code NUMBER} requires a later lossless decimal parsing layer.
     *
     * @param wire the exact source code from the canonical schema
     * @param kind the canonical scalar kind of the enum
     * @param javaTarget whether to render Java instead of Python
     * @return a valid exact-value language literal
     * @throws IllegalArgumentException if lexical syntax is invalid
     * @throws UnsupportedOperationException if the scalar kind is unsupported
     */
    private static String enumLiteral(String wire, AInDefsCodegenScalarKind kind, boolean javaTarget) {
        return switch (kind) {
            case STRING -> javaTarget ? javaString(wire) : pyString(wire);
            case INTEGER -> {
                if (!wire.matches("0|-?[1-9][0-9]*")) {
                    throw new IllegalArgumentException("Invalid integer enum code " + wire);
                }
                yield javaTarget ? "new java.math.BigInteger(" + javaString(wire) + ")" : wire;
            }
            case BOOLEAN -> {
                if (!wire.equals("true") && !wire.equals("false")) {
                    throw new IllegalArgumentException("Invalid boolean enum code " + wire);
                }
                yield javaTarget ? wire : wire.equals("true") ? "True" : "False";
            }
            default -> throw new UnsupportedOperationException("Exact enum code unsupported for " + kind);
        };
    }

    /**
     * Quotes the original lexical enum code in Python syntax.
     *
     * @param value original wire code
     * @return escaped Python string literal
     */
    private static String pyString(String value) {
        return javaString(value);
    }
}
