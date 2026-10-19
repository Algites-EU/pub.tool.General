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
import eu.algites.lib.naming.convention.impl.algites.AIcAlgitesNamingProfiles_1;
import eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1;
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
        Map<String, Path> outputRoots = new LinkedHashMap<>();
        Map<String, AIcNameConventionCatalog_1> catalogs = new LinkedHashMap<>();
        Map<String, AIiNameConventionCatalog> targetProfiles = new LinkedHashMap<>();
        Map<String, AIcNameConventionCatalog_1> sourceCatalogs = new LinkedHashMap<>();
        for (var entry : iterable(manifest.path("technology_outputs").fields()))
            outputRoots.put(entry.getKey(), inside(repository, entry.getValue().asText()));
        for (var entry : iterable(manifest.path("technology_naming_profiles").fields())) {
            Path file = inside(repository, entry.getValue().asText());
            catalogs.put(entry.getKey(), AIcNameConventionCatalog_1.load(file));
            targetProfiles.put(entry.getKey(), AIcNameConventionCatalog_1.load(file));
        }
        for (var entry : iterable(manifest.path("schema_input_naming_profiles").fields()))
            sourceCatalogs.put(entry.getKey(), AIcNameConventionCatalog_1.load(inside(repository, entry.getValue().asText())));
        if (explicit) {
            for (String technology : outputRoots.keySet())
                if (!catalogs.containsKey(technology))
                    throw new IllegalArgumentException("Missing output naming profile for " + technology);
        }
        if (manifest.path("clean_only").asBoolean()) {
            for (var entry : outputRoots.entrySet())
                catalogs.get(entry.getKey()).clean(entry.getValue(), Set.of(
                        "algites-" + entry.getKey() + "-gen-intf-versioned",
                        "algites-" + entry.getKey() + "-gen-enum-versioned",
                        "algites-" + entry.getKey() + "-gen-xml-element-intf-versioned",
                        "algites-" + entry.getKey() + "-gen-xml-element-intf"));
            return List.of();
        }
        Map<String, Path> rootBySchema = new LinkedHashMap<>();
        Map<String, String> kindBySchema = new LinkedHashMap<>();
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
        for (var sourceInput : sourceRoots) {
            String kind = sourceInput.getKey();
            Path root = sourceInput.getValue();
            if (!Files.isDirectory(root)) continue;
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
                    AIcNameConventionCatalog_1 sourceCatalog = sourceCatalogs.get(kind);
                    if (sourceCatalog != null) {
                        var named = sourceCatalog.recognizeFilename(source.getFileName().toString(), null);
                        if (named == null) throw new IllegalArgumentException("Invalid schema filename: " + schema);
                        String sourceName = kind.substring(0, kind.length() - 1);
                        if (!manifest.path("allow_unversioned_schemas").asBoolean()
                                && !named.conventionName().equals("algites-" + sourceName + "-schema-versioned"))
                            throw new IllegalArgumentException("Unversioned schema is not allowed: " + schema);
                    }
                    JsonNode document = kind.equals("xmldefs") ? mapper.createObjectNode() : mapper.readTree(source.toFile());
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
        for (String key : overrides.keySet()) {
            if (units.stream().noneMatch(unit -> (unit.schema + "#" + unit.pointer).equals(key))) {
                throw new IllegalArgumentException("Binding override no longer identifies a schema object: " + key);
            }
        }
        Map<Path, String> pending = new TreeMap<>();
        List<Map<String, String>> result = new ArrayList<>();
        Map<String, List<AIcdCodeGenerationRequest>> requests = new LinkedHashMap<>();
        Map<String, AIcdCodeGenerationRequest> unitRequests = new LinkedHashMap<>();
        Map<String, List<AIcdUnit>> relations = new LinkedHashMap<>();
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
                String declaredId = unit.document.path("x-yamldefs-id").asText("");
                if (declaredId.isEmpty()) declaredId = unit.document.path("x-jsondefs-id").asText("");
                if (declaredId.isEmpty()) declaredId = unit.document.path("$id").asText(unit.schema);
                projection.put("x-jsondefs-id", declaredId + (unit.pointer.isEmpty() ? "" : "#" + unit.pointer));
                projection.put("x-jsondefs-name", unit.name);
            }
            AIcdUnit parentUnit = sourceKind.equals("xmldefs") ? null : parentUnit(unit, unitIndex, repository);
            for (JsonNode language : manifest.required("languages")) {
                String targetText = language.asText();
                AInCodeGenerationTarget target = switch (targetText) {
                    case "python" -> AInCodeGenerationTarget.PYTHON;
                    case "java" -> AInCodeGenerationTarget.JAVA;
                    default -> throw new IllegalArgumentException("Unsupported target: " + targetText);
                };
                AIiNameConventionCatalog profile = targetProfiles.get(targetText);
                if (profile == null) profile = target == AInCodeGenerationTarget.PYTHON
                    ? AIcAlgitesNamingProfiles_1.pythonProfile() : AIcAlgitesNamingProfiles_1.javaProfile();
                var sourceType = switch (sourceKind) {
                    case "yamldefs" -> AInDefinitionSourceKind.YAMLDEFS;
                    case "xmldefs" -> AInDefinitionSourceKind.XMLDEFS;
                    default -> AInDefinitionSourceKind.JSONDEFS;
                };
                var load = new AIcdDefinitionLoadRequest(source, sourceType, profile);
                var loaded = sourceKind.equals("xmldefs")
                        ? (unit.pointer().startsWith("@type/")
                            ? new AIcXmlDefsFrontend().loadNamedType(load, unit.pointer().substring(6))
                            : new AIcXmlDefsFrontend().load(load))
                        : reader.read(projection, load, load.sourceKind(), "x-jsondefs-id", "x-jsondefs-version", "x-jsondefs-name");
                var definition = new AIcdCanonicalDefinition(loaded.identity(), loaded.version(), loaded.logicalName(), loaded.sourceKind(), unit.schema + (unit.pointer.isEmpty() ? "" : "#" + unit.pointer), loaded.description(), loaded.dataType(), loaded.enumValues(), loaded.title());
                String locXmlTypeQName = sourceKind.equals("xmldefs")
                        ? (unit.pointer().startsWith("@type/")
                            ? "{" + new AIcXmlDefsFrontend().schemaNamespace(load) + "}" + unit.pointer().substring(6)
                            : new AIcXmlDefsFrontend().rootTypeQName(load)) : null;
                if (locXmlTypeQName != null && locXmlTypeQName.endsWith("}__root__")) locXmlTypeQName = null;
                var request = new AIcdCodeGenerationRequest(definition, target, packageName, profile, locXmlTypeQName);
                var preview = new AIcSchemaContractInterfaceGenerator().generate(request);
                String outputKey = targetText + "#" + preview.relativePath();
                requests.computeIfAbsent(outputKey, key -> new ArrayList<>()).add(request);
                unitRequests.put(targetText + "#" + unit.schema + "#" + unit.pointer, request);
                relations.computeIfAbsent(outputKey, key -> new ArrayList<>()).add(parentUnit);
                result.add(Map.of("schema", unit.schema, "pointer", unit.pointer, "language", targetText, "type", preview.typeName(),
                    "path", portable(repository.relativize(outputRoots.getOrDefault(targetText,
                        intf.resolve("src/product/" + targetText + ".gen")).resolve(preview.relativePath())))));
            }
        }
        /* Resolve named XML extension bases against the complete emitted-type index.
         * A base that is not emitted cannot be represented by Java/Python inheritance:
         * silently flattening it would destroy the XSD type hierarchy. */
        Map<String, AIcdCodeGenerationRequest> locXmlTypeRequests = new LinkedHashMap<>();
        for (var locUnitRequest : unitRequests.entrySet()) {
            var locCandidate = locUnitRequest.getValue();
            if (locCandidate.xmlTypeQName() == null) continue;
            String locKey = locCandidate.target().name() + "#" + locCandidate.xmlTypeQName();
            var locPrevious = locXmlTypeRequests.putIfAbsent(locKey, locCandidate);
            if (locPrevious != null && !locPrevious.packageName().equals(locCandidate.packageName()))
                throw new IllegalArgumentException("Ambiguous XML named type " + locCandidate.xmlTypeQName());
        }
        for (var representations : requests.values()) {
            var first = representations.get(0);
            long identityCount = representations.stream().map(r -> canonicalIdentity(
                    r.definition(), r.packageName(), unitIndex)).distinct().count();
            if (identityCount != 1)
                throw new IllegalArgumentException("Canonical identity collision for one generated output: "
                    + representations.stream().map(r -> r.definition().identity() + " (" + r.definition().sourceResource() + ")").toList());
            var merged = AIcCanonicalDefinitionMerger.AIcMergeStrict(representations.stream().map(AIcdCodeGenerationRequest::definition).toList(), repository);
            String targetText = first.target() == AInCodeGenerationTarget.PYTHON ? "python" : "java";
            String outputKey = targetText + "#" + new AIcSchemaContractInterfaceGenerator().generate(first).relativePath();
            List<AIcdUnit> linked = relations.get(outputKey);
            var inheritedRequests = linked.stream().map(u -> u == null ? null
                : unitRequests.get(targetText + "#" + u.schema + "#" + u.pointer)).toList();
            long parentKinds = inheritedRequests.stream().map(q -> q == null ? ""
                : q.packageName() + "." + new AIcSchemaContractInterfaceGenerator().generate(q).typeName()).distinct().count();
            if (parentKinds != 1) throw new IllegalArgumentException("Conflicting inherited contracts across schema representations");
            String parentName = null, parentModule = null;
            if (inheritedRequests.get(0) != null) {
                AIcdCodeGenerationRequest inherited = inheritedRequests.get(0);
                if (merged.dataType().kind() != AInDataTypeKind.OBJECT || inherited.definition().dataType().kind() != AInDataTypeKind.OBJECT)
                    throw new IllegalArgumentException("allOf inheritance must connect object contracts");
                Map<String, AIcdPropertyDefinition> inheritedFields = new LinkedHashMap<>();
                for (var field : inherited.definition().properties()) inheritedFields.put(field.sourceName(), field);
                List<AIcdPropertyDefinition> locOverrides = new ArrayList<>();
                for (var field : merged.dataType().properties()) {
                    var previous = inheritedFields.get(field.sourceName());
                    if (previous == null || !fieldShape(previous).equals(fieldShape(field))) {
                        if (previous != null && !fieldNarrows(previous, field))
                            throw new IllegalArgumentException("Conflicting inherited field: " + field.sourceName());
                        locOverrides.add(field);
                    }
                }
                merged = new AIcdCanonicalDefinition(merged.identity(), merged.version(), merged.logicalName(), merged.sourceKind(), merged.sourceResource(), merged.description(), merged.dataType(), merged.enumValues(), merged.title());
                var parentSource = new AIcSchemaContractInterfaceGenerator().generate(inherited);
                parentName = parentSource.typeName();
                parentModule = inherited.packageName();
                if (first.target() == AInCodeGenerationTarget.PYTHON)
                    parentModule += "." + Path.of(parentSource.relativePath()).getFileName().toString().replaceFirst("\\.py$", "");
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
                    var locXmlParent = locXmlTypeRequests.get(first.target().name() + "#" + locXmlParentQName);
                    if (locXmlParent == null || locXmlParent == first)
                        throw new IllegalArgumentException("XML extension base has no independently emitted contract: "
                                + locXmlParentQName + " for " + first.xmlTypeQName());
                    if (merged.dataType().kind() != AInDataTypeKind.OBJECT
                            || locXmlParent.definition().dataType().kind() != AInDataTypeKind.OBJECT)
                        throw new IllegalArgumentException("XML extension requires object contracts");
                    Map<String, AIcdPropertyDefinition> locInheritedFields = new LinkedHashMap<>();
                    for (var locField : locXmlParent.definition().properties())
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
                            first.namingProfile(), first.xmlTypeQName()),
                    parentName, parentModule)) {
                eu.algites.tool.codegen.defs.AIcdDefinitionReference locChoiceReference = null;
                if (merged.sourceKind() != AInDefinitionSourceKind.XMLDEFS
                        && merged.dataType() != null && (merged.dataType().kind() == eu.algites.tool.codegen.defs.AInDataTypeKind.ONE_OF
                        || merged.dataType().kind() == eu.algites.tool.codegen.defs.AInDataTypeKind.ANY_OF) && locIndex > 0) {
                    var locAlternative = merged.dataType().alternatives().get(locIndex - 1);
                    if (locAlternative.kind() == eu.algites.tool.codegen.defs.AInDataTypeKind.REFERENCE)
                        locChoiceReference = locAlternative.reference();
                }
                add(pending, outputRoots.getOrDefault(targetText, intf.resolve("src/product/" + targetText + ".gen"))
                        .resolve(pair.relativePath()), qualifyReferences(pair.source(), first, requests, true, locChoiceReference));
                locIndex++;
            }
        }
        /* Global XML element declarations are indexed independently from named XSD
         * content types. This preserves substitution across source files and modules. */
        var locXmlGenerator = new AIcXmlElementContractGenerator();
        var locXmlFrontend = new AIcXmlDefsFrontend();
        for (JsonNode locLanguage : manifest.required("languages")) {
            String locTarget = locLanguage.asText();
            Map<String, String> locTypes = new LinkedHashMap<>();
            Map<String, String> locElements = new LinkedHashMap<>();
            Set<String> locValueTypes = new java.util.HashSet<>();
            record AIcdElementWork(String source, AIcdCodeGenerationRequest request,
                                   eu.algites.tool.codegen.defs.AIcdXmlElementDeclaration element) { }
            List<AIcdElementWork> locWork = new ArrayList<>();
            for (AIcdUnit locUnit : units) {
                if (!kindBySchema.get(locUnit.schema()).equals("xmldefs")) continue;
                AIcdCodeGenerationRequest locRequest = unitRequests.get(
                        locTarget + "#" + locUnit.schema() + "#" + locUnit.pointer());
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
                        locValueTypes.add(locRootQName);
                    var locPreview = new AIcSchemaContractInterfaceGenerator().generate(locRequest);
                    String locQualified = locRequest.packageName() + "."
                            + (locTarget.equals("python")
                                ? Path.of(locPreview.relativePath()).getFileName().toString().replaceFirst("\\.py$", "") + "."
                                : "") + locPreview.typeName();
                    String locPrevious = locTypes.putIfAbsent(locRootQName, locQualified);
                    if (locPrevious != null && !locPrevious.equals(locQualified))
                        throw new IllegalArgumentException("Duplicate XML content type " + locRootQName);
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
                    if (locElements.putIfAbsent(locElement.qName(), locQualified) != null)
                        throw new IllegalArgumentException("Duplicate XML global element " + locElement.qName());
                    locWork.add(new AIcdElementWork(locUnit.schema(), locRequest, locElement));
                }
            }
            for (AIcdElementWork locEntry : locWork) {
                var locGenerated = locXmlGenerator.generate(locEntry.request(), locEntry.element(), locTypes, locElements, locValueTypes);
                Path locOutputRoot = outputRoots.getOrDefault(locTarget, intf.resolve("src/product/" + locTarget + ".gen"));
                add(pending, locOutputRoot.resolve(locGenerated.relativePath()), locGenerated.source());
                result.add(Map.of("schema", locEntry.source(), "pointer", "@element/" + locEntry.element().localName(),
                        "language", locTarget, "type", locGenerated.typeName(),
                        "path", portable(repository.relativize(locOutputRoot.resolve(locGenerated.relativePath())))));
            }
        }

        /* Validate the complete batch before cleaning any previously generated source. */
        if (explicit && !check) {
            for (var entry : outputRoots.entrySet())
                catalogs.get(entry.getKey()).clean(entry.getValue(), Set.of(
                        "algites-" + entry.getKey() + "-gen-intf-versioned",
                        "algites-" + entry.getKey() + "-gen-enum-versioned",
                        "algites-" + entry.getKey() + "-gen-xml-element-intf-versioned",
                        "algites-" + entry.getKey() + "-gen-xml-element-intf"));
        }
        Path state = repository.resolve("build/run/schema-contract-bindings/generated-files.json");
        List<String> previous = explicit ? List.of() : Files.isRegularFile(state)
                ? mapper.readValue(state.toFile(), mapper.getTypeFactory().constructCollectionType(List.class, String.class)) : List.of();
        /* Only recorded files owned by this generator may be removed. */
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
        if (!check && !explicit) {
            Files.createDirectories(state.getParent());
            mapper.writerWithDefaultPrettyPrinter().writeValue(state.toFile(), pending.keySet().stream().map(repository::relativize).map(AIcSchemaContractBindingsGenerator::portable).toList());
        }
        return result;
    }

    private static <K, V> Iterable<Map.Entry<K, V>> iterable(java.util.Iterator<Map.Entry<K, V>> aIterator) {
        return () -> aIterator;
    }

    /** Distinguishes semantic schema IDs from format-specific publication URL aliases. */
    private static Object canonicalIdentity(AIcdCanonicalDefinition definition, String packageName,
                                            Map<String, AIcdUnit> unitIndex) {
        AIcdUnit origin = unitIndex.get(definition.sourceResource());
        if (origin == null) origin = unitIndex.get(definition.sourceResource() + "#");
        if (origin == null) throw new IllegalArgumentException("Unknown canonical source " + definition.sourceResource());
        JsonNode document = origin.document();
        String explicit = document.path("x-yamldefs-id").asText("");
        if (explicit.isEmpty()) explicit = document.path("x-jsondefs-id").asText("");
        if (explicit.isEmpty()) explicit = document.path("$id").asText("");
        if (explicit.isEmpty() && (definition.sourceKind() != AInDefinitionSourceKind.XMLDEFS
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

    /** Resolve exactly one local or canonical-identity allOf parent into an emitted contract. */
    private static AIcdUnit parentUnit(AIcdUnit aUnit, Map<String, AIcdUnit> aIndex, Path aRepository) {
        JsonNode locAllOf = aUnit.node.path("allOf");
        if (locAllOf.isMissingNode()) return null;
        if (!locAllOf.isArray()) throw new IllegalArgumentException("allOf must be an array");
        List<String> locReferences = new ArrayList<>();
        for (JsonNode locPart : locAllOf) if (locPart.has("$ref")) locReferences.add(locPart.path("$ref").asText());
        if (locReferences.isEmpty()) return null;
        if (locReferences.size() != 1) throw new IllegalArgumentException("Exactly one allOf parent is supported");
        String locReference = locReferences.get(0);
        URI locUri = URI.create(locReference);
        String locPointer = locUri.getRawFragment() == null ? "" : java.net.URLDecoder.decode(locUri.getRawFragment(), java.nio.charset.StandardCharsets.UTF_8);
        if (!locPointer.isEmpty() && !locPointer.startsWith("/"))
            throw new IllegalArgumentException("Unsupported allOf parent anchor: " + locReference);
        if (locUri.isAbsolute() && !locUri.getScheme().equals("file")) {
            var locCandidates = aIndex.values().stream().filter(u ->
                u.document.path("$id").asText().equals(locReference.split("#", 2)[0])
                && u.pointer.equals(locPointer)).toList();
            if (locCandidates.size() != 1) throw new IllegalArgumentException("Unresolved allOf parent: " + locReference);
            return locCandidates.get(0);
        }
        Path locSource = aRepository.resolve(aUnit.schema);
        Path locParent = (locUri.isAbsolute() ? Path.of(locUri.getPath()) : locUri.getPath().isEmpty() ? locSource
                : locSource.getParent().resolve(locUri.getPath())).toAbsolutePath().normalize();
        if (!locParent.startsWith(aRepository)) throw new IllegalArgumentException("allOf parent escapes repository: " + locReference);
        AIcdUnit locUnit = aIndex.get(portable(aRepository.relativize(locParent)) + "#" + locPointer);
        if (locUnit == null) throw new IllegalArgumentException("allOf parent is not an emitted contract: " + locReference);
        return locUnit;
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
            String local = java.net.URI.create(resource).isAbsolute() ? null : resource.isEmpty() ? owner : portable(Path.of(owner).getParent().resolve(resource).normalize());
            var candidates = requests.values().stream().flatMap(List::stream).filter(candidate ->
                candidate.target() == request.target() && (candidate.definition().sourceResource().equals(local)
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
}
