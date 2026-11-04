package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.*;
import java.io.StringReader;
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
 * and xs:unique are attached only to directly repeated, inline typed lists.
 */
public final class AIcDefsCodegenCanonicalSchemaFrontend {
    /** Namespace URI for XML Schema. */
    private static final String XS = XMLConstants.W3C_XML_SCHEMA_NS_URI;
    /** Resolved naming conventions including Defs synthetic-type naming. */
    private final AIcCodegenNamingProfileResolver.Profile naming;

    /**
     * Creates a frontend with already validated Common and Defs conventions.
     *
     * @param naming resolved conventions shared by all source technologies
     * @throws NullPointerException when naming is null
     */
    public AIcDefsCodegenCanonicalSchemaFrontend(AIcCodegenNamingProfileResolver.Profile naming) {
        this.naming = Objects.requireNonNull(naming, "naming");
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
    public AIcdDefsCodegenType loadJsonOrYaml(Map<String, Object> source, String resource,
            AInDefsCodegenSourceInputKind kind) {
        Objects.requireNonNull(source, "source");
        Objects.requireNonNull(resource, "resource");
        if (kind != AInDefsCodegenSourceInputKind.JSONDEFS &&
                kind != AInDefsCodegenSourceInputKind.YAMLDEFS) {
            throw new IllegalArgumentException("Source must be JSONDEFS or YAMLDEFS");
        }
        String name = string(source.get("title"), resource.substring(resource.lastIndexOf('/') + 1).split("\\.")[0]);
        String identity = string(source.get("x-algites-schema-id"), string(source.get("$id"), resource));
        List<String> inherited = new ArrayList<>();
        for (Object item : list(source.get("allOf"))) {
            if (item instanceof Map<?, ?> map && map.get("$ref") instanceof String reference) {
                inherited.add(reference);
            }
        }
        var root = new AIcdDefsCodegenType(identity, name, AInDefsCodegenTypeOrigin.DECLARED,
                List.of(name), inherited, jsonNode(source, name, "#", kind, resource),
                AInDefsCodegenResolutionState.RESOLVED, binding(kind, resource, "#", "root"),
                "", String.valueOf(source.getOrDefault("x-algites-schema-version", "")),
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
    public List<AIcdDefsCodegenType> loadJsonOrYamlTypes(Map<String, Object> source, String resource,
            AInDefsCodegenSourceInputKind kind) {
        Objects.requireNonNull(source, "source");
        if (kind != AInDefsCodegenSourceInputKind.JSONDEFS &&
                kind != AInDefsCodegenSourceInputKind.YAMLDEFS) {
            throw new IllegalArgumentException("Source must be JSONDEFS or YAMLDEFS");
        }
        List<AIcdDefsCodegenType> result = new ArrayList<>();
        if (List.of("type", "properties", "additionalProperties", "items", "prefixItems", "$ref",
                "oneOf", "anyOf", "enum", "required", "minItems", "maxItems", "allOf")
                .stream().anyMatch(source::containsKey)
                || (!source.containsKey("$defs") && !source.containsKey("definitions"))) {
            result.add(loadJsonOrYaml(source, resource, kind));
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
                    if (part instanceof Map<?, ?> mapping && mapping.get("$ref") instanceof String base) {
                        inherited.add(base);
                    }
                }
                var type = new AIcdDefsCodegenType(identity, name,
                        AInDefsCodegenTypeOrigin.DECLARED, List.of(name), inherited, node,
                        AInDefsCodegenResolutionState.RESOLVED, binding(kind, resource, pointer, section),
                        "", String.valueOf(definition.getOrDefault("x-algites-schema-version",
                                source.getOrDefault("x-algites-schema-version", ""))),
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
    public List<AIcdDefsCodegenType> loadXsd(String xml, String resource) {
        Objects.requireNonNull(xml, "xml");
        Objects.requireNonNull(resource, "resource");
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
                if (List.of("include", "import", "redefine", "override").contains(child.getLocalName())) {
                    throw new UnsupportedOperationException("External XML schema composition requires a resolver");
                }
            }
            List<Element> named = new ArrayList<>();
            for (var child : elements(schema)) {
                if ((is(child, "complexType") || is(child, "simpleType")) && child.hasAttribute("name")) {
                    named.add(child);
                }
            }
            var declared = new java.util.HashSet<String>();
            for (var child : named) declared.add(child.getAttribute("name"));
            List<AIcdDefsCodegenType> result = new ArrayList<>();
            for (var child : named) {
                String name = child.getAttribute("name");
                var value = xmlNode(child, name, "/schema/" + name, resource, declared);
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
                result.add(new AIcdDefsCodegenType(identity, name, AInDefsCodegenTypeOrigin.DECLARED,
                        List.of(name), inherited, value, AInDefsCodegenResolutionState.RESOLVED,
                        binding(AInDefsCodegenSourceInputKind.XMLDEFS, resource,
                                "/schema/" + name, child.getLocalName()),
                        "", child.hasAttribute("x-algites-schema-version")
                                ? child.getAttribute("x-algites-schema-version")
                                : schema.getAttribute("x-algites-schema-version"),
                        xmlDescription(child)));
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

    private AIiDefsCodegenStructure jsonNode(Map<String, Object> schema, String owner,
            String path, AInDefsCodegenSourceInputKind kind, String resource) {
        for (String forbidden : List.of("not", "if", "then", "else", "contains", "unevaluatedItems",
                "unevaluatedProperties", "patternProperties", "dependentSchemas", "propertyNames",
                "$dynamicRef", "$recursiveRef", "const", "dependencies", "additionalItems",
                "minLength", "maxLength", "pattern", "contentEncoding", "contentMediaType", "contentSchema", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "uniqueItems", "minProperties", "maxProperties", "dependentRequired", "minContains", "maxContains", "readOnly", "writeOnly")) {
            if (schema.containsKey(forbidden)) {
                throw new UnsupportedOperationException("Unsupported schema keyword " + forbidden + " at " + path);
            }
        }
        for (Object part : list(schema.get("allOf"))) {
            if (!(part instanceof Map<?, ?> mapping) || !(mapping.get("$ref") instanceof String)) {
                throw new UnsupportedOperationException("Inline allOf is not yet canonicalized at " + path);
            }
        }
        if (schema.get("$ref") instanceof String reference) {
            return new AIcdDefsCodegenType(reference, reference.substring(reference.lastIndexOf('/') + 1),
                    AInDefsCodegenTypeOrigin.DECLARED, List.of(owner, reference), List.of(), null,
                    AInDefsCodegenResolutionState.REFERENCE, binding(kind, resource, path, "$ref"));
        }
        if (schema.containsKey("anyOf")) {
            throw new UnsupportedOperationException("Unsupported oneOf/anyOf: anyOf may match multiple branches; CHOICE cannot represent it at " + path);
        }
        Object rawType = schema.get("type");
        String type;
        if (rawType instanceof List<?> types) {
            /* Do not silently discard secondary union branches or nullable values. */
            if (types.size() != 1 || !(types.get(0) instanceof String)) {
                throw new UnsupportedOperationException("JSON Schema type unions (including nullable types) "
                        + "are not yet canonicalized at " + path);
            }
            type = (String) types.get(0);
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
        if (Boolean.TRUE.equals(schema.get("additionalProperties"))) {
            throw new UnsupportedOperationException("Explicit additionalProperties:true cannot be "
                    + "represented losslessly at " + path);
        }
        if (schema.get("items") instanceof Boolean) {
            throw new UnsupportedOperationException("Boolean items constraints are not yet canonicalized at " + path);
        }
        if (schema.containsKey("enum")) {
            var raw = list(schema.get("enum"));
            if (raw.isEmpty()) throw new IllegalArgumentException("Empty enum at " + path);
            if ("object".equals(type) || "array".equals(type)) {
                throw new UnsupportedOperationException("Structured enum values cannot be canonicalized at " + path);
            }
            var base = scalarKind(type);
            if (base == AInDefsCodegenScalarKind.ANY) base = inferScalar(raw.get(0));
            for (var item : raw) {
                var actual = inferScalar(item);
                if (actual != base && !(base == AInDefsCodegenScalarKind.NUMBER
                        && actual == AInDefsCodegenScalarKind.INTEGER)) {
                    throw new IllegalArgumentException("Mixed or incompatible enum scalar kinds at "
                            + path + ": " + base + " versus " + actual);
                }
            }
            List<AIcdDefsCodegenEnumValue> values = new ArrayList<>();
            for (var item : raw) values.add(new AIcdDefsCodegenEnumValue(String.valueOf(item), ""));
            return new AIcdDefsCodegenEnum(base, values);
        }
        for (String choice : List.of("oneOf")) {
            if (schema.containsKey(choice)) {
                var alternatives = list(schema.get(choice));
                if (alternatives.isEmpty()) throw new IllegalArgumentException("Empty " + choice + " at " + path);
                List<AIiDefsCodegenStructure> children = new ArrayList<>();
                for (int i = 0; i < alternatives.size(); i++) {
                    String pointer = path + "/" + choice + "/" + i;
                    var structure = jsonNode(map(alternatives.get(i), pointer), owner, pointer, kind, resource);
                    var synthetic = synthetic(owner, choice, pointer, "synthetic_choice_variant_type",
                            structure, kind, resource, i);
                    String name = naming.render("positional_item_synthetic_getter", "item",
                            Map.of("position", Integer.toString(naming.positionalNumber(i))));
                    children.add(new AIcdDefsCodegenElement(name, synthetic, List.of(),
                            binding(kind, resource, pointer, choice)));
                }
                return new AIcdDefsCodegenElementList(AInDefsCodegenComposition.CHOICE, children);
            }
        }
        if ("object".equals(type) || schema.containsKey("properties") || schema.containsKey("additionalProperties")) {
            if (schema.containsKey("patternProperties")) {
                throw new UnsupportedOperationException("patternProperties intentionally deferred");
            }
            List<AIiDefsCodegenStructure> members = new ArrayList<>();
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
            for (var entry : properties.entrySet()) {
                String name = entry.getKey();
                String pointer = path + "/properties/" + name.replace("~", "~0").replace("/", "~1");
                var node = jsonNode(map(entry.getValue(), pointer), owner, pointer, kind, resource);
                if (node instanceof AIcdDefsCodegenElementList) {
                    node = synthetic(owner, name, pointer, "synthetic_property_type", node, kind, resource, null);
                }
                members.add(new AIcdDefsCodegenElement(name, node, List.of(),
                        binding(kind, resource, pointer, "properties"),
                        required.contains(name) ? 1 : 0, 1,
                        string(map(entry.getValue(), pointer).get("description"), "")));
            }
            if (schema.get("additionalProperties") instanceof Map<?, ?> raw) {
                String pointer = path + "/additionalProperties";
                var value = jsonNode(map(raw, pointer), owner, pointer, kind, resource);
                if (value instanceof AIcdDefsCodegenElementList) {
                    value = synthetic(owner, "additionalProperties", pointer,
                            "synthetic_map_value_type", value, kind, resource, null);
                }
                var integrated = new AIcdDefsCodegenMap("additionalProperties",
                        AInDefsCodegenMapKind.INTEGRATED_PROPERTY_MAP,
                        new AIcdDefsCodegenScalar(AInDefsCodegenScalarKind.STRING, ""), value,
                        binding(kind, resource, pointer, "additionalProperties"));
                /* Integrated property maps are direct ELEMENTLIST children. */
                members.add(integrated);
            }
            return new AIcdDefsCodegenElementList(AInDefsCodegenComposition.SEQUENCE, members);
        }
        if ("array".equals(type) || schema.containsKey("prefixItems") || schema.containsKey("items")) {
            int minItems = optionalBound(schema.get("minItems"), 0, path);
            int maxItems = optionalBound(schema.get("maxItems"), -1, path);
            AIcDefsCodegenOccurrences.check(minItems, maxItems);
            if (schema.containsKey("prefixItems") && (schema.containsKey("minItems") || schema.containsKey("maxItems"))) {
                throw new UnsupportedOperationException("Tuple minItems/maxItems constraints require a tuple-length model at " + path);
            }
            List<AIiDefsCodegenStructure> items = new ArrayList<>();
            int i = 0;
            for (var item : list(schema.get("prefixItems"))) {
                String pointer = path + "/prefixItems/" + i;
                var node = jsonNode(map(item, pointer), owner, pointer, kind, resource);
                var synthetic = synthetic(owner, "item", pointer, "synthetic_positional_item_type",
                        node, kind, resource, i);
                String getter = naming.render("positional_item_synthetic_getter", "item",
                        Map.of("position", Integer.toString(naming.positionalNumber(i))));
                items.add(new AIcdDefsCodegenElement(getter, synthetic, List.of(),
                        binding(kind, resource, pointer, "prefixItems")));
                i++;
            }
            if (schema.get("items") instanceof Map<?, ?> rest) {
                String pointer = path + "/items";
                var node = jsonNode(map(rest, pointer), owner, pointer, kind, resource);
                if (node instanceof AIcdDefsCodegenElementList) {
                    node = synthetic(owner, "item", pointer, "synthetic_list_item_type", node, kind, resource, null);
                }
                var listNode = new AIcdDefsCodegenList("items", node, minItems, maxItems);
                if (items.isEmpty()) return listNode;
                items.add(listNode);
            }
            if (items.isEmpty()) {
                /* A bare array is unconstrained, not an empty fixed-length tuple. */
                return new AIcdDefsCodegenList("items", new AIcdDefsCodegenScalar(AInDefsCodegenScalarKind.ANY, ""), minItems, maxItems);
            }
            if (!schema.containsKey("items")) {
                /* prefixItems by itself still permits additional unconstrained entries. */
                items.add(new AIcdDefsCodegenList("items", new AIcdDefsCodegenScalar(AInDefsCodegenScalarKind.ANY, "")));
            }
            return new AIcdDefsCodegenElementList(AInDefsCodegenComposition.SEQUENCE, items);
        }
        if (schema.containsKey("required")) throw new IllegalArgumentException("required is valid only for object schemas at " + path);
        if (schema.containsKey("minItems") || schema.containsKey("maxItems"))
            throw new IllegalArgumentException("minItems/maxItems require an array schema at " + path);
        return new AIcdDefsCodegenScalar(scalarKind(type), string(schema.get("format"), ""));
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

    private AIcdDefsCodegenType synthetic(String owner, String name, String pointer, String role,
            AIiDefsCodegenStructure node, AInDefsCodegenSourceInputKind kind,
            String resource, Integer index) {
        List<String> segments = new ArrayList<>(List.of(owner, role, name));
        if (index != null) segments.add(index.toString());
        return new AIcdDefsCodegenType(resource + pointer + "#synthetic:" + role,
                naming.syntheticTypeName(role, owner, name, index), AInDefsCodegenTypeOrigin.SYNTHETIC,
                segments, List.of(), node, AInDefsCodegenResolutionState.RESOLVED,
                binding(kind, resource, pointer, role));
    }

    private AIiDefsCodegenStructure xmlNode(Element element, String owner, String path,
            String resource, java.util.Set<String> declared) {
        String tag = element.getLocalName();
        var kind = AInDefsCodegenSourceInputKind.XMLDEFS;
        if ("simpleType".equals(tag)) {
            Element restriction = first(element, "restriction");
            if (restriction != null) {
                String baseReference = xmlTypeIdentity(restriction,
                        restriction.getAttribute("base"), declared);
                if (!baseReference.startsWith("@xs:")) {
                    throw new UnsupportedOperationException("Named XSD simpleType restrictions are not yet canonicalized");
                }
                var base = scalarKindXsd(baseReference.substring(4));
                if (base == AInDefsCodegenScalarKind.ANY
                        && !List.of("anyType", "anySimpleType").contains(baseReference.substring(4))) {
                    throw new UnsupportedOperationException("Unsupported XSD scalar base " + baseReference);
                }
                List<AIcdDefsCodegenEnumValue> values = new ArrayList<>();
                for (var value : elements(restriction)) {
                    if (is(value, "enumeration")) values.add(new AIcdDefsCodegenEnumValue(value.getAttribute("value"), ""));
                    else if (!is(value, "annotation")) throw new UnsupportedOperationException(
                            "Unsupported XML restriction facet " + value.getLocalName());
                }
                return values.isEmpty() ? new AIcdDefsCodegenScalar(base, "") : new AIcdDefsCodegenEnum(base, values);
            }
            for (var child : elements(element)) {
                if (!is(child, "annotation")) {
                    throw new UnsupportedOperationException("Unsupported XML simpleType without xs:restriction at " + path);
                }
            }
            return new AIcdDefsCodegenScalar(AInDefsCodegenScalarKind.ANY, "");
        }
        if (List.of("sequence", "all", "choice").contains(tag)) {
            AInDefsCodegenComposition composition = switch (tag) {
                case "all" -> AInDefsCodegenComposition.ALL;
                case "choice" -> AInDefsCodegenComposition.CHOICE;
                default -> AInDefsCodegenComposition.SEQUENCE;
            };
            List<AIiDefsCodegenStructure> children = new ArrayList<>();
            int index = 0;
            for (var child : elements(element)) {
                if (List.of("element", "sequence", "all", "choice").contains(child.getLocalName())) {
                    children.add(xmlNode(child, owner, path + "/" + tag + "/" + index,
                            resource, declared));
                } else if (!is(child, "annotation")) {
                    throw new UnsupportedOperationException("Unsupported XML group child "
                            + child.getLocalName() + " at " + path);
                }
                index++;
            }
            return new AIcdDefsCodegenElementList(composition, children,
                    xmlOccurs(element.getAttribute("minOccurs"), 1, false, path),
                    xmlOccurs(element.getAttribute("maxOccurs"), 1, true, path));
        }
        if (List.of("complexType", "complexContent", "extension", "restriction").contains(tag)) {
            List<AIiDefsCodegenStructure> groups = new ArrayList<>();
            for (var child : elements(element)) {
                if (List.of("sequence", "all", "choice", "complexContent", "extension", "restriction")
                        .contains(child.getLocalName())) {
                    groups.add(xmlNode(child, owner, path + "/" + child.getLocalName(), resource, declared));
                } else if (is(child, "attribute")) {
                    groups.add(xmlNode(child, owner, path + "/attribute/" + child.getAttribute("name"),
                            resource, declared));
                } else if (!is(child, "annotation")) {
                    throw new UnsupportedOperationException("Unsupported XML complexType child " + child.getLocalName());
                }
            }
            if (groups.size() == 1 && groups.get(0) instanceof AIcdDefsCodegenElementList) {
                return groups.get(0);
            }
            return new AIcdDefsCodegenElementList(AInDefsCodegenComposition.SEQUENCE, groups);
        }
        if ("attribute".equals(tag)) {
            if (element.hasAttribute("ref") || element.hasAttribute("default") || element.hasAttribute("fixed")) {
                throw new UnsupportedOperationException("Referenced/defaulted/fixed XML attribute unsupported at " + path);
            }
            String name = element.getAttribute("name");
            if (name.isBlank()) throw new IllegalArgumentException("XSD attribute needs a name at " + path);
            String use = element.hasAttribute("use") ? element.getAttribute("use") : "optional";
            if (!List.of("optional", "required").contains(use)) {
                throw new UnsupportedOperationException("Unsupported XML attribute use " + use + " at " + path);
            }
            AIiDefsCodegenStructure value;
            if (element.hasAttribute("type")) {
                String reference = xmlTypeIdentity(element, element.getAttribute("type"), declared);
                if (!reference.startsWith("@xs:")) {
                    value = new AIcdDefsCodegenType(reference, local(element.getAttribute("type")),
                            AInDefsCodegenTypeOrigin.DECLARED, List.of(owner, name), List.of(), null,
                            AInDefsCodegenResolutionState.REFERENCE,
                            binding(kind, resource, path, "xs:attribute/@type"));
                } else {
                    var scalar = scalarKindXsd(reference.substring(4));
                    if (scalar == AInDefsCodegenScalarKind.ANY) {
                        throw new UnsupportedOperationException("Unsupported XML attribute type " + reference);
                    }
                    value = new AIcdDefsCodegenScalar(scalar, "");
                }
            } else {
                Element inline = first(element, "simpleType");
                value = inline == null ? new AIcdDefsCodegenScalar(AInDefsCodegenScalarKind.STRING, "")
                        : xmlNode(inline, owner, path, resource, declared);
            }
            return new AIcdDefsCodegenElement(name, value, List.of(),
                    binding(kind, resource, path, "xs:attribute"), "required".equals(use) ? 1 : 0, 1,
                    xmlDescription(element), xmlWire(element, name, AInDefsCodegenXmlValueKind.ATTRIBUTE));
        }
        if ("element".equals(tag)) {
            for (String unsupported : List.of("default", "fixed", "nillable", "substitutionGroup")) {
                if (element.hasAttribute(unsupported)) {
                    throw new UnsupportedOperationException("Unsupported XSD element facet "
                            + unsupported + " at " + path);
                }
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
            AIiDefsCodegenStructure value;
            if (!rawType.isEmpty()) {
                String type = xmlTypeIdentity(element, rawType, declared);
                if (type.startsWith("@xs:")) {
                    String builtinName = type.substring(4);
                    var builtin = scalarKindXsd(builtinName);
                    if (builtin == AInDefsCodegenScalarKind.ANY
                            && !List.of("anyType", "anySimpleType").contains(builtinName)) {
                        throw new UnsupportedOperationException("Unsupported XSD built-in type "
                                + rawType + " at " + resource + path);
                    }
                    value = new AIcdDefsCodegenScalar(builtin, "");
                } else {
                    value = new AIcdDefsCodegenType(type, local(rawType), AInDefsCodegenTypeOrigin.DECLARED,
                            List.of(owner, name), List.of(), null, AInDefsCodegenResolutionState.REFERENCE,
                            binding(kind, resource, path, "xs:element/@type"));
                }
            } else {
                Element inline = first(element, "complexType");
                if (inline == null) inline = first(element, "simpleType");
                value = inline == null ? new AIcdDefsCodegenScalar(AInDefsCodegenScalarKind.ANY, "")
                        : xmlNode(inline, owner, path, resource, declared);
            }
            if (!constraints.isEmpty()) {
                if (!rawType.isEmpty() || !(value instanceof AIcdDefsCodegenElementList group)) {
                    throw new UnsupportedOperationException("XSD local key requires an inline complexType at " + path);
                }
                List<AIiDefsCodegenStructure> children = new ArrayList<>(group.children());
                java.util.Set<String> keyNames = new java.util.HashSet<>();
                int keyIndex = 0;
                for (var constraint : constraints) {
                    String keyName = constraint.getAttribute("name");
                    Element selectorNode = first(constraint, "selector");
                    List<String> paths = new ArrayList<>();
                    for (var f : elements(constraint)) {
                        if (is(f, "field")) {
                            if (!f.hasAttribute("xpath") || f.getAttribute("xpath").isBlank()) {
                                throw new IllegalArgumentException("Missing XSD key field XPath at " + path);
                            }
                            paths.add(f.getAttribute("xpath"));
                        } else if (!(is(f, "selector") || is(f, "annotation"))) {
                            throw new UnsupportedOperationException("Unknown XSD identity constraint child at " + path);
                        }
                    }
                    if (keyName.isBlank() || !keyNames.add(keyName) || selectorNode == null ||
                            !selectorNode.hasAttribute("xpath") || paths.isEmpty()) {
                        throw new IllegalArgumentException("XSD key/unique requires unique name, selector, fields at " + path);
                    }
                    String selector = selectorNode.getAttribute("xpath");
                    String selected = selector.startsWith("./") ? selector.substring(2) : selector;
                    int hit = -1;
                    for (int i = 0; i < children.size(); i++) {
                        if (children.get(i) instanceof AIcdDefsCodegenList list && list.name().equals(selected)) {
                            if (hit != -1) throw new IllegalArgumentException("Ambiguous XSD index selector " + selector);
                            hit = i;
                        }
                    }
                    if (hit == -1) {
                        throw new UnsupportedOperationException("XSD key selector must target exactly one directly "
                                + "repeated element: " + selector + " at " + path);
                    }
                    var original = (AIcdDefsCodegenList) children.get(hit);
                    List<AIcdDefsCodegenKeyDefinition> keys = new ArrayList<>(original.keyDefinitions());
                    keys.add(new AIcdDefsCodegenKeyDefinition(keyName, selector,
                            path + "/" + constraint.getLocalName() + "/" + keyIndex++, paths,
                            is(constraint, "key")));
                    children.set(hit, new AIcdDefsCodegenList(original.name(), original.item(),
                            original.minOccurs(), original.maxOccurs(), keys, original.xmlWire()));
                }
                value = new AIcdDefsCodegenElementList(group.composition(), children,
                        group.minOccurs(), group.maxOccurs());
            }
            if (value instanceof AIcdDefsCodegenElementList) {
                value = synthetic(owner, name, path, "synthetic_property_type", value,
                        kind, resource, null);
            }
            int minimum = xmlOccurs(element.getAttribute("minOccurs"), 1, false, path);
            int maximum = xmlOccurs(element.getAttribute("maxOccurs"), 1, true, path);
            AIcDefsCodegenOccurrences.check(minimum, maximum);
            AIcdDefsCodegenXmlWireName wire = xmlWire(element, name, AInDefsCodegenXmlValueKind.ELEMENT);
            if (maximum == -1 || maximum > 1) {
                return new AIcdDefsCodegenList(name, value, minimum, maximum, List.of(), wire);
            }
            return new AIcdDefsCodegenElement(name, value, List.of(),
                    binding(kind, resource, path, "xs:element"), minimum, maximum,
                    xmlDescription(element), wire);
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
    private static AIcdDefsCodegenXmlWireName xmlWire(Element element, String name,
            AInDefsCodegenXmlValueKind valueKind) {
        Element schema = element.getOwnerDocument().getDocumentElement();
        String attribute = valueKind == AInDefsCodegenXmlValueKind.ELEMENT
                ? "elementFormDefault" : "attributeFormDefault";
        String fallback = schema.hasAttribute(attribute) ? schema.getAttribute(attribute) : "unqualified";
        String form = element.hasAttribute("form") ? element.getAttribute("form") : fallback;
        if (!List.of("qualified", "unqualified").contains(form)) {
            throw new IllegalArgumentException("Invalid XML form for " + name + ": " + form);
        }
        String namespace = "qualified".equals(form) ? schema.getAttribute("targetNamespace") : "";
        return new AIcdDefsCodegenXmlWireName(namespace, name, valueKind);
    }

    private static Map<AInDefsCodegenSourceInputKind, List<AIcdDefsCodegenSourceBinding>> binding(
            AInDefsCodegenSourceInputKind kind, String resource, String path, String representation) {
        return Map.of(kind, List.of(new AIcdDefsCodegenSourceBinding(resource, path, representation)));
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
    private static String xmlTypeIdentity(Element element, String qname, java.util.Set<String> declared) {
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
        throw new UnsupportedOperationException("Unresolved or external XSD QName '" + qname
                + "' (namespace '" + namespace + "')");
    }

    private static AInDefsCodegenScalarKind scalarKind(String type) {
        return switch (type) {
            case "string" -> AInDefsCodegenScalarKind.STRING;
            case "integer" -> AInDefsCodegenScalarKind.INTEGER;
            case "number" -> AInDefsCodegenScalarKind.NUMBER;
            case "boolean" -> AInDefsCodegenScalarKind.BOOLEAN;
            case "null" -> AInDefsCodegenScalarKind.NULL;
            default -> AInDefsCodegenScalarKind.ANY;
        };
    }

    private static AInDefsCodegenScalarKind inferScalar(Object value) {
        if (value instanceof Boolean) return AInDefsCodegenScalarKind.BOOLEAN;
        if (value instanceof Byte || value instanceof Short || value instanceof Integer ||
                value instanceof Long || value instanceof java.math.BigInteger)
            return AInDefsCodegenScalarKind.INTEGER;
        if (value instanceof Number) return AInDefsCodegenScalarKind.NUMBER;
        if (value == null) return AInDefsCodegenScalarKind.NULL;
        return AInDefsCodegenScalarKind.STRING;
    }

    private static AInDefsCodegenScalarKind scalarKindXsd(String qname) {
        return switch (local(qname)) {
            case "string", "normalizedString", "token", "anyURI", "date", "dateTime" -> AInDefsCodegenScalarKind.STRING;
            case "int", "integer", "long", "short", "positiveInteger", "nonNegativeInteger" -> AInDefsCodegenScalarKind.INTEGER;
            case "decimal", "float", "double" -> AInDefsCodegenScalarKind.NUMBER;
            case "boolean" -> AInDefsCodegenScalarKind.BOOLEAN;
            default -> AInDefsCodegenScalarKind.ANY;
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
