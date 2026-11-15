package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalEnum;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
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
     * Emitted units plus typed contexts for shared-interface coalescing.
     * @param outputs one shared output unit per canonical declaration and target language
     * @param shared source-neutral output name to its canonical model projection
     */
    public record Compilation(List<AIcDefsCodegenCanonicalSourceEmitter.Output> outputs,
            Map<String, AIcDefsCodegenCanonicalSourceEmitter.CommonProjection> shared) { }

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
        return compile(documents, Map.of(), Set.of());
    }

    /**
     * Compile with externally resolved, already published parent interfaces.
     * External parent types are not included in emitted Java/Python sources.
     *
     * @param documents input source schemas belonging to this generation run
     * @param externalParents public parent TYPE identity to compiled output names;
     *        Java names must be qualified, Python modules absolute import paths
     * @param importedXsdTypes expanded XSD QNames verified by the schema resolver
     * @return complete Java and Python source units excluding external dependencies
     * @throws IllegalArgumentException for unresolved/missing parent contracts
     * @throws NullPointerException if a required argument is null
     */
    public List<AIcDefsCodegenCanonicalSourceEmitter.Output> compile(
            List<AIcdDefsCodegenSourceDocument> documents,
            Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> externalParents,
            Set<String> importedXsdTypes) {
        return compileWithCommon(documents, externalParents, importedXsdTypes).outputs();
    }

    /**
     * Compile while retaining canonical graphs for merging common contracts
     * generated from different representation-specific manifests.
     * @param documents source schemas
     * @param externalParents verified existing read-only type contracts
     * @param importedXsdTypes imported QName types
     * @return complete source batch and common projection context
     */
    public Compilation compileWithCommon(
            List<AIcdDefsCodegenSourceDocument> documents,
            Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> externalParents,
            Set<String> importedXsdTypes) {
        Objects.requireNonNull(documents, "documents");
        Objects.requireNonNull(externalParents, "externalParents");
        Objects.requireNonNull(importedXsdTypes, "importedXsdTypes");
        // The logical x-algites-schema-id is never a substitute for the
        // representation's published $id URL. Keep the latter with the source
        // document and provide it only for root annotations.
        Map<String, String> publishedSchemaUrls = new LinkedHashMap<>();
        for (var source : documents) {
            if (source.kind() == eu.algites.tool.codegen.defs.model.AIngSourceInputKind_1.XMLDEFS
                    || !(source.content() instanceof Map<?, ?> parsed)) continue;
            Object declared = parsed.get("$id");
            if (!(declared instanceof String url) || !url.startsWith("https://") || url.contains("#"))
                continue;
            String previous = publishedSchemaUrls.putIfAbsent(source.resource(), url);
            if (previous != null && !previous.equals(url))
                throw new IllegalArgumentException("Conflicting published URL for " + source.resource());
        }
        Map<String, String> sourceVersions = new LinkedHashMap<>();
        for (var source : documents) {
            if (!source.sourceVersion().isBlank()) {
                String previous = sourceVersions.putIfAbsent(source.resource(), source.sourceVersion());
                if (previous != null && !previous.equals(source.sourceVersion())) {
                    throw new IllegalArgumentException("Different filename versions for " + source.resource());
                }
            }
        }
        List<AIcDefsCodegenCanonicalSourceEmitter.Output> output = new ArrayList<>();
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.CommonProjection> shared = new LinkedHashMap<>();
        for (String target : List.of("java", "python")) {
            var naming = target.equals("java") ? javaNaming : pythonNaming;
            var composition = target.equals("java") ? javaCompositions : pythonCompositions;
            var model = new AIcDefsCodegenCanonicalPipeline(naming, contractValidator,
                    importedXsdTypes).process(documents, externalParents.keySet());
            var declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(model.types());
            Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> commonNames = new LinkedHashMap<>();
            if (!composition.containsKey("common_interface") || !composition.containsKey("common_interface_file"))
                throw new IllegalArgumentException("Missing required common output naming conventions for " + target);
            int ordinal = 0;
            for (AIcDefsCanonicalType type : declarations) {
                java.util.Set<String> sourcePaths = new java.util.LinkedHashSet<>();
                for (var bindings : type.sourceBindings().values()) {
                    for (var binding : bindings) sourcePaths.add(binding.sourceResource());
                }
                java.util.Set<String> selectedVersions = new java.util.LinkedHashSet<>();
                for (String path : sourcePaths) {
                    if (sourceVersions.containsKey(path)) selectedVersions.add(sourceVersions.get(path));
                }
                if (selectedVersions.size() > 1) {
                    throw new IllegalArgumentException("Different input filename versions "
                            + selectedVersions + " for " + type.identity() + " from " + sourcePaths);
                }
                String sourceVersion = selectedVersions.isEmpty() ? "" : selectedVersions.iterator().next();
                if (!sourceVersion.isBlank() && !type.schemaVersion().isBlank()
                        && !sourceVersion.equals(type.schemaVersion())) {
                    throw new IllegalArgumentException("Declared schema version " + type.schemaVersion()
                            + " disagrees with input filename version " + sourceVersion
                            + " for " + type.identity() + " from " + sourcePaths);
                }
                String version = !sourceVersion.isBlank() ? sourceVersion
                        : !type.schemaVersion().isBlank() ? type.schemaVersion()
                        : versions.getOrDefault(type.identity(), versions.get("*"));
                if (version == null || version.isBlank()) {
                    throw new IllegalArgumentException("Missing schema version for " + type.identity());
                }
                String kind = type.structure() instanceof AIcDefsCanonicalEnum ? "enum" : "interface";
                String typeName = naming.composedName(composition.get(kind), type.name(),
                        Map.of("version", version));
                String moduleName = naming.composedName(composition.get(kind + "_file"), type.name(),
                        Map.of("version", version));
                String commonType = type.structure() instanceof AIcDefsCanonicalEnum ? typeName
                        : naming.composedName(composition.get("common_interface"), type.name(),
                                Map.of("version", version));
                String commonModule = type.structure() instanceof AIcDefsCanonicalEnum ? moduleName
                        : naming.composedName(composition.get("common_interface_file"), type.name(),
                                Map.of("version", version));
                commonNames.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                        target.equals("java") ? commonType : "AIxUnused" + ordinal,
                        target.equals("python") ? commonType : "AIxUnused" + ordinal,
                        target.equals("python") ? commonModule : "aix_unused_" + ordinal));
                ordinal++;
            }
            // Only the schema-neutral read interface is an output. Source
            // technologies contribute independent metadata during coalescing;
            // they do not own additional Java/Python nominal interfaces.
            var commonRenderer = AIcDefsCodegenCanonicalSourceEmitter.commonOnly(
                    naming, commonNames, packageName, externalParents, publishedSchemaUrls);
            Map<String, AIcDefsCanonicalType> registry = new LinkedHashMap<>();
            for (var declaration : declarations) registry.put(declaration.identity(), declaration);
            String packagePath = packageName.replace('.', '/') + '/';
            for (var rendered : commonRenderer.render(model.types())) {
                if (!rendered.language().equals(target)) continue;
                var owner = registry.get(rendered.typeIdentity());
                if (owner == null || owner.structure() instanceof AIcDefsCanonicalList) continue;
                // Exactly one read-only type per canonical declaration.
                if (owner.structure() instanceof AIcDefsCanonicalEnum) {
                    output.add(rendered); // enums already have one shared value type
                    continue;
                }
                var namesForOwner = commonNames.get(owner.identity());
                String commonFile = packagePath + (target.equals("java")
                        ? namesForOwner.javaType() + ".java" : namesForOwner.pythonModule() + ".py");
                if (!commonFile.equals(rendered.relativePath())) continue;
                output.add(rendered);
                var previous = shared.putIfAbsent(rendered.relativePath(),
                        new AIcDefsCodegenCanonicalSourceEmitter.CommonProjection(
                                owner, Map.copyOf(registry), commonRenderer, target, rendered));
                if (previous != null) throw new IllegalArgumentException(
                        "Duplicate unified declaration inside one Defs manifest: " + commonFile);
            }
        }
        return new Compilation(List.copyOf(output), Map.copyOf(shared));
    }
}
