package eu.algites.tool.codegen.defs.impl.standard;


import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import eu.algites.lib.naming.convention.impl.standard.AIcNameConventionCatalog;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
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
import java.util.Set;
import java.util.HashMap;

/** Contract-only generator. Owns AIig interfaces and enums but never implementation output roots. */
public final class AIcSchemaContractBindingsGenerator {
    private final ObjectMapper mapper = new ObjectMapper()
            .enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private final AIcJsonSchemaReader reader = new AIcJsonSchemaReader();
    private record AIcdUnit(String schema, String pointer, String name, JsonNode node, JsonNode document) { }

    /** Generate only read contracts/enums. Implementation generation belongs to SdoCodegen. */
    public List<Map<String, String>> generateRepository(Path repository, Path manifestFile, boolean check) throws IOException {
        return generateManifest(repository, mapper.readTree(manifestFile.toFile()), check);
    }

    /** Executes a declarative batch without writing a temporary manifest to the product repository. */
    public List<Map<String, String>> generateManifest(Path repository, JsonNode manifest, boolean check) throws IOException {
        repository = repository.toAbsolutePath().normalize();
        Path intf = inside(repository, manifest.path("artifact").asText("."));
        boolean explicit = manifest.has("schema_inputs");
        boolean locConfigured = manifest.has("technology_output_naming_conventions");
        AIcNameConventionCatalog locSharedNames = null;
        if (locConfigured) {
            List<String> locCatalogFiles = new ArrayList<>();
            for (JsonNode locFile : manifest.path("naming_convention_files")) {
                String locName = locFile.asText();
                String locResolved = AIcNamingCatalogSource.normalize(locName);
                locCatalogFiles.add(locResolved.startsWith("resource:") ? locResolved
                        : inside(repository, locResolved).toString());
            }
            locSharedNames = AIcNamingCatalogCollector.load(locCatalogFiles);
        }
        Map<String, Path> outputRoots = new LinkedHashMap<>();
        Map<String, AIcNameConventionCatalog> catalogs = new LinkedHashMap<>();
        Map<String, AIiNameConventionCatalog> targetProfiles = new LinkedHashMap<>();
        Map<String, AIcNameConventionCatalog> sourceCatalogs = new LinkedHashMap<>();
        for (var entry : iterable(manifest.path("technology_outputs").fields()))
            outputRoots.put(entry.getKey(), inside(repository, entry.getValue().asText()));
        for (var entry : iterable(manifest.path("technology_naming_profiles").fields())) {
            Path file = inside(repository, entry.getValue().asText());
            catalogs.put(entry.getKey(), AIcNameConventionCatalog.load(file));
            targetProfiles.put(entry.getKey(), AIcNameConventionCatalog.load(file));
        }
        for (var entry : iterable(manifest.path("schema_input_naming_profiles").fields()))
            sourceCatalogs.put(entry.getKey(), AIcNameConventionCatalog.load(inside(repository, entry.getValue().asText())));
        if (locConfigured) {
            for (String locTechnology : outputRoots.keySet()) {
                catalogs.put(locTechnology, locSharedNames);
                String locMethods = manifest.path("generated_dataobject_method_naming_conventions")
                        .path(locTechnology).asText("");
                targetProfiles.put(locTechnology, locMethods.isBlank()
                        ? locSharedNames : locSharedNames.withGeneratedMethodProfile(locMethods));
            }
            for (var locEntry : iterable(manifest.path("schema_input_naming_conventions").fields()))
                sourceCatalogs.put(locEntry.getKey(), locSharedNames);
        }
        if (!locConfigured && !manifest.has("technology_naming_profiles"))
            throw new IllegalArgumentException("No explicit output naming catalog configured");
        if (explicit && !locConfigured) {
            for (String technology : outputRoots.keySet())
                if (!catalogs.containsKey(technology))
                    throw new IllegalArgumentException("Missing output naming profile for " + technology);
        }
        /* Recorded output ownership, never matching a naming profile alone,
         * determines which old files the generator is permitted to remove. */
        Path state = repository.resolve("build/run/schema-contract-bindings/generated-files.json");
        List<String> previouslyRecorded = Files.isRegularFile(state)
                ? mapper.readValue(state.toFile(), mapper.getTypeFactory()
                        .constructCollectionType(List.class, String.class)) : List.of();
        Set<Path> previouslyOwned = new java.util.HashSet<>();
        Set<Path> unrelatedOwned = new java.util.HashSet<>();
        for (String old : previouslyRecorded) {
            Path stale = inside(repository, old);
            if (!hasGeneratedRoot(stale))
                throw new IllegalArgumentException("Invalid ownership state: " + old);
            if (outputRoots.values().stream().anyMatch(stale::startsWith)) previouslyOwned.add(stale);
            else unrelatedOwned.add(stale);
        }
        if (manifest.path("clean_only").asBoolean()) {
            for (Path stale : previouslyOwned) Files.deleteIfExists(stale);
            Files.createDirectories(state.getParent());
            mapper.writerWithDefaultPrettyPrinter().writeValue(state.toFile(),
                    unrelatedOwned.stream().sorted().map(repository::relativize)
                            .map(AIcSchemaContractBindingsGenerator::portable).toList());
            return List.of();
        }
        Map<String, Path> rootBySchema = new LinkedHashMap<>();
        Map<String, String> profileBySchema = new LinkedHashMap<>();
        Map<String, String> kindBySchema = new LinkedHashMap<>();
        Map<String, Boolean> declaredIdentityBySchema = new LinkedHashMap<>();
        Map<String, JsonNode> overrides = new LinkedHashMap<>();
        for (JsonNode entry : manifest.path("bindings")) overrides.put(entry.required("schema").asText() + "#" + entry.path("pointer").asText(), entry);
        List<AIcdUnit> units = new ArrayList<>();
        List<Map.Entry<String, Path>> sourceRoots = new ArrayList<>();
        if (explicit) {
            for (JsonNode item : manifest.path("schema_inputs"))
                sourceRoots.add(Map.entry(item.required("kind").asText(), inside(repository, item.required("directory").asText())));
        } else {
            for (String kind : List.of("jsondefs", "yamldefs", "xmldefs"))
                sourceRoots.add(Map.entry(kind, intf.resolve("src/product/" + kind)));
        }
        int locExistingSourceDirectories = 0;
        for (var sourceInput : sourceRoots) {
            String kind = sourceInput.getKey();
            Path root = sourceInput.getValue();
            if (!Files.isDirectory(root)) {
                System.err.println("Defs Codegen: skipping configured " + kind
                        + " input directory (not found): " + root);
                continue;
            }
            locExistingSourceDirectories++;
            String suffix = switch (kind) {
                case "jsondefs" -> ".jsondef.schema.json";
                case "yamldefs" -> ".yamldef.schema.json";
                default -> ".xsd";
            };
            try (var paths = Files.walk(root)) {
                for (Path source : paths.filter(Files::isRegularFile).sorted().toList()) {
                    if (!source.getFileName().toString().endsWith(suffix)) continue;
                    String schema = portable(repository.relativize(source));
                    if (rootBySchema.putIfAbsent(schema, root) != null)
                        throw new IllegalArgumentException("Overlapping input roots for " + schema);
                    kindBySchema.put(schema, kind);
                    AIcNameConventionCatalog sourceCatalog = sourceCatalogs.get(kind);
                    if (sourceCatalog != null) {
                        String locRequired = locConfigured
                                ? manifest.path("schema_input_naming_conventions").path(kind).asText("") : null;
                        if (locConfigured && locRequired.isEmpty())
                            throw new IllegalArgumentException("Missing schema input naming convention for " + kind);
                        var named = sourceCatalog.recognizeFilename(source.getFileName().toString(),
                                locRequired == null ? null : Set.of(locRequired));
                        if (named == null) throw new IllegalArgumentException("Invalid schema filename: " + schema);
                        profileBySchema.put(schema, named.conventionName());
                        if (!manifest.path("allow_unversioned_schemas").asBoolean()
                                && !named.variables().containsKey("version"))
                            throw new IllegalArgumentException("Unversioned schema is not allowed: " + schema);
                    }
                    JsonNode document = kind.equals("xmldefs") ? mapper.createObjectNode() : mapper.readTree(source.toFile());
                    if (!kind.equals("xmldefs")) {
                        AIcNameConventionCatalog locCatalog = sourceCatalogs.get(kind);
                        if (locCatalog == null || !profileBySchema.containsKey(schema))
                            throw new IllegalArgumentException("Missing source naming catalog/profile for " + schema);
                        String locSourceProfile = profileBySchema.get(schema);
                        String locIdField = locCatalog.schemaMetadataField(locSourceProfile, "schema_source", "identifier");
                        declaredIdentityBySchema.put(schema, !locIdField.isBlank()
                                && !document.path(locIdField).asText("").isBlank());
                    }
                    String base = source.getFileName().toString().substring(0, source.getFileName().toString().length() - suffix.length()).replaceFirst("_[0-9]+$", "");
                    if (kind.equals("xmldefs")) {
                        units.add(new AIcdUnit(schema, "", base, mapper.createObjectNode(), document));
                        for (String locTypeName : new AIcXmlDefsFrontend().additionalNamedTypeNames(source))
                            units.add(new AIcdUnit(schema, "@type/" + locTypeName, locTypeName,
                                    mapper.createObjectNode(), document));
                    } else collect(document, "", base, schema, document, overrides, units);
                }
            }
        }
        if (locExistingSourceDirectories == 0) {
            System.err.println("Defs Codegen: no configured schema input directory exists; nothing to generate");
            return List.of();
        }
        /* Anonymous XML namespaces are document-local for generator symbol resolution.
         * Unqualified QNames from separate XSD documents do not identify one
         * interchangeable Java/Python type, even if the local names coincide.
         * Name-clashing XML projections receive a stable document-specific package;
         * common cross-format contracts retain their original package. */
        Map<String, Set<String>> locAnonymousXmlOwners = new LinkedHashMap<>();
        var locScopeFrontend = new AIcXmlDefsFrontend();
        for (AIcdUnit locUnit : units) {
            if (!"xmldefs".equals(kindBySchema.get(locUnit.schema()))) continue;
            Path locSource = inside(repository, locUnit.schema());
            if (targetProfiles.isEmpty()) throw new IllegalArgumentException("No output naming profile configured");
            var locLoad = new AIcdDefinitionLoadRequest(locSource, AInDefinitionSourceKind.XMLDEFS,
                    targetProfiles.values().iterator().next());
            String locQName = locUnit.pointer().startsWith("@type/")
                    ? "{" + locScopeFrontend.schemaNamespace(locLoad) + "}" + locUnit.pointer().substring(6)
                    : locScopeFrontend.rootTypeQName(locLoad);
            if (locQName.startsWith("{}"))
                locAnonymousXmlOwners.computeIfAbsent("type#" + locQName, key -> new java.util.LinkedHashSet<>())
                        .add(locUnit.schema());
            if (locUnit.pointer().isEmpty()) {
                for (var locElement : locScopeFrontend.globalElementDeclarations(locLoad)) {
                    if (locElement.namespace().isEmpty())
                        locAnonymousXmlOwners.computeIfAbsent("element#" + locElement.qName(),
                                key -> new java.util.LinkedHashSet<>()).add(locUnit.schema());
                }
            }
        }
        Set<String> locScopedXmlDocuments = new java.util.HashSet<>();
        for (var locOwners : locAnonymousXmlOwners.values())
            if (locOwners.size() > 1) locScopedXmlDocuments.addAll(locOwners);
        for (String key : overrides.keySet()) {
            if (units.stream().noneMatch(unit -> (unit.schema + "#" + unit.pointer).equals(key))) {
                throw new IllegalArgumentException("Binding override no longer identifies a schema object: " + key);
            }
        }
        Map<Path, String> pending = new TreeMap<>();
        List<Map<String, String>> result = new ArrayList<>();
        Map<String, List<AIcdCodeGenerationRequest>> requests = new LinkedHashMap<>();
        Map<String, AIcdCodeGenerationRequest> unitRequests = new LinkedHashMap<>();
        Map<String, List<List<AIcdUnit>>> relations = new LinkedHashMap<>();
        Map<String, AIcdUnit> unitIndex = new LinkedHashMap<>();
        for (AIcdUnit unit : units) unitIndex.put(unit.schema + "#" + unit.pointer, unit);
        for (AIcdUnit unit : units) {
            Path source = inside(repository, unit.schema);
            String sourceKind = kindBySchema.get(unit.schema);
            Path schemaRoot = rootBySchema.get(unit.schema);
            String packageName = portable(schemaRoot.relativize(source.getParent())).replace('/', '.');
            if (!packageName.matches("[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)*")) {
                throw new IllegalArgumentException("Schema must have a legal package path: " + unit.schema);
            }
            ObjectNode projection = ((ObjectNode) unit.node).deepCopy();
            if (!sourceKind.equals("xmldefs")) {
                if (unit.document.has("$defs")) projection.set("$defs", unit.document.get("$defs"));
                AIcNameConventionCatalog locSourceCatalog = sourceCatalogs.get(sourceKind);
                if (locSourceCatalog == null || !profileBySchema.containsKey(unit.schema))
                    throw new IllegalArgumentException("Missing source naming catalog/profile for " + unit.schema);
                String locSourceProfile = profileBySchema.get(unit.schema);
                String locIdKey = locSourceCatalog != null && !locSourceProfile.isBlank()
                        ? locSourceCatalog.schemaMetadataField(locSourceProfile, "schema_source", "identifier") : "";
                String locVersionKey = locSourceCatalog != null && !locSourceProfile.isBlank()
                        ? locSourceCatalog.schemaMetadataField(locSourceProfile, "schema_source", "version") : "";
                String locUrlKey = locSourceCatalog != null && !locSourceProfile.isBlank()
                        ? locSourceCatalog.schemaMetadataField(locSourceProfile, "schema_source", "url") : "";
                String locDeclaredId = locIdKey.isEmpty() ? "" : unit.document.path(locIdKey).asText("");
                if (locDeclaredId.isBlank()) locDeclaredId = unit.name;
                projection.put("x-jsondefs-id", locDeclaredId + (unit.pointer.isEmpty() ? "" : "#" + unit.pointer));
                if (!locVersionKey.isEmpty() && unit.document.has(locVersionKey))
                    projection.set("x-jsondefs-version", unit.document.get(locVersionKey));
                if (!locUrlKey.isEmpty() && unit.document.has(locUrlKey))
                    projection.set("$id", unit.document.get(locUrlKey));
                projection.put("x-jsondefs-name", unit.name);
            }
            List<AIcdUnit> parentUnits = sourceKind.equals("xmldefs") ? List.of() : parentUnits(unit, unitIndex, repository);
            for (JsonNode language : manifest.required("languages")) {
                String targetText = language.asText();
                AInCodeGenerationTarget target = switch (targetText) {
                    case "python" -> AInCodeGenerationTarget.PYTHON;
                    case "java" -> AInCodeGenerationTarget.JAVA;
                    default -> throw new IllegalArgumentException("Unsupported target: " + targetText);
                };
                AIiNameConventionCatalog baseProfile = targetProfiles.get(targetText);
                if (baseProfile == null)
                    throw new IllegalArgumentException("No output naming profile configured for " + targetText);
                var sourceType = switch (sourceKind) {
                    case "yamldefs" -> AInDefinitionSourceKind.YAMLDEFS;
                    case "xmldefs" -> AInDefinitionSourceKind.XMLDEFS;
                    default -> AInDefinitionSourceKind.JSONDEFS;
                };
                var load = new AIcdDefinitionLoadRequest(source, sourceType, baseProfile);
                var loaded = sourceKind.equals("xmldefs")
                        ? (unit.pointer().startsWith("@type/")
                            ? new AIcXmlDefsFrontend().loadNamedType(load, unit.pointer().substring(6))
                            : new AIcXmlDefsFrontend().load(load))
                        : reader.read(projection, load, load.sourceKind(), "x-jsondefs-id", "x-jsondefs-version", "x-jsondefs-name", "$id");
                var definition = new AIcdCanonicalDefinition(loaded.identity(), loaded.version(), loaded.logicalName(), loaded.sourceKind(), unit.schema + (unit.pointer.isEmpty() ? "" : "#" + unit.pointer), loaded.description(), loaded.dataType(), loaded.enumValues(), loaded.title(), loaded.schemaUrl(),
                        sourceKind.equals("xmldefs") ? "" : outputMetadataField(baseProfile, sourceCatalogs.get(sourceKind), sourceKind,
                                profileBySchema.get(unit.schema), "url"),
                        sourceKind.equals("xmldefs") ? "" : outputMetadataField(baseProfile, sourceCatalogs.get(sourceKind), sourceKind,
                                profileBySchema.get(unit.schema), "identifier"),
                        sourceKind.equals("xmldefs") ? "" : outputMetadataField(baseProfile, sourceCatalogs.get(sourceKind), sourceKind,
                                profileBySchema.get(unit.schema), "version"),
                        sourceKind.equals("xmldefs") ? null : sourceAnnotationField(baseProfile, sourceCatalogs.get(sourceKind), sourceKind,
                                profileBySchema.get(unit.schema), "url"),
                        sourceKind.equals("xmldefs") ? null : sourceAnnotationField(baseProfile, sourceCatalogs.get(sourceKind), sourceKind,
                                profileBySchema.get(unit.schema), "identifier"),
                        sourceKind.equals("xmldefs") ? null : sourceAnnotationField(baseProfile, sourceCatalogs.get(sourceKind), sourceKind,
                                profileBySchema.get(unit.schema), "version"));
                String locXmlTypeQName = sourceKind.equals("xmldefs")
                        ? (unit.pointer().startsWith("@type/")
                            ? "{" + new AIcXmlDefsFrontend().schemaNamespace(load) + "}" + unit.pointer().substring(6)
                            : new AIcXmlDefsFrontend().rootTypeQName(load)) : null;
                if (locXmlTypeQName != null && locXmlTypeQName.endsWith("}__root__")) locXmlTypeQName = null;
                String locSourceRole = sourceKind.equals("xmldefs") ? "xmldefs_type" : sourceKind;
                List<String> locEnabledRoles = new ArrayList<>();
                if (locConfigured) {
                    JsonNode locMappings = manifest.path("technology_output_naming_conventions").path(targetText);
                    if (locMappings.hasNonNull("common")) locEnabledRoles.add("common");
                    if (locMappings.hasNonNull(locSourceRole)) locEnabledRoles.add(locSourceRole);
                } else locEnabledRoles.add("");
                for (String locRole : locEnabledRoles) {
                    String locSelectedId = locConfigured
                            ? manifest.path("technology_output_naming_conventions").path(targetText)
                                    .path(locRole).asText() : "";
                    AIiNameConventionCatalog profile = baseProfile;
                    if (locConfigured) {
                        var locNames = new java.util.EnumMap<AInDefsNameRole, String>(AInDefsNameRole.class);
                        for (AInDefsNameRole locNameRole : List.of(AInDefsNameRole.INTERFACE_TYPE,
                                AInDefsNameRole.INTERFACE_TYPE_FILE_STEM,
                                AInDefsNameRole.DATA_TYPE, AInDefsNameRole.DATA_TYPE_FILE_STEM))
                            locNames.put(locNameRole, locSelectedId);
                        String locElementConvention = manifest.path("technology_output_naming_conventions")
                                .path(targetText).path("xmldefs_element").asText("");
                        if (!locElementConvention.isEmpty()) {
                            locNames.put(AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE, locElementConvention);
                            locNames.put(AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM, locElementConvention);
                        }
                        String locNamespaceConvention = manifest.path("technology_output_naming_conventions")
                                .path(targetText).path("xmldefs_namespace").asText("");
                        if (!locNamespaceConvention.isBlank()) {
                            locNames.put(AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE, locNamespaceConvention);
                            locNames.put(AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM, locNamespaceConvention);
                        }
                        String locEnumConvention = manifest.path("technology_enum_output_naming_conventions")
                                .path(targetText).asText("");
                        if (locEnumConvention.isEmpty()) locEnumConvention = locSelectedId;
                        locNames.put(AInDefsNameRole.ENUM_TYPE, locEnumConvention);
                        locNames.put(AInDefsNameRole.ENUM_TYPE_FILE_STEM, locEnumConvention);
                        profile = new AIcSelectedNamingCatalog(baseProfile, locNames);
                    }
                    String locOutputPackage = packageName;
                    if (sourceKind.equals("xmldefs") && !locRole.equals("common")
                            && locScopedXmlDocuments.contains(unit.schema())) {
                        String locDocument = source.getFileName().toString().replaceFirst("\\.xsd$", "")
                                .replaceAll("[^A-Za-z0-9_]", "_").toLowerCase(java.util.Locale.ROOT);
                        locOutputPackage += ".xmlschema_" + locDocument;
                    }
                    var request = new AIcdCodeGenerationRequest(definition, target, locOutputPackage, profile,
                            locXmlTypeQName, locSelectedId, locRole);
                var preview = new AIcSchemaContractInterfaceGenerator().generate(request);
                String outputKey = targetText + "#" + preview.relativePath();
                requests.computeIfAbsent(outputKey, key -> new ArrayList<>()).add(request);
                unitRequests.put(targetText + "#" + locRole + "#" + unit.schema + "#" + unit.pointer, request);
                relations.computeIfAbsent(outputKey, key -> new ArrayList<>()).add(parentUnits);
                result.add(Map.of("schema", unit.schema, "pointer", unit.pointer, "language", targetText, "type", preview.typeName(),
                    "path", portable(repository.relativize(outputRoots.getOrDefault(targetText,
                        intf.resolve("src/product/" + targetText + ".gen")).resolve(preview.relativePath())))));
                }
            }
        }
        /* Resolve named XML extension bases against the complete emitted-type index.
         * A base that is not emitted cannot be represented by Java/Python inheritance:
         * silently flattening it would destroy the XSD type hierarchy. */
        Map<String, AIcdCodeGenerationRequest> locXmlTypeRequests = new LinkedHashMap<>();
        for (var locUnitRequest : unitRequests.entrySet()) {
            var locCandidate = locUnitRequest.getValue();
            if (locCandidate.xmlTypeQName() == null) continue;
            String locKey = locCandidate.target().name() + "#" + locCandidate.contractRole() + "#"
                    + (locCandidate.xmlTypeQName().startsWith("{}") ? locCandidate.packageName() + "#" : "")
                    + locCandidate.xmlTypeQName();
            var locPrevious = locXmlTypeRequests.putIfAbsent(locKey, locCandidate);
            if (locPrevious != null && !locPrevious.packageName().equals(locCandidate.packageName()))
                throw new IllegalArgumentException("Ambiguous XML named type " + locCandidate.xmlTypeQName());
        }
        /* XML-only namespace contracts are resolved before rendering their type-safe wildcard getters. */
        Map<String, AIcdCodeGenerationRequest> locNamespaceOwners = new LinkedHashMap<>();
        for (var locItem : unitRequests.entrySet()) {
            AIcdCodeGenerationRequest locRequest = locItem.getValue();
            if (!locItem.getKey().contains("#xmldefs_type#") && !locItem.getKey().contains("##"))
                continue;
            if (locRequest.definition().sourceKind() != AInDefinitionSourceKind.XMLDEFS
                    || locRequest.contractRole().equals("common")) continue;
            String locLanguage = locRequest.target() == AInCodeGenerationTarget.JAVA ? "java" : "python";
            if (locRequest.xmlTypeQName() != null) {
                String locNamespace = locRequest.xmlTypeQName().substring(1, locRequest.xmlTypeQName().indexOf('}'));
                locNamespaceOwners.putIfAbsent(xmlNamespaceOwnerKey(locLanguage, locNamespace,
                        locRequest, locScopedXmlDocuments), locRequest);
            }
            for (AIcdPropertyDefinition locField : locRequest.definition().dataType().properties()) {
                if (locField.xmlField() == null || locField.xmlField().wildcardNamespace().isBlank()) continue;
                String locNamespace = AIcXmlNamespaceContracts.selectedNamespace(
                        locField.xmlField().wildcardNamespace(), locField.xmlField().namespace());
                if (locNamespace != null) locNamespaceOwners.putIfAbsent(xmlNamespaceOwnerKey(locLanguage, locNamespace,
                        locRequest, locScopedXmlDocuments), locRequest);
            }
        }
        for (var representations : requests.values()) {
            var first = representations.get(0);
            long identityCount = representations.stream().map(r -> canonicalIdentity(
                    r.definition(), r.packageName(), unitIndex, declaredIdentityBySchema)).distinct().count();
            boolean locIsCommonRole = first.contractRole().equals("common");
            if (locIsCommonRole) {
                var locIdentities = representations.stream().map(r ->
                        AIcCommonContractProjection.canonicalIdentity(r.definition(), r.packageName(),
                            canonicalIdentity(r.definition(), r.packageName(), unitIndex, declaredIdentityBySchema))).toList();
                var locExplicit = locIdentities.stream().filter(aIdentity ->
                        !((List<?>) aIdentity).get(0).equals("implicit")).distinct().toList();
                identityCount = locExplicit.isEmpty() ? locIdentities.stream().distinct().count() : locExplicit.size();
                if (!locExplicit.isEmpty() && locIdentities.stream().anyMatch(aIdentity ->
                        ((List<?>) aIdentity).get(0).equals("implicit"))) {
                    String locExplicitId = String.valueOf(((List<?>) locExplicit.get(0)).get(1));
                    String locTail = ":" + first.definition().logicalName() + ":" + first.definition().version();
                    if (!locExplicitId.startsWith("urn:algites:") || !locExplicitId.endsWith(locTail))
                        identityCount = 2;
                }
            }
            if (identityCount != 1)
                throw new IllegalArgumentException("Canonical identity collision for one generated output: "
                    + representations.stream().map(r -> r.definition().identity() + " (" + r.definition().sourceResource() + ")").toList());
            var merged = locIsCommonRole && representations.size() > 1
                    ? AIcCommonContractProjection.merge(representations.stream()
                        .map(AIcdCodeGenerationRequest::definition).toList())
                    : AIcCanonicalDefinitionMerger.AIcMergeStrict(representations.stream()
                        .map(AIcdCodeGenerationRequest::definition).toList(), repository);
            String targetText = first.target() == AInCodeGenerationTarget.PYTHON ? "python" : "java";
            String outputKey = targetText + "#" + new AIcSchemaContractInterfaceGenerator().generate(first).relativePath();
            List<List<AIcdUnit>> linked = relations.get(outputKey);
            List<String> expectedParents = new ArrayList<>();
            for (AIcdUnit parent : linked.get(0)) {
                AIcdCodeGenerationRequest request = unitRequests.get(targetText + "#" + first.contractRole()
                        + "#" + parent.schema() + "#" + parent.pointer());
                if (request == null) throw new IllegalArgumentException("allOf parent has no generated contract: " + parent.schema());
                expectedParents.add(request.packageName() + "." + new AIcSchemaContractInterfaceGenerator().generate(request).typeName());
            }
            boolean locSharedParents = true;
            for (List<AIcdUnit> representationParents : linked) {
                List<String> actualParents = new ArrayList<>();
                for (AIcdUnit parent : representationParents) {
                    AIcdCodeGenerationRequest request = unitRequests.get(targetText + "#" + first.contractRole()
                            + "#" + parent.schema() + "#" + parent.pointer());
                    if (request == null) throw new IllegalArgumentException("allOf parent has no generated contract: " + parent.schema());
                    actualParents.add(request.packageName() + "." + new AIcSchemaContractInterfaceGenerator().generate(request).typeName());
                }
                if (!expectedParents.equals(actualParents)) locSharedParents = false;
            }
            if (!locSharedParents && !locIsCommonRole)
                throw new IllegalArgumentException("Conflicting allOf parents across schema representations");
            List<AIcdCodeGenerationRequest> inheritedRequests = new ArrayList<>();
            for (AIcdUnit inheritedUnit : locSharedParents ? linked.get(0) : List.<AIcdUnit>of()) {
                AIcdCodeGenerationRequest inherited = unitRequests.get(targetText + "#" + first.contractRole()
                        + "#" + inheritedUnit.schema() + "#" + inheritedUnit.pointer());
                if (inherited == null) {
                    throw new IllegalArgumentException("allOf parent has no generated contract in role "
                            + first.contractRole() + ": " + inheritedUnit.schema() + "#" + inheritedUnit.pointer());
                }
                inheritedRequests.add(inherited);
            }
            String parentName = null, parentModule = null;
            List<String> additionalParents = new ArrayList<>();
            Map<String, AIcdPropertyDefinition> inheritedFields = new LinkedHashMap<>();
            for (AIcdCodeGenerationRequest inherited : inheritedRequests) {
                if (merged.dataType().kind() != AInDataTypeKind.OBJECT
                        || inherited.definition().dataType().kind() != AInDataTypeKind.OBJECT) {
                    throw new IllegalArgumentException("allOf inheritance must connect object contracts");
                }
                for (AIcdPropertyDefinition field : inherited.definition().dataType().properties()) {
                    AIcdPropertyDefinition existing = inheritedFields.putIfAbsent(field.sourceName(), field);
                    if (existing != null && !fieldShape(existing).equals(fieldShape(field))) {
                        throw new IllegalArgumentException("Conflicting fields among allOf parents: " + field.sourceName());
                    }
                }
                var inheritedSource = new AIcSchemaContractInterfaceGenerator().generate(inherited);
                String inheritedModule = inherited.packageName();
                if (first.target() == AInCodeGenerationTarget.PYTHON) {
                    inheritedModule += "." + Path.of(inheritedSource.relativePath()).getFileName()
                            .toString().replaceFirst("\\.py$", "");
                }
                if (parentName == null) {
                    parentName = inheritedSource.typeName();
                    parentModule = inheritedModule;
                } else {
                    additionalParents.add(first.target() == AInCodeGenerationTarget.PYTHON
                            ? inheritedSource.typeName() : inheritedModule + "." + inheritedSource.typeName());
                }
            }
            if (!inheritedRequests.isEmpty()) {
                List<AIcdPropertyDefinition> ownFields = new ArrayList<>();
                for (AIcdPropertyDefinition field : merged.dataType().properties()) {
                    AIcdPropertyDefinition previous = inheritedFields.get(field.sourceName());
                    if (previous == null || !fieldShape(previous).equals(fieldShape(field))) {
                        if (previous != null && !fieldNarrows(previous, field)) {
                            throw new IllegalArgumentException("Conflicting inherited field: " + field.sourceName());
                        }
                        ownFields.add(field);
                    }
                }
                merged = new AIcdCanonicalDefinition(merged.identity(), merged.version(), merged.logicalName(),
                        merged.sourceKind(), merged.sourceResource(), merged.description(),
                        merged.dataType().withProperties(ownFields), merged.enumValues(), merged.title());
            }
            if (first.xmlTypeQName() != null) {
                var locXmlOrigin = unitIndex.get(first.definition().sourceResource() + "#");
                if (locXmlOrigin == null) locXmlOrigin = unitIndex.get(first.definition().sourceResource());
                if (locXmlOrigin == null)
                    throw new IllegalArgumentException("Unknown XSD source " + first.definition().sourceResource());
                var locXmlLoad = new AIcdDefinitionLoadRequest(inside(repository, locXmlOrigin.schema()),
                        AInDefinitionSourceKind.XMLDEFS, first.namingProfile());
                String locXmlParentQName = locXmlOrigin.pointer().startsWith("@type/")
                        ? new AIcXmlDefsFrontend().namedTypeExtensionBaseQName(
                                locXmlLoad, locXmlOrigin.pointer().substring(6))
                        : new AIcXmlDefsFrontend().rootExtensionBaseQName(locXmlLoad);
                if (locXmlParentQName != null) {
                    var locXmlParent = locXmlTypeRequests.get(first.target().name() + "#" + first.contractRole() + "#"
                            + (locXmlParentQName.startsWith("{}") ? first.packageName() + "#" : "")
                            + locXmlParentQName);
                    if (locXmlParent == null || locXmlParent == first)
                        throw new IllegalArgumentException("XML extension base has no independently emitted contract: "
                                + locXmlParentQName + " for " + first.xmlTypeQName());
                    if (merged.dataType().kind() != AInDataTypeKind.OBJECT
                            || locXmlParent.definition().dataType().kind() != AInDataTypeKind.OBJECT)
                        throw new IllegalArgumentException("XML extension requires object contracts");
                    Map<String, AIcdPropertyDefinition> locInheritedFields = new LinkedHashMap<>();
                    for (var locField : locXmlParent.definition().dataType().properties())
                        locInheritedFields.put(locField.sourceName(), locField);
                    List<AIcdPropertyDefinition> locOwnFields = new ArrayList<>();
                    for (var locField : merged.dataType().properties()) {
                        var locInherited = locInheritedFields.get(locField.sourceName());
                        if (locInherited == null) locOwnFields.add(locField);
                        else if (!fieldShape(locInherited).equals(fieldShape(locField)))
                            throw new IllegalArgumentException("Incompatible inherited XML extension field: "
                                    + locField.sourceName());
                    }
                    merged = new AIcdCanonicalDefinition(merged.identity(), merged.version(), merged.logicalName(), merged.sourceKind(), merged.sourceResource(), merged.description(), eu.algites.tool.codegen.defs.AIcdDataType.object(locOwnFields), merged.enumValues(), merged.title());
                    var locParentPreview = new AIcSchemaContractInterfaceGenerator().generate(locXmlParent);
                    parentName = locParentPreview.typeName();
                    parentModule = locXmlParent.packageName();
                    if (first.target() == AInCodeGenerationTarget.PYTHON)
                        parentModule += "." + Path.of(locParentPreview.relativePath()).getFileName().toString()
                                .replaceFirst("\\.py$", "");
                }
            }
            int locIndex = 0;
            for (var pair : new AIcSchemaContractInterfaceGenerator().generateSources(
                    new AIcdCodeGenerationRequest(merged, first.target(), first.packageName(),
                            first.namingProfile(), first.xmlTypeQName(), first.namingConvention(), first.contractRole()),
                    parentName, parentModule)) {
                eu.algites.tool.codegen.defs.AIcdDefinitionReference locChoiceReference = null;
                if (merged.sourceKind() != AInDefinitionSourceKind.XMLDEFS
                        && merged.dataType() != null && (merged.dataType().kind() == eu.algites.tool.codegen.defs.AInDataTypeKind.ONE_OF
                        || merged.dataType().kind() == eu.algites.tool.codegen.defs.AInDataTypeKind.ANY_OF) && locIndex > 0) {
                    var locAlternative = merged.dataType().alternatives().get(locIndex - 1);
                    if (locAlternative.kind() == eu.algites.tool.codegen.defs.AInDataTypeKind.REFERENCE)
                        locChoiceReference = locAlternative.reference();
                }
                String locSource = pair.source();
                if (!additionalParents.isEmpty()) {
                    if (targetText.equals("java")) {
                        String locDeclaration = "public interface " + pair.typeName() + " extends ";
                        int locStart = locSource.indexOf(locDeclaration);
                        int locEnd = locSource.indexOf(" {", locStart);
                        if (locStart < 0 || locEnd < 0) throw new IllegalStateException("Missing Java interface declaration");
                        locSource = locSource.substring(0, locEnd) + ", "
                                + String.join(", ", additionalParents) + locSource.substring(locEnd);
                    } else {
                        for (int locExtra = 0; locExtra < additionalParents.size(); locExtra++) {
                            AIcdCodeGenerationRequest locInherited = inheritedRequests.get(locExtra + 1);
                            var locPreview = new AIcSchemaContractInterfaceGenerator().generate(locInherited);
                            String locStem = Path.of(locPreview.relativePath()).getFileName()
                                    .toString().replaceFirst("\\.py$", "");
                            locSource = locSource.replace("from __future__ import annotations\n",
                                    "from __future__ import annotations\nfrom " + locInherited.packageName() + "."
                                            + locStem + " import " + locPreview.typeName() + "\n");
                        }
                        String locDeclaration = "class " + pair.typeName() + "(";
                        int locStart = locSource.indexOf(locDeclaration);
                        int locEnd = locSource.indexOf("):", locStart);
                        if (locStart < 0 || locEnd < 0) throw new IllegalStateException("Missing Python class declaration");
                        locSource = locSource.substring(0, locEnd) + ", "
                                + String.join(", ", additionalParents) + locSource.substring(locEnd);
                    }
                }
                if (locConfigured && !first.contractRole().equals("common")
                        && (merged.dataType().kind() == AInDataTypeKind.OBJECT
                            || merged.dataType().kind() == AInDataTypeKind.ONE_OF
                            || merged.dataType().kind() == AInDataTypeKind.ANY_OF
                            || merged.dataType().kind() == AInDataTypeKind.REFERENCE)
                        && locIndex == 0) {
                    AIcdUnit locOrigin = unitIndex.get(first.definition().sourceResource());
                    if (locOrigin == null) locOrigin = unitIndex.get(first.definition().sourceResource() + "#");
                    if (locOrigin != null) {
                        var locCommon = unitRequests.get(targetText + "#common#" + locOrigin.schema()
                                + "#" + locOrigin.pointer());
                        if (locCommon != null) {
                            var locCommonPreview = new AIcSchemaContractInterfaceGenerator().generate(locCommon);
                            if (targetText.equals("java")) {
                                String locDeclaration = "public interface " + pair.typeName() + " extends ";
                                if (merged.dataType().kind() == AInDataTypeKind.OBJECT
                                        || merged.dataType().kind() == AInDataTypeKind.REFERENCE) {
                                    locSource = locSource.replace(locDeclaration, locDeclaration
                                            + locCommon.packageName() + "." + locCommonPreview.typeName() + ", ");
                                } else {
                                    String locChoiceDeclaration = "public sealed interface " + pair.typeName() + " permits ";
                                    locSource = locSource.replace(locChoiceDeclaration,
                                            "public sealed interface " + pair.typeName() + " extends "
                                            + locCommon.packageName() + "." + locCommonPreview.typeName()
                                            + " permits ");
                                }
                            } else {
                                String locStem = Path.of(locCommonPreview.relativePath()).getFileName()
                                        .toString().replaceFirst("\\.py$", "");
                                locSource = locSource.replace("from __future__ import annotations\n",
                                        "from __future__ import annotations\nfrom " + locCommon.packageName()
                                                + "." + locStem + " import " + locCommonPreview.typeName() + "\n");
                                String locDeclaration = "class " + pair.typeName() + "(";
                                if (locSource.contains(locDeclaration)) {
                                    locSource = locSource.replace(locDeclaration,
                                            locDeclaration + locCommonPreview.typeName() + ", ");
                                } else {
                                    String locChoiceDeclaration = "class " + pair.typeName() + ":";
                                    locSource = locSource.replace(locChoiceDeclaration,
                                            "class " + pair.typeName() + "(" + locCommonPreview.typeName() + "):");
                                }
                            }
                        }
                    }
                }
                locSource = qualifyReferences(locSource, first, requests, true, locChoiceReference);
                if (first.xmlTypeQName() != null && !first.contractRole().equals("common")
                        && locIndex == 0 && (merged.dataType().kind() == AInDataTypeKind.OBJECT
                        || merged.dataType().kind() == AInDataTypeKind.ONE_OF
                        || merged.dataType().kind() == AInDataTypeKind.ANY_OF)) {
                    String locNamespace = first.xmlTypeQName().substring(1, first.xmlTypeQName().indexOf('}'));
                    Map<String, String> locWildcardFields = new LinkedHashMap<>();
                    for (AIcdPropertyDefinition locField : merged.dataType().properties()) {
                        var locXml = locField.xmlField();
                        if (locXml == null || locXml.wildcardNamespace().isBlank()) continue;
                        String locSelected = AIcXmlNamespaceContracts.selectedNamespace(
                                locXml.wildcardNamespace(), locXml.namespace());
                        String locQualified = locSelected == null
                                ? targetText.equals("java")
                                        ? "eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject"
                                        : "eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object.AIiXmlDataObject"
                                : namespaceType(locNamespaceOwners, targetText, locSelected, first, locScopedXmlDocuments);
                        locWildcardFields.put(locField.sourceName(), locQualified);
                    }
                    locSource = AIcXmlNamespaceContracts.decorate(locSource, first,
                            namespaceType(locNamespaceOwners, targetText, locNamespace, first, locScopedXmlDocuments), locWildcardFields);
                }
                add(pending, outputRoots.getOrDefault(targetText, intf.resolve("src/product/" + targetText + ".gen"))
                        .resolve(pair.relativePath()), locSource);
                locIndex++;
            }
        }
        /* Global XML element declarations are indexed independently from named XSD
         * content types. This preserves substitution across source files and modules. */
        var locXmlGenerator = new AIcXmlElementContractGenerator();
        var locXmlFrontend = new AIcXmlDefsFrontend();
        for (JsonNode locLanguage : manifest.required("languages")) {
            String locTarget = locLanguage.asText();
            if (locConfigured && !manifest.path("technology_output_naming_conventions").path(locTarget)
                    .hasNonNull("xmldefs_element")) continue;
            Map<String, String> locTypes = new LinkedHashMap<>();
            Map<String, String> locElements = new LinkedHashMap<>();
            Set<String> locValueTypes = new java.util.HashSet<>();
            Map<String, Map<String, String>> locDocumentTypes = new LinkedHashMap<>();
            Map<String, Map<String, String>> locDocumentElements = new LinkedHashMap<>();
            Map<String, Set<String>> locDocumentValueTypes = new LinkedHashMap<>();
            record AIcdElementWork(String source, AIcdCodeGenerationRequest request,
                                   eu.algites.tool.codegen.defs.AIcdXmlElementDeclaration element) { }
            List<AIcdElementWork> locWork = new ArrayList<>();
            for (AIcdUnit locUnit : units) {
                if (!kindBySchema.get(locUnit.schema()).equals("xmldefs")) continue;
                AIcdCodeGenerationRequest locRequest = unitRequests.get(
                        locTarget + "#" + (locConfigured ? "xmldefs_type" : "") + "#" + locUnit.schema() + "#" + locUnit.pointer());
                if (locRequest == null) continue;
                var locLoad = new AIcdDefinitionLoadRequest(inside(repository, locUnit.schema()),
                        AInDefinitionSourceKind.XMLDEFS, locRequest.namingProfile());
                String locRootQName = locRequest.xmlTypeQName() == null
                        ? locXmlFrontend.rootTypeQName(locLoad) : locRequest.xmlTypeQName();
                if (locRequest.definition().dataType().kind() == AInDataTypeKind.OBJECT
                        || locRequest.definition().dataType().kind() == AInDataTypeKind.ENUM
                        || locRequest.definition().dataType().kind() == AInDataTypeKind.ONE_OF
                        || locRequest.definition().dataType().kind() == AInDataTypeKind.ANY_OF) {
                    if (locRequest.definition().dataType().kind() == AInDataTypeKind.ENUM
                            || locRequest.definition().dataType().kind() == AInDataTypeKind.ONE_OF
                            || locRequest.definition().dataType().kind() == AInDataTypeKind.ANY_OF)
                        if (locRootQName.startsWith("{}"))
                            locDocumentValueTypes.computeIfAbsent(locUnit.schema(), key -> new java.util.HashSet<>())
                                    .add(locRootQName);
                        else locValueTypes.add(locRootQName);
                    var locPreview = new AIcSchemaContractInterfaceGenerator().generate(locRequest);
                    String locQualified = locRequest.packageName() + "."
                            + (locTarget.equals("python")
                                ? Path.of(locPreview.relativePath()).getFileName().toString().replaceFirst("\\.py$", "") + "."
                                : "") + locPreview.typeName();
                    Map<String, String> locIndex = locRootQName.startsWith("{}")
                            ? locDocumentTypes.computeIfAbsent(locUnit.schema(), key -> new LinkedHashMap<>())
                            : locTypes;
                    String locPrevious = locIndex.putIfAbsent(locRootQName, locQualified);
                    if (locPrevious != null && !locPrevious.equals(locQualified))
                        throw new IllegalArgumentException("Duplicate XML content type " + locRootQName
                                + " in " + locUnit.schema());
                }
                if (!locUnit.pointer().isEmpty()) continue;
                for (var locElement : locXmlFrontend.globalElementDeclarations(locLoad)) {
                    var locNames = new AIcGenerationNames();
                    String locName = locNames.referenceTypeName(AIcXmlElementContractGenerator.xmlIdentifier(locElement.localName()), locRequest.definition().version(),
                            locRequest.namingProfile(), AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE);
                    String locStem = locNames.referenceTypeName(AIcXmlElementContractGenerator.xmlIdentifier(locElement.localName()), locRequest.definition().version(),
                            locRequest.namingProfile(), AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM);
                    String locQualified = locRequest.packageName() + "."
                            + (locTarget.equals("python") ? locStem + "." : "") + locName;
                    Map<String, String> locIndex = locElement.namespace().isEmpty()
                            ? locDocumentElements.computeIfAbsent(locUnit.schema(), key -> new LinkedHashMap<>())
                            : locElements;
                    if (locIndex.putIfAbsent(locElement.qName(), locQualified) != null)
                        throw new IllegalArgumentException("Duplicate XML global element " + locElement.qName()
                                + " in " + locUnit.schema());
                    locWork.add(new AIcdElementWork(locUnit.schema(), locRequest, locElement));
                }
            }
            for (AIcdElementWork locEntry : locWork) {
                Map<String, String> locResolvedTypes = new LinkedHashMap<>(locTypes);
                locResolvedTypes.putAll(locDocumentTypes.getOrDefault(locEntry.source(), Map.of()));
                Map<String, String> locResolvedElements = new LinkedHashMap<>(locElements);
                locResolvedElements.putAll(locDocumentElements.getOrDefault(locEntry.source(), Map.of()));
                Set<String> locResolvedValueTypes = new java.util.HashSet<>(locValueTypes);
                locResolvedValueTypes.addAll(locDocumentValueTypes.getOrDefault(locEntry.source(), Set.of()));
                var locGenerated = locXmlGenerator.generate(locEntry.request(), locEntry.element(),
                        locResolvedTypes, locResolvedElements, locResolvedValueTypes);
                Path locOutputRoot = outputRoots.getOrDefault(locTarget, intf.resolve("src/product/" + locTarget + ".gen"));
                String locElementNamespace = locEntry.element().namespace();
                locNamespaceOwners.putIfAbsent(xmlNamespaceOwnerKey(locTarget, locElementNamespace,
                        locEntry.request(), locScopedXmlDocuments), locEntry.request());
                String locElementSource = AIcXmlNamespaceContracts.decorate(locGenerated.source(),
                        locEntry.request(), namespaceType(locNamespaceOwners, locTarget, locElementNamespace,
                                locEntry.request(), locScopedXmlDocuments), Map.of());
                add(pending, locOutputRoot.resolve(locGenerated.relativePath()), locElementSource);
                result.add(Map.of("schema", locEntry.source(), "pointer", "@element/" + locEntry.element().localName(),
                        "language", locTarget, "type", locGenerated.typeName(),
                        "path", portable(repository.relativize(locOutputRoot.resolve(locGenerated.relativePath())))));
            }
        }

        for (var locEntry : locNamespaceOwners.entrySet()) {
            String locLanguage = locEntry.getKey().substring(0, locEntry.getKey().indexOf('#'));
            String locNamespace = locEntry.getKey().substring(locEntry.getKey().indexOf('#') + 1).split("#", 2)[0];
            var locGenerated = AIcXmlNamespaceContracts.generate(locEntry.getValue(), locNamespace);
            Path locRoot = outputRoots.getOrDefault(locLanguage, intf.resolve("src/product/" + locLanguage + ".gen"));
            add(pending, locRoot.resolve(locGenerated.relativePath()), locGenerated.source());
            result.add(Map.of("schema", locEntry.getValue().definition().sourceResource(),
                    "pointer", "@namespace/" + locNamespace, "language", locLanguage,
                    "type", locGenerated.typeName(),
                    "path", portable(repository.relativize(locRoot.resolve(locGenerated.relativePath())))));
        }

        /* Validation is complete. Never delete a foreign file merely because
         * its filename happens to match a configured naming convention. */
        for (Path stale : previouslyOwned) {
            if (!pending.containsKey(stale) && Files.exists(stale)) {
                if (check) throw new IllegalStateException("Stale generated binding: " + stale);
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
            Set<Path> owned = new java.util.HashSet<>(unrelatedOwned);
            owned.addAll(pending.keySet());
            mapper.writerWithDefaultPrettyPrinter().writeValue(state.toFile(),
                    owned.stream().sorted().map(repository::relativize)
                            .map(AIcSchemaContractBindingsGenerator::portable).toList());
        }
        return result;
    }

    private static <K, V> Iterable<Map.Entry<K, V>> iterable(java.util.Iterator<Map.Entry<K, V>> aIterator) {
        return () -> aIterator;
    }

    /**
     * Classifies identity using the source naming convention, not JSON Schema {@code $id}.
     * An input URL identifies a published schema resource and must not turn an otherwise
     * implicit logical name into a separately declared semantic identity.
     *
     * @param definition loaded schema definition
     * @param packageName destination package for an implicit identity
     * @param unitIndex schema units by source resource
     * @param declaredIdentityBySchema whether the configured logical-ID source field has a value
     * @return stable explicit or implicit canonical identity key
     */
    private static Object canonicalIdentity(AIcdCanonicalDefinition definition, String packageName,
                                            Map<String, AIcdUnit> unitIndex,
                                            Map<String, Boolean> declaredIdentityBySchema) {
        AIcdUnit origin = unitIndex.get(definition.sourceResource());
        if (origin == null) origin = unitIndex.get(definition.sourceResource() + "#");
        if (origin == null) throw new IllegalArgumentException("Unknown canonical source " + definition.sourceResource());
        if (!Boolean.TRUE.equals(declaredIdentityBySchema.get(origin.schema()))
                && (definition.sourceKind() != AInDefinitionSourceKind.XMLDEFS
                || definition.identity().equals(definition.logicalName())))
            return java.util.Arrays.asList("implicit", packageName, definition.logicalName(), definition.version(), origin.pointer());
        String identity = definition.identity()
                .replaceAll("(/api/)(?:yamldefs|jsondefs|xmldefs)(/)", "$1schema$2")
                .replaceAll("\\.(?:yamldef|jsondef)\\.schema\\.json(?=#|$)|\\.xsd(?=#|$)", ".schema");
        return java.util.Arrays.asList("explicit", identity, definition.version());
    }

    /** Keep canonical inherited field compatibility independent of documentation. */
    private static List<Object> fieldShape(AIcdPropertyDefinition aField) {
        return java.util.Arrays.asList(aField.sourceName(), aField.dataType(), aField.presence(),
            aField.nullable(), aField.xmlField());
    }

    /** Inherited redeclarations must narrow presence or nullability without changing the value shape. */
    private static boolean fieldNarrows(AIcdPropertyDefinition aParent, AIcdPropertyDefinition aChild) {
        if (!java.util.Objects.equals(aParent.sourceName(), aChild.sourceName())
                || !java.util.Objects.equals(aParent.dataType(), aChild.dataType())
                || !java.util.Objects.equals(aParent.xmlField(), aChild.xmlField())) return false;
        if (aParent.presence() == eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED
                && aChild.presence() != eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED) return false;
        if (aParent.presence() == eu.algites.lib.data.dataobject.AInFieldPresenceKind.FORBIDDEN
                && aChild.presence() != eu.algites.lib.data.dataobject.AInFieldPresenceKind.FORBIDDEN) return false;
        return (aParent.nullable() || !aChild.nullable())
                && (aParent.presence() != aChild.presence() || aParent.nullable() != aChild.nullable());
    }

    /**
     * Resolve every allOf reference branch in document order to an emitted contract.
     * Both local fragment references and canonical cross-file schema IDs are supported;
     * unresolved references must fail rather than silently lose inherited fields.
     *
     * @param aUnit schema unit declaring the composition
     * @param aIndex indexed schema units, including nested definitions
     * @param aRepository sandbox root against which relative references are resolved
     * @return independently emitted parent contracts, in declaration order
     */
    private static List<AIcdUnit> parentUnits(AIcdUnit aUnit, Map<String, AIcdUnit> aIndex, Path aRepository) {
        JsonNode locAllOf = aUnit.node.path("allOf");
        if (locAllOf.isMissingNode()) return List.of();
        if (!locAllOf.isArray()) throw new IllegalArgumentException("allOf must be an array");
        List<String> locReferences = new ArrayList<>();
        for (JsonNode locPart : locAllOf) if (locPart.has("$ref")) locReferences.add(locPart.path("$ref").asText());
        if (locReferences.isEmpty()) return List.of();
        List<AIcdUnit> locParents = new ArrayList<>();
        for (String locReference : locReferences) {
        URI locUri = URI.create(locReference);
        String locPointer = locUri.getRawFragment() == null ? "" : java.net.URLDecoder.decode(locUri.getRawFragment(), java.nio.charset.StandardCharsets.UTF_8);
        if (!locPointer.isEmpty() && !locPointer.startsWith("/"))
            throw new IllegalArgumentException("Unsupported allOf parent anchor: " + locReference);
        if (locUri.isAbsolute() && !locUri.getScheme().equals("file")) {
            var locCandidates = aIndex.values().stream().filter(u ->
                u.document.path("$id").asText().equals(locReference.split("#", 2)[0])
                && u.pointer.equals(locPointer)).toList();
            if (locCandidates.size() != 1) throw new IllegalArgumentException("Unresolved allOf parent: " + locReference);
            locParents.add(locCandidates.get(0));
            continue;
        }
        Path locSource = aRepository.resolve(aUnit.schema);
        Path locParent = (locUri.isAbsolute() ? Path.of(locUri.getPath()) : locUri.getPath().isEmpty() ? locSource
                : locSource.getParent().resolve(locUri.getPath())).toAbsolutePath().normalize();
        if (!locParent.startsWith(aRepository)) throw new IllegalArgumentException("allOf parent escapes repository: " + locReference);
        AIcdUnit locUnit = aIndex.get(portable(aRepository.relativize(locParent)) + "#" + locPointer);
        if (locUnit == null) throw new IllegalArgumentException("allOf parent is not an emitted contract: " + locReference);
        locParents.add(locUnit);
        }
        if (locParents.stream().distinct().count() != locParents.size()) {
            throw new IllegalArgumentException("Duplicate allOf parent in " + aUnit.schema());
        }
        return List.copyOf(locParents);
    }

    private static String qualifyReferences(String source, AIcdCodeGenerationRequest request,
            Map<String, List<AIcdCodeGenerationRequest>> requests, boolean contract,
            eu.algites.tool.codegen.defs.AIcdDefinitionReference aChoiceReference) {
        var names = new AIcGenerationNames();
        List<eu.algites.tool.codegen.defs.AIcdDefinitionReference> locReferences = new ArrayList<>();
        for (var property : request.definition().dataType().properties())
            if (property.dataType().referencedDefinition() != null) locReferences.add(property.dataType().referencedDefinition());
        if (aChoiceReference != null) locReferences.add(aChoiceReference);
        for (var ref : locReferences) {
            String resource = ref.identity().split("#", 2)[0];
            String owner = request.definition().sourceResource().split("#", 2)[0];
            URI locRefUri = URI.create(resource);
            String local = locRefUri.isAbsolute() ? null : resource.isEmpty() ? owner
                    : portable(Path.of(owner).getParent().resolve(resource).normalize());
            /* Public definition URLs are publication aliases, not necessarily the
             * x-*-id of the schema. Resolve against the corresponding input path. */
            String locPublished = null;
            if ("https".equalsIgnoreCase(locRefUri.getScheme())
                    && "defs.dev.algites.eu".equalsIgnoreCase(locRefUri.getHost())) {
                String locPath = locRefUri.getPath();
                for (String locKind : List.of("yamldefs", "jsondefs", "xmldefs")) {
                    String locPrefix = "/api/" + locKind + "/";
                    if (locPath.startsWith(locPrefix))
                        locPublished = "src/product/" + locKind + "/" + locPath.substring(locPrefix.length());
                }
            }
            String locPublishedPath = locPublished;
            var candidates = requests.values().stream().flatMap(List::stream).filter(candidate ->
                candidate.target() == request.target() && (candidate.definition().sourceResource().equals(local)
                    || candidate.definition().sourceResource().equals(locPublishedPath)
                    || candidate.definition().identity().equals(resource))).map(AIcdCodeGenerationRequest::packageName).distinct().toList();
            if (candidates.size() != 1) throw new IllegalArgumentException("Cannot resolve generated reference package: " + ref.identity() + " in " + owner);
            String packageName = candidates.get(0);
            if (packageName.equals(request.packageName())) continue;
            boolean isEnum = ref.targetsEnum();
            var typeKind = isEnum ? eu.algites.tool.codegen.defs.AInDefsNameRole.ENUM_TYPE : contract
                ? eu.algites.tool.codegen.defs.AInDefsNameRole.INTERFACE_TYPE : eu.algites.tool.codegen.defs.AInDefsNameRole.DATA_TYPE;
            var fileKind = isEnum ? eu.algites.tool.codegen.defs.AInDefsNameRole.ENUM_TYPE_FILE_STEM : contract
                ? eu.algites.tool.codegen.defs.AInDefsNameRole.INTERFACE_TYPE_FILE_STEM : eu.algites.tool.codegen.defs.AInDefsNameRole.DATA_TYPE_FILE_STEM;
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
        if (pointer.isEmpty() || node.path("type").asText().equals("object") || node.has("properties") || node.has("enum") || node.has("oneOf") || node.has("anyOf")) {
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
    /**
     * Identify the XML namespace contract that owns a declaration. Explicit target
     * namespaces are repository-wide; an empty namespace is scoped to the XSD
     * document when otherwise-independent definitions have conflicting QNames.
     *
     * @param language target source language
     * @param namespace XML namespace URI or the empty namespace
     * @param request source contract carrying the defining schema path
     * @param scopedDocuments documents requiring their own nominal XML scope
     * @return stable lookup key for the namespace interface owner
     */
    private static String xmlNamespaceOwnerKey(String language, String namespace,
            AIcdCodeGenerationRequest request, Set<String> scopedDocuments) {
        String source = request.definition().sourceResource().split("#", 2)[0];
        return language + "#" + namespace
                + (namespace.isEmpty() && scopedDocuments.contains(source) ? "#" + source : "");
    }

    /**
     * Resolve a generated XML namespace interface without mixing unrelated
     * no-targetNamespace XSD documents.
     *
     * @param owners available namespace interface owners
     * @param language generated source language
     * @param namespace namespace URI or empty XML namespace
     * @param request definition whose XML scope is being resolved
     * @param scopedDocuments documents scoped independently because of QName collisions
     * @return fully qualified generated namespace contract type
     */
    private static String namespaceType(Map<String, AIcdCodeGenerationRequest> owners,
            String language, String namespace, AIcdCodeGenerationRequest request,
            Set<String> scopedDocuments) {
        AIcdCodeGenerationRequest owner = owners.get(
                xmlNamespaceOwnerKey(language, namespace, request, scopedDocuments));
        if (owner == null) throw new IllegalArgumentException("Missing XML namespace contract " + namespace);
        return AIcXmlNamespaceContracts.generate(owner, namespace).qualifiedName();
    }

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
    /**
     * Resolves the configured source-schema annotation member for one metadata kind.
     * Both the selected schema input and the output method naming profile must
     * permit extraction. A blank source disables the generated annotation member.
     *
     * @param aTarget output naming catalog
     * @param aSourceCatalog input naming catalog, must be explicitly provided
     * @param aSourceKind schema family
     * @param aSourceProfile selected source profile, must be explicitly provided
     * @param aKind metadata kind
     * @return declared source metadata field, or empty if disabled
     * @throws IOException if the schema inputs cannot be read
     */
    private static String sourceAnnotationField(AIiNameConventionCatalog aTarget,
            AIcNameConventionCatalog aSourceCatalog, String aSourceKind,
            String aSourceProfile, String aKind) throws IOException {
        AIcNameConventionCatalog locSource = requireSourceNaming(aSourceCatalog, aSourceProfile, aSourceKind);
        String locValue = locSource.schemaMetadataField(aSourceProfile, "schema_source", aKind);
        if (aTarget instanceof AIcNameConventionCatalog locCatalog
                && locCatalog.generatedMethodProfile() != null
                && locCatalog.schemaMetadataField(locCatalog.generatedMethodProfile(),
                    "schema_source", aKind).isBlank()) return "";
        return locValue;
    }

    /**
     * Selects the instance-document metadata field from the generated-method
     * naming profile, independently of the input schema's logical identity.
     * A profile may suppress any field with an empty mapping. Enabling a target
     * without the corresponding input and output source mappings is rejected.
     * Legacy callers without a selected generated-method profile retain their
     * input catalog's instance-metadata conventions.
     *
     * @param aTarget target naming catalog, possibly without a method profile
     * @param aSourceCatalog catalog chosen for the schema input, if supplied
     * @param aSourceKind source schema technology
     * @param aSourceProfile source name convention, must be explicitly provided
     * @param aKind metadata kind: url, identifier or version
     * @return configured target field, or empty string when suppressed
     * @throws IOException if the schema input cannot be read
     * @throws IllegalArgumentException if an output target lacks a source mapping
     */
    private static String outputMetadataField(AIiNameConventionCatalog aTarget,
            AIcNameConventionCatalog aSourceCatalog, String aSourceKind,
            String aSourceProfile, String aKind) throws IOException {
        String locSourceTarget = locSourceMetadataField(aSourceCatalog, aSourceKind, aSourceProfile, aKind);
        if (!(aTarget instanceof AIcNameConventionCatalog locCatalog)
                || locCatalog.generatedMethodProfile() == null) return locSourceTarget;
        String locMethodProfile = locCatalog.generatedMethodProfile();
        String locTarget = locCatalog.schemaMetadataField(locMethodProfile, "data_source", aKind);
        if (!locTarget.isBlank()) {
            String locMethodSource = locCatalog.schemaMetadataField(locMethodProfile, "schema_source", aKind);
            AIcNameConventionCatalog locSource = requireSourceNaming(aSourceCatalog, aSourceProfile, aSourceKind);
            if (locMethodSource.isBlank() || locSource.schemaMetadataField(aSourceProfile,
                    "schema_source", aKind).isBlank())
                throw new IllegalArgumentException("data_source_schema_" + aKind
                        + " has no schema_source_schema_" + aKind);
        }
        return locTarget;
    }

    /**
     * Looks up the instance metadata field from the source-profile catalog for
     * compatibility with generators that do not select an output method profile.
     * Does not infer a target name from the schema ID or the schema URL.
     *
     * @param sourceCatalog optional input naming catalog
     * @param sourceKind source family required for diagnostics
     * @param profile selected source profile, must be explicitly selected
     * @param kind metadata kind: url, identifier, or version
     * @return configured instance metadata field or empty string when disabled
     * @throws IOException if the schema input cannot be read
     */
    private static String locSourceMetadataField(AIcNameConventionCatalog sourceCatalog,
            String sourceKind, String profile, String kind) throws IOException {
        AIcNameConventionCatalog locCatalog = requireSourceNaming(sourceCatalog, profile, sourceKind);
        return locCatalog.schemaMetadataField(profile, "data_source", kind);
    }


    /**
     * Require an explicitly supplied schema-source catalog and its selected profile.
     * Never substitute an Algites-specific catalog when the generator was started
     * without a schema naming configuration.
     *
     * @param catalog schema-source naming catalog
     * @param profile chosen name-convention identifier
     * @param sourceKind source representation being generated
     * @return the caller-selected naming catalog
     * @throws IllegalArgumentException when a source catalog or profile is absent
     */
    private static AIcNameConventionCatalog requireSourceNaming(
            AIcNameConventionCatalog catalog, String profile, String sourceKind) {
        if (catalog == null || profile == null || profile.isBlank()) {
            throw new IllegalArgumentException("Missing explicit " + sourceKind + " schema-source naming profile");
        }
        return catalog;
    }

}