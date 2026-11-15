package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.*;
import java.io.StringReader;
import java.math.BigDecimal;
import java.io.StringWriter;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.InputSource;

/**
 * Independent source-schema frontend for the new seven-kind canonical model.
 * XMLDEFS, JSONDEFS and YAMLDEFS all map to the same contracts, without importing
 * any legacy generator classes. JSON and YAML documents must have been parsed into
 * ordinary maps by their respective adapters; XML is parsed as namespace-aware XSD.
 * References are retained as unresolved {@code TYPE} records for the later resolver.
 * This class does not implement schema validation, reference resolution, XML-to-MAP,
 * patternProperties, global XML keys or XML key references. Local xs:key
 * and xs:unique remain occurrence-scoped on the referring element; they do
 * not synthesize, clone, or mutate its referenced nominal TYPE.
 */
public final class AIcDefsCodegenCanonicalSchemaFrontend {
    /** Namespace URI for XML Schema. */
    private static final String XS = XMLConstants.W3C_XML_SCHEMA_NS_URI;
    /** Resolved naming conventions including Defs synthetic-type naming. */
    private final AIcCodegenNamingProfileResolver.Profile naming;
    /** Restriction resolution stack used to reject cyclic named scalar aliases. */
    private final java.util.Set<String> resolvingXsdSimpleTypes = new java.util.HashSet<>();
    /** Qualified names verified by the reference resolver as imported XSD TYPEs. */
    private final java.util.Set<String> importedTypes;
    /** Verified imported complex definitions, used only for element-scoped key projection. */
    private final Map<String, Element> importedComplexTypes;
    /** Per-document schema versions for every nested or synthetic canonical TYPE. */
    private final Map<String, String> sourceVersions = new java.util.HashMap<>();


    /**
     * Creates a frontend with already validated Common and Defs conventions.
     *
     * @param naming resolved conventions shared by all source technologies
     * @throws NullPointerException when naming is null
     */
    public AIcDefsCodegenCanonicalSchemaFrontend(AIcCodegenNamingProfileResolver.Profile naming) {
        this(naming, java.util.Set.of());
    }

    /**
     * Create a frontend accepting precisely the externally resolved XSD QNames.
     * @param naming explicitly resolved Common+Defs naming conventions
     * @param importedTypes expanded XSD QNames confirmed from imports by the resolver
     * @throws NullPointerException if naming or importedTypes is null
     */
    public AIcDefsCodegenCanonicalSchemaFrontend(AIcCodegenNamingProfileResolver.Profile naming,
            java.util.Set<String> importedTypes) {
        this(naming, importedTypes, Map.of());
    }

    /**
     * Create a frontend with verified source documents for imported XSD types.
     * @param naming resolved conventions
     * @param importedTypes verified imported QName identities
     * @param importedDocuments imported schema URI to XSD source text
     * @throws IllegalArgumentException when an imported XSD is malformed
     */
    public AIcDefsCodegenCanonicalSchemaFrontend(AIcCodegenNamingProfileResolver.Profile naming,
            java.util.Set<String> importedTypes, Map<String, String> importedDocuments) {
        this.naming = Objects.requireNonNull(naming, "naming");
        this.importedTypes = java.util.Set.copyOf(Objects.requireNonNull(importedTypes, "importedTypes"));
        var indexed = new java.util.LinkedHashMap<String, Element>();
        for (var entry : Objects.requireNonNull(importedDocuments, "importedDocuments").entrySet()) {
            try {
                var factory = DocumentBuilderFactory.newInstance();
                factory.setNamespaceAware(true);
                factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
                factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
                factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
                factory.setXIncludeAware(false);
                factory.setExpandEntityReferences(false);
                var document = factory.newDocumentBuilder().parse(
                        new InputSource(new StringReader(entry.getValue())));
                Element root = document.getDocumentElement();
                if (!is(root, "schema")) throw new IllegalArgumentException(
                        "Imported document is not an XSD schema: " + entry.getKey());
                String ns = root.getAttribute("targetNamespace");
                for (var child : elements(root)) {
                    if (!is(child, "complexType") || !child.hasAttribute("name")) continue;
                    String id = ns.isEmpty() ? child.getAttribute("name")
                            : "{" + ns + "}" + child.getAttribute("name");
                    if (this.importedTypes.contains(id) && indexed.putIfAbsent(id, child) != null) {
                        throw new IllegalArgumentException("Duplicate imported complexType: " + id);
                    }
                }
            } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException
                    | java.io.IOException e) {
                throw new IllegalArgumentException("Cannot parse imported XSD " + entry.getKey(), e);
            }
        }
        this.importedComplexTypes = Map.copyOf(indexed);
    }

    /**
     * Rejects structural choice declarations nested inside validation-only subschemas.
     * @param node current schema map, list or scalar
     * @param path JSON pointer for precise diagnostics
     * @param blocked whether an ancestor is already a validation-only keyword
     * @throws IllegalArgumentException when a choice appears under oneOf/anyOf etc.
     */
    private static void validateChoicePlacements(Object node, String path, boolean blocked) {
        var validators = java.util.Set.of("oneOf", "anyOf", "allOf", "not", "if", "then",
                "else", "contains", "dependentSchemas", "dependencies", "propertyNames");
        if (node instanceof Map<?, ?> mapping) {
            if (blocked && mapping.containsKey("x-algites-defscodegen-choice")) {
                throw new IllegalArgumentException("Structural choice inside validation-only branch at " + path);
            }
            for (var entry : mapping.entrySet()) {
                String key = String.valueOf(entry.getKey());
                validateChoicePlacements(entry.getValue(),
                        path + "/" + key.replace("~", "~0").replace("/", "~1"),
                        blocked || validators.contains(key));
            }
        } else if (node instanceof List<?> items) {
            for (int index = 0; index < items.size(); index++) {
                validateChoicePlacements(items.get(index), path + "/" + index, blocked);
            }
        }
    }

    /**
     * Loads a parsed JSONDEFS or YAMLDEFS schema into one declared canonical type.
     *
     * @param source schema root map, preserving its ordered fields
     * @param resource original document identifier used in source bindings
     * @param kind either JSONDEFS or YAMLDEFS, never XMLDEFS
     * @return unnormalized declared type, including source provenance
     * @throws IllegalArgumentException for malformed or unsupported schema structures
     */
    public AIcDefsCanonicalType loadJsonOrYaml(Map<String, Object> source, String resource,
            AIngSourceInputKind_1 kind) {
        return loadJsonOrYaml(source, resource, kind, "", "");
    }

    /**
     * Parse a JSONDEFS/YAMLDEFS document root using externally validated filename naming.
     * @param source parsed schema
     * @param resource source location
     * @param kind input technology
     * @param rootName type name produced from the selected source filename catalog
     * @param sourceVersion version extracted from the selected source filename catalog
     * @return canonical root declaration
     * @throws IllegalArgumentException for invalid schema structures
     */
    public AIcDefsCanonicalType loadJsonOrYaml(Map<String, Object> source, String resource,
            AIngSourceInputKind_1 kind, String rootName, String sourceVersion) {
        Objects.requireNonNull(source, "source");
        Objects.requireNonNull(resource, "resource");
        if (kind != AIngSourceInputKind_1.JSONDEFS &&
                kind != AIngSourceInputKind_1.YAMLDEFS) {
            throw new IllegalArgumentException("Source must be JSONDEFS or YAMLDEFS");
        }
        validateChoicePlacements(source, "#", false);
        sourceVersions.put(resource, string(source.get("x-algites-schema-version"), sourceVersion));
        String name = rootName.isEmpty() ? string(source.get("title"),
                resource.substring(resource.lastIndexOf('/') + 1).split("\\.")[0]) : rootName;
        String identity = string(source.get("x-algites-schema-id"), string(source.get("$id"), resource));
        List<String> inherited = new ArrayList<>();
        for (Object item : list(source.get("allOf"))) {
            if (item instanceof Map<?, ?> map && map.get("$ref") instanceof String reference
                    && !inherited.contains(reference)) {
                inherited.add(reference);
            }
        }
        for (Object reference : list(source.get("x-algites-defscodegen-extends"))) {
            if (!(reference instanceof String)) throw new IllegalArgumentException("Invalid x-algites-defscodegen-extends");
            if (!inherited.contains(reference)) inherited.add((String) reference);
        }
        var root = new AIcDefsCanonicalType(identity, name, AIngTypeOrigin_1.DECLARED,
                List.of(name), inherited, jsonNode(source, name, "#", kind, resource),
                AIngResolutionState_1.RESOLVED, binding(kind, resource, "#", "root"),
                "", String.valueOf(source.getOrDefault("x-algites-schema-version", sourceVersion)),
                string(source.get("description"), ""));
        return root;
    }

    /**
     * Collects a schema's root and all standalone named {@code $defs}/{@code definitions}.
     * References remain symbolic until a later source-aware linking pass.
     *
     * @param source root parsed schema mapping
     * @param resource source resource identifier
     * @param kind JSONDEFS or YAMLDEFS input kind
     * @return immutable ordered named canonical types, without name-based replacement
     * @throws IllegalArgumentException when the definitions structure is invalid
     */
    public List<AIcDefsCanonicalType> loadJsonOrYamlTypes(Map<String, Object> source, String resource,
            AIngSourceInputKind_1 kind) {
        return loadJsonOrYamlTypes(source, resource, kind, "", "");
    }

    /**
     * Enumerate named definitions with a filename-derived document root.
     * @param source parsed input schema
     * @param resource original input path
     * @param kind input technology
     * @param rootName filename-derived root type name
     * @param sourceVersion filename-derived version
     * @return ordered canonical declarations
     */
    public List<AIcDefsCanonicalType> loadJsonOrYamlTypes(Map<String, Object> source, String resource,
            AIngSourceInputKind_1 kind, String rootName, String sourceVersion) {
        Objects.requireNonNull(source, "source");
        if (kind != AIngSourceInputKind_1.JSONDEFS &&
                kind != AIngSourceInputKind_1.YAMLDEFS) {
            throw new IllegalArgumentException("Source must be JSONDEFS or YAMLDEFS");
        }
        validateChoicePlacements(source, "#", false);
        sourceVersions.put(resource, string(source.get("x-algites-schema-version"), sourceVersion));
        List<AIcDefsCanonicalType> result = new ArrayList<>();
        if (List.of("type", "properties", "additionalProperties", "items", "prefixItems", "$ref",
                "oneOf", "anyOf", "enum", "const", "required", "minItems", "maxItems", "allOf")
                .stream().anyMatch(source::containsKey)
                || (!source.containsKey("$defs") && !source.containsKey("definitions"))) {
            result.add(loadJsonOrYaml(source, resource, kind, rootName, sourceVersion));
        }
        for (String section : List.of("$defs", "definitions")) {
            Map<String, Object> definitions = source.containsKey(section)
                    ? map(source.get(section), section) : Map.of();
            for (var entry : definitions.entrySet()) {
                String name = entry.getKey();
                String pointer = "#/" + section + "/" + name.replace("~", "~0").replace("/", "~1");
                var node = jsonNode(map(entry.getValue(), pointer), name, pointer, kind, resource);
                String baseIdentity = string(source.get("x-algites-schema-id"),
                        string(source.get("$id"), resource));
                Map<String, Object> definition = map(entry.getValue(), pointer);
                String identity = string(definition.get("x-algites-schema-id"),
                        string(definition.get("$id"), baseIdentity + pointer));
                List<String> inherited = new ArrayList<>();
                for (Object part : list(definition.get("allOf"))) {
                    if (part instanceof Map<?, ?> mapping && mapping.get("$ref") instanceof String base
                            && !inherited.contains(base)) {
                        inherited.add(base);
                    }
                }
                for (Object reference : list(definition.get("x-algites-defscodegen-extends"))) {
                    if (!(reference instanceof String)) throw new IllegalArgumentException("Invalid x-algites-defscodegen-extends");
                    if (!inherited.contains(reference)) inherited.add((String) reference);
                }
                var type = new AIcDefsCanonicalType(identity, name,
                        AIngTypeOrigin_1.DECLARED, List.of(name), inherited, node,
                        AIngResolutionState_1.RESOLVED, binding(kind, resource, pointer, section),
                        "", String.valueOf(definition.getOrDefault("x-algites-schema-version",
                                source.getOrDefault("x-algites-schema-version", sourceVersion))),
                        string(definition.get("description"), ""));
                result.add(type);
            }
        }
        return List.copyOf(result);
    }

    /**
     * Parses XSD named complex and simple types, retaining their compositional groups.
     * DTD/external-entity loading is disabled to prevent resolution outside the document.
     *
     * @param xml complete XSD text
     * @param resource original schema identifier
     * @return declared types in source order
     * @throws IllegalArgumentException for invalid XML or unsupported schema structures
     */
    private Map<String, Element> localXsdSimpleTypes = Map.of();
    /** Named complex declarations used to project element-scoped XML identity constraints. */
    private Map<String, Element> localXsdComplexTypes = Map.of();
    /** Named xs:group definitions keyed by expanded QName, independent of the type symbol space. */
    private Map<String, Element> localXsdGroups = Map.of();

    public List<AIcDefsCanonicalType> loadXsd(String xml, String resource) {
        return loadXsd(xml, resource, "");
    }

    /**
     * Read named XSD types, taking the schema version from the selected input
     * filename convention when no XML declaration supplies it.
     * @param xml complete source XSD
     * @param resource original source path
     * @param sourceVersion version parsed by the input filename naming catalog
     * @return declared canonical TYPE definitions
     * @throws NullPointerException if a required argument is null
     * @throws IllegalArgumentException for malformed XML or invalid schema constructs
     * @throws UnsupportedOperationException for unsupported schema constructs
     */
    public List<AIcDefsCanonicalType> loadXsd(String xml, String resource, String sourceVersion) {
        Objects.requireNonNull(xml, "xml");
        Objects.requireNonNull(resource, "resource");
        Objects.requireNonNull(sourceVersion, "sourceVersion");
        try {
            var factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
            factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
            factory.setXIncludeAware(false);
            factory.setExpandEntityReferences(false);
            var document = factory.newDocumentBuilder().parse(new InputSource(new StringReader(xml)));
            Element schema = document.getDocumentElement();
            if (!is(schema, "schema")) throw new IllegalArgumentException("Expected xs:schema");
            sourceVersions.put(resource, schema.hasAttribute("x-algites-schema-version")
                    ? schema.getAttribute("x-algites-schema-version") : sourceVersion);
            /* Validate form defaults even for an attribute-only or empty schema.
             * Otherwise Java could accept an input rejected by the Python frontend,
             * or silently ignore a malformed default when no fields are visited. */
            for (String formAttribute : List.of("elementFormDefault", "attributeFormDefault")) {
                if (schema.hasAttribute(formAttribute)
                        && !List.of("qualified", "unqualified")
                                .contains(schema.getAttribute(formAttribute))) {
                    throw new IllegalArgumentException("Invalid XSD element/attribute form default: "
                            + formAttribute + "=" + schema.getAttribute(formAttribute));
                }
            }
            /* Global element declarations are not traversed by this named-type
             * frontend. Their identity constraints cannot silently disappear. */
            for (var constraint : List.of("keyref", "identityConstraint")) {
                if (schema.getElementsByTagNameNS(XS, constraint).getLength() > 0) {
                    throw new UnsupportedOperationException(
                            "XSD keyref/identityConstraint requires a dedicated resolver: " + constraint);
                }
            }
            for (var child : elements(schema)) {
                if (is(child, "element")) {
                    for (var constraint : List.of("key", "unique")) {
                        if (child.getElementsByTagNameNS(XS, constraint).getLength() > 0) {
                            throw new UnsupportedOperationException("Global element identity constraints "
                                    + "require global-element loading");
                        }
                    }
                }
            }
            for (var child : elements(schema)) {
                if (List.of("include", "redefine", "override").contains(child.getLocalName())) {
                    throw new UnsupportedOperationException("XSD include/redefine/override is not supported");
                }
                if (is(child, "import") && !child.hasAttribute("schemaLocation")) {
                    throw new IllegalArgumentException("XSD import must have a schemaLocation");
                }
            }
            Map<String, Element> groups = new java.util.LinkedHashMap<>();
            String groupNamespace = schema.getAttribute("targetNamespace");
            for (var child : elements(schema)) {
                if (is(child, "group") && child.hasAttribute("name")) {
                    String name = child.getAttribute("name");
                    String identity = groupNamespace.isEmpty() ? name : "{" + groupNamespace + "}" + name;
                    if (groups.putIfAbsent(identity, child) != null) {
                        throw new IllegalArgumentException("Duplicate named xs:group " + identity
                                + " in " + resource);
                    }
                }
            }
            localXsdGroups = Map.copyOf(groups);
            List<Element> named = new ArrayList<>();
            for (var child : elements(schema)) {
                if ((is(child, "complexType") || is(child, "simpleType")) && child.hasAttribute("name")) {
                    named.add(child);
                }
            }
            var declared = new java.util.HashSet<String>();
            for (var child : named) declared.add(child.getAttribute("name"));
            for (var child : groups.values()) {
                if (xmlNamedListGroup(child) != null) continue;
                String name = child.getAttribute("name");
                if (!declared.add(name)) {
                    throw new IllegalArgumentException("XSD group/type canonical identity conflict: " + name
                            + " in " + resource);
                }
                named.add(child);
            }
            String targetNamespace = schema.getAttribute("targetNamespace");
            Map<String, Element> localSimpleTypes = new java.util.LinkedHashMap<>();
            for (var child : named) {
                if (is(child, "simpleType")) {
                    String name = child.getAttribute("name");
                    String identity = targetNamespace.isEmpty() ? name : "{" + targetNamespace + "}" + name;
                    localSimpleTypes.put(identity, child);
                }
            }
            localXsdSimpleTypes = Map.copyOf(localSimpleTypes);
            Map<String, Element> localComplexTypes = new java.util.LinkedHashMap<>();
            for (var child : named) {
                if (is(child, "complexType")) {
                    String name = child.getAttribute("name");
                    String identity = targetNamespace.isEmpty() ? name : "{" + targetNamespace + "}" + name;
                    localComplexTypes.put(identity, child);
                }
            }
            localXsdComplexTypes = Map.copyOf(localComplexTypes);
            resolvingXsdSimpleTypes.clear();
            List<AIcDefsCanonicalType> result = new ArrayList<>();
            for (var child : named) {
                String name = child.getAttribute("name");
                List<String> ignoredWildcards = new ArrayList<>();
                var value = xmlNode(child, name, "/schema/" + name, resource, declared, false, ignoredWildcards);
                if (is(child, "simpleType") && value instanceof AIcDefsCanonicalScalar) {
                    // Inline scalar alias restrictions on their consuming DO fields.
                    continue;
                }
                String namespace = schema.getAttribute("targetNamespace");
                String identity = namespace.isEmpty() ? name : "{" + namespace + "}" + name;
                List<String> inherited = new ArrayList<>();
                for (var group : elements(child)) {
                    if (is(group, "complexContent")) {
                        for (var derivation : elements(group)) {
                            if ((is(derivation, "extension") || is(derivation, "restriction"))
                                    && derivation.hasAttribute("base")) {
                                String base = xmlTypeIdentity(derivation,
                                        derivation.getAttribute("base"), declared);
                                if (base.startsWith("@xs:")) {
                                    if (!List.of("anyType", "anySimpleType").contains(base.substring(4))) {
                                        throw new UnsupportedOperationException("Unsupported XSD built-in extension base "
                                                + derivation.getAttribute("base"));
                                    }
                                } else {
                                    inherited.add(base);
                                }
                            }
                        }
                    }
                }
                result.add(new AIcDefsCanonicalType(identity, name, AIngTypeOrigin_1.DECLARED,
                        List.of(name), inherited, value, AIngResolutionState_1.RESOLVED,
                        binding(AIngSourceInputKind_1.XMLDEFS, resource,
                                "/schema/" + name, child.getLocalName()),
                        "", child.hasAttribute("x-algites-schema-version")
                                ? child.getAttribute("x-algites-schema-version")
                                : (schema.hasAttribute("x-algites-schema-version")
                                        ? schema.getAttribute("x-algites-schema-version") : sourceVersion),
                        String.join("\n", java.util.stream.Stream.concat(
                                java.util.stream.Stream.of(xmlDescription(child)),
                                ignoredWildcards.stream()).filter(note -> !note.isBlank()).toList())));
            }
            return List.copyOf(result);
        } catch (IllegalArgumentException | UnsupportedOperationException ex) {
            /* Preserve a precise validation or unsupported-feature diagnostic;
             * only actual XML parse failures are wrapped with the resource. */
            throw ex;
        } catch (Exception ex) {
            throw new IllegalArgumentException("Cannot parse XMLDEFS schema " + resource, ex);
        }
    }

    /**
     * Projects a homogeneous JSON/YAML property map with an explicit key into
     * a typed indexed LIST, without losing the raw enum identity.
     * Explicit properties are accepted only when their value schemas match
     * additionalProperties exactly; distinct constraints cannot be erased.
     *
     * @param schema JSON/YAML object schema with x-algites-defscodegen-key
     * @param owner logical owner of this schema node
     * @param path original JSON Pointer
     * @param kind JSONDEFS or YAMLDEFS
     * @param resource defining schema resource
     * @return keyed LIST with a synthetic key/value TYPE
     * @throws IllegalArgumentException for malformed metadata
     * @throws UnsupportedOperationException for unsupported map constraints
     */
    /** Validation-only JSON Schema facets which cannot change map value storage type. */
    private static final java.util.Set<String> INDEXED_VALUE_VALIDATION_FACETS = java.util.Set.of(
            "minLength", "maxLength", "pattern", "format", "minimum", "maximum",
            "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minItems",
            "maxItems", "uniqueItems", "minProperties", "maxProperties", "enum",
            "const", "required", "title", "description", "examples", "default");

    /**
     * Return the structural part of an indexed-map value schema.
     * @param source map-value definition to normalize
     * @return mapping without exclusively validation/documentation assertions
     */
    private static Map<String, Object> indexedMapStorageShape(Map<String, Object> source) {
        Map<String, Object> result = new java.util.LinkedHashMap<>();
        for (var entry : source.entrySet()) {
            if (INDEXED_VALUE_VALIDATION_FACETS.contains(entry.getKey())) continue;
            Object value = entry.getValue();
            if (value instanceof Map<?, ?> nested) {
                value = indexedMapStorageShape(map(nested, entry.getKey()));
            }
            if ("type".equals(entry.getKey()) && value instanceof List<?> types &&
                    types.size() == 2 && types.contains("null")) {
                Object other = types.get(0).equals("null") ? types.get(1) : types.get(0);
                if (other instanceof String) value = other;
            }
            result.put(entry.getKey(), value);
        }
        return result;
    }

    /**
     * Interpret an explicit JSON/YAML array key as an identity constraint on
     * each named item field. Object-property maps use jsonIndexedMap instead.
     * @param schema array schema carrying the key metadata
     * @param owner surrounding canonical type name
     * @param path source JSON pointer
     * @param kind JSONDEFS/YAMLDEFS source kind
     * @param resource source file identifier
     * @return typed list with a canonical key definition
     * @throws IllegalArgumentException when the key or item shape is invalid
     */
    private AIcDefsCanonicalList jsonKeyedArray(Map<String, Object> schema, String owner,
            String path, AIngSourceInputKind_1 kind, String resource) {
        String location = resource + path + "/x-algites-defscodegen-key";
        Map<String, Object> metadata = map(schema.get("x-algites-defscodegen-key"), location);
        String id = string(metadata.get("id"), "");
        String field = string(metadata.get("field-name"), "");
        if (!metadata.keySet().equals(java.util.Set.of("id", "field-name")) || id.isBlank() || field.isBlank()) {
            throw new IllegalArgumentException("Invalid x-algites-defscodegen-key at " + location);
        }
        if (schema.containsKey("prefixItems") || !(schema.get("items") instanceof Map<?, ?> item)) {
            throw new IllegalArgumentException("Keyed array needs homogeneous items schema at " + location);
        }
        Map<String, Object> itemSchema = map(item, path + "/items");
        if (!itemSchema.containsKey("$ref")) {
            if (!"object".equals(itemSchema.get("type")) ||
                    !(itemSchema.get("properties") instanceof Map<?, ?>)) {
                throw new IllegalArgumentException("Keyed array item must be an object or typed $ref at " + location);
            }
            Map<String, Object> properties = map(itemSchema.get("properties"), path + "/items/properties");
            if (!properties.containsKey(field)) {
                throw new IllegalArgumentException("Keyed array item is missing field " + field + " at " + location);
            }
            if (!list(itemSchema.get("required")).contains(field)) {
                throw new IllegalArgumentException("Keyed array requires field " + field + " in items.required at " + location);
            }
            Map<String, Object> fieldSchema = map(properties.get(field), path + "/items/properties/" + field);
            if (!fieldSchema.containsKey("$ref") && !fieldSchema.containsKey("enum")
                    && !fieldSchema.containsKey("const") && !fieldSchema.containsKey("allOf")
                    && !java.util.Set.of("string", "number", "integer", "boolean")
                            .contains(String.valueOf(fieldSchema.get("type")))) {
                throw new IllegalArgumentException("Keyed array field must be a typed scalar/enum at " + location);
            }
        }
        var unkeyed = new java.util.LinkedHashMap<>(schema);
        unkeyed.remove("x-algites-defscodegen-key");
        AIiDefsCanonicalStructure result = jsonNode(unkeyed, owner, path, kind, resource);
        if (!(result instanceof AIcDefsCanonicalList listNode)) {
            throw new IllegalArgumentException("Keyed array did not resolve to a LIST at " + location);
        }
        String member = path.substring(path.lastIndexOf('/') + 1).replace("~1", "/").replace("~0", "~");
        return new AIcDefsCanonicalList(member, listNode.item(), listNode.minItemCount(),
                listNode.maxItemCount(), List.of(new AIcDefsCanonicalKeyDefinition(
                    id, member, path + "/x-algites-defscodegen-key", List.of(field), true)),
                listNode.xmlWire(), listNode.uniqueItems());
    }

    private AIcDefsCanonicalList jsonIndexedMap(Map<String, Object> schema, String owner,
            String path, AIngSourceInputKind_1 kind, String resource) {
        Map<String, Object> metadata = map(schema.get("x-algites-defscodegen-key"), path);
        if (!metadata.keySet().equals(java.util.Set.of("id", "field-name"))
                || !(metadata.get("id") instanceof String id) || id.isBlank()
                || !(metadata.get("field-name") instanceof String fieldName) || fieldName.isBlank()) {
            throw new IllegalArgumentException("Invalid x-algites-defscodegen-key at " + path);
        }
        if (!"object".equals(schema.getOrDefault("type", "object"))
                || !(schema.get("additionalProperties") instanceof Map<?, ?>)) {
            throw new IllegalArgumentException("Indexed map requires object/additionalProperties at " + path);
        }
        // JSON Schema properties constrain values at named keys; they do not
        // introduce additional DataObject members beside the indexed map.
        // A homogeneous map may list those keys explicitly without changing
        // the value type. Reject distinct constraints instead of silently
        // widening them to the common additionalProperties schema.
        if (schema.containsKey("properties")) {
            Map<String, Object> properties = map(schema.get("properties"), path + "/properties");
            Map<String, Object> baseShape = indexedMapStorageShape(
                    map(schema.get("additionalProperties"), path + "/additionalProperties"));
            for (var named : properties.entrySet()) {
                String propertyPath = path + "/properties/" + named.getKey().replace("~", "~0").replace("/", "~1");
                Map<String, Object> definition = map(named.getValue(), propertyPath);
                if (!baseShape.equals(indexedMapStorageShape(definition))) {
                    throw new UnsupportedOperationException("Indexed map value has a different structural type at "
                            + propertyPath);
                }
                if (!definition.equals(schema.get("additionalProperties"))) {
                    System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                            .log(System.Logger.Level.WARNING,
                                    "Validation-only indexed map key constraints are not enforced by generated DataObjects at "
                                            + resource + propertyPath);
                }
            }
        }
        for (String entry : schema.keySet()) {
            if (!java.util.Set.of("type", "additionalProperties", "propertyNames", "properties",
                    "x-algites-defscodegen-key", "description", "title").contains(entry)) {
                boolean conditionalAllOf = "allOf".equals(entry) && schema.get(entry) instanceof List<?> branches
                        && branches.stream().allMatch(part -> part instanceof Map<?, ?> conditional
                                && java.util.Set.of("if", "then", "else", "contains", "minContains", "maxContains", "not").containsAll(conditional.keySet()));
                if (INDEXED_VALUE_VALIDATION_FACETS.contains(entry) || conditionalAllOf) {
                    System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                            .log(System.Logger.Level.WARNING,
                                    "Validation-only indexed map constraint " + entry
                                            + " is not enforced by generated DataObjects at " + resource + path);
                } else {
                    throw new UnsupportedOperationException("Indexed map structural constraint unsupported at "
                            + path + ": " + entry);
                }
            }
        }
        String keyPath = path + "/propertyNames";
        Map<String, Object> keySchema = schema.containsKey("propertyNames")
                ? map(schema.get("propertyNames"), keyPath) : Map.of("type", "string");
        /* Property names are always JSON strings. An external schema only
         * validates allowed key spellings and must not become a required
         * cross-package field type in the generated storage structure.
         * Local enum references continue to provide typed keys. */
        Object externalKeyRef = keySchema.get("$ref");
        AIiDefsCanonicalStructure keyType;
        if (externalKeyRef instanceof String uri && uri.startsWith("https://")) {
            System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                    .log(System.Logger.Level.WARNING,
                            "Validation-only external propertyNames is not enforced by generated DataObjects at "
                                    + resource + keyPath + ": " + uri);
            keyType = new AIcDefsCanonicalScalar(AIngScalarKind_1.STRING, "");
        } else {
            keyType = jsonNode(keySchema, owner, keyPath, kind, resource);
        }
        if (keyType instanceof AIcDefsCanonicalEnum) {
            /* A propertyNames enum uses the same nominal inline-enum role
             * as an inline enum on an XML element/attribute. */
            keyType = synthetic(owner, fieldName, keyPath, "synthetic_inline_enum_type",
                    keyType, kind, resource, null);
        }
        if (!(keyType instanceof AIcDefsCanonicalScalar || keyType instanceof AIcDefsCanonicalType)) {
            throw new UnsupportedOperationException("Indexed map propertyNames must be scalar or enum at " + path);
        }
        String valuePath = path + "/additionalProperties";
        AIiDefsCanonicalStructure value = jsonNode(map(schema.get("additionalProperties"), valuePath),
                owner, valuePath, kind, resource);
        if (value instanceof AIcDefsCanonicalElementList) {
            value = synthetic(owner, "value", valuePath, "synthetic_map_value_type",
                    value, kind, resource, null);
        }
        if (!(value instanceof AIcDefsCanonicalScalar || value instanceof AIcDefsCanonicalType)) {
            throw new UnsupportedOperationException("Indexed map value must be scalar or named TYPE at " + path);
        }
        var itemFields = new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE, List.of(
                new AIcDefsCanonicalElement(fieldName, keyType, List.of(),
                        binding(kind, resource, keyPath, "synthetic_map_key"), 1, 1),
                new AIcDefsCanonicalElement("value", value, List.of(),
                        binding(kind, resource, valuePath, "synthetic_map_value"), 1, 1)));
        /* Distinct indexed properties require distinct synthetic list-item names.
         * Render the logical field through the configured naming composition. */
        String member = path.substring(path.lastIndexOf('/') + 1).replace("~1", "/").replace("~0", "~");
        var item = synthetic(owner, member, path, "synthetic_list_item_type",
                itemFields, kind, resource, null);
        var key = new AIcDefsCanonicalKeyDefinition(id, member,
                path + "/x-algites-defscodegen-key", List.of(fieldName), true);
        return new AIcDefsCanonicalList(member, item, 0, -1, List.of(key));
    }

    /** Read a nonnegative integral cardinality facet, distinguishing booleans and decimals.
     * @param schema JSON/YAML Schema node
     * @param name facet name
     * @param path source pointer for diagnostics
     * @return exact integer facet, -1 when absent
     * @throws IllegalArgumentException for an invalid facet
     */
    private static int nonnegativeFacet(Map<String, Object> schema, String name, String path) {
        if (!schema.containsKey(name)) return -1;
        Object raw = schema.get(name);
        if (!(raw instanceof Number number) || raw instanceof Float || raw instanceof Double) {
            throw new IllegalArgumentException(name + " requires a nonnegative integer at " + path);
        }
        try {
            int result = new BigDecimal(number.toString()).intValueExact();
            if (result < 0) throw new IllegalArgumentException(name + " must not be negative at " + path);
            return result;
        } catch (ArithmeticException ex) {
            throw new IllegalArgumentException(name + " requires a nonnegative integer at " + path, ex);
        }
    }

    /** Preserve supported scalar restrictions without dropping their lexical precision.
     * @param schema source schema object
     * @param scalar type of scalar
     * @param format optional declared format
     * @param path source pointer for diagnostics
     * @return canonical scalar with typed facets
     * @throws IllegalArgumentException for invalid numeric or length bounds
     * @throws UnsupportedOperationException for constraints on incompatible scalar types
     */
    private static AIcDefsCanonicalScalar scalarFacets(Map<String, Object> schema,
            AIngScalarKind_1 scalar, String format, String path) {
        boolean string = List.of("minLength", "maxLength", "pattern").stream().anyMatch(schema::containsKey);
        boolean numeric = List.of("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf")
                .stream().anyMatch(schema::containsKey);
        if (string && scalar != AIngScalarKind_1.STRING)
            throw new UnsupportedOperationException("String constraints require a string schema at " + path);
        if (numeric && scalar != AIngScalarKind_1.INTEGER && scalar != AIngScalarKind_1.NUMBER)
            throw new UnsupportedOperationException("Numeric constraints require numeric schema at " + path);
        int min = nonnegativeFacet(schema, "minLength", path);
        int max = nonnegativeFacet(schema, "maxLength", path);
        if (max >= 0 && min > max) throw new IllegalArgumentException("minLength exceeds maxLength at " + path);
        String pattern = string(schema.get("pattern"), "");
        if (schema.containsKey("pattern") && !(schema.get("pattern") instanceof String))
            throw new IllegalArgumentException("pattern must be string at " + path);
        if (!pattern.isEmpty()) try { java.util.regex.Pattern.compile(pattern); }
            catch (java.util.regex.PatternSyntaxException e) { throw new IllegalArgumentException("Invalid pattern at " + path, e); }
        String lower = "", upper = "", multiple = "";
        boolean lowerExclusive = false, upperExclusive = false;
        for (String key : List.of("minimum", "maximum", "multipleOf")) {
            if (!schema.containsKey(key)) continue;
            Object raw = schema.get(key);
            if (!(raw instanceof Number number)) throw new IllegalArgumentException(key + " must be number at " + path);
            BigDecimal value = new BigDecimal(number.toString());
            if (key.equals("multipleOf")) {
                if (value.signum() <= 0) throw new IllegalArgumentException("Invalid multipleOf at " + path);
                multiple = value.toPlainString();
            } else if (key.equals("minimum")) lower = value.toPlainString();
            else upper = value.toPlainString();
        }
        for (String key : List.of("exclusiveMinimum", "exclusiveMaximum")) {
            if (!schema.containsKey(key)) continue;
            Object raw = schema.get(key);
            boolean exclusive;
            String bound = key.equals("exclusiveMinimum") ? lower : upper;
            if (raw instanceof Boolean flag) {
                exclusive = flag;
                if (flag && bound.isEmpty()) throw new IllegalArgumentException(key + " lacks bound at " + path);
            } else if (raw instanceof Number number) {
                BigDecimal candidate = new BigDecimal(number.toString());
                BigDecimal inclusive = bound.isEmpty() ? null : new BigDecimal(bound);
                boolean tighter = inclusive == null || (key.equals("exclusiveMinimum")
                        ? candidate.compareTo(inclusive) >= 0 : candidate.compareTo(inclusive) <= 0);
                exclusive = tighter;
                if (tighter) bound = candidate.toPlainString();
            } else throw new IllegalArgumentException("Invalid " + key + " at " + path);
            if (key.equals("exclusiveMinimum")) { lower = bound; lowerExclusive = exclusive; }
            else { upper = bound; upperExclusive = exclusive; }
        }
        if (!lower.isEmpty() && !upper.isEmpty()) {
            int comparison = new BigDecimal(lower).compareTo(new BigDecimal(upper));
            if (comparison > 0 || comparison == 0 && (lowerExclusive || upperExclusive))
                throw new IllegalArgumentException("Unsatisfiable numeric bounds at " + path);
        }
        return new AIcDefsCanonicalScalar(scalar, format, min, max, pattern,
                lower, upper, lowerExclusive, upperExclusive, multiple);
    }

    /** Conjoin inherited and local scalar facets for a named XML simpleType.
     * A constraint chain is represented by its effective scalar bounds.
     * Different regular expressions cannot be represented by the one-pattern
     * contract and are rejected rather than silently discarded.
     *
     * @param parent resolved base scalar including its inherited restrictions
     * @param child additional local facet restrictions
     * @param path declaration location for diagnostics
     * @return scalar with the effective intersection of both restrictions
     * @throws IllegalArgumentException if the intersection is contradictory
     * @throws UnsupportedOperationException if multiple patterns need a composite contract
     */
    private static AIcDefsCanonicalScalar intersectScalarFacets(
            AIcDefsCanonicalScalar parent, AIcDefsCanonicalScalar child, String path) {
        if (parent.scalarKind() != child.scalarKind())
            throw new IllegalArgumentException("XSD simpleType scalar kind mismatch at " + path);
        if (!parent.pattern().isEmpty() && !child.pattern().isEmpty()
                && !parent.pattern().equals(child.pattern()))
            throw new UnsupportedOperationException("Multiple inherited XSD patterns require conjunctive pattern annotations at " + path);
        int minimumLength = Math.max(parent.minLength(), child.minLength());
        int maximumLength = parent.maxLength() < 0 ? child.maxLength()
                : child.maxLength() < 0 ? parent.maxLength()
                : Math.min(parent.maxLength(), child.maxLength());
        if (maximumLength >= 0 && minimumLength > maximumLength)
            throw new IllegalArgumentException("Unsatisfiable inherited XSD length bounds at " + path);
        String lower = parent.minimum();
        boolean lowerExclusive = parent.exclusiveMinimum();
        if (!child.minimum().isEmpty()) {
            int comparison = lower.isEmpty() ? 1 : new BigDecimal(child.minimum()).compareTo(new BigDecimal(lower));
            if (comparison > 0) { lower = child.minimum(); lowerExclusive = child.exclusiveMinimum(); }
            else if (comparison == 0) lowerExclusive |= child.exclusiveMinimum();
        }
        String upper = parent.maximum();
        boolean upperExclusive = parent.exclusiveMaximum();
        if (!child.maximum().isEmpty()) {
            int comparison = upper.isEmpty() ? -1 : new BigDecimal(child.maximum()).compareTo(new BigDecimal(upper));
            if (comparison < 0) { upper = child.maximum(); upperExclusive = child.exclusiveMaximum(); }
            else if (comparison == 0) upperExclusive |= child.exclusiveMaximum();
        }
        if (!lower.isEmpty() && !upper.isEmpty()) {
            int comparison = new BigDecimal(lower).compareTo(new BigDecimal(upper));
            if (comparison > 0 || (comparison == 0 && (lowerExclusive || upperExclusive)))
                throw new IllegalArgumentException("Unsatisfiable inherited XSD numeric bounds at " + path);
        }
        String multiple = parent.multipleOf().isEmpty() ? child.multipleOf() : parent.multipleOf();
        if (!parent.multipleOf().isEmpty() && !child.multipleOf().isEmpty()) {
            BigDecimal a = new BigDecimal(parent.multipleOf());
            BigDecimal b = new BigDecimal(child.multipleOf());
            int scale = Math.max(0, Math.max(a.scale(), b.scale()));
            var ai = a.setScale(scale).unscaledValue().abs();
            var bi = b.setScale(scale).unscaledValue().abs();
            multiple = new BigDecimal(ai.divide(ai.gcd(bi)).multiply(bi), scale)
                    .stripTrailingZeros().toPlainString();
        }
        return new AIcDefsCanonicalScalar(child.scalarKind(),
                parent.format().isEmpty() ? child.format() : parent.format(),
                minimumLength, maximumLength, child.pattern().isEmpty() ? parent.pattern() : child.pattern(),
                lower, upper, lowerExclusive, upperExclusive,
                multiple);
    }

    /** Confirm that an ENUM or CONST member satisfies every projected scalar facet.
     * Once all finite members satisfy the restrictions, the ENUM contract itself
     * implies those facets; therefore no separate intersection kind is needed.
     *
     * @param facets scalar JSON/YAML or parsed XSD restriction facets
     * @param kind declared scalar kind of the finite enumeration
     * @param literal original JSON literal or XSD lexical value
     * @param path source location used in diagnostics
     * @param xmlLexical true when literal uses XSD lexical numeric and pattern rules
     * @throws IllegalArgumentException when a member contradicts a restriction
     * @throws UnsupportedOperationException when a facet is incompatible with the kind
     */
    private static void validateEnumFacets(Map<String, Object> facets, AIngScalarKind_1 kind,
            Object literal, String path, boolean xmlLexical) {
        AIcDefsCanonicalScalar limits = scalarFacets(facets, kind, "", path);
        if (kind == AIngScalarKind_1.STRING) {
            String value = Objects.toString(literal, "");
            if (limits.minLength() >= 0 && value.codePointCount(0, value.length()) < limits.minLength()
                    || limits.maxLength() >= 0 && value.codePointCount(0, value.length()) > limits.maxLength())
                throw new IllegalArgumentException("Enum/const literal violates length constraint at " + path);
            if (!limits.pattern().isEmpty()) {
                var matcher = java.util.regex.Pattern.compile(limits.pattern()).matcher(value);
                if (!(xmlLexical ? matcher.matches() : matcher.find()))
                    throw new IllegalArgumentException("Enum/const literal violates pattern at " + path);
            }
        } else if (kind == AIngScalarKind_1.NUMBER || kind == AIngScalarKind_1.INTEGER) {
            BigDecimal value;
            try { value = new BigDecimal(Objects.toString(literal, "")); }
            catch (NumberFormatException error) {
                throw new IllegalArgumentException("Invalid numeric enum/const literal at " + path, error);
            }
            if (!limits.minimum().isEmpty()) {
                int compare = value.compareTo(new BigDecimal(limits.minimum()));
                if (compare < 0 || compare == 0 && limits.exclusiveMinimum())
                    throw new IllegalArgumentException("Enum/const literal violates minimum at " + path);
            }
            if (!limits.maximum().isEmpty()) {
                int compare = value.compareTo(new BigDecimal(limits.maximum()));
                if (compare > 0 || compare == 0 && limits.exclusiveMaximum())
                    throw new IllegalArgumentException("Enum/const literal violates maximum at " + path);
            }
            if (!limits.multipleOf().isEmpty() &&
                    value.remainder(new BigDecimal(limits.multipleOf())).signum() != 0)
                throw new IllegalArgumentException("Enum/const literal violates multipleOf at " + path);
        }
    }

    /** Intersect all inline scalar allOf facets without dropping any member.
     * Only a supported, typed scalar intersection can be reduced to one
     * canonical SCALAR; non-scalar branches remain explicit failures.
     *
     * @param schema source schema with an inline allOf array
     * @param path source pointer used for precise diagnostics
     * @return effective scalar restrictions from every inline branch
     * @throws IllegalArgumentException if types or limits contradict
     * @throws UnsupportedOperationException if the intersection is not representable
     */
    private static AIcDefsCanonicalScalar jsonInlineScalarAllOf(
            Map<String, Object> schema, String path) {
        List<?> parts = list(schema.get("allOf"));
        if (parts.isEmpty()) throw new IllegalArgumentException("allOf requires a nonempty array at " + path);
        var outer = new java.util.LinkedHashMap<>(schema);
        outer.remove("allOf");
        var sources = new ArrayList<Map<String, Object>>();
        sources.add(outer);
        for (Object part : parts) {
            if (!(part instanceof Map<?, ?>))
                throw new UnsupportedOperationException("Inline non-scalar allOf requires canonical intersection at " + path);
            sources.add(map(part, path));
        }
        var allowed = java.util.Set.of("type", "minLength", "maxLength", "pattern", "format",
                "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "title", "description");
        var declaredTypes = new ArrayList<String>();
        for (var part : sources) {
            if (!allowed.containsAll(part.keySet()))
                throw new UnsupportedOperationException("Inline non-scalar allOf requires canonical intersection at " + path);
            if (part.containsKey("type")) {
                Object raw = part.get("type");
                if (!(raw instanceof String candidate) ||
                        !List.of("string", "number", "integer", "boolean", "null").contains(candidate))
                    throw new UnsupportedOperationException("Inline non-scalar allOf requires canonical intersection at " + path);
                declaredTypes.add(candidate);
            }
        }
        if (declaredTypes.isEmpty())
            throw new UnsupportedOperationException("Untyped inline allOf cannot be represented as a scalar at " + path);
        String type = declaredTypes.contains("integer") &&
                declaredTypes.stream().allMatch(t -> t.equals("integer") || t.equals("number"))
                ? "integer" : declaredTypes.get(0);
        for (String current : declaredTypes) {
            if (!current.equals(type) && !(type.equals("integer") && current.equals("number")))
                throw new IllegalArgumentException("Unsatisfiable scalar allOf types at " + path);
        }
        if (sources.stream().anyMatch(part -> part.containsKey("format")) &&
                !List.of("string", "number", "integer").contains(type))
            throw new UnsupportedOperationException("format on an untyped or non-scalar schema at " + path);
        AIngScalarKind_1 kind = scalarKind(type);
        AIcDefsCanonicalScalar merged = null;
        for (var part : sources) {
            if (part.containsKey("format") && !(part.get("format") instanceof String))
                throw new IllegalArgumentException("format must be a string at " + path);
            AIcDefsCanonicalScalar current = scalarFacets(part, kind, string(part.get("format"), ""), path);
            if (merged == null) merged = current;
            else {
                if (!merged.format().isEmpty() && !current.format().isEmpty()
                        && !merged.format().equals(current.format()))
                    throw new UnsupportedOperationException("Multiple different allOf formats need conjunctive validation at " + path);
                merged = intersectScalarFacets(merged, current, path);
            }
        }
        return merged;
    }

    private AIiDefsCanonicalStructure jsonNode(Map<String, Object> schema, String owner,
            String path, AIngSourceInputKind_1 kind, String resource) {
        // JSON Schema alternatives are validation-only, not structural CHOICE.
        // The explicit Algites choice marker is handled in the object branch.
        for (String assertion : List.of("oneOf", "anyOf")) {
            if (schema.containsKey(assertion)) {
                Object raw = schema.get(assertion);
                if (!(raw instanceof List<?> branches) || branches.isEmpty() ||
                        branches.stream().anyMatch(v -> !(v instanceof Map<?, ?> || v instanceof Boolean))) {
                    throw new IllegalArgumentException("Invalid " + assertion + " at " + path);
                }
                System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                        .log(System.Logger.Level.WARNING, "Validation-only JSON Schema " + assertion
                                + " is not enforced by generated DataObjects at " + resource + path);
            }
        }
        if (schema.containsKey("x-algites-defscodegen-key")) {
            if ("array".equals(schema.get("type"))) {
                return jsonKeyedArray(schema, owner, path, kind, resource);
            }
            return jsonIndexedMap(schema, owner, path, kind, resource);
        }
        for (String keyword : List.of("not", "if", "then", "else", "contains",
                "unevaluatedItems", "unevaluatedProperties", "dependentSchemas", "propertyNames",
                "dependencies", "contentEncoding", "contentMediaType", "contentSchema",
                "dependentRequired", "minContains", "maxContains", "readOnly", "writeOnly")) {
            if (schema.containsKey(keyword)) {
                System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                        .log(System.Logger.Level.WARNING, "Validation-only JSON Schema keyword " + keyword
                                + " is not enforced by generated DataObjects at " + resource + path);
            }
        }
        for (String keyword : List.of("patternProperties", "$dynamicRef", "$recursiveRef", "additionalItems")) {
            if (schema.containsKey(keyword)) {
                throw new UnsupportedOperationException("Unsupported structural schema keyword " + keyword
                        + " at " + path);
            }
        }
        boolean conditionalAllOf = schema.get("allOf") instanceof List<?> parts &&
                !parts.isEmpty() && parts.stream().allMatch(part -> part instanceof Map<?, ?> map &&
                        !map.isEmpty() && java.util.Set.of("if", "then", "else", "contains", "minContains", "maxContains", "not").containsAll(map.keySet()));
        if (conditionalAllOf) {
            System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                    .log(System.Logger.Level.WARNING,
                            "Validation-only allOf assertions are not enforced by generated DataObjects at "
                                    + resource + path);
        } else {
            for (Object part : list(schema.get("allOf"))) {
                if (!(part instanceof Map<?, ?> mapping) || !(mapping.get("$ref") instanceof String)) {
                    return jsonInlineScalarAllOf(schema, path);
                }
            }
        }
        if (schema.get("$ref") instanceof String reference) {
            var constrained = new java.util.TreeSet<String>();
            for (String keyword : List.of("minLength", "maxLength", "pattern", "format",
                    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
                    "minItems", "maxItems", "uniqueItems", "minProperties", "maxProperties",
                    "const", "enum", "properties", "items", "additionalProperties", "required")) {
                if (schema.containsKey(keyword)) constrained.add(keyword);
            }
            if (!constrained.isEmpty()) throw new UnsupportedOperationException(
                    "Ref sibling constraints need canonical intersection at " + path + ": " + constrained);
            return new AIcDefsCanonicalType(reference, reference.substring(reference.lastIndexOf('/') + 1),
                    AIngTypeOrigin_1.DECLARED, List.of(owner, reference), List.of(), null,
                    AIngResolutionState_1.REFERENCE, binding(kind, resource, path, "$ref"));
        }
        Object rawType = schema.get("type");
        String type;
        if (rawType instanceof List<?> types) {
            if (types.size() == 2 && types.contains("null") &&
                    types.stream().allMatch(value -> value instanceof String)) {
                type = (String) (types.get(0).equals("null") ? types.get(1) : types.get(0));
                System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                        .log(System.Logger.Level.WARNING,
                                "Nullable JSON Schema type is represented as " + type
                                        + "; null validation is deferred at " + resource + path);
            } else if (types.size() == 1 && types.get(0) instanceof String singular) {
                type = singular;
            } else {
                throw new UnsupportedOperationException("JSON Schema incompatible type unions "
                        + "are not structurally representable at " + path);
            }
        } else if (rawType instanceof String text) {
            type = text;
        } else if (rawType == null) {
            type = "";
        } else {
            throw new IllegalArgumentException("Invalid JSON Schema type at " + path + ": " + rawType);
        }
        if (!type.isEmpty() && !List.of("object", "array", "string", "integer", "number", "boolean", "null")
                .contains(type)) {
            throw new IllegalArgumentException("Unknown JSON Schema type at " + path + ": " + type);
        }
        /* Reject incompatible conditional facets before object/array/choice
         * branches can silently discard them. Missing JSON type is not itself
         * a type assertion, so inferring a type would also change semantics. */
        for (var family : List.of(
                Map.entry("string", List.of("minLength", "maxLength", "pattern")),
                Map.entry("number", List.of("minimum", "maximum", "exclusiveMinimum",
                        "exclusiveMaximum", "multipleOf")),
                Map.entry("array", List.of("minItems", "maxItems", "uniqueItems")),
                Map.entry("object", List.of("minProperties", "maxProperties")))) {
            boolean applicable = switch (family.getKey()) {
                case "string" -> "string".equals(type);
                case "number" -> "integer".equals(type) || "number".equals(type);
                case "array" -> "array".equals(type) || type.isEmpty() &&
                        (schema.containsKey("items") || schema.containsKey("prefixItems"));
                default -> "object".equals(type) || type.isEmpty() &&
                        (schema.containsKey("properties") || schema.containsKey("additionalProperties"));
            };
            if (!applicable) for (String keyword : family.getValue()) {
                if (schema.containsKey(keyword)) throw new UnsupportedOperationException(
                        "Conditional " + family.getKey() + " constraints require an explicit compatible type at "
                                + path + ": " + keyword);
            }
        }
        if (schema.containsKey("format") && !List.of("string", "number", "integer").contains(type))
            throw new UnsupportedOperationException("format on an untyped or non-scalar schema at " + path);
        /* A scalar `const` is a singleton ENUM in the seven-kind canonical
         * model. Preserve the fixed wire value for later type emission;
         * reject conjunctions that cannot be projected without losing rules. */
        if (schema.containsKey("const")) {
            // A scalar const already implies any restriction satisfied by its
            // only member. Validate scalar facets before reducing to ENUM.
            for (String keyword : List.of("format", "minItems", "maxItems", "uniqueItems",
                    "minProperties", "maxProperties")) {
                if (schema.containsKey(keyword)) throw new UnsupportedOperationException(
                        "Scalar const with additional constraints needs canonical intersection at " + path
                                + ": " + keyword);
            }
            Object value = schema.get("const");
            if (value instanceof Map<?, ?> || value instanceof List<?>) {
                throw new UnsupportedOperationException("Structured JSON Schema const needs a "
                        + "structured-value constraint model at " + path);
            }
            if (schema.containsKey("$ref") || schema.containsKey("oneOf")
                    || schema.containsKey("anyOf") || schema.containsKey("allOf")) {
                throw new UnsupportedOperationException("Combined const/reference/composition constraints "
                        + "need canonical intersection at " + path);
            }
            var actual = inferScalar(value);
            var base = scalarKind(type);
            if (base == AIngScalarKind_1.ANY) base = actual;
            if (base != actual && !(base == AIngScalarKind_1.NUMBER
                    && actual == AIngScalarKind_1.INTEGER)) {
                throw new IllegalArgumentException("JSON Schema const conflicts with declared type at " + path);
            }
            if (schema.containsKey("enum")) {
                boolean memberFound = false;
                for (Object member : list(schema.get("enum"))) {
                    if (sameJsonScalar(member, value)) {
                        memberFound = true;
                        break;
                    }
                }
                if (!memberFound) {
                    throw new IllegalArgumentException("JSON Schema const is not allowed by enum at " + path);
                }
            }
            if (base == AIngScalarKind_1.NUMBER && actual == AIngScalarKind_1.INTEGER)
                base = AIngScalarKind_1.INTEGER;
            validateEnumFacets(schema, base, value, path, false);
            if (base == AIngScalarKind_1.NULL)
                throw new UnsupportedOperationException("Null const needs a nullable literal "
                        + "representation at " + path);
            if (base == AIngScalarKind_1.NUMBER)
                throw new UnsupportedOperationException("Non-integer numeric const needs exact "
                        + "decimal ENUM emission at " + path);
            return new AIcDefsCanonicalEnum(base,
                    List.of(new AIcDefsCanonicalEnumValue(String.valueOf(value), "")));
        }
        if (schema.get("items") instanceof Boolean) {
            throw new UnsupportedOperationException("Boolean items constraints are not yet canonicalized at " + path);
        }
        if (schema.containsKey("enum")) {
            if (schema.containsKey("format")) throw new UnsupportedOperationException(
                    "Enum format assertions require format-aware validation at " + path);
            var raw = list(schema.get("enum"));
            if (raw.isEmpty()) throw new IllegalArgumentException("Empty enum at " + path);
            if ("object".equals(type) || "array".equals(type)) {
                throw new UnsupportedOperationException("Structured enum values cannot be canonicalized at " + path);
            }
            var base = scalarKind(type);
            if (base == AIngScalarKind_1.ANY) base = inferScalar(raw.get(0));
            for (var item : raw) {
                var actual = inferScalar(item);
                if (actual != base && !(base == AIngScalarKind_1.NUMBER
                        && actual == AIngScalarKind_1.INTEGER)) {
                    throw new IllegalArgumentException("Mixed or incompatible enum scalar kinds at "
                            + path + ": " + base + " versus " + actual);
                }
                validateEnumFacets(schema, base, item, path, false);
            }
            List<AIcDefsCanonicalEnumValue> values = new ArrayList<>();
            for (var item : raw) values.add(new AIcDefsCanonicalEnumValue(String.valueOf(item), ""));
            return new AIcDefsCanonicalEnum(base, values);
        }
        if ("object".equals(type) || schema.containsKey("properties") || schema.containsKey("additionalProperties")) {
            if (schema.containsKey("patternProperties")) {
                throw new UnsupportedOperationException("patternProperties intentionally deferred");
            }
            List<AIiDefsCanonicalStructure> members = new ArrayList<>();
            Map<String, Object> properties = schema.containsKey("properties")
                    ? map(schema.get("properties"), path + "/properties") : Map.of();
            List<?> required = list(schema.get("required"));
            if (required.stream().anyMatch(item -> !(item instanceof String))
                    || new java.util.HashSet<>(required).size() != required.size()) {
                throw new IllegalArgumentException("Expected unique string required-property names at " + path);
            }
            if (!properties.keySet().containsAll(required)) {
                throw new UnsupportedOperationException("Required properties without definitions cannot be represented at " + path);
            }
            /* Configured serialized-document schema metadata is not a
             * DataObject property. Match its actual naming-convention values,
             * never a hard-coded "$schema" field. */
            var reserved = new java.util.HashSet<String>();
            for (String role : List.of("data_source_schema_url",
                    "data_source_schema_identifier", "data_source_schema_version")) {
                String configured = naming.schemaMetadata().get(role);
                if (configured != null && !configured.isEmpty()) reserved.add(configured);
            }
            for (var entry : properties.entrySet()) {
                String name = entry.getKey();
                if (reserved.contains(name)) continue;
                String pointer = path + "/properties/" + name.replace("~", "~0").replace("/", "~1");
                var node = jsonNode(map(entry.getValue(), pointer), owner, pointer, kind, resource);
                if (node instanceof AIcDefsCanonicalList indexed && !indexed.keyDefinitions().isEmpty()) {
                    List<AIcDefsCanonicalKeyDefinition> keys = new ArrayList<>();
                    for (var key : indexed.keyDefinitions()) {
                        keys.add(new AIcDefsCanonicalKeyDefinition(key.identifier(), name,
                                key.sourcePointer(), key.fields(), key.required()));
                    }
                    members.add(new AIcDefsCanonicalList(name, indexed.item(),
                            indexed.minItemCount(), indexed.maxItemCount(), keys));
                    continue;
                }
                if (!schema.containsKey("x-algites-defscodegen-choice") &&
                        (node instanceof AIcDefsCanonicalElementList || node instanceof AIcDefsCanonicalEnum)) {
                    /* Inline enums have their own cross-dialect naming role;
                     * inline object properties keep their existing role. */
                    String role = node instanceof AIcDefsCanonicalEnum
                            ? "synthetic_inline_enum_type" : "synthetic_property_type";
                    node = synthetic(owner, name, pointer, role, node, kind, resource, null);
                }
                Map<String, Object> property = map(entry.getValue(), pointer);
                String defaultKind = "";
                String defaultValue = "";
                if (property.containsKey("default")) {
                    Object value = property.get("default");
                    if (value != null && !(value instanceof String || value instanceof Number
                            || value instanceof Boolean)) {
                        throw new UnsupportedOperationException(
                                "Structured JSON/YAML defaults require typed metadata at " + pointer);
                    }
                    defaultKind = "DECLARATION_ONLY";
                    defaultValue = value == null ? "null" : String.valueOf(value);
                }
                members.add(new AIcDefsCanonicalElement(name, node, List.of(),
                        binding(kind, resource, pointer, "properties"),
                        required.contains(name) ? 1 : 0, 1,
                        string(property.get("description"), ""), null,
                        defaultKind, defaultValue, false));
            }
            Object additional = schema.get("additionalProperties");
            boolean unrestricted = Boolean.TRUE.equals(additional)
                    || additional instanceof Map<?, ?> meta &&
                    java.util.Set.of("title", "description", "examples", "default", "$comment")
                            .containsAll(meta.keySet());
            if (unrestricted) {
                System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                        .log(System.Logger.Level.WARNING,
                                "WARNING [DEFS-UNTYPED-ADDITIONAL-PROPERTIES] at " + resource + path
                                + "/additionalProperties: unconstrained additionalProperties ignored by typed "
                                + "DataObject code generation; unknown instance values may be lost on roundtrip. "
                                + "Hint: use \"additionalProperties\": {\"$ref\": \"#/$defs/Item\"} "
                                + "or {\"type\": \"string\"}.");
            }
            if (additional instanceof Map<?, ?> raw && !unrestricted) {
                String pointer = path + "/additionalProperties";
                AIiDefsCanonicalStructure value = jsonNode(map(raw, pointer), owner, pointer, kind, resource);
                if (value instanceof AIcDefsCanonicalScalar scalar &&
                        scalar.scalarKind() == AIngScalarKind_1.ANY) {
                    System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                            .log(System.Logger.Level.WARNING,
                                    "WARNING [DEFS-UNTYPED-ADDITIONAL-PROPERTIES] at " + resource + pointer
                                    + ": no concrete value type; ignoring untyped values. Hint: use "
                                    + "\"additionalProperties\": {\"type\": \"string\"} or a typed $ref.");
                } else {
                    if (value instanceof AIcDefsCanonicalElementList || value instanceof AIcDefsCanonicalEnum) {
                        value = synthetic(owner, "additionalProperties", pointer,
                                "synthetic_map_value_type", value, kind, resource, null);
                    }
                    var integrated = new AIcDefsCanonicalMap("additionalProperties",
                            AIngMapKind_1.INTEGRATED_PROPERTY_MAP,
                            new AIcDefsCanonicalScalar(AIngScalarKind_1.STRING, ""), value,
                            binding(kind, resource, pointer, "additionalProperties"));
                    members.add(integrated);
                }
            }
            int minProperties = nonnegativeFacet(schema, "minProperties", path);
            int maxProperties = nonnegativeFacet(schema, "maxProperties", path);
            if (maxProperties >= 0 && minProperties > maxProperties)
                throw new IllegalArgumentException("minProperties exceeds maxProperties at " + path);
            boolean explicitChoice = schema.containsKey("x-algites-defscodegen-choice");
            if (explicitChoice) {
                if (!Boolean.TRUE.equals(schema.get("x-algites-defscodegen-choice")) ||
                        !"object".equals(type) || properties.size() < 2 || !required.isEmpty() ||
                        minProperties != 1 || maxProperties != 1 ||
                        !Boolean.FALSE.equals(schema.get("additionalProperties"))) {
                    throw new IllegalArgumentException("Invalid x-algites-defscodegen-choice at " + path
                            + ": requires object, >=2 variants, minProperties=1, maxProperties=1, "
                            + "additionalProperties=false and no required fields");
                }
                List<AIiDefsCanonicalStructure> variants = new ArrayList<>();
                int index = 0;
                for (var member : members) {
                    if (!(member instanceof AIcDefsCanonicalElement field)) {
                        throw new IllegalArgumentException("Invalid choice member at " + path);
                    }
                    String pointer = path + "/properties/" + field.name().replace("~", "~0").replace("/", "~1");
                    // Named $defs choice matches XSD named complexType/choice.
                    // Inline alternatives retain the established record payload
                    // contract. Neither creates an extra JSON/YAML wire level.
                    boolean namedChoice = path.startsWith("#/$defs/")
                            && path.indexOf('/', "#/$defs/".length()) < 0;
                    AIiDefsCanonicalStructure branch = field.structure();
                    if (namedChoice || (branch instanceof AIcDefsCanonicalType ref
                            && ref.resolutionState() == AIngResolutionState_1.REFERENCE)) {
                        branch = new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE,
                                List.of(new AIcDefsCanonicalElement(field.name(), branch, List.of(),
                                        binding(kind, resource, pointer, "choice_value"), 1, 1)));
                    }
                    var variant = synthetic(owner, field.name(), pointer,
                            "synthetic_choice_variant_type", branch, kind, resource, index++);
                    variants.add(new AIcDefsCanonicalElement(field.name(), variant, field.keyDefinitions(),
                            field.sourceBindings(), field.minItemCount(), field.maxItemCount(),
                            field.description(), field.xmlWire(), field.defaultKind(),
                            field.defaultValue(), field.isEmptyAllowed(), field.elementKind()));
                }
                members = variants;
            }
            return new AIcDefsCanonicalElementList(
                    explicitChoice ? AIngComposition_1.CHOICE : AIngComposition_1.SEQUENCE,
                    members, 1, 1, minProperties, maxProperties);
        }
        if (schema.containsKey("x-algites-defscodegen-choice")) {
            throw new IllegalArgumentException("Invalid x-algites-defscodegen-choice at " + path
                    + ": choice must be an explicitly declared object");
        }
        if ("array".equals(type) || schema.containsKey("prefixItems") || schema.containsKey("items")) {
            int minItems = optionalBound(schema.get("minItems"), 0, path);
            int maxItems = optionalBound(schema.get("maxItems"), -1, path);
            Object uniqueValue = schema.getOrDefault("uniqueItems", Boolean.FALSE);
            if (!(uniqueValue instanceof Boolean))
                throw new IllegalArgumentException("uniqueItems must be boolean at " + path);
            boolean uniqueItems = (Boolean) uniqueValue;
            AIcDefsCodegenOccurrences.check(minItems, maxItems);
            if (schema.containsKey("prefixItems") && (schema.containsKey("minItems") || schema.containsKey("maxItems") || uniqueItems)) {
                throw new UnsupportedOperationException("Tuple minItems/maxItems constraints require a tuple-length model at " + path);
            }
            List<AIiDefsCanonicalStructure> items = new ArrayList<>();
            int i = 0;
            for (var item : list(schema.get("prefixItems"))) {
                String pointer = path + "/prefixItems/" + i;
                var node = jsonNode(map(item, pointer), owner, pointer, kind, resource);
                var synthetic = synthetic(owner, "item", pointer, "synthetic_positional_item_type",
                        node, kind, resource, i);
                String getter = naming.render("positional_item_synthetic_getter", "item",
                        Map.of("position", Integer.toString(naming.positionalNumber(i))));
                items.add(new AIcDefsCanonicalElement(getter, synthetic, List.of(),
                        binding(kind, resource, pointer, "prefixItems")));
                i++;
            }
            if (schema.get("items") instanceof Map<?, ?> rest) {
                String pointer = path + "/items";
                var node = jsonNode(map(rest, pointer), owner, pointer, kind, resource);
                if (node instanceof AIcDefsCanonicalElementList || node instanceof AIcDefsCanonicalEnum) {
                    node = synthetic(owner, "item", pointer, "synthetic_list_item_type", node, kind, resource, null);
                }
                var listNode = new AIcDefsCanonicalList("items", node, minItems, maxItems, List.of(), null, uniqueItems);
                if (items.isEmpty()) return listNode;
                items.add(listNode);
            }
            if (items.isEmpty()) {
                /* A bare array is unconstrained, not an empty fixed-length tuple. */
                return new AIcDefsCanonicalList("items", new AIcDefsCanonicalScalar(AIngScalarKind_1.ANY, ""), minItems, maxItems, List.of(), null, uniqueItems);
            }
            if (!schema.containsKey("items")) {
                /* prefixItems by itself still permits additional unconstrained entries. */
                items.add(new AIcDefsCanonicalList("items", new AIcDefsCanonicalScalar(AIngScalarKind_1.ANY, "")));
            }
            return new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE, items);
        }
        if (schema.containsKey("required")) throw new IllegalArgumentException("required is valid only for object schemas at " + path);
        if (schema.containsKey("minItems") || schema.containsKey("maxItems") || schema.containsKey("uniqueItems"))
            throw new IllegalArgumentException("minItems/maxItems require an array schema at " + path);
        if (schema.containsKey("minProperties") || schema.containsKey("maxProperties"))
            throw new IllegalArgumentException("Object constraints require object schema at " + path);
        return scalarFacets(schema, scalarKind(type), string(schema.get("format"), ""), path);
    }

    /**
     * Parses a JSON Schema array bound and rejects fractional or boolean values.
     * @param raw raw JSON integer, or null
     * @param fallback default bound
     * @param path source pointer for diagnostics
     * @return a canonical bound value
     */
    private static int optionalBound(Object raw, int fallback, String path) {
        if (raw == null) return fallback;
        if (!(raw instanceof Number number) || !(raw instanceof Byte || raw instanceof Short
                || raw instanceof Integer || raw instanceof Long) || number.longValue() > Integer.MAX_VALUE
                || number.longValue() < 0) {
            throw new IllegalArgumentException("Invalid minItems/maxItems bound at " + path + ": " + raw);
        }
        return number.intValue();
    }

    /**
     * Parses XSD occurrence bounds without losing explicit optional/unbounded cases.
     * @param text XML attribute value, or empty if missing
     * @param fallback specification default value
     * @param upper whether an unbounded maximum is allowed
     * @param path source pointer for diagnostics
     * @return canonical numeric bound
     */
    private static int xmlOccurs(String text, int fallback, boolean upper, String path) {
        if (text == null || text.isEmpty()) return fallback;
        if (upper && "unbounded".equals(text)) return -1;
        try {
            int result = Integer.parseInt(text);
            if (result < 0) throw new NumberFormatException();
            return result;
        } catch (NumberFormatException invalid) {
            throw new IllegalArgumentException("Invalid XSD occurrence at " + path + ": " + text, invalid);
        }
    }

    private AIcDefsCanonicalType synthetic(String owner, String name, String pointer, String role,
            AIiDefsCanonicalStructure node, AIngSourceInputKind_1 kind,
            String resource, Integer index) {
        List<String> segments = new ArrayList<>(List.of(owner, role, name));
        if (index != null) segments.add(index.toString());
        return new AIcDefsCanonicalType(resource + pointer + "#synthetic:" + role,
                naming.syntheticTypeName(role, owner, name, index), AIngTypeOrigin_1.SYNTHETIC,
                segments, List.of(), node, AIngResolutionState_1.RESOLVED,
                binding(kind, resource, pointer, role), "", sourceVersions.getOrDefault(resource, ""), "");
    }

    /** Translate XSD default/fixed facets without materializing defaults in raw storage.
     * @param element XML declaration, local attribute or element
     * @param value canonical value structure
     * @param attribute whether the declaration is an XML attribute
     * @param path diagnostics path
     * @return the default kind, lexical value and empty permission
     * @throws IllegalArgumentException when default and fixed are both declared
     * @throws UnsupportedOperationException for unsupported complex typed defaults
     */
    private static XmlDefault xmlDefault(Element element, AIiDefsCanonicalStructure value,
            boolean attribute, String path) {
        if (element.hasAttribute("default") && element.hasAttribute("fixed")) {
            throw new IllegalArgumentException("XSD default and fixed are mutually exclusive at " + path);
        }
        boolean stringType = value instanceof AIcDefsCanonicalScalar scalar
                && scalar.scalarKind() == AIngScalarKind_1.STRING;
        boolean hasFixed = element.hasAttribute("fixed");
        boolean hasDefault = element.hasAttribute("default");
        if ((hasFixed || hasDefault) && !(value instanceof AIcDefsCanonicalScalar
                || value instanceof AIcDefsCanonicalType || value instanceof AIcDefsCanonicalEnum)) {
            throw new UnsupportedOperationException("Structured XML default/fixed unsupported at " + path);
        }
        return new XmlDefault(hasFixed ? "CONSTRAINT_DEFAULT"
                : hasDefault ? attribute ? "IF_FIELD_VALUE_NOT_PRESENT" : "IF_FIELD_VALUE_EMPTY" : "",
                hasFixed ? element.getAttribute("fixed")
                        : hasDefault ? element.getAttribute("default") : "", stringType);
    }

    /** Parsed XSD declaration default metadata: kind, lexical literal and empty permission.
     * @param kind default kind or empty
     * @param lexical lexical value, possibly empty
     * @param emptyAllowed true for string scalars
     */
    private record XmlDefault(String kind, String lexical, boolean emptyAllowed) { }

    /**
     * Find a named group whose only particle is a repeated reference to one
     * reusable named item group. The outer group supplies the semantic field
     * name; it is not a wire element or an independently allocated object.
     * @param declaration global xs:group to inspect
     * @return repeated group reference, or null when this is an ordinary group
     */
    private static Element xmlNamedListGroup(Element declaration) {
        var particles = elements(declaration).stream().filter(child -> !is(child, "annotation")).toList();
        if (particles.size() != 1 || !is(particles.get(0), "sequence")) return null;
        var members = elements(particles.get(0)).stream().filter(child -> !is(child, "annotation")).toList();
        if (members.size() != 1 || !is(members.get(0), "group")
                || !members.get(0).hasAttribute("ref")
                || !members.get(0).hasAttribute("maxOccurs")
                || "1".equals(members.get(0).getAttribute("maxOccurs"))) return null;
        return members.get(0);
    }

    /**
     * Resolve an xs:group reference in the dedicated group QName namespace.
     * @param element group reference declaration
     * @param path source location for diagnostics
     * @return expanded QName registered by this schema
     */
    private String xmlGroupIdentity(Element element, String path) {
        String qname = element.getAttribute("ref");
        int colon = qname.indexOf(':');
        String prefix = colon < 0 ? null : qname.substring(0, colon);
        String name = colon < 0 ? qname : qname.substring(colon + 1);
        String namespace = element.lookupNamespaceURI(prefix);
        if (colon >= 0 && namespace == null) {
            throw new IllegalArgumentException("Undeclared group QName prefix '" + prefix
                    + "' at " + path);
        }
        String identity = namespace == null || namespace.isEmpty()
                ? name : "{" + namespace + "}" + name;
        if (!localXsdGroups.containsKey(identity)) {
            throw new UnsupportedOperationException("Unresolved or imported xs:group ref "
                    + qname + " at " + path);
        }
        return identity;
    }

    /**
     * Convert a named group reference into either a no-wrapper embedded TYPE
     * or a named LIST of another reusable TYPE. No XML QName is synthesized.
     * @param group reference particle
     * @param owner canonical containing type name
     * @param path source location
     * @param resource source artifact
     * @return resolved canonical group particle
     */
    private AIiDefsCanonicalStructure xmlGroupReference(Element group, String owner,
            String path, String resource) {
        String identity = xmlGroupIdentity(group, resource + path);
        Element definition = localXsdGroups.get(identity);
        String label = definition.getAttribute("name");
        int minimum = xmlOccurs(group.getAttribute("minOccurs"), 1, false, path);
        int maximum = xmlOccurs(group.getAttribute("maxOccurs"), 1, true, path);
        Element inner = xmlNamedListGroup(definition);
        if (inner != null) {
            if (maximum != 1) throw new UnsupportedOperationException(
                    "Repeated outer named list group is ambiguous at " + resource + path);
            String innerIdentity = xmlGroupIdentity(inner, resource + path);
            if (identity.equals(innerIdentity) || xmlNamedListGroup(localXsdGroups.get(innerIdentity)) != null) {
                throw new IllegalArgumentException("Cyclic/nested named list group " + label
                        + " at " + resource + path);
            }
            var item = new AIcDefsCanonicalType(innerIdentity,
                    localXsdGroups.get(innerIdentity).getAttribute("name"), AIngTypeOrigin_1.DECLARED,
                    List.of(owner, label), List.of(), null, AIngResolutionState_1.REFERENCE,
                    binding(AIngSourceInputKind_1.XMLDEFS, resource, path, "xs:group/@ref"));
            int innerMin = xmlOccurs(inner.getAttribute("minOccurs"), 1, false, path);
            int innerMax = xmlOccurs(inner.getAttribute("maxOccurs"), 1, true, path);
            return new AIcDefsCanonicalList(label, item, minimum == 0 ? 0 : innerMin, innerMax);
        }
        var item = new AIcDefsCanonicalType(identity, label, AIngTypeOrigin_1.DECLARED,
                List.of(owner, label), List.of(), null, AIngResolutionState_1.REFERENCE,
                binding(AIngSourceInputKind_1.XMLDEFS, resource, path, "xs:group/@ref"));
        if (maximum == -1 || maximum > 1) {
            return new AIcDefsCanonicalList(label, item, minimum, maximum);
        }
        return new AIcDefsCanonicalElement(label, item, List.of(),
                binding(AIngSourceInputKind_1.XMLDEFS, resource, path, "xs:group"),
                minimum, maximum, "", null, "", "", false, AIngElementKind_1.EMBEDDED);
    }

    private AIiDefsCanonicalStructure xmlNode(Element element, String owner, String path,
            String resource, java.util.Set<String> declared, boolean optionalContext,
            List<String> ignoredWildcards) {
        String tag = element.getLocalName();
        var kind = AIngSourceInputKind_1.XMLDEFS;
        if ("group".equals(tag)) {
            if (element.hasAttribute("ref")) return xmlGroupReference(element, owner, path, resource);
            if (!element.hasAttribute("name")) throw new IllegalArgumentException(
                    "xs:group requires name or ref at " + resource + path);
            var particles = elements(element).stream().filter(child -> !is(child, "annotation")).toList();
            if (particles.size() != 1 || !List.of("sequence", "all", "choice")
                    .contains(particles.get(0).getLocalName())) {
                throw new UnsupportedOperationException("Named xs:group requires one compositor at "
                        + resource + path);
            }
            return xmlNode(particles.get(0), owner, path + "/group", resource,
                    declared, optionalContext, ignoredWildcards);
        }
        if ("any".equals(tag) || "anyAttribute".equals(tag)) {
            /* An attribute wildcard has no minItemCount and is never a required field.
             * xs:any is mandatory unless its own particle or an enclosing group
             * makes it optional. Neither wildcard becomes a generated field. */
            boolean optional = "anyAttribute".equals(tag) || optionalContext
                    || "0".equals(element.getAttribute("minOccurs"));
            if (!optional) {
                throw new UnsupportedOperationException("Required XSD wildcard xs:" + tag
                        + " cannot be represented as a DataObject field at " + resource + path
                        + ". Hint: replace the wildcard with a named typed xs:element or xs:attribute declaration.");
            }
            String original;
            try {
                var transformer = TransformerFactory.newInstance().newTransformer();
                transformer.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "yes");
                StringWriter writer = new StringWriter();
                transformer.transform(new DOMSource(element), new StreamResult(writer));
                original = writer.toString().trim();
            } catch (javax.xml.transform.TransformerException invalid) {
                throw new IllegalArgumentException("Unable to retain XSD wildcard declaration at "
                        + path, invalid);
            }
            String hint = "anyAttribute".equals(tag)
                    ? "<xs:attribute name=\"Extra\" type=\"xs:string\"/>"
                    : "<xs:element name=\"Extra\" type=\"xs:string\" minOccurs=\"0\"/>";
            String diagnostic = "Ignored optional XML wildcard xs:" + tag + " at " + resource + path
                    + ": " + original + ". Hint: declare explicit typed fields instead, e.g. " + hint
                    + "; arbitrary wildcard values are not represented in DataObject and may be lost on roundtrip.";
            System.getLogger(AIcDefsCodegenCanonicalSchemaFrontend.class.getName())
                    .log(System.Logger.Level.WARNING, diagnostic);
            ignoredWildcards.add(diagnostic);
            return null;
        }
        if ("simpleType".equals(tag)) {
            Element restriction = first(element, "restriction");
            if (restriction != null) {
                String baseReference = xmlTypeIdentity(restriction,
                        restriction.getAttribute("base"), declared);
                AIcDefsCanonicalScalar inheritedScalar = null;
                AIngScalarKind_1 base;
                if (!baseReference.startsWith("@xs:")) {
                    Element definition = localXsdSimpleTypes.get(baseReference);
                    if (definition == null) {
                        throw new UnsupportedOperationException("XSD simpleType restriction base is not a local scalar: " + baseReference);
                    }
                    if (!resolvingXsdSimpleTypes.add(baseReference)) {
                        throw new IllegalArgumentException("Cyclic XSD simpleType restriction at " + path + ": " + baseReference);
                    }
                    AIiDefsCanonicalStructure resolved;
                    try {
                        resolved = xmlNode(definition, owner, path + "/base", resource,
                                declared, optionalContext, ignoredWildcards);
                    } finally {
                        resolvingXsdSimpleTypes.remove(baseReference);
                    }
                    if (!(resolved instanceof AIcDefsCanonicalScalar scalarAlias)) {
                        throw new UnsupportedOperationException("Restriction of an XSD enum base needs explicit enum narrowing: " + path);
                    }
                    inheritedScalar = scalarAlias;
                    base = scalarAlias.scalarKind();
                } else {
                    base = scalarKindXsd(baseReference.substring(4));
                }
                if (base == AIngScalarKind_1.ANY
                        && !List.of("anyType", "anySimpleType").contains(baseReference.substring(4))) {
                    throw new UnsupportedOperationException("Unsupported XSD scalar base " + baseReference);
                }
                List<AIcDefsCanonicalEnumValue> values = new ArrayList<>();
                Map<String, Object> facets = new java.util.LinkedHashMap<>();
                for (var value : elements(restriction)) {
                    String facet = value.getLocalName();
                    if (is(value, "enumeration")) {
                        values.add(new AIcDefsCanonicalEnumValue(value.getAttribute("value"), ""));
                        continue;
                    }
                    if (is(value, "annotation")) continue;
                    String literal = value.getAttribute("value");
                    if (!value.hasAttribute("value"))
                        throw new IllegalArgumentException("Missing XML facet value for " + facet);
                    switch (facet) {
                        case "length" -> {
                            facets.put("minLength", Integer.parseInt(literal));
                            facets.put("maxLength", Integer.parseInt(literal));
                        }
                        case "minLength", "maxLength" -> {
                            if (facets.containsKey(facet)) throw new UnsupportedOperationException("Repeated XML facet " + facet);
                            facets.put(facet, Integer.parseInt(literal));
                        }
                        case "pattern" -> {
                            if (facets.containsKey(facet)) throw new UnsupportedOperationException("Repeated XML pattern facet");
                            facets.put(facet, literal);
                        }
                        case "minInclusive", "maxInclusive", "minExclusive", "maxExclusive" -> {
                            boolean lower = facet.startsWith("min");
                            String bound = lower ? "minimum" : "maximum";
                            if (facets.containsKey(bound)) throw new UnsupportedOperationException("Conflicting XSD bound facets");
                            facets.put(bound, new BigDecimal(literal));
                            if (facet.endsWith("Exclusive"))
                                facets.put(lower ? "exclusiveMinimum" : "exclusiveMaximum", Boolean.TRUE);
                        }
                        default -> throw new UnsupportedOperationException("Unsupported XML restriction facet " + facet);
                    }
                }
                if (!values.isEmpty()) {
                    for (var item : values) validateEnumFacets(
                            facets, base, item.wireValue(), path, true);
                    return new AIcDefsCanonicalEnum(base, values);
                }
                AIcDefsCanonicalScalar localScalar = scalarFacets(facets, base, "", path);
                return inheritedScalar == null ? localScalar : intersectScalarFacets(inheritedScalar, localScalar, path);
            }
            for (var child : elements(element)) {
                if (!is(child, "annotation")) {
                    throw new UnsupportedOperationException("Unsupported XML simpleType without xs:restriction at " + path);
                }
            }
            return new AIcDefsCanonicalScalar(AIngScalarKind_1.ANY, "");
        }
        if (List.of("sequence", "all", "choice").contains(tag)) {
            AIngComposition_1 composition = switch (tag) {
                case "all" -> AIngComposition_1.ALL;
                case "choice" -> AIngComposition_1.CHOICE;
                default -> AIngComposition_1.SEQUENCE;
            };
            List<AIiDefsCanonicalStructure> children = new ArrayList<>();
            int index = 0;
            for (var child : elements(element)) {
                if (List.of("element", "sequence", "all", "choice", "any", "group").contains(child.getLocalName())) {
                    var nested = xmlNode(child, owner, path + "/" + tag + "/" + index,
                            resource, declared, optionalContext
                                    || "0".equals(element.getAttribute("minOccurs")), ignoredWildcards);
                    if (nested instanceof AIcDefsCanonicalElementList group
                            && composition != AIngComposition_1.CHOICE) {
                        String groupName = switch (child.getLocalName()) {
                            case "choice" -> "Choice";
                            case "all" -> "All";
                            default -> "Sequence";
                        };
                        String groupPath = path + "/" + tag + "/" + index;
                        var groupType = synthetic(owner, groupName, groupPath,
                                "synthetic_group_type", group, AIngSourceInputKind_1.XMLDEFS,
                                resource, index);
                        children.add(new AIcDefsCanonicalElement(groupName + (index + 1),
                                groupType, List.of(), Map.of(),
                                group.minItemCount(), group.maxItemCount(), "", null,
                                "", "", false, AIngElementKind_1.EMBEDDED));
                    } else if (nested != null) children.add(nested);
                } else if (!is(child, "annotation")) {
                    throw new UnsupportedOperationException("Unsupported XML group child "
                            + child.getLocalName() + " at " + path);
                }
                index++;
            }
            int minimum = xmlOccurs(element.getAttribute("minOccurs"), 1, false, path);
            int maximum = xmlOccurs(element.getAttribute("maxOccurs"), 1, true, path);
            if (composition == AIngComposition_1.CHOICE && minimum == 1 && maximum == 1) {
                /* An xs:choice declares storage alternatives, exactly like an
                 * explicit JSON/YAML choice. Keep XML wire metadata inside
                 * each immutable named variant, rather than treating the
                 * alternatives as unrelated scalar properties. */
                List<AIiDefsCanonicalStructure> selected = new ArrayList<>();
                for (int position = 0; position < children.size(); position++) {
                    AIiDefsCanonicalStructure candidate = children.get(position);
                    if (candidate instanceof AIcDefsCanonicalElementList sequence
                            && sequence.composition() == AIngComposition_1.SEQUENCE) {
                        if (sequence.children().isEmpty() || sequence.children().stream()
                                .anyMatch(part -> !(part instanceof AIcDefsCanonicalElement))) {
                            throw new UnsupportedOperationException(
                                    "Nested XML choice sequence requires fields at " + resource + path);
                        }
                        String groupName = sequence.children().stream()
                                .map(part -> ((AIcDefsCanonicalElement) part).name())
                                .collect(java.util.stream.Collectors.joining());
                        candidate = new AIcDefsCanonicalElement(groupName,
                                synthetic(owner, groupName, path + "/" + tag + "/" + position,
                                        "synthetic_group_type", sequence,
                                        AIngSourceInputKind_1.XMLDEFS, resource, null),
                                List.of(), Map.of(), 1, 1, "", null,
                                "", "", false, AIngElementKind_1.EMBEDDED);
                    }
                    if (!(candidate instanceof AIcDefsCanonicalElement field)
                            || field.maxItemCount() != 1) {
                        throw new UnsupportedOperationException(
                                "XML choice requires single-valued element alternatives at " + path);
                    }
                    var variant = synthetic(owner, field.name(), path + "/" + tag + "/" + position,
                            "synthetic_choice_variant_type",
                            new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE, List.of(field)),
                            AIngSourceInputKind_1.XMLDEFS, resource, position);
                    selected.add(new AIcDefsCanonicalElement(field.name(), variant,
                            field.keyDefinitions(), field.sourceBindings(), 0, 1,
                            field.description(), field.xmlWire(), field.defaultKind(),
                            field.defaultValue(), field.isEmptyAllowed(), field.elementKind()));
                }
                children = selected;
            }
            return new AIcDefsCanonicalElementList(composition, children, minimum, maximum);
        }
        if (List.of("complexType", "complexContent", "extension", "restriction").contains(tag)) {
            List<AIiDefsCanonicalStructure> groups = new ArrayList<>();
            for (var child : elements(element)) {
                if (List.of("sequence", "all", "choice", "complexContent", "extension", "restriction", "group")
                        .contains(child.getLocalName())) {
                    groups.add(xmlNode(child, owner, path + "/" + child.getLocalName(), resource,
                            declared, optionalContext, ignoredWildcards));
                } else if (is(child, "attribute")) {
                    groups.add(xmlNode(child, owner, path + "/attribute/" + child.getAttribute("name"),
                            resource, declared, optionalContext, ignoredWildcards));
                } else if (is(child, "anyAttribute")) {
                    xmlNode(child, owner, path + "/anyAttribute", resource,
                            declared, optionalContext, ignoredWildcards);
                } else if (!is(child, "annotation")) {
                    throw new UnsupportedOperationException("Unsupported XML complexType child " + child.getLocalName());
                }
            }
            if (groups.size() == 1 && groups.get(0) instanceof AIcDefsCanonicalElementList) {
                return groups.get(0);
            }
            var particles = groups.stream().filter(AIcDefsCanonicalElementList.class::isInstance)
                    .map(AIcDefsCanonicalElementList.class::cast).toList();
            if (!particles.isEmpty()) {
                var particle = particles.get(0);
                if (particles.size() != 1 || !List.of(AIngComposition_1.SEQUENCE, AIngComposition_1.ALL)
                        .contains(particle.composition()) || particle.minItemCount() != 1 || particle.maxItemCount() != 1) {
                    throw new UnsupportedOperationException("XML group plus attributes requires "
                            + "SEQUENCE/ALL with cardinality 1..1 at " + path);
                }
                List<AIiDefsCanonicalStructure> flattened = new ArrayList<>();
                for (var group : groups) {
                    if (group instanceof AIcDefsCanonicalElementList nested) flattened.addAll(nested.children());
                    else flattened.add(group);
                }
                return new AIcDefsCanonicalElementList(particle.composition(), flattened);
            }
            return new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE, groups);
        }
        if ("attribute".equals(tag)) {
            if (element.hasAttribute("ref")) {
                throw new UnsupportedOperationException("Referenced XML attribute unsupported at " + path);
            }
            String name = element.getAttribute("name");
            if (name.isBlank()) throw new IllegalArgumentException("XSD attribute needs a name at " + path);
            String use = element.hasAttribute("use") ? element.getAttribute("use") : "optional";
            if (!List.of("optional", "required").contains(use)) {
                throw new UnsupportedOperationException("Unsupported XML attribute use " + use + " at " + path);
            }
            AIiDefsCanonicalStructure value;
            if (element.hasAttribute("type")) {
                String reference = xmlTypeIdentity(element, element.getAttribute("type"), declared);
                if (!reference.startsWith("@xs:")) {
                    Element declaration = localXsdSimpleTypes.get(reference);
                    AIiDefsCanonicalStructure resolved = declaration == null ? null
                            : xmlNode(declaration, owner, path, resource, declared, optionalContext, ignoredWildcards);
                    value = resolved instanceof AIcDefsCanonicalScalar ? resolved
                            : new AIcDefsCanonicalType(reference, local(element.getAttribute("type")),
                                    AIngTypeOrigin_1.DECLARED, List.of(owner, name), List.of(), null,
                                    AIngResolutionState_1.REFERENCE,
                                    binding(kind, resource, path, "xs:attribute/@type"));
                } else {
                    var scalar = scalarKindXsd(reference.substring(4));
                    if (scalar == AIngScalarKind_1.ANY) {
                        throw new UnsupportedOperationException("Unsupported XML attribute type " + reference);
                    }
                    value = new AIcDefsCanonicalScalar(scalar, "");
                }
            } else {
                Element inline = first(element, "simpleType");
                value = inline == null ? new AIcDefsCanonicalScalar(AIngScalarKind_1.STRING, "")
                        : xmlNode(inline, owner, path, resource, declared, optionalContext, ignoredWildcards);
            }
            if (value instanceof AIcDefsCanonicalEnum && !element.hasAttribute("type")) {
                value = synthetic(owner, name, path, "synthetic_inline_enum_type",
                        value, kind, resource, null);
            }
            var defaults = xmlDefault(element, value, true, path);
            return new AIcDefsCanonicalElement(name, value, List.of(),
                    binding(kind, resource, path, "xs:attribute"), "required".equals(use) ? 1 : 0, 1,
                    xmlDescription(element), xmlWire(element, name, AIngXmlWireNameValueKind_1.ATTRIBUTE),
                    defaults.kind(), defaults.lexical(), defaults.emptyAllowed());
        }
        if ("element".equals(tag)) {
            if (element.hasAttribute("nillable") && !"false".equals(element.getAttribute("nillable"))) {
                throw new UnsupportedOperationException("Nillable XSD elements require null semantics at " + path);
            }
            if (element.hasAttribute("substitutionGroup")) {
                throw new UnsupportedOperationException("XSD substitutionGroup requires an element resolver at " + path);
            }
            List<Element> constraints = new ArrayList<>();
            for (var child : elements(element)) {
                if (is(child, "key") || is(child, "unique")) constraints.add(child);
                if (is(child, "keyref") || is(child, "identityConstraint")) {
                    throw new UnsupportedOperationException("XSD keyref/identityConstraint unsupported at " + path);
                }
            }
            if (element.hasAttribute("ref")) {
                throw new UnsupportedOperationException(
                        "External XML element declaration references require an element resolver");
            }
            String name = element.hasAttribute("name") ? element.getAttribute("name") :
                    element.hasAttribute("ref") ? element.getAttribute("ref") : "unnamed";
            String rawType = element.getAttribute("type");
            AIiDefsCanonicalStructure value;
            if (!rawType.isEmpty()) {
                String type = xmlTypeIdentity(element, rawType, declared);
                if (type.startsWith("@xs:")) {
                    String builtinName = type.substring(4);
                    var builtin = scalarKindXsd(builtinName);
                    if (builtin == AIngScalarKind_1.ANY
                            && !List.of("anyType", "anySimpleType").contains(builtinName)) {
                        throw new UnsupportedOperationException("Unsupported XSD built-in type "
                                + rawType + " at " + resource + path);
                    }
                    value = new AIcDefsCanonicalScalar(builtin, "");
                } else {
                    Element declaration = localXsdSimpleTypes.get(type);
                    AIiDefsCanonicalStructure resolved = declaration == null ? null
                            : xmlNode(declaration, owner, path, resource, declared, optionalContext, ignoredWildcards);
                    value = resolved instanceof AIcDefsCanonicalScalar ? resolved
                            : new AIcDefsCanonicalType(type, local(rawType), AIngTypeOrigin_1.DECLARED,
                                    List.of(owner, name), List.of(), null, AIngResolutionState_1.REFERENCE,
                                    binding(kind, resource, path, "xs:element/@type"));
                }
            } else {
                Element inline = first(element, "complexType");
                if (inline == null) inline = first(element, "simpleType");
                value = inline == null ? new AIcDefsCanonicalScalar(AIngScalarKind_1.ANY, "")
                        : xmlNode(inline, owner, path, resource, declared, optionalContext, ignoredWildcards);
            }
            if (value instanceof AIcDefsCanonicalEnum && rawType.isEmpty()) {
                value = synthetic(owner, name, path, "synthetic_inline_enum_type",
                        value, kind, resource, null);
            }
            // Identity constraints are scoped to this element occurrence.
            // Parsing its named TYPE for selector validation must never create
            // a derived or synthetic copy of the shared nominal definition.
            List<AIcDefsCanonicalKeyDefinition> scopedKeys = new ArrayList<>();
            if (!constraints.isEmpty()) {
                AIiDefsCanonicalStructure inspected = value;
                if (value instanceof AIcDefsCanonicalType reference) {
                    Element declaration = localXsdComplexTypes.get(reference.identity());
                    java.util.Set<String> definitionNames = declared;
                    if (declaration == null) {
                        declaration = importedComplexTypes.get(reference.identity());
                        if (declaration != null) {
                            definitionNames = new java.util.HashSet<>();
                            for (var candidate : elements(declaration.getOwnerDocument().getDocumentElement())) {
                                if ((is(candidate, "complexType") || is(candidate, "simpleType"))
                                        && candidate.hasAttribute("name"))
                                    definitionNames.add(candidate.getAttribute("name"));
                            }
                        }
                    }
                    if (declaration != null)
                        inspected = xmlNode(declaration, owner, path + "/@type", resource,
                                definitionNames, optionalContext, ignoredWildcards);
                }
                if (!(inspected instanceof AIcDefsCanonicalElementList group)) {
                    throw new UnsupportedOperationException("Local XSD keys require a resolved object TYPE at "
                            + resource + path + ": " + rawType);
                }
                java.util.Set<String> keyNames = new java.util.HashSet<>();
                int keyIndex = 0;
                for (var constraint : constraints) {
                    String keyName = constraint.getAttribute("name");
                    Element selectorNode = first(constraint, "selector");
                    List<String> paths = new ArrayList<>();
                    for (var candidate : elements(constraint)) {
                        if (is(candidate, "field")) {
                            if (!candidate.hasAttribute("xpath") || candidate.getAttribute("xpath").isBlank())
                                throw new IllegalArgumentException("Missing XSD key field XPath at " + resource + path);
                            paths.add(candidate.getAttribute("xpath"));
                        } else if (!(is(candidate, "selector") || is(candidate, "annotation"))) {
                            throw new UnsupportedOperationException("Unknown XSD identity constraint child at "
                                    + resource + path);
                        }
                    }
                    if (keyName.isBlank() || !keyNames.add(keyName) || selectorNode == null
                            || !selectorNode.hasAttribute("xpath") || paths.isEmpty()) {
                        throw new IllegalArgumentException("XSD key/unique requires unique name, selector, fields at "
                                + resource + path);
                    }
                    String selector = selectorNode.getAttribute("xpath");
                    String selected = selector.startsWith("./") ? selector.substring(2) : selector;
                    long hits = group.children().stream().filter(child -> child instanceof AIcDefsCanonicalList list
                            && list.name().equals(selected)).count();
                    if (hits != 1) {
                        throw new UnsupportedOperationException("XSD key selector must target exactly one directly "
                                + "repeated element: " + selector + " at " + resource + path);
                    }
                    scopedKeys.add(new AIcDefsCanonicalKeyDefinition(keyName, selector,
                            path + "/" + constraint.getLocalName() + "/" + keyIndex++, paths,
                            is(constraint, "key")));
                }
            }
            if (value instanceof AIcDefsCanonicalElementList) {
                value = synthetic(owner, name, path, "synthetic_property_type", value,
                        kind, resource, null);
            }
            int minimum = xmlOccurs(element.getAttribute("minOccurs"), 1, false, path);
            int maximum = xmlOccurs(element.getAttribute("maxOccurs"), 1, true, path);
            AIcDefsCodegenOccurrences.check(minimum, maximum);
            AIcDefsCanonicalXmlWireName wire = xmlWire(element, name, AIngXmlWireNameValueKind_1.ELEMENT);
            if (maximum == -1 || maximum > 1) {
                if (!scopedKeys.isEmpty()) throw new UnsupportedOperationException(
                        "Contextual XSD keys on a repeated owner require separate scope at " + resource + path);
                if (element.hasAttribute("default") || element.hasAttribute("fixed")) {
                    throw new UnsupportedOperationException(
                            "Repeated XML element defaults/fixed require per-item metadata at " + path);
                }
                return new AIcDefsCanonicalList(name, value, minimum, maximum, List.of(), wire);
            }
            var defaults = xmlDefault(element, value, false, path);
            return new AIcDefsCanonicalElement(name, value, scopedKeys,
                    binding(kind, resource, path, "xs:element"), minimum, maximum,
                    xmlDescription(element), wire, defaults.kind(), defaults.lexical(),
                    defaults.emptyAllowed());
        }
        throw new IllegalArgumentException("Unsupported XML schema construct " + tag);
    }

    /**
     * Resolves a locally declared element/attribute QName using the schema's form defaults.
     * @param element XSD declaration
     * @param name unprefixed local field name
     * @param valueKind element or attribute representation
     * @return exact XML wire identity for serialization and SDO metadata
     * @throws IllegalArgumentException for an unknown form override
     */
    private static AIcDefsCanonicalXmlWireName xmlWire(Element element, String name,
            AIngXmlWireNameValueKind_1 valueKind) {
        Element schema = element.getOwnerDocument().getDocumentElement();
        String attribute = valueKind == AIngXmlWireNameValueKind_1.ELEMENT
                ? "elementFormDefault" : "attributeFormDefault";
        String fallback = schema.hasAttribute(attribute) ? schema.getAttribute(attribute) : "unqualified";
        String form = element.hasAttribute("form") ? element.getAttribute("form") : fallback;
        if (!List.of("qualified", "unqualified").contains(form)) {
            throw new IllegalArgumentException("Invalid XML form for " + name + ": " + form);
        }
        String namespace = "qualified".equals(form) ? schema.getAttribute("targetNamespace") : "";
        return new AIcDefsCanonicalXmlWireName(namespace, name, valueKind);
    }

    private static Map<AIngSourceInputKind_1, List<AIcDefsCanonicalSourceBinding>> binding(
            AIngSourceInputKind_1 kind, String resource, String path, String representation) {
        return Map.of(kind, List.of(new AIcDefsCanonicalSourceBinding(resource, path, representation)));
    }

    /**
     * Extracts source documentation without treating XSD annotation markup as text.
     *
     * @param element declaration whose annotation is examined
     * @return first xs:documentation text, empty when undocumented
     */
    private static String xmlDescription(Element element) {
        for (var child : elements(element)) {
            if (is(child, "annotation")) {
                for (var documentation : elements(child)) {
                    if (is(documentation, "documentation")) {
                        return documentation.getTextContent().trim();
                    }
                }
            }
        }
        return "";
    }

    private static String string(Object input, String fallback) {
        return input instanceof String value && !value.isEmpty() ? value : fallback;
    }

    private static String local(String qname) {
        return qname.substring(qname.lastIndexOf(':') + 1);
    }

    /**
     * Resolves the lexical prefix of a QName-valued XSD type attribute in the
     * declaration's real namespace context. Built-in XML Schema types are
     * tagged distinctly from locally declared types, even when they share a name.
     *
     * @param element containing declaration, whose in-scope prefix bindings are used
     * @param qname QName-valued type or extension base attribute
     * @param declared names of types declared in the current XSD document
     * @return a canonical expanded local identity, or an @xs:-prefixed built-in name
     * @throws IllegalArgumentException when the QName prefix has no namespace binding
     * @throws UnsupportedOperationException for external or unresolved types
     */
    private String xmlTypeIdentity(Element element, String qname, java.util.Set<String> declared) {
        if (qname == null || qname.isEmpty()) {
            throw new IllegalArgumentException("Empty XSD type QName");
        }
        int separator = qname.indexOf(':');
        String prefix = separator < 0 ? null : qname.substring(0, separator);
        String name = separator < 0 ? qname : qname.substring(separator + 1);
        String namespace = element.lookupNamespaceURI(prefix);
        if (separator >= 0 && namespace == null) {
            throw new IllegalArgumentException("Undeclared XSD QName prefix '" + prefix + "' in " + qname);
        }
        if (XS.equals(namespace)) {
            return "@xs:" + name;
        }
        String targetNamespace = element.getOwnerDocument().getDocumentElement().getAttribute("targetNamespace");
        if (declared.contains(name)
                && (namespace == null || namespace.isEmpty() || namespace.equals(targetNamespace))) {
            return targetNamespace.isEmpty() ? name : "{" + targetNamespace + "}" + name;
        }
        String expanded = "{" + namespace + "}" + name;
        if (importedTypes.contains(expanded)) return expanded;
        throw new UnsupportedOperationException("Unresolved or external XSD QName '" + qname
                + "' (namespace '" + namespace + "')");
    }

    /**
     * Compare JSON scalar values with JSON numeric equality but without
     * accidentally treating Java booleans as numbers.
     *
     * @param first a parsed JSON scalar
     * @param second another parsed JSON scalar
     * @return whether they denote the same JSON scalar value
     */
    private static boolean sameJsonScalar(Object first, Object second) {
        if (first instanceof Number left && second instanceof Number right) {
            return new java.math.BigDecimal(left.toString()).compareTo(
                    new java.math.BigDecimal(right.toString())) == 0;
        }
        return Objects.equals(first, second);
    }

    private static AIngScalarKind_1 scalarKind(String type) {
        return switch (type) {
            case "string" -> AIngScalarKind_1.STRING;
            case "integer" -> AIngScalarKind_1.INTEGER;
            case "number" -> AIngScalarKind_1.NUMBER;
            case "boolean" -> AIngScalarKind_1.BOOLEAN;
            case "null" -> AIngScalarKind_1.NULL;
            default -> AIngScalarKind_1.ANY;
        };
    }

    private static AIngScalarKind_1 inferScalar(Object value) {
        if (value instanceof Boolean) return AIngScalarKind_1.BOOLEAN;
        if (value instanceof Byte || value instanceof Short || value instanceof Integer ||
                value instanceof Long || value instanceof java.math.BigInteger)
            return AIngScalarKind_1.INTEGER;
        if (value instanceof Number) return AIngScalarKind_1.NUMBER;
        if (value == null) return AIngScalarKind_1.NULL;
        return AIngScalarKind_1.STRING;
    }

    private static AIngScalarKind_1 scalarKindXsd(String qname) {
        return switch (local(qname)) {
            case "string", "normalizedString", "token", "anyURI", "date", "dateTime" -> AIngScalarKind_1.STRING;
            case "int", "integer", "long", "short", "positiveInteger", "nonNegativeInteger" -> AIngScalarKind_1.INTEGER;
            case "decimal", "float", "double" -> AIngScalarKind_1.NUMBER;
            case "boolean" -> AIngScalarKind_1.BOOLEAN;
            default -> AIngScalarKind_1.ANY;
        };
    }

    private static List<?> list(Object value) {
        if (value == null) return List.of();
        if (value instanceof List<?> list) return list;
        throw new IllegalArgumentException("Expected source list, got " + value.getClass().getName());
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> map(Object value, String path) {
        if (!(value instanceof Map<?, ?> source)) throw new IllegalArgumentException("Expected object at " + path);
        for (var key : source.keySet()) {
            if (!(key instanceof String)) throw new IllegalArgumentException("Non-string object key at " + path);
        }
        return (Map<String, Object>) source;
    }

    private static boolean is(Element node, String localName) {
        return XS.equals(node.getNamespaceURI()) && localName.equals(node.getLocalName());
    }

    private static List<Element> elements(Element parent) {
        List<Element> result = new ArrayList<>();
        for (Node child = parent.getFirstChild(); child != null; child = child.getNextSibling()) {
            if (child instanceof Element element && XS.equals(element.getNamespaceURI())) result.add(element);
        }
        return result;
    }

    private static Element first(Element parent, String localName) {
        for (var element : elements(parent)) if (is(element, localName)) return element;
        return null;
    }
}
