package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalEnum;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalMap;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalScalar;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.impl.standard.model.AIiDefsCanonicalStructure;
import eu.algites.tool.codegen.defs.model.AIngComposition_1;
import eu.algites.tool.codegen.defs.model.AIngMapKind_1;
import eu.algites.tool.codegen.defs.model.AIngResolutionState_1;
import eu.algites.tool.codegen.defs.model.AIngScalarKind_1;
import java.util.Locale;
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
    /** Shared schema-neutral type names, generated independently of source families. */
    private final Map<String, Names> commonOutputNames;
    /** XML declaration QName and symbol-space kind as recorded by the source frontend. */
    private record XmlDeclaration(String kind, String namespace, String localName) { }

    /**
     * Obtain a global ELEMENT's wire QName from its source pointer rather than
     * treating it as a same-named nominal TYPE. Java and Python emitters must
     * agree even when a global element and a complexType share their QName.
     */
    private static XmlDeclaration xmlDeclaration(AIcDefsCanonicalType node) {
        var sources = node.sourceBindings().getOrDefault(AIngSourceInputKind_1.XMLDEFS, List.of());
        if (sources.isEmpty()) return null;
        var elementNames = new java.util.LinkedHashSet<String>();
        for (var binding : sources) {
            if ("xs:element".equals(binding.representationKind())) {
                String pointer = binding.sourcePointer();
                elementNames.add(pointer.substring(pointer.lastIndexOf('/') + 1));
            }
        }
        String kind = elementNames.isEmpty() ? "TYPE" : "ELEMENT";
        if (elementNames.size() > 1) {
            throw new IllegalArgumentException("Ambiguous global XML element identity: "
                    + node.identity());
        }
        String identity = node.identity();
        String namespace = "";
        String localName = identity;
        if (identity.startsWith("{") && identity.contains("}")) {
            int end = identity.indexOf('}');
            namespace = identity.substring(1, end);
            localName = identity.substring(end + 1);
        }
        if (!elementNames.isEmpty()) localName = elementNames.iterator().next();
        return new XmlDeclaration(kind, namespace, localName);
    }

    /** True when rendering the schema-neutral base contract. */
    private final boolean commonProjection;
    /** Source dialects contributing metadata to the single read-only contract. */
    private final Map<AIngSourceInputKind_1, AIcDefsCanonicalType> representations;
    /** Validated target package shared by both output technologies. */
    private final String packageName;
    /** Verified externally compiled parents; never emitted as local files. */
    private final Map<String, Names> externalParents;
    /** Published schema document URLs keyed by source resource, not by logical TYPE ID. */
    private final Map<String, String> publishedSchemaUrls;
    /** Referenced TYPE members that are capable of holding scoped XML indexes. */
    private Set<String> scopedIndexedMembers = Set.of();

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
     * One schema's canonical common-contract projection for batch coalescing.
     * Retains typed graph data: no generated source is parsed to reconstruct
     * schema semantics. Both output technologies have independent projections.
     *
     * @param type local canonical declaration
     * @param declarations source-local resolved TYPE registry
     * @param renderer common-only source emitter configured by the same profile
     * @param language target Java or Python
     * @param original originally emitted common interface
     */
    public record CommonProjection(AIcDefsCanonicalType type,
            Map<String, AIcDefsCanonicalType> declarations,
            AIcDefsCodegenCanonicalSourceEmitter renderer, String language, Output original) { }

    /**
     * Create the common-only renderer from the selected naming catalog.
     * @param naming Common/Defs naming conventions
     * @param names names of schema-neutral interfaces
     * @param packageName destination package
     * @param external existing declared read-only parents
     * @return renderer with representation metadata suppressed
     */
    public static AIcDefsCodegenCanonicalSourceEmitter commonOnly(
            AIcCodegenNamingProfileResolver.Profile naming, Map<String, Names> names,
            String packageName, Map<String, Names> external,
            Map<String, String> publishedSchemaUrls) {
        return new AIcDefsCodegenCanonicalSourceEmitter(naming, names, packageName,
                external, publishedSchemaUrls, Map.of(), true);
    }

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
        this(naming, outputNames, packageName, Map.of(), Map.of());
    }

    /**
     * Bind existing external parent symbols without adding source declarations.
     * @param naming explicit Common+Defs naming catalog
     * @param outputNames names of local canonical declarations
     * @param packageName output package for local generated sources
     * @param externalParents verified external parent names with fully-qualified Java
     *        and Python modules; these are never added to generated source outputs
     * @throws NullPointerException on missing arguments
     * @throws IllegalArgumentException on malformed output package
     */
    public AIcDefsCodegenCanonicalSourceEmitter(AIcCodegenNamingProfileResolver.Profile naming,
            Map<String, Names> outputNames, String packageName, Map<String, Names> externalParents) {
        this(naming, outputNames, packageName, externalParents, Map.of());
    }

    /**
     * Supply published format document URLs independently from logical type IDs.
     *
     * @param naming resolved naming profile
     * @param outputNames declared source output symbols
     * @param packageName output package
     * @param externalParents verified external parent interfaces
     * @param publishedSchemaUrls source resource to published document URL
     */
    public AIcDefsCodegenCanonicalSourceEmitter(AIcCodegenNamingProfileResolver.Profile naming,
            Map<String, Names> outputNames, String packageName, Map<String, Names> externalParents,
            Map<String, String> publishedSchemaUrls) {
        this(naming, outputNames, packageName, externalParents, publishedSchemaUrls, Map.of(), false);
    }

    /**
     * Configure mandatory common contracts alongside the source-family interfaces.
     * @param naming resolved Common/Defs naming profile
     * @param outputNames canonical catalog names
     * @param packageName destination package
     * @param externalParents resolved compiled external parents
     * @param publishedSchemaUrls published format document IDs
     * @param commonOutputNames schema-neutral catalog names
     */
    public AIcDefsCodegenCanonicalSourceEmitter(AIcCodegenNamingProfileResolver.Profile naming,
            Map<String, Names> outputNames, String packageName, Map<String, Names> externalParents,
            Map<String, String> publishedSchemaUrls, Map<String, Names> commonOutputNames) {
        this(naming, outputNames, packageName, externalParents, publishedSchemaUrls, commonOutputNames, false);
    }

    /** Rendering constructor for the two independent contract projections. */
    private AIcDefsCodegenCanonicalSourceEmitter(AIcCodegenNamingProfileResolver.Profile naming,
            Map<String, Names> outputNames, String packageName, Map<String, Names> externalParents,
            Map<String, String> publishedSchemaUrls, Map<String, Names> commonOutputNames,
            boolean commonProjection) {
        this.naming = Objects.requireNonNull(naming, "naming");
        this.outputNames = Map.copyOf(Objects.requireNonNull(outputNames, "outputNames"));
        if (!Objects.requireNonNull(commonOutputNames, "commonOutputNames").isEmpty()) {
            throw new IllegalArgumentException("Defs Codegen emits only unified read-only contracts; "
                    + "separate per-format interfaces are not supported");
        }
        this.commonOutputNames = Map.of();
        this.commonProjection = commonProjection;
        this.representations = Map.of();
        this.externalParents = Map.copyOf(Objects.requireNonNull(externalParents, "externalParents"));
        this.publishedSchemaUrls = Map.copyOf(Objects.requireNonNull(publishedSchemaUrls, "publishedSchemaUrls"));
        this.packageName = Objects.requireNonNull(packageName, "packageName");
        for (var part : packageName.split("\\.", -1)) identifier(part, true);
    }

    /**
     * Rebind a stateless shared renderer to the source schema representations of
     * exactly one canonical contract. A new renderer is used for each merge so
     * concurrent processing cannot contaminate another type's format metadata.
     *
     * @param sources source family to canonical declaration, all type-checked
     * @return independent renderer containing only the requested representation metadata
     */
    private AIcDefsCodegenCanonicalSourceEmitter withRepresentations(
            Map<AIngSourceInputKind_1, AIcDefsCanonicalType> sources,
            Map<String, String> sourceUrls) {
        return new AIcDefsCodegenCanonicalSourceEmitter(this, sources, sourceUrls);
    }

    /** Copy immutable naming state and install per-contract representation metadata. */
    private AIcDefsCodegenCanonicalSourceEmitter(AIcDefsCodegenCanonicalSourceEmitter source,
            Map<AIngSourceInputKind_1, AIcDefsCanonicalType> sources,
            Map<String, String> sourceUrls) {
        this.naming = source.naming;
        this.outputNames = source.outputNames;
        this.commonOutputNames = source.commonOutputNames;
        this.commonProjection = source.commonProjection;
        this.packageName = source.packageName;
        this.externalParents = source.externalParents;
        this.publishedSchemaUrls = Map.copyOf(sourceUrls);
        this.scopedIndexedMembers = source.scopedIndexedMembers;
        this.representations = Map.copyOf(sources);
    }

    /**
     * Return the original declaration for a source family, when present.
     * @param kind desired input technology
     * @param fallback canonical declaration being rendered
     * @return original source-family TYPE, or fallback when rendering legacy output
     */
    private AIcDefsCanonicalType representation(AIngSourceInputKind_1 kind, AIcDefsCanonicalType fallback) {
        return representations.getOrDefault(kind, fallback);
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
    /**
     * Resolve only document-root provenance to a published representation URL.
     * $defs and synthetic definitions share the source document but are not
     * independent URI roots and must not shadow the actual root contract.
     *
     * @param type local declared TYPE
     * @param kind representation family
     * @return published schema URL or empty string
     */
    private String publishedSchemaUrl(AIcDefsCanonicalType type, AIngSourceInputKind_1 kind) {
        Set<String> urls = new HashSet<>();
        for (var source : type.sourceBindings().getOrDefault(kind, List.of())) {
            if (!"#".equals(source.sourcePointer())) continue;
            var url = publishedSchemaUrls.get(source.sourceResource());
            if (url != null && !url.isBlank()) urls.add(url);
        }
        if (urls.size() > 1)
            throw new IllegalArgumentException("Conflicting published schema URLs for " + type.identity());
        return urls.isEmpty() ? "" : urls.iterator().next();
    }

    public List<Output> render(List<AIcDefsCanonicalType> roots) {
        Objects.requireNonNull(roots, "roots");
        Map<String, AIcDefsCanonicalType> types = new LinkedHashMap<>();
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
            if (!paths.add("java:" + names.javaType().toLowerCase(Locale.ROOT)) ||
                    !paths.add("python:" + names.pythonModule().toLowerCase(Locale.ROOT))) {
                throw new IllegalArgumentException("Generated output path collision at " + type.identity());
            }
            for (String parent : type.inheritedFromTypes()) {
                if (!types.containsKey(parent) && !externalParents.containsKey(parent))
                    throw new IllegalArgumentException("Unresolved parent " + parent);
            }
        }
        Set<String> indexed = new HashSet<>();
        for (var definition : types.values()) {
            if (!(definition.structure() instanceof AIcDefsCanonicalElementList group)) continue;
            for (var child : group.children()) {
                if (!(child instanceof AIcDefsCanonicalElement element) || element.keyDefinitions().isEmpty()) continue;
                if (!(element.structure() instanceof AIcDefsCanonicalType reference))
                    throw new IllegalArgumentException("Contextual xs:key requires a named object TYPE: " + element.name());
                String identity = reference.targetIdentity().isEmpty() ? reference.identity() : reference.targetIdentity();
                for (var key : scopedIndexKeys(element, types)) indexed.add(identity + "#" + key.selector());
            }
        }
        scopedIndexedMembers = Set.copyOf(indexed);
        Map<String, String> choiceParents = choiceParents(types);
        List<Output> result = new ArrayList<>();
        String folder = packageName.replace('.', '/') + '/';
        for (var type : types.values()) {
            // A named list schema is a referenceable collection shape, not
            // a generated DataObject that inherits AIiMultiMappedList.
            if (type.structure() instanceof AIcDefsCanonicalList) {
                if (!type.inheritedFromTypes().isEmpty())
                    throw new IllegalArgumentException("List alias cannot have DataObject parents: " + type.identity());
                continue;
            }
            var names = outputNames.get(type.identity());
            result.add(new Output("java", folder + names.javaType() + ".java", javaSource(type, types, choiceParents), type.identity()));
            result.add(new Output("python", folder + names.pythonModule() + ".py", pythonSource(type, types, choiceParents), type.identity()));
        }
        return List.copyOf(result);
    }

    /**
     * Merge one shared output from schema representations in a single batch.
     * A common getter must be present in all representations with an identical
     * catalog-derived name and compatible return type. Incompatible or missing
     * semantic fields are diagnosed rather than silently dropped or typed as Object.
     * Matching member restrictions are widened without imposing one format's facets.
     *
     * @param path unique output path shared by all representations
     * @param contexts canonical graphs producing that shared path
     * @return single source text for the shared DataObject interface
     * @throws IllegalArgumentException for incompatible group shapes
     */
    public static String mergeCommon(String path, List<CommonProjection> contexts) {
        // Select a stable representative by source content, not manifest order.
        // The common-member intersection itself is independent of this order.
        contexts = contexts.stream().sorted(java.util.Comparator
                .comparing((CommonProjection context) ->
                        !context.type().sourceBindings().containsKey(AIngSourceInputKind_1.XMLDEFS))
                .thenComparing(context -> context.original().sourceText())).toList();
        if (contexts.isEmpty()) throw new IllegalArgumentException("Empty common projections: " + path);
        Map<AIngSourceInputKind_1, AIcDefsCanonicalType> sources = new LinkedHashMap<>();
        for (var context : contexts) {
            for (var kind : context.type().sourceBindings().keySet()) {
                var existing = sources.putIfAbsent(kind, context.type());
                if (existing != null && !existing.equals(context.type()))
                    throw new IllegalArgumentException(path + ": multiple distinct " + kind
                            + " representations of one contract");
            }
        }
        // A shared TYPE can represent several schema documents. Preserve each
        // format's own published URL rather than using just the first renderer.
        Map<String, String> publishedUrls = new LinkedHashMap<>();
        for (var context : contexts) {
            for (var entry : context.renderer().publishedSchemaUrls.entrySet()) {
                var previous = publishedUrls.putIfAbsent(entry.getKey(), entry.getValue());
                if (previous != null && !previous.equals(entry.getValue()))
                    throw new IllegalArgumentException(path + ": conflicting published schema URL for "
                            + entry.getKey());
            }
        }
        if (contexts.size() == 1) {
            var only = contexts.get(0);
            var renderer = only.renderer().withRepresentations(sources, publishedUrls);
            return only.language().equals("java")
                    ? renderer.javaSource(only.type(), only.declarations(), choiceParents(only.declarations()))
                    : renderer.pythonSource(only.type(), only.declarations(), choiceParents(only.declarations()));
        }
        boolean choices = contexts.stream().allMatch(ctx ->
                ctx.type().structure() instanceof AIcDefsCanonicalElementList group
                && group.composition() == AIngComposition_1.CHOICE);
        if (choices) {
            var first = contexts.get(0);
            var renderer = first.renderer().withRepresentations(sources, publishedUrls);
            return first.language().equals("java")
                    ? renderer.javaSource(first.type(), first.declarations(), choiceParents(first.declarations()))
                    : renderer.pythonSource(first.type(), first.declarations(), choiceParents(first.declarations()));
        }
        for (var context : contexts) {
            if (!(context.type().structure() instanceof AIcDefsCanonicalElementList group)
                    || (group.composition() != AIngComposition_1.ALL
                        && group.composition() != AIngComposition_1.SEQUENCE)) {
                throw new IllegalArgumentException(path + ": cannot merge non-object shared TYPE "
                        + context.type().identity());
            }
        }
        var maps = new ArrayList<Map<String, Member>>();
        for (var context : contexts) {
            Map<String, Member> byName = new LinkedHashMap<>();
            for (var member : context.renderer().members(context.type(),
                    context.declarations(), context.language().equals("java"))) {
                byName.put(member.sourceName(), member);
            }
            maps.add(byName);
        }
        // Neither silent member intersection nor Object/Any fallbacks are
        // permissible in the shared semantic DataObject. Each wire-specific
        // getter must originate from a compatible neutral typed field.
        Set<String> shared = new HashSet<>();
        for (var members : maps) shared.addAll(members.keySet());
        for (String name : shared.stream().sorted().toList()) {
            var absent = new ArrayList<String>();
            for (int index = 0; index < maps.size(); index++) {
                if (!maps.get(index).containsKey(name))
                    absent.add(contexts.get(index).type().origin().toString());
            }
            if (!absent.isEmpty())
                throw new IllegalArgumentException(path + ": semantic field " + name
                        + " is absent in " + absent + "; harmonize the XML/JSON/YAML schemas");
            Member original = maps.get(0).get(name);
            for (int index = 1; index < maps.size(); index++) {
                Member alternative = maps.get(index).get(name);
                if (!original.getter().equals(alternative.getter())
                        || !original.type().equals(alternative.type())) {
                    throw new IllegalArgumentException(path + ": incompatible types for semantic field "
                            + name + " (" + original.getter() + ": " + original.type()
                            + " versus " + alternative.getter() + ": " + alternative.type()
                            + "); harmonize the XML/JSON/YAML structures; never discard a getter or use Object/Any");
                }
            }
        }
        var first = contexts.get(0);
        var firstGroup = (AIcDefsCanonicalElementList) first.type().structure();
        List<AIiDefsCanonicalStructure> commonChildren = new ArrayList<>();
        for (var member : firstGroup.children()) {
            String name = member instanceof AIcDefsCanonicalElement element ? element.name()
                    : member instanceof AIcDefsCanonicalList list ? list.name()
                    : member instanceof AIcDefsCanonicalMap map ? map.name() : "";
            if (!shared.contains(name)) continue;
            List<AIiDefsCanonicalStructure> counterparts = new ArrayList<>();
            for (var context : contexts) {
                var group = (AIcDefsCanonicalElementList) context.type().structure();
                var matching = group.children().stream().filter(child ->
                        child instanceof AIcDefsCanonicalElement e && e.name().equals(name)
                        || child instanceof AIcDefsCanonicalList l && l.name().equals(name)
                        || child instanceof AIcDefsCanonicalMap m && m.name().equals(name))
                        .findFirst().orElseThrow();
                counterparts.add(matching);
            }
            commonChildren.add(commonMember(member, counterparts));
        }
        var mergedGroup = new AIcDefsCanonicalElementList(firstGroup.composition(), commonChildren,
                firstGroup.minItemCount(), firstGroup.maxItemCount(), -1, -1);
        var type = first.type();
        Map<AIngSourceInputKind_1, List<AIcDefsCanonicalSourceBinding>> mergedBindings = new LinkedHashMap<>();
        for (var source : sources.values()) source.sourceBindings().forEach((kind, bindings) -> {
            if (mergedBindings.putIfAbsent(kind, bindings) != null)
                throw new IllegalArgumentException(path + ": duplicate representation " + kind);
        });
        var mergedType = new AIcDefsCanonicalType(type.identity(), type.name(), type.origin(),
                type.pathSegments(), type.inheritedFromTypes(), mergedGroup,
                type.resolutionState(), mergedBindings, type.targetIdentity(),
                type.schemaVersion(), type.description());
        Map<String, AIcDefsCanonicalType> registry = new LinkedHashMap<>(first.declarations());
        registry.put(mergedType.identity(), mergedType);
        var renderer = first.renderer().withRepresentations(sources, publishedUrls);
        String text = first.language().equals("java")
                ? renderer.javaSource(mergedType, registry, choiceParents(registry))
                : renderer.pythonSource(mergedType, registry, choiceParents(registry));
        return text;
    }

    /**
     * Compute the least restrictive source-neutral scalar constraints.
     * @param candidates equivalent-typed scalar representations
     * @return constraints shared safely across every representation
     */
    private static AIiDefsCanonicalStructure commonScalar(List<AIiDefsCanonicalStructure> candidates) {
        if (candidates.stream().anyMatch(value -> !(value instanceof AIcDefsCanonicalScalar)))
            return candidates.get(0);
        var scalars = candidates.stream().map(value -> (AIcDefsCanonicalScalar) value).toList();
        var source = scalars.get(0);
        if (scalars.stream().anyMatch(value -> value.scalarKind() != source.scalarKind()))
            throw new IllegalArgumentException("Different scalar kinds in a shared getter");
        int min = scalars.stream().anyMatch(value -> value.minLength() == -1)
                ? -1 : scalars.stream().mapToInt(AIcDefsCanonicalScalar::minLength).min().orElse(-1);
        int max = scalars.stream().anyMatch(value -> value.maxLength() == -1)
                ? -1 : scalars.stream().mapToInt(AIcDefsCanonicalScalar::maxLength).max().orElse(-1);
        String pattern = scalars.stream().allMatch(value -> value.pattern().equals(source.pattern()))
                ? source.pattern() : "";
        String format = scalars.stream().allMatch(value -> value.format().equals(source.format()))
                ? source.format() : "";
        String minimum = scalars.stream().anyMatch(value -> value.minimum().isBlank()) ? ""
                : scalars.stream().map(AIcDefsCanonicalScalar::minimum)
                    .min((a, b) -> new java.math.BigDecimal(a).compareTo(new java.math.BigDecimal(b))).orElse("");
        String maximum = scalars.stream().anyMatch(value -> value.maximum().isBlank()) ? ""
                : scalars.stream().map(AIcDefsCanonicalScalar::maximum)
                    .max((a, b) -> new java.math.BigDecimal(a).compareTo(new java.math.BigDecimal(b))).orElse("");
        boolean exclusiveMinimum = !minimum.isBlank() && scalars.stream().allMatch(value ->
                value.minimum().equals(minimum) && value.exclusiveMinimum());
        boolean exclusiveMaximum = !maximum.isBlank() && scalars.stream().allMatch(value ->
                value.maximum().equals(maximum) && value.exclusiveMaximum());
        String multiple = scalars.stream().allMatch(value -> value.multipleOf().equals(source.multipleOf()))
                ? source.multipleOf() : "";
        return new AIcDefsCanonicalScalar(source.scalarKind(), format, min, max, pattern,
                minimum, maximum, exclusiveMinimum, exclusiveMaximum, multiple);
    }

    /**
     * Strip source-specific wire annotations and intersect shared constraints.
     * @param member first representation's common member
     * @param candidates same named member from every representation
     * @return source-neutral typed member
     */
    private static AIiDefsCanonicalStructure commonMember(AIiDefsCanonicalStructure member,
            List<AIiDefsCanonicalStructure> candidates) {
        if (member instanceof AIcDefsCanonicalElement first && candidates.stream().allMatch(
                item -> item instanceof AIcDefsCanonicalElement)) {
            var values = candidates.stream().map(item -> (AIcDefsCanonicalElement) item).toList();
            var structures = values.stream().map(AIcDefsCanonicalElement::structure).toList();
            int min = values.stream().mapToInt(AIcDefsCanonicalElement::minItemCount).min().orElse(0);
            int max = values.stream().anyMatch(value -> value.maxItemCount() == -1) ? -1
                    : values.stream().mapToInt(AIcDefsCanonicalElement::maxItemCount).max().orElse(-1);
            boolean sameDefault = values.stream().allMatch(value ->
                    value.defaultKind().equals(first.defaultKind())
                    && value.defaultValue().equals(first.defaultValue()));
            boolean emptyAllowed = values.stream().anyMatch(AIcDefsCanonicalElement::isEmptyAllowed);
            var xml = values.stream().map(AIcDefsCanonicalElement::xmlWire)
                    .filter(Objects::nonNull).findFirst().orElse(null);
            return new AIcDefsCanonicalElement(first.name(), commonScalar(structures), first.keyDefinitions(),
                    Map.of(), min, max, first.description(), xml,
                    sameDefault ? first.defaultKind() : "", sameDefault ? first.defaultValue() : "",
                    emptyAllowed, first.elementKind());
        }
        if (member instanceof AIcDefsCanonicalList first && candidates.stream().allMatch(
                item -> item instanceof AIcDefsCanonicalList)) {
            var values = candidates.stream().map(item -> (AIcDefsCanonicalList) item).toList();
            int min = values.stream().mapToInt(AIcDefsCanonicalList::minItemCount).min().orElse(0);
            int max = values.stream().anyMatch(value -> value.maxItemCount() == -1) ? -1
                    : values.stream().mapToInt(AIcDefsCanonicalList::maxItemCount).max().orElse(-1);
            var xml = values.stream().map(AIcDefsCanonicalList::xmlWire)
                    .filter(Objects::nonNull).findFirst().orElse(null);
            return new AIcDefsCanonicalList(first.name(), first.item(), min, max, first.keyDefinitions(),
                    xml, values.stream().allMatch(AIcDefsCanonicalList::uniqueItems));
        }
        return member;
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
    public static List<AIcDefsCanonicalType> declarations(List<AIcDefsCanonicalType> roots) {
        Objects.requireNonNull(roots, "roots");
        Map<String, AIcDefsCanonicalType> registry = new LinkedHashMap<>();
        for (var type : roots) collect(type, registry);
        return List.copyOf(registry.values());
    }

    /**
     * Collects an embedded synthetic type exactly once and detects inconsistent aliases.
     *
     * @param node canonical node under traversal
     * @param result mutable insertion-order identity registry
     */
    private static void collect(AIiDefsCanonicalStructure node, Map<String, AIcDefsCanonicalType> result) {
        if (node instanceof AIcDefsCanonicalType type) {
            if (type.resolutionState() != AIngResolutionState_1.RESOLVED) {
                throw new IllegalArgumentException("Unresolved canonical TYPE " + type.identity());
            }
            if (!type.targetIdentity().isBlank()) return;
            var previous = result.putIfAbsent(type.identity(), type);
            if (previous != null) {
                if (!previous.equals(type)) throw new IllegalArgumentException("Conflicting canonical identity " + type.identity());
                return;
            }
            collect(type.structure(), result);
        } else if (node instanceof AIcDefsCanonicalElementList group) {
            for (var child : group.children()) collect(child, result);
        } else if (node instanceof AIcDefsCanonicalElement member) {
            collect(member.structure(), result);
        } else if (node instanceof AIcDefsCanonicalList list) {
            collect(list.item(), result);
        } else if (node instanceof AIcDefsCanonicalMap map) {
            collect(map.keyType(), result);
            collect(map.valueType(), result);
        } else if (!(node instanceof AIcDefsCanonicalScalar) && !(node instanceof AIcDefsCanonicalEnum)) {
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
    private static Map<String, String> choiceParents(Map<String, AIcDefsCanonicalType> types) {
        Map<String, String> result = new LinkedHashMap<>();
        for (var owner : types.values()) {
            if (!(owner.structure() instanceof AIcDefsCanonicalElementList group) ||
                    group.composition() != AIngComposition_1.CHOICE) continue;
            if (group.minItemCount() != 1 || group.maxItemCount() != 1 || !owner.inheritedFromTypes().isEmpty()) {
                throw new UnsupportedOperationException("CHOICE group occurrences/inheritance unsupported: " + owner.identity());
            }
            if (group.children().isEmpty()) throw new IllegalArgumentException("Empty CHOICE " + owner.identity());
            for (var child : group.children()) {
                if (!(child instanceof AIcDefsCanonicalElement element) ||
                        !(element.structure() instanceof AIcDefsCanonicalType variant) ||
                        !variant.targetIdentity().isEmpty() || element.minItemCount() != 0 || element.maxItemCount() != 1) {
                    throw new UnsupportedOperationException("CHOICE requires named exclusive variants: " + owner.identity());
                }
                if (!(variant.structure() instanceof AIcDefsCanonicalScalar) &&
                        !(variant.structure() instanceof AIcDefsCanonicalElementList object &&
                        (object.composition() == AIngComposition_1.SEQUENCE ||
                         object.composition() == AIngComposition_1.ALL))) {
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
    /** One declared key whose selector is relative to the referencing element. */
    private record ScopedKey(String selector, IndexKey index) { }

    /**
     * Resolve keys through an existing named TYPE without ever projecting a new
     * nominal TYPE. Only a temporary LIST descriptor is used for validation.
     * @param element referencing element carrying occurrence-local constraints
     * @param types fully resolved canonical declarations
     * @return semantic index descriptions grouped by selected direct list
     */
    private static List<ScopedKey> scopedIndexKeys(AIcDefsCanonicalElement element,
            Map<String, AIcDefsCanonicalType> types) {
        if (element.keyDefinitions().isEmpty()) return List.of();
        if (!(element.structure() instanceof AIcDefsCanonicalType reference))
            throw new IllegalArgumentException("Scoped XSD key requires named object TYPE: " + element.name());
        String identity = reference.targetIdentity().isEmpty() ? reference.identity() : reference.targetIdentity();
        AIcDefsCanonicalType resolved = types.get(identity);
        if (resolved == null || !(resolved.structure() instanceof AIcDefsCanonicalElementList group))
            throw new IllegalArgumentException("Unresolved scoped XSD key owner TYPE " + identity
                    + " at " + element.name());
        List<ScopedKey> result = new ArrayList<>();
        for (var key : element.keyDefinitions()) {
            String selector = key.selector().startsWith("./") ? key.selector().substring(2) : key.selector();
            AIcDefsCanonicalList matched = null;
            for (var child : group.children()) {
                if (child instanceof AIcDefsCanonicalList list && list.name().equals(selector)) {
                    if (matched != null) throw new IllegalArgumentException("Ambiguous XSD key selector " + selector);
                    matched = list;
                }
            }
            if (matched == null) throw new IllegalArgumentException(
                    "Missing repeated member " + selector + " in named TYPE " + identity);
            var view = new AIcDefsCanonicalList(matched.name(), matched.item(),
                    matched.minItemCount(), matched.maxItemCount(), List.of(key), matched.xmlWire());
            for (var index : indexKeys(view, types)) result.add(new ScopedKey(selector, index));
        }
        return List.copyOf(result);
    }

    private static List<IndexKey> indexKeys(AIcDefsCanonicalList list,
            Map<String, AIcDefsCanonicalType> types) {
        if (list.keyDefinitions().isEmpty()) return List.of();
        if (list.minItemCount() != 0 || list.maxItemCount() != -1) {
            throw new UnsupportedOperationException("Indexed LIST cardinality unsupported: " + list.name());
        }
        if (!(list.item() instanceof AIcDefsCanonicalType)) {
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
                boolean attributeTerminal = false;
                for (int i = 0; i < segments.length; i++) {
                    String segment = segments[i];
                    if (segment.startsWith("@")) {
                        if (i != segments.length - 1)
                            throw new UnsupportedOperationException("XML XPath attribute must be terminal: " + xpath);
                        attributeTerminal = true;
                        segment = segment.substring(1);
                    }
                    if (!segment.matches("[A-Za-z_][A-Za-z0-9_-]*")) {
                        throw new UnsupportedOperationException("Namespace/predicate/axis in indexed LIST XPath needs a resolver: " + xpath);
                    }
                    names.add(segment);
                }
                String normalized = String.join(".", names);
                validateIndexPath(list.item(), normalized, types, attributeTerminal);
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
    private static AIiDefsCanonicalStructure indexStructure(AIiDefsCanonicalStructure node,
            Map<String, AIcDefsCanonicalType> types) {
        Set<String> seen = new HashSet<>();
        while (node instanceof AIcDefsCanonicalType type) {
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
    private static void validateIndexPath(AIiDefsCanonicalStructure item, String path,
            Map<String, AIcDefsCanonicalType> types, boolean attributeTerminal) {
        String[] components = path.split("\\.", -1);
        AIiDefsCanonicalStructure node = item;
        for (int index = 0; index < components.length; index++) {
            node = indexStructure(node, types);
            if (!(node instanceof AIcDefsCanonicalElementList group) ||
                    group.composition() == AIngComposition_1.CHOICE) {
                throw new UnsupportedOperationException("Indexed LIST path crosses a non-object: " + path);
            }
            AIcDefsCanonicalElement match = null;
            for (var child : group.children()) {
                if (child instanceof AIcDefsCanonicalElement element &&
                        element.name().equals(components[index])) {
                    if (match != null) throw new IllegalArgumentException("Ambiguous indexed field: " + path);
                    match = element;
                }
            }
            if (match == null) throw new IllegalArgumentException("Unresolved indexed LIST field: " + path);
            node = match.structure();
            if (index == components.length - 1) {
                var wire = match.xmlWire();
                boolean isAttribute = wire != null && wire.valueKind() == AIngXmlWireNameValueKind_1.ATTRIBUTE;
                if (attributeTerminal != isAttribute && wire != null) throw new IllegalArgumentException(
                        "Indexed XML path attribute mismatch: " + path);
                node = indexStructure(node, types);
                if (!(node instanceof AIcDefsCanonicalScalar) && !(node instanceof AIcDefsCanonicalEnum)) {
                    throw new UnsupportedOperationException("Index must resolve to a typed scalar: " + path);
                }
                if (node instanceof AIcDefsCanonicalScalar scalar &&
                        (scalar.scalarKind() == AIngScalarKind_1.ANY ||
                         scalar.scalarKind() == AIngScalarKind_1.NULL)) {
                    throw new UnsupportedOperationException("Unindexable scalar kind at " + path);
                }
                boolean virtualMapKey = match.sourceBindings().values().stream()
                        .flatMap(List::stream)
                        .anyMatch(binding -> "synthetic_map_key".equals(binding.representationKind()));
                if (virtualMapKey &&
                        (node instanceof AIcDefsCanonicalScalar scalar
                            && scalar.scalarKind() != AIngScalarKind_1.STRING ||
                         node instanceof AIcDefsCanonicalEnum enumeration
                            && enumeration.baseScalarType() != AIngScalarKind_1.STRING)) {
                    throw new UnsupportedOperationException(
                            "JSON/YAML propertyNames keys must resolve to string or string enum: " + path);
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
    private static AIcDefsCanonicalList directList(AIcDefsCanonicalType type, String member) {
        if (!(type.structure() instanceof AIcDefsCanonicalElementList group)) return null;
        for (var entry : group.children()) {
            if (entry instanceof AIcDefsCanonicalList list && list.name().equals(member)) return list;
        }
        return null;
    }

    /**
     * Canonicalizes a member/key pair into an unambiguous Java constant identifier.
     * This helper is intentionally identical in meaning to the Python emitter.
     *
     * @param field XML repeated child element name
     * @param key local XSD identity constraint name
     * @return normalized KEY_ID__ constant identifier
     * @throws IllegalArgumentException when either name has no usable lexical words
     */
    private static String keyConstant(String field, String key) {
        return identifier("KEY_ID__" + keyWords(key), true);
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
     * @return source-ordered scoped symbol to original key or field identity
     * @throws IllegalArgumentException on normalized naming collisions
     */
    private static Map<String, String> keyConstants(AIcDefsCanonicalType type,
            Map<String, AIcDefsCanonicalType> types) {
        Map<String, String> result = new LinkedHashMap<>();
        if (!(type.structure() instanceof AIcDefsCanonicalElementList group)) return result;
        // Every direct field owns a stable constant in all three Defs source
        // families; XML keys are additional constants, not a precondition.
        for (var member : group.children()) {
            String fieldName;
            if (member instanceof AIcDefsCanonicalElement element) fieldName = element.name();
            else if (member instanceof AIcDefsCanonicalList list) fieldName = list.name();
            else if (member instanceof AIcDefsCanonicalMap map) fieldName = map.name();
            else continue;
            String symbol = identifier("FIELD_NAME__" + keyWords(fieldName), true);
            String prior = result.putIfAbsent(symbol, fieldName);
            if (prior != null && !prior.equals(fieldName)) {
                throw new IllegalArgumentException("Conflicting field constant in "
                        + type.identity() + ": " + symbol);
            }
        }
        for (var member : group.children()) {
            List<IndexKey> defined;
            String owner;
            if (member instanceof AIcDefsCanonicalList list) {
                defined = indexKeys(list, types);
                owner = list.name();
            } else if (member instanceof AIcDefsCanonicalElement element && !element.keyDefinitions().isEmpty()) {
                defined = scopedIndexKeys(element, types).stream().map(ScopedKey::index).toList();
                owner = element.name();
            } else continue;
            for (var key : defined) {
                String symbol = keyConstant(owner, key.name());
                String prior = result.putIfAbsent(symbol, key.name());
                if (prior != null && !prior.equals(key.name()))
                    throw new IllegalArgumentException("Conflicting key ID constant in " + type.identity() + ": " + symbol);
                for (String path : key.fields()) {
                    String fieldSymbol = identifier("FIELD_NAME__" + keyWords(path), true);
                    String former = result.putIfAbsent(fieldSymbol, path);
                    if (former != null && !former.equals(path))
                        throw new IllegalArgumentException("Conflicting key field constant in " + type.identity() + ": " + fieldSymbol);
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
    private List<Member> members(AIcDefsCanonicalType type, Map<String, AIcDefsCanonicalType> types, boolean javaTarget) {
        if (!(type.structure() instanceof AIcDefsCanonicalElementList group)) {
            throw new UnsupportedOperationException("Only object and top-level enum supported: " + type.identity());
        }
        if ((group.composition() != AIngComposition_1.SEQUENCE &&
                group.composition() != AIngComposition_1.ALL) ||
                group.minItemCount() != 1 || group.maxItemCount() != 1) {
            throw new UnsupportedOperationException("CHOICE/group-cardinality emission needs a dedicated backend: " + type.identity());
        }
        List<Member> result = new ArrayList<>();
        Set<String> methods = new HashSet<>();
        for (var entry : group.children()) {
            String field;
            AIiDefsCanonicalStructure structure;
            int minimum;
            int maximum;
            String description;
            if (entry instanceof AIcDefsCanonicalElement element) {
                if (element.maxItemCount() != 1) {
                    throw new UnsupportedOperationException("Identity/repeated-field emission needs extended backend: "
                            + type.identity() + '/' + element.name());
                }
                field = element.name();
                structure = element.structure();
                minimum = element.minItemCount();
                maximum = element.maxItemCount();
                description = element.description();
            } else if (entry instanceof AIcDefsCanonicalList list) {
                /* A direct XSD repeated particle is LIST, not ELEMENT(LIST).
                 * Keep the collection's original bounds; typed() rejects all
                 * bounds which the current emitter cannot represent safely. */
                if (list.name().isBlank()) {
                    throw new IllegalArgumentException("Unnamed direct LIST inside " + type.identity());
                }
                field = list.name();
                structure = list;
                minimum = list.minItemCount();
                maximum = list.maxItemCount();
                description = "";
            } else if (entry instanceof AIcDefsCanonicalMap map &&
                    map.mapKind() == AIngMapKind_1.INTEGRATED_PROPERTY_MAP) {
                field = map.name();
                structure = map;
                minimum = 0;
                maximum = -1;
                description = "";
            } else {
                throw new UnsupportedOperationException("Unsupported object child " + entry.kind());
            }
            boolean virtualKey = entry instanceof AIcDefsCanonicalElement element
                    && element.sourceBindings().values().stream().flatMap(List::stream)
                    .anyMatch(binding -> "synthetic_map_key".equals(binding.representationKind()));
            boolean virtualValue = entry instanceof AIcDefsCanonicalElement element
                    && element.sourceBindings().values().stream().flatMap(List::stream)
                    .anyMatch(binding -> "synthetic_map_value".equals(binding.representationKind()));
            String getterRole = virtualKey ? "multi_mapped_list_key_synthetic_getter"
                    : virtualValue ? "multi_mapped_list_value_synthetic_getter"
                    : structure instanceof AIcDefsCanonicalList ? "list_getter" : "standard_getter";
            String getter = identifier(naming.render(getterRole, field, Map.of()), javaTarget);
            String setter = identifier(naming.render("standard_setter", field, Map.of()), javaTarget);
            if (getter.equals(setter) || !methods.add(getter) || !methods.add(setter)) {
                throw new IllegalArgumentException("Duplicate getter/setter in " + type.identity() + '/' + field);
            }
            String resolvedType = typed(structure, types, javaTarget, type.identity() + '/' + field);
            if (structure instanceof AIcDefsCanonicalList list
                    && scopedIndexedMembers.contains(type.identity() + "#" + field)) {
                String itemType = typed(list.item(), types, javaTarget, type.identity() + '/' + field + "/items");
                resolvedType = javaTarget ? "eu.algites.lib.common.list.AIiMultiMappedList<"
                        + "? extends " + itemType + ">"
                        : "AIiMultiMappedList[" + itemType + "]";
            }
            result.add(new Member(field, getter, setter, resolvedType,
                    minimum, maximum, description));
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
    private String typed(AIiDefsCanonicalStructure node, Map<String, AIcDefsCanonicalType> types,
            boolean javaTarget, String context) {
        if (node instanceof AIcDefsCanonicalType reference) {
            String key = reference.targetIdentity().isEmpty() ? reference.identity() : reference.targetIdentity();
            if (!types.containsKey(key)) throw new IllegalArgumentException("Unknown referenced TYPE " + key + " at " + context);
            var declaration = types.get(key);
            if (declaration.structure() instanceof AIcDefsCanonicalList list) {
                return typed(list, types, javaTarget, context);
            }
            var names = outputNames.get(key);
            return javaTarget ? names.javaType() : names.pythonType();
        }
        if (node instanceof AIcDefsCanonicalScalar scalar) {
            if (!scalar.format().isEmpty() && scalar.scalarKind() != AIngScalarKind_1.STRING
                    && scalar.scalarKind() != AIngScalarKind_1.INTEGER
                    && scalar.scalarKind() != AIngScalarKind_1.NUMBER) {
                throw new UnsupportedOperationException("Unsupported scalar format " + scalar.format() + " at " + context);
            }
            return switch (scalar.scalarKind()) {
                case STRING -> javaTarget ? "String" : "str";
                case INTEGER -> javaTarget ? "Long" : "int";
                case NUMBER -> javaTarget ? "Double" : "float";
                case BOOLEAN -> javaTarget ? "Boolean" : "bool";
                case ANY -> throw new IllegalArgumentException(context
                        + ": untyped ANY scalar cannot be emitted as a public "
                        + (javaTarget ? "Java" : "Python")
                        + " DataObject getter (Object/Any is forbidden); "
                        + "supply a concrete scalar, enum, or named structured type in the schema");
                default -> throw new UnsupportedOperationException("Unrepresentable scalar " + scalar.scalarKind() + " at " + context);
            };
        }
        if (node instanceof AIcDefsCanonicalList list) {
            indexKeys(list, types);
            // Bounds apply to the list items, not to the existence of the
            // containing property. Both emitted field metadata and the list
            // constraints annotation preserve them independently.
            String value = typed(list.item(), types, javaTarget, context + "/items");
            if (!list.keyDefinitions().isEmpty()) {
                return javaTarget ? "eu.algites.lib.common.list.AIiMultiMappedList<"
                        + "? extends " + value + ">"
                        : "AIiMultiMappedList[" + value + "]";
            }
            return javaTarget ? "eu.algites.lib.common.list.AIiBoundedList<? extends " + value + ">" : "AIiBoundedList[" + value + "]";
        }
        if (node instanceof AIcDefsCanonicalMap map) {
            String key = typed(map.keyType(), types, javaTarget, context + "/key");
            String value = typed(map.valueType(), types, javaTarget, context + "/value");
            return javaTarget ? "java.util.Map<" + (commonProjection ? "? extends " : "")
                    + key + ", " + "? extends " + value + ">"
                    : "dict[" + key + ", " + value + "]";
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
    /** Recover the schema structure owning a direct getter, following validated TYPE references.
     * @param type source declaration
     * @param fieldName logical member name
     * @param types all linked declarations
     * @return canonical constrained value, or null when there is no matching field
     */
    private static AIiDefsCanonicalStructure constrainedValue(AIcDefsCanonicalType type, String fieldName,
            Map<String, AIcDefsCanonicalType> types) {
        if (!(type.structure() instanceof AIcDefsCanonicalElementList parent)) return null;
        AIiDefsCanonicalStructure value = null;
        for (var member : parent.children()) {
            if (member instanceof AIcDefsCanonicalElement element && element.name().equals(fieldName))
                value = element.structure();
            if (member instanceof AIcDefsCanonicalList list && list.name().equals(fieldName))
                value = list;
        }
        var visited = new java.util.HashSet<String>();
        while (value instanceof AIcDefsCanonicalType reference) {
            String identity = reference.targetIdentity().isEmpty() ? reference.identity() : reference.targetIdentity();
            if (!visited.add(identity)) throw new IllegalArgumentException("Recursive constrained TYPE " + identity);
            AIcDefsCanonicalType target = types.get(identity);
            if (target == null) throw new IllegalArgumentException("Missing constrained TYPE " + identity);
            value = target.structure();
        }
        return value;
    }

    /** Render type-specific getter annotations from canonical constraint values.
     * @param value resolved canonical value
     * @param java whether Java (rather than Python) is emitted
     * @return complete annotation lines with indentation
     */
    private static String constraintAnnotations(AIiDefsCanonicalStructure value, boolean java) {
        if (value == null) return "";
        String category = "";
        var values = new LinkedHashMap<String, Object>();
        if (value instanceof AIcDefsCanonicalScalar scalar) {
            if (scalar.scalarKind() == AIngScalarKind_1.STRING) {
                category = "String";
                if (scalar.minLength() >= 0) values.put("minLength", scalar.minLength());
                if (scalar.maxLength() >= 0) values.put("maxLength", scalar.maxLength());
                if (!scalar.pattern().isEmpty()) values.put("pattern", scalar.pattern());
                if (!scalar.format().isEmpty()) values.put("format", scalar.format());
            } else if (scalar.scalarKind() == AIngScalarKind_1.INTEGER
                    || scalar.scalarKind() == AIngScalarKind_1.NUMBER) {
                category = "Numeric";
                if (!scalar.minimum().isEmpty()) values.put("minimum", scalar.minimum());
                if (!scalar.maximum().isEmpty()) values.put("maximum", scalar.maximum());
                if (scalar.exclusiveMinimum()) values.put("exclusiveMinimum", true);
                if (scalar.exclusiveMaximum()) values.put("exclusiveMaximum", true);
                if (!scalar.multipleOf().isEmpty()) values.put("multipleOf", scalar.multipleOf());
                if (!scalar.format().isEmpty()) values.put("format", scalar.format());
            }
        } else if (value instanceof AIcDefsCanonicalList list) {
            category = "List";
            if (list.minItemCount() > 0) values.put("minItems", list.minItemCount());
            if (list.maxItemCount() >= 0) values.put("maxItems", list.maxItemCount());
            if (list.uniqueItems()) values.put("uniqueItems", true);
        } else if (value instanceof AIcDefsCanonicalElementList group) {
            category = "Object";
            if (group.minProperties() >= 0) values.put("minProperties", group.minProperties());
            if (group.maxProperties() >= 0) values.put("maxProperties", group.maxProperties());
        }
        if (values.isEmpty()) return "";
        StringBuilder result = new StringBuilder("    @");
        if (java) result.append("eu.algites.lib.data.dataobject.");
        result.append("AIaDataObjectField").append(category).append("Constraints(");
        String comma = "";
        for (var entry : values.entrySet()) {
            String field = entry.getKey();
            if (!java) field = field.replaceAll("([A-Z])", "_$1").toLowerCase(Locale.ROOT);
            Object raw = entry.getValue();
            result.append(comma).append(field).append(" = ")
                    .append(raw instanceof String literal ? java ? javaString(literal) : pyString(literal)
                            : raw instanceof Boolean bool ? java ? bool.toString() : bool ? "True" : "False"
                            : raw.toString());
            comma = ", ";
        }
        return result.append(")\n").toString();
    }

    private String javaSource(AIcDefsCanonicalType type, Map<String, AIcDefsCanonicalType> types,
            Map<String, String> choiceParents) {
        String name = outputNames.get(type.identity()).javaType();
        StringBuilder result = new StringBuilder("package ").append(packageName).append(";\n\n")
                .append("/**\n * ").append(javaDoc(type.description().isEmpty() ? "Contract for " + type.name() : type.description()))
                .append("\n *\n * <p>Canonical identity: ").append(javaDoc(type.identity())).append("; version: ")
                .append(javaDoc(type.schemaVersion())).append(".</p>\n */\n");
        if (type.structure() instanceof AIcDefsCanonicalElementList choice &&
                choice.composition() == AIngComposition_1.CHOICE) {
            if (commonProjection && representations.isEmpty()) {
                return result.append("public interface ").append(name).append(" {\n}\n").toString();
            }
            result.append("public sealed interface ").append(name);
            if (!commonOutputNames.isEmpty())
                result.append(" extends ").append(commonOutputNames.get(type.identity()).javaType());
            else result.append(" extends eu.algites.lib.data.dataobject.AIiDataObject");
            result.append(" permits ");
            String separator = "";
            for (var child : choice.children()) {
                var variant = (AIcDefsCanonicalType) ((AIcDefsCanonicalElement) child).structure();
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
            if (type.structure() instanceof AIcDefsCanonicalScalar) {
                String scalarType = typed(type.structure(), types, true, type.identity() + "/value");
                String getter = identifier(naming.render("standard_getter", "value", Map.of()), true);
                return result.append("public record ").append(name).append('(').append(scalarType)
                        .append(" value) implements ").append(parent).append(" {\n")
                        .append(constraintAnnotations(type.structure(), true))
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
                result.append(constraintAnnotations(
                        constrainedValue(type, field.sourceName(), types), true));
                result.append("    /** @return ").append(doc)
                        .append(field.minimum() > 0 ? " (required)" : " (optional)")
                        .append(" */\n    public ").append(field.type()).append(' ')
                        .append(field.getter()).append("() { return field")
                        .append(++index).append("; }\n");
            }
            return result.append("}\n").toString();
        }
        if (type.structure() instanceof AIcDefsCanonicalEnum enumeration) {
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
            Set<String> identifiers = new HashSet<>();
            int index = 0;
            for (var value : enumeration.values()) {
                if (!values.add(value.wireValue())) {
                    throw new IllegalArgumentException("Duplicate enum wire code at " + type.identity());
                }
                if (index > 0) result.append(",\n");
                String role = enumeration.baseScalarType() == AIngScalarKind_1.STRING
                        ? "string_enum_item" : "non_string_enum_item";
                String symbol = identifier(naming.render(role, value.wireValue(), Map.of()), true);
                if (!identifiers.add(symbol)) throw new IllegalArgumentException("Enum symbol collision: " + symbol);
                result.append("    /** Exact source code ").append(javaDoc(value.wireValue()))
                        .append(". */\n    ").append(symbol).append('(');
                result.append(enumLiteral(value.wireValue(), enumeration.baseScalarType(), true)).append(')');
                index++;
            }
            return result.append(";\n\n    private final ").append(codeType).append(" wireCode;\n\n")
                    .append("    /** @param aWireCode original typed schema code */\n")
                    .append("    ").append(name).append('(').append(codeType)
                    .append(" aWireCode) { wireCode = aWireCode; }\n\n")
                    .append("    /** @return exact typed schema wire code */\n")
                    .append("    public ").append(codeType).append(" code() { return wireCode; }\n}\n").toString();
        }
        var members = members(type, types, true);
        /* A read-only DataObject always carries a complete declaration identity.
         * The effective naming profile is selected by the independent SDO step. */
        int schemaVersion;
        try {
            schemaVersion = type.schemaVersion().isBlank() ? -1 : Integer.parseInt(type.schemaVersion());
        } catch (NumberFormatException invalidVersion) {
            throw new IllegalArgumentException("Invalid schema version at " + type.identity(), invalidVersion);
        }
        for (AIngSourceInputKind_1 kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            if (commonProjection && representations.isEmpty()
                    || !type.sourceBindings().containsKey(kind)) continue;
            var sourceType = representation(kind, type);
            String technology = kind == AIngSourceInputKind_1.JSONDEFS
                    ? "jsondefs.AIaDataObjectJsonSchema" : "yamldefs.AIaDataObjectYamlSchema";
            result.append("@eu.algites.lib.data.dataobject.").append(technology)
                    .append("(schemaId = ").append(javaString(sourceType.identity()))
                    .append(", schemaVersion = ").append(schemaVersion);
            String schemaUrl = publishedSchemaUrl(sourceType, kind);
            if (!schemaUrl.isEmpty()) result.append(", schemaUrl = ").append(javaString(schemaUrl));
            result.append(")\n");
        }
        if ((!commonProjection || !representations.isEmpty())
                && type.sourceBindings().containsKey(AIngSourceInputKind_1.XMLDEFS)) {
            var declaration = xmlDeclaration(representation(AIngSourceInputKind_1.XMLDEFS, type));
            if (declaration != null) {
                result.append("@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(")
                        .append("definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.")
                        .append(declaration.kind())
                        .append(", namespace = ").append(javaString(declaration.namespace()))
                        .append(", namespaceLocalName = ").append(javaString(declaration.localName()))
                        .append(")\n");
            }
        }
        if (commonProjection) result.append("@eu.algites.lib.data.dataobject.AIaDataObject(description = ")
                .append(javaString(type.description())).append(")\n");
        result.append("public interface ").append(name);
        result.append(" extends ");
        if (commonProjection) {
            if (type.inheritedFromTypes().isEmpty()) {
                result.append("eu.algites.lib.data.dataobject.AIiDataObject");
            } else {
                String sep = "";
                for (var parent : type.inheritedFromTypes()) {
                    result.append(sep).append((outputNames.containsKey(parent) ? outputNames.get(parent)
                            : externalParents.get(parent)).javaType());
                    sep = ", ";
                }
            }
        } else {
            if (!commonOutputNames.isEmpty()) {
                result.append(commonOutputNames.get(type.identity()).javaType()).append(", ");
            }
            for (var parent : type.inheritedFromTypes()) {
                result.append((outputNames.containsKey(parent) ? outputNames.get(parent)
                        : externalParents.get(parent)).javaType()).append(", ");
            }
            if (commonOutputNames.isEmpty() && type.inheritedFromTypes().isEmpty())
                result.append("eu.algites.lib.data.dataobject.AIiDataObject");
            else if (result.toString().endsWith(", "))
                result.setLength(result.length() - 2);
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
            result.append("    /** Canonical key IDs and logical field names for this DataObject. */\n")
                    .append("    interface ").append(constContainer).append(" {\n");
            for (var entry : constValues.entrySet()) {
                result.append("        /** Canonical source identifier ")
                        .append(javaDoc(entry.getValue())).append(". */\n")
                        .append("        String ").append(entry.getKey()).append(" = ")
                        .append(javaString(entry.getValue())).append(";\n");
            }
            result.append("    }\n\n");
        }
        for (int position = 0; position < members.size(); position++) {
            var field = members.get(position);
            boolean virtualEntry = type.structure() instanceof AIcDefsCanonicalElementList group
                    && group.children().stream().filter(child -> child instanceof AIcDefsCanonicalElement element
                            && element.name().equals(field.sourceName()))
                    .map(child -> (AIcDefsCanonicalElement) child)
                    .flatMap(element -> element.sourceBindings().values().stream().flatMap(List::stream))
                    .anyMatch(binding -> "synthetic_map_key".equals(binding.representationKind())
                            || "synthetic_map_value".equals(binding.representationKind()));
            if (virtualEntry) {
                result.append("    /** @return synthetic indexed-map entry key/value; not a persisted field */\n"
                        + "    ").append(field.type()).append(' ').append(field.getter()).append("();\n\n");
                continue;
            }
            var xmlWire = type.structure() instanceof AIcDefsCanonicalElementList group
                    ? group.children().stream().filter(child ->
                            child instanceof AIcDefsCanonicalElement element && element.name().equals(field.sourceName())
                            || child instanceof AIcDefsCanonicalList collection && collection.name().equals(field.sourceName()))
                            .findFirst().map(child -> child instanceof AIcDefsCanonicalElement element
                                    ? element.xmlWire() : ((AIcDefsCanonicalList) child).xmlWire()).orElse(null)
                    : null;
            if (xmlWire != null && (!commonProjection || !representations.isEmpty())) {
                result.append("    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = ")
                        .append(javaString(xmlWire.namespaceUri()))
                        .append(", namespaceLocalName = ").append(javaString(xmlWire.localName()))
                        .append(", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.")
                        .append(xmlWire.valueKind().name()).append(")\n");
            }
            var metadata = type.structure() instanceof AIcDefsCanonicalElementList fieldsGroup
                    ? fieldsGroup.children().stream().filter(child ->
                            child instanceof AIcDefsCanonicalElement element
                                    && element.name().equals(field.sourceName()))
                            .map(child -> (AIcDefsCanonicalElement) child).findFirst().orElse(null)
                    : null;
            var constrained = constrainedValue(type, field.sourceName(), types);
            int countMinimum = constrained instanceof AIcDefsCanonicalList collection
                    ? collection.minItemCount() : field.minimum();
            int countMaximum = constrained instanceof AIcDefsCanonicalList collection
                    ? collection.maxItemCount() : field.maximum();
            if (commonProjection) {
            result.append("    @eu.algites.lib.data.dataobject.AIaDataObjectField(")
                    .append(metadata != null && metadata.elementKind() == AIngElementKind_1.EMBEDDED
                            ? "embedded = true" : "dataFieldName = " + javaString(field.sourceName()))
                    .append(", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.")
                    .append(field.minimum() > 0 ? "REQUIRED" : "ALLOWED")
                    .append(", allowsNull = false, order = ").append(position)
                    .append(", minItemCount = ").append(countMinimum)
                    .append(", maxItemCount = ").append(countMaximum)
                    .append(", isEmptyAllowed = ").append(metadata != null && metadata.isEmptyAllowed());
            result.append(")\n");
            if (metadata != null && !metadata.defaultKind().isEmpty()) {
                result.append("    @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(")
                        .append("kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.")
                        .append(metadata.defaultKind())
                        .append(", defaultValueFactory = @eu.algites.lib.factory.cpdiscovery.AIaCategoryProviderFactoryDefinition(")
                        .append("factoryInterface = eu.algites.lib.data.dataobject.AIiFieldDefaultScalarValueFactory.class)")
                        .append(", defaultArguments = {").append(javaString(metadata.defaultValue()))
                        .append("})\n");
            }
            result.append(constraintAnnotations(constrained, true));
            }
            var list = directList(type, field.sourceName());
            if (list != null) {
                for (var key : indexKeys(list, types)) {
                    result.append("    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = ")
                            .append(constContainer).append('.').append(keyConstant(list.name(), key.name()))
                            .append(", fields = {");
                    String separator = "";
                    for (var path : key.fields()) {
                        result.append(separator).append(constContainer).append(".FIELD_NAME__").append(keyWords(path));
                        separator = ", ";
                    }
                    result.append("}, required = ").append(key.required()).append(")\n");
                }
            }
            if (metadata != null && !metadata.keyDefinitions().isEmpty()) {
                for (var scoped : scopedIndexKeys(metadata, types)) {
                    var key = scoped.index();
                    result.append("    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = ")
                            .append(constContainer).append('.').append(keyConstant(metadata.name(), key.name()))
                            .append(", selector = ").append(javaString(scoped.selector())).append(", fields = {");
                    String separator = "";
                    for (var path : key.fields()) {
                        result.append(separator).append(constContainer).append(".FIELD_NAME__").append(keyWords(path));
                        separator = ", ";
                    }
                    result.append("}, required = ").append(key.required()).append(")\n");
                }
            }
            String doc = javaDoc(field.description().isBlank()
                    ? "Value of schema field " + field.sourceName() : field.description());
            String required = field.minimum() == 0 ? "optional" : "required";
            result.append("    /** ").append(doc).append(" Field is ").append(required)
                    .append("; cardinality ").append(countMinimum).append("..").append(countMaximum)
                    .append(".\n     * @return canonical field value\n     */\n    ")
                    .append(field.type()).append(' ').append(field.getter()).append("();\n\n");
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
    private String pythonSource(AIcDefsCanonicalType type, Map<String, AIcDefsCanonicalType> types,
            Map<String, String> choiceParents) {
        String name = outputNames.get(type.identity()).pythonType();
        StringBuilder result = new StringBuilder("from __future__ import annotations\n\n");
        if (type.structure() instanceof AIcDefsCanonicalElementList choice &&
                choice.composition() == AIngComposition_1.CHOICE) {
            result.append("from abc import ABC\n");
            if (!commonOutputNames.isEmpty()) {
                var common = commonOutputNames.get(type.identity());
                result.append("from .").append(common.pythonModule()).append(" import ")
                        .append(common.pythonType()).append("\n");
            }
            return result.append("\n\nclass ").append(name).append('(')
                    .append(commonOutputNames.isEmpty() ? "ABC" : commonOutputNames.get(type.identity()).pythonType())
                    .append("):\n")
                    .append("    \"\"\"").append(pyDoc(type.description().isEmpty()
                            ? "Exclusive canonical choice" : type.description()))
                    .append("\"\"\"\n    pass\n").toString();
        }
        if (choiceParents.containsKey(type.identity())) {
            if (!type.inheritedFromTypes().isEmpty()) {
                throw new UnsupportedOperationException("CHOICE variant inheritance unsupported: " + type.identity());
            }
            var parent = outputNames.get(choiceParents.get(type.identity()));
            result.append("from dataclasses import dataclass\nfrom typing import final\n");
            for (String category : List.of("string", "numeric", "list", "object")) {
                String symbol = Character.toUpperCase(category.charAt(0)) + category.substring(1);
                result.append("from eu.algites.lib.data.dataobject.aia_data_object_field_")
                        .append(category).append("_constraints import AIaDataObjectField")
                        .append(symbol).append("Constraints\n");
            }
            result.append("from .").append(parent.pythonModule()).append(" import ")
                    .append(parent.pythonType()).append("\n\n\n@final\n@dataclass(frozen=True)\nclass ")
                    .append(name).append('(').append(parent.pythonType()).append("):\n")
                    .append("    \"\"\"").append(pyDoc(type.description().isEmpty()
                            ? "Exclusive canonical variant" : type.description()))
                    .append("\"\"\"\n");
            if (type.structure() instanceof AIcDefsCanonicalScalar) {
                String scalarType = typed(type.structure(), types, false, type.identity() + "/value");
                String getter = identifier(naming.render("standard_getter", "value", Map.of()), false);
                return result.append("    value: ").append(scalarType).append("\n\n")
                        .append(constraintAnnotations(type.structure(), false))
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
                result.append('\n').append(constraintAnnotations(
                        constrainedValue(type, field.sourceName(), types), false));
                result.append("    def ").append(field.getter()).append("(self) -> ").append(annotation)
                        .append(":\n        \"\"\"Return ").append(doc)
                        .append(".\"\"\"\n        return self.field")
                        .append(++index).append('\n');
            }
            return result.toString();
        }
        if (type.structure() instanceof AIcDefsCanonicalEnum enumeration) {
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
                    .append("\n\n    Canonical identity: ").append(pyDoc(type.identity()))
                    .append("; version: ").append(type.schemaVersion())
                    .append(".\"\"\"\n\n");
            Set<String> values = new HashSet<>();
            Set<String> identifiers = new HashSet<>();
            int index = 0;
            for (var value : enumeration.values()) {
                if (!values.add(value.wireValue())) throw new IllegalArgumentException("Duplicate enum wire code at " + type.identity());
                String role = enumeration.baseScalarType() == AIngScalarKind_1.STRING
                        ? "string_enum_item" : "non_string_enum_item";
                String symbol = identifier(naming.render(role, value.wireValue(), Map.of()), false);
                if (!identifiers.add(symbol)) throw new IllegalArgumentException("Enum symbol collision: " + symbol);
                result.append("    ").append(symbol).append(" = ")
                        .append(enumLiteral(value.wireValue(), enumeration.baseScalarType(), false)).append('\n');
                index++;
            }
            return result.append("\n    def code(self) -> ").append(returnType).append(":\n")
                    .append("        \"\"\"Return the exact typed wire code.\"\"\"\n")
                    .append("        return self.value\n").toString();
        }
        var fields = members(type, types, false);
        result.append("from abc import ABC, abstractmethod\nfrom typing import TYPE_CHECKING\n")
                .append("from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n")
                .append("from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField\n")
                .append("from eu.algites.lib.data.dataobject.aia_data_object_field_default import AIaDataObjectFieldDefault\n")
                .append("from eu.algites.lib.data.dataobject.ain_data_object_field_default_kind import AInDataObjectFieldDefaultKind\n")
                .append("from eu.algites.lib.data.dataobject.aii_field_default_scalar_value_factory import AIiFieldDefaultScalarValueFactory\n")
                .append("from eu.algites.lib.factory.cpdiscovery.aia_category_provider_factory_definition import AIaCategoryProviderFactoryDefinition\n")
                .append("from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind\n");
        for (String category : List.of("string", "numeric", "list", "object")) {
            String symbol = switch (category) {
                case "string" -> "String";
                case "numeric" -> "Numeric";
                case "list" -> "List";
                default -> "Object";
            };
            result.append("from eu.algites.lib.data.dataobject.aia_data_object_field_")
                    .append(category).append("_constraints import AIaDataObjectField")
                    .append(symbol).append("Constraints\n");
        }
        if (commonProjection || type.inheritedFromTypes().isEmpty() || !commonOutputNames.isEmpty()) {
            result.append("from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n");
        }
        if (!commonOutputNames.isEmpty()) {
            var common = commonOutputNames.get(type.identity());
            result.append("from .").append(common.pythonModule()).append(" import ")
                    .append(common.pythonType()).append("\n");
        }
        boolean hasIndexedList = fields.stream().anyMatch(field -> {
            var list = directList(type, field.sourceName());
            return list != null && !list.keyDefinitions().isEmpty();
        });
        if (hasIndexedList || fields.stream().anyMatch(field -> field.type().contains("AIiMultiMappedList["))
                || scopedIndexedMembers.stream().anyMatch(member ->
                member.startsWith(type.identity() + "#"))) {
            result.append("from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList\n");
        }
        if (fields.stream().anyMatch(field -> field.type().contains("AIiBoundedList["))) {
            result.append("from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList\n");
        }
        boolean hasXmlWires = type.structure() instanceof AIcDefsCanonicalElementList group
                && group.children().stream().anyMatch(child ->
                        child instanceof AIcDefsCanonicalElement element && element.xmlWire() != null
                        || child instanceof AIcDefsCanonicalList list && list.xmlWire() != null);
        for (AIngSourceInputKind_1 kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            if (commonProjection || !type.sourceBindings().containsKey(kind)) continue;
            String prefix = kind == AIngSourceInputKind_1.JSONDEFS ? "json" : "yaml";
            String typeName = kind == AIngSourceInputKind_1.JSONDEFS ? "Json" : "Yaml";
            result.append("from eu.algites.lib.data.dataobject.").append(prefix)
                    .append("defs.aia_data_object_").append(prefix).append("_schema import AIaDataObject")
                    .append(typeName).append("Schema\n");
        }
        if (hasXmlWires && !commonProjection) {
            result.append("from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema "
                    + "import AIaDataObjectFieldXmlSchema\n")
                    .append("from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind "
                    + "import AInXmlValueKind\n");
        }
        for (String parent : commonProjection ? List.<String>of() : type.inheritedFromTypes()) {
            var names = outputNames.containsKey(parent) ? outputNames.get(parent) : externalParents.get(parent);
            result.append("from ");
            if (externalParents.containsKey(parent)) result.append(names.pythonModule());
            else result.append(".").append(names.pythonModule());
            result.append(" import ").append(names.pythonType()).append('\n');
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
        if (!commonProjection && !commonOutputNames.isEmpty()) {
            result.append(commonOutputNames.get(type.identity()).pythonType());
            separator = ", ";
        }
        for (var parent : commonProjection ? List.<String>of() : type.inheritedFromTypes()) {
            result.append(separator).append((outputNames.containsKey(parent) ? outputNames.get(parent)
                    : externalParents.get(parent)).pythonType());
            separator = ", ";
        }
        if (separator.isEmpty()) result.append("AIiDataObject, ABC");
        result.append("):\n    \"\"\"").append(pyDoc(type.description().isEmpty() ? "Contract for " + type.name() : type.description()))
                .append("\"\"\"\n\n");
        int schemaVersion;
        try {
            schemaVersion = type.schemaVersion().isBlank() ? -1 : Integer.parseInt(type.schemaVersion());
        } catch (NumberFormatException invalidVersion) {
            throw new IllegalArgumentException("Invalid schema version at " + type.identity(), invalidVersion);
        }
        if (commonProjection) result.append("    __data_object__ = AIcdDataObject(description=")
                .append(pyString(type.description())).append(")\n");
        for (AIngSourceInputKind_1 kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            if (commonProjection || !type.sourceBindings().containsKey(kind)) continue;
            String prefix = kind == AIngSourceInputKind_1.JSONDEFS ? "json" : "yaml";
            result.append("    __").append(prefix).append("_schema__ = AIaDataObject")
                    .append(kind == AIngSourceInputKind_1.JSONDEFS ? "Json" : "Yaml")
                    .append("Schema(schema_id=").append(pyString(type.identity()))
                    .append(", schema_version=").append(schemaVersion);
            String schemaUrl = publishedSchemaUrl(type, kind);
            if (!schemaUrl.isEmpty()) result.append(", schema_url=").append(pyString(schemaUrl));
            result.append(")\n");
        }
        result.append("\n");
        if ((!commonProjection || !representations.isEmpty())
                && type.sourceBindings().containsKey(AIngSourceInputKind_1.XMLDEFS)) {
            var declaration = xmlDeclaration(representation(AIngSourceInputKind_1.XMLDEFS, type));
            if (declaration != null) {
                result.insert("from __future__ import annotations\n\n".length(),
                        "from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema "
                        + "import AIaDataObjectXmlSchema\n"
                        + "from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind "
                        + "import AInXmlObjectDefinitionKind\n");
                result.append("    __xml_schema__ = AIaDataObjectXmlSchema(")
                        .append("definition_kind=AInXmlObjectDefinitionKind.")
                        .append(declaration.kind()).append(", namespace=")
                        .append(pyString(declaration.namespace())).append(", namespace_local_name=")
                        .append(pyString(declaration.localName())).append(")\n\n");
            }
        }
        if (hasXmlWires && !commonProjection && type.structure() instanceof AIcDefsCanonicalElementList group) {
            result.append("    __xml_schema_fields__ = {\n");
            for (var child : group.children()) {
                var wire = child instanceof AIcDefsCanonicalElement element ? element.xmlWire()
                        : child instanceof AIcDefsCanonicalList collection ? collection.xmlWire() : null;
                if (wire == null) continue;
                String fieldName = child instanceof AIcDefsCanonicalElement element ? element.name()
                        : ((AIcDefsCanonicalList) child).name();
                result.append("        ").append(pyString(fieldName))
                        .append(": AIaDataObjectFieldXmlSchema(namespace=").append(pyString(wire.namespaceUri()))
                        .append(", namespace_local_name=").append(pyString(wire.localName()))
                        .append(", value_kind=AInXmlValueKind.").append(wire.valueKind().name())
                        .append("),\n");
            }
            result.append("    }\n\n");
            result.append("    __xml_repeated_fields__ = (");
            for (var child : group.children()) {
                if (child instanceof AIcDefsCanonicalList list) result.append(pyString(list.name())).append(", ");
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
                    .append("        \"\"\"Stable key IDs and logical field names for this DataObject.\"\"\"\n");
            for (var entry : pythonConstValues.entrySet()) {
                result.append("        ").append(entry.getKey()).append(" = ")
                        .append(pyString(entry.getValue())).append('\n');
            }
            result.append('\n');
        }
        if (hasIndexedList) {
            result.append("    __key_definitions__ = {\n");
            for (var field : fields) {
                var list = directList(type, field.sourceName());
                if (list == null || list.keyDefinitions().isEmpty()) continue;
                result.append("        ").append(pyString(field.sourceName())).append(": (");
                for (var key : indexKeys(list, types)) {
                    result.append('(').append(pythonConstContainer).append('.')
                            .append(keyConstant(list.name(), key.name())).append(", (");
                    for (var path : key.fields()) result.append(pythonConstContainer)
                            .append(".FIELD_NAME__").append(keyWords(path)).append(", ");
                    result.append("), ").append(key.required() ? "True" : "False").append("), ");
                }
                result.append("),\n");
            }
            result.append("    }\n\n");
        }
        if (type.structure() instanceof AIcDefsCanonicalElementList group) {
            boolean hasScoped = group.children().stream().anyMatch(child ->
                    child instanceof AIcDefsCanonicalElement element && !element.keyDefinitions().isEmpty());
            if (hasScoped) {
                result.append("    __scoped_key_definitions__ = {\n");
                for (var child : group.children()) {
                    if (!(child instanceof AIcDefsCanonicalElement element) || element.keyDefinitions().isEmpty()) continue;
                    result.append("        ").append(pyString(element.name())).append(": (\n");
                    for (var scoped : scopedIndexKeys(element, types)) {
                        result.append("            (").append(pyString(scoped.selector()))
                                .append(", ").append(pyString(scoped.index().name())).append(", (");
                        for (var path : scoped.index().fields()) result.append(pyString(path)).append(", ");
                        result.append("), ").append(scoped.index().required() ? "True" : "False")
                                .append("),\n");
                    }
                    result.append("        ),\n");
                }
                result.append("    }\n\n");
            }
        }
        if (fields.isEmpty()) result.append("    pass\n");
        for (int position = 0; position < fields.size(); position++) {
            var field = fields.get(position);
            boolean virtualEntry = type.structure() instanceof AIcDefsCanonicalElementList group
                    && group.children().stream().filter(child -> child instanceof AIcDefsCanonicalElement element
                            && element.name().equals(field.sourceName()))
                    .map(child -> (AIcDefsCanonicalElement) child)
                    .flatMap(element -> element.sourceBindings().values().stream().flatMap(List::stream))
                    .anyMatch(binding -> "synthetic_map_key".equals(binding.representationKind())
                            || "synthetic_map_value".equals(binding.representationKind()));
            if (virtualEntry) {
                result.append("    @abstractmethod\n    def ").append(field.getter())
                        .append("(self) -> ").append(field.type())
                        .append(":\n        \"\"\"Return synthetic indexed-map entry key/value.\"\"\"\n"
                                + "        raise NotImplementedError\n\n");
                continue;
            }
            String required = field.minimum() == 0 ? "optional" : "required";
            String doc = pyDoc(field.description().isBlank() ? "Canonical field " + field.sourceName() : field.description());
            var metadata = type.structure() instanceof AIcDefsCanonicalElementList fieldsGroup
                    ? fieldsGroup.children().stream().filter(child ->
                            child instanceof AIcDefsCanonicalElement element
                                    && element.name().equals(field.sourceName()))
                            .map(child -> (AIcDefsCanonicalElement) child).findFirst().orElse(null)
                    : null;
            var constrained = constrainedValue(type, field.sourceName(), types);
            int countMinimum = constrained instanceof AIcDefsCanonicalList collection
                    ? collection.minItemCount() : field.minimum();
            int countMaximum = constrained instanceof AIcDefsCanonicalList collection
                    ? collection.maxItemCount() : field.maximum();
            if (commonProjection) {
            result.append("    @AIaDataObjectField(")
                    .append(metadata != null && metadata.elementKind() == AIngElementKind_1.EMBEDDED
                            ? "embedded=True" : "field_name=" + pyString(field.sourceName()))
                    .append(", presence=AInFieldPresenceKind.")
                    .append(field.minimum() > 0 ? "REQUIRED" : "ALLOWED")
                    .append(", allows_null=False, order=").append(position)
                    .append(", min_item_count=").append(countMinimum)
                    .append(", max_item_count=").append(countMaximum)
                    .append(", is_empty_allowed=").append(metadata != null && metadata.isEmptyAllowed() ? "True" : "False");
            if (metadata != null && !metadata.defaultKind().isEmpty()) {

            }
            result.append(")\n");
            if (metadata != null && !metadata.defaultKind().isEmpty()) {
                result.append("    @AIaDataObjectFieldDefault(kind=AInDataObjectFieldDefaultKind.")
                        .append(metadata.defaultKind())
                        .append(", default_value_factory=AIaCategoryProviderFactoryDefinition(")
                        .append("AIiFieldDefaultScalarValueFactory), default_arguments=(")
                        .append(pyString(metadata.defaultValue())).append(",))\n");
            }
            result.append(constraintAnnotations(constrained, false));
            }
            result.append("    @abstractmethod\n    def ").append(field.getter()).append("(self) -> ")
                    .append(field.type()).append(":\n        \"\"\"Return ")
                    .append(doc).append(" (").append(required).append(", cardinality ")
                    .append(countMinimum).append("..").append(countMaximum)
                    .append(").\"\"\"\n        raise NotImplementedError\n\n");

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
    private static String enumLiteral(String wire, AIngScalarKind_1 kind, boolean javaTarget) {
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
