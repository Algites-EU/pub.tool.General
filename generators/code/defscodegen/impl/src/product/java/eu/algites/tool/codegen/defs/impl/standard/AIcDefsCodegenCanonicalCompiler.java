package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenEnum;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenType;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Consumer;

/**
 * Java-native end-to-end canonical Defs compiler service for supported contract
 * structures. It coordinates typed schema frontends, source/identity merge,
 * reference linking, generated-schema validation and native Java/Python source
 * rendering without invoking any {@code defs.old} classes.
 *
 * <p>Each language uses its own explicitly selected Common+Defs naming profile,
 * including imported source-code naming compositions. The resulting canonical
 * graph may have target-specific synthetic type names, but the source identity,
 * structure and validation remain the same. The caller is responsible for
 * writing the returned sources to owned generated-source directories.</p>
 */
public final class AIcDefsCodegenCanonicalCompiler {
    /** Java-specific selected naming profile with resolved standard catalog fragments. */
    private final AIcCodegenNamingProfileResolver.Profile javaNaming;
    /** Python-specific selected naming profile with resolved standard catalog fragments. */
    private final AIcCodegenNamingProfileResolver.Profile pythonNaming;
    /** Mandatory canonical contract validator, supplied by the host JSON Schema runtime. */
    private final Consumer<Map<String, Object>> contractValidator;
    /** Java target class/interface/enum output naming composition IDs. */
    private final Map<String, String> javaCompositions;
    /** Python target class/module/enum output naming composition IDs. */
    private final Map<String, String> pythonCompositions;
    /** Exact versions by logical identity or explicit wildcard version. */
    private final Map<String, String> versions;
    /** Configured package for the compilation units. */
    private final String packageName;

    /**
     * Configures one independent compiler with explicit per-language naming.
     *
     * @param javaNaming resolved Java Common+Defs/source-code naming profile
     * @param pythonNaming resolved Python Common+Defs/source-code naming profile
     * @param contractValidator schema validator applied before normalization
     * @param javaCompositions explicit Java interface/enum/file name composition IDs
     * @param pythonCompositions explicit Python interface/enum/file name composition IDs
     * @param versions explicit version tokens keyed by type identity, or {@code *}
     * @param packageName Java package shared with the target Python module hierarchy
     */
    public AIcDefsCodegenCanonicalCompiler(
            AIcCodegenNamingProfileResolver.Profile javaNaming,
            AIcCodegenNamingProfileResolver.Profile pythonNaming,
            Consumer<Map<String, Object>> contractValidator,
            Map<String, String> javaCompositions, Map<String, String> pythonCompositions,
            Map<String, String> versions, String packageName) {
        this.javaNaming = Objects.requireNonNull(javaNaming, "javaNaming");
        this.pythonNaming = Objects.requireNonNull(pythonNaming, "pythonNaming");
        this.contractValidator = Objects.requireNonNull(contractValidator, "contractValidator");
        this.javaCompositions = Map.copyOf(Objects.requireNonNull(javaCompositions, "javaCompositions"));
        this.pythonCompositions = Map.copyOf(Objects.requireNonNull(pythonCompositions, "pythonCompositions"));
        this.versions = Map.copyOf(Objects.requireNonNull(versions, "versions"));
        this.packageName = Objects.requireNonNull(packageName, "packageName");
        for (var language : List.of(javaCompositions, pythonCompositions)) {
            for (var key : List.of("interface", "interface_file", "enum", "enum_file")) {
                if (!language.containsKey(key) || language.get(key).isBlank()) {
                    throw new IllegalArgumentException("Missing required output composition " + key);
                }
            }
        }
    }

    /**
     * Compiles every source twice, using target-specific naming conventions.
     * Both results are fully rendered before the method returns; on a validation
     * or code generation error, the caller receives no partial source list.
     *
     * @param documents typed schema documents in reproducible input order
     * @return unmodifiable list of fully rendered Java and Python compilation units
     * @throws IllegalArgumentException for unresolved schema references, missing
     *         names/versions or incompatible logical identities
     * @throws UnsupportedOperationException for source structures with no lossless emitter
     */
    public List<AIcDefsCodegenCanonicalSourceEmitter.Output> compile(
            List<AIcdDefsCodegenSourceDocument> documents) {
        Objects.requireNonNull(documents, "documents");
        List<AIcDefsCodegenCanonicalSourceEmitter.Output> output = new ArrayList<>();
        for (String target : List.of("java", "python")) {
            var naming = target.equals("java") ? javaNaming : pythonNaming;
            var composition = target.equals("java") ? javaCompositions : pythonCompositions;
            var model = new AIcDefsCodegenCanonicalPipeline(naming, contractValidator).process(documents);
            var declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(model.types());
            Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> names = new LinkedHashMap<>();
            int ordinal = 0;
            for (AIcdDefsCodegenType type : declarations) {
                String version = !type.schemaVersion().isBlank() ? type.schemaVersion()
                        : versions.getOrDefault(type.identity(), versions.get("*"));
                if (version == null || version.isBlank()) {
                    throw new IllegalArgumentException("Missing schema version for " + type.identity());
                }
                String kind = type.structure() instanceof AIcdDefsCodegenEnum ? "enum" : "interface";
                String typeName = naming.composedName(composition.get(kind), type.name(),
                        Map.of("version", version));
                String moduleName = naming.composedName(composition.get(kind + "_file"), type.name(),
                        Map.of("version", version));
                names.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                        target.equals("java") ? typeName : "AIxUnused" + ordinal,
                        target.equals("python") ? typeName : "AIxUnused" + ordinal,
                        target.equals("python") ? moduleName : "aix_unused_" + ordinal));
                ordinal++;
            }
            var renderer = new AIcDefsCodegenCanonicalSourceEmitter(naming, names, packageName);
            for (var rendered : renderer.render(model.types())) {
                if (rendered.language().equals(target)) output.add(rendered);
            }
        }
        return List.copyOf(output);
    }
}
