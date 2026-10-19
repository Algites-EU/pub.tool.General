package eu.algites.tool.codegen.defs.impl.standard;


import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdDefinitionReference;
import eu.algites.tool.codegen.defs.AIcdEnumValueDefinition;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AIcdXmlFieldRepresentation;
import eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind;
import eu.algites.tool.codegen.defs.AIcdXmlElementDeclaration;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIiDefinitionFrontend;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.lib.data.dataobject.AInFieldPresenceKind;
import java.io.IOException;
import java.math.BigDecimal;
import java.net.URI;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

/** Loads the supported XML Schema projection into the format-neutral canonical model. */
public final class AIcXmlDefsFrontend implements AIiDefinitionFrontend {
    private static final String XS = XMLConstants.W3C_XML_SCHEMA_NS_URI;
    private static final Set<String> STRINGS = Set.of("string", "normalizedString", "token", "language",
            "Name", "NCName", "NMTOKEN", "ID", "IDREF", "ENTITY", "duration", "dateTime", "time", "date",
            "gYearMonth", "gYear", "gMonthDay", "gDay", "gMonth", "hexBinary", "base64Binary", "anyURI",
            "QName", "NOTATION", "dateTimeStamp", "yearMonthDuration", "dayTimeDuration");
    private static final Set<String> INTEGERS = Set.of("integer", "nonPositiveInteger", "negativeInteger",
            "long", "int", "short", "byte", "nonNegativeInteger", "unsignedLong", "unsignedInt",
            "unsignedShort", "unsignedByte", "positiveInteger");
    private final AIcDefinitionIdentityResolver identities = new AIcDefinitionIdentityResolver();

    /** Creates the XML Schema frontend. */
    public AIcXmlDefsFrontend() { }

    /** Returns the XML canonical definition family. */
    @Override
    public AInDefinitionSourceKind sourceKind() { return AInDefinitionSourceKind.XMLDEFS; }

    /** Loads a definition, resolving imported canonical types from local XSD resources only. */
    @Override
    public AIcdCanonicalDefinition load(AIcdDefinitionLoadRequest aRequest) throws IOException {
        Element locSchema = schema(aRequest.path());
        var locParsed = identities.fromFileName(aRequest, integer(locSchema.getAttribute("version")));
        String locIdentity = locSchema.getAttribute("targetNamespace");
        if (locIdentity.isBlank()) locIdentity = locParsed.logicalName();
        Element locType = rootType(locSchema);
        List<AIcdEnumValueDefinition> locValues = enumValues(locType);
        String locDescription = documentation(locType);
        String locTitle = title(locType);
        if (locDescription == null) locDescription = documentation(locSchema);
        if (locTitle == null) locTitle = title(locSchema);
        if (!locValues.isEmpty()) return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locParsed.logicalName(), sourceKind(), aRequest.path().toString(), locDescription, AIcdDataType.atom(AInDataTypeKind.ENUM, null), locValues, locTitle);
        List<AIcdPropertyDefinition> locProperties = new ArrayList<>();
        if (locType != null && "complexType".equals(locType.getLocalName())) {
            AIcdDataType locChoice = rootChoice(locType, aRequest, locSchema);
            if (locChoice != null) return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locParsed.logicalName(), sourceKind(), aRequest.path().toString(), locDescription, locChoice, List.of(), locTitle);
            locProperties.addAll(complexProperties(locType, aRequest, locSchema, new HashSet<>()));
            return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locParsed.logicalName(), sourceKind(), aRequest.path().toString(), locDescription, AIcdDataType.object(locProperties), List.of(), locTitle);
        }
        Element locElement = child(locSchema, "element");
        AIcdShape locShape = locType != null ? simpleShape(locType, aRequest, locSchema, new HashSet<>())
                : locElement != null ? shape(locElement, locElement.getAttribute("type"), aRequest, locSchema, new HashSet<>())
                : new AIcdShape(AInDataTypeKind.ANY, null, null);
        var locProperty = new AIcdPropertyDefinition("value", AIcSourceDataType.fromSourceHints(locShape.kind(), locShape.itemKind(), locShape.reference(), locShape.constraints(), locShape.itemConstraints()), ((true) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), locElement != null && Set.of("true", "1").contains(locElement.getAttribute("nillable")), locDescription, title(locElement != null ? locElement : locType), null);
        return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locParsed.logicalName(), sourceKind(), aRequest.path().toString(), locDescription, locProperty.dataType(), List.of(), locTitle);
    }

    /**
     * Project a direct, mandatory XSD choice as a closed union of single-element records.
     * The branch objects retain each element's expanded QName, unlike a union of scalar values.
     * Mixed particles, occurrence ranges and global-element references require a richer XSD
     * particle model and are rejected, rather than reduced to unrelated optional fields.
     *
     * @param aType selected complexType declaration
     * @param aRequest request identifying the XSD source
     * @param aSchema containing XSD schema
     * @return closed recursive type, or null when no direct choice is declared
     * @throws IOException when the choice lies outside the supported exact-one subset
     */
    private AIcdDataType rootChoice(Element aType, AIcdDefinitionLoadRequest aRequest,
            Element aSchema) throws IOException {
        Element locChoice = child(aType, "choice");
        if (locChoice == null) return null;
        if (child(aType, "complexContent", "simpleContent", "sequence", "all", "group",
                "attribute", "attributeGroup", "anyAttribute") != null
                || children(aType, "choice").size() != 1
                || !"1".equals(locChoice.getAttribute("minOccurs").isBlank()
                        ? "1" : locChoice.getAttribute("minOccurs"))
                || !"1".equals(locChoice.getAttribute("maxOccurs").isBlank()
                        ? "1" : locChoice.getAttribute("maxOccurs")))
            throw new IOException("Unsupported mixed or repeated XSD choice in " + aRequest.path());
        List<Element> locBranches = children(locChoice);
        if (locBranches.isEmpty()) throw new IOException("Empty XSD choice in " + aRequest.path());
        List<AIcdDataType> locAlternatives = new ArrayList<>();
        List<AIcdPropertyDefinition> locFields = new ArrayList<>();
        elements(locChoice, false, aRequest, aSchema, locFields);
        if (locFields.size() != locBranches.size())
            throw new IOException("Invalid XSD choice projection in " + aRequest.path());
        for (Element locBranch : locBranches) {
            if (!"element".equals(locBranch.getLocalName())
                    || locBranch.hasAttribute("name") == locBranch.hasAttribute("ref")
                    || locBranch.hasAttribute("minOccurs") || locBranch.hasAttribute("maxOccurs"))
                throw new IOException("Unsupported XSD choice branch in " + aRequest.path());
            locAlternatives.add(AIcdDataType.object(List.of(locFields.get(locAlternatives.size()))));
        }
        return AIcdDataType.choice(AInDataTypeKind.ONE_OF, locAlternatives);
    }

    /**
     * Lists named schema types that do not already own the primary file-based
     * contract. The repository generator emits these as independent sibling
     * types so that a local complex-content base can be inherited nominally.
     *
     * @param aPath XSD source file
     * @return distinct named type identifiers in declaration order
     * @throws IOException if the schema cannot be parsed
     */
    public List<String> additionalNamedTypeNames(Path aPath) throws IOException {
        Element locSchema = schema(aPath);
        Element locRoot = rootType(locSchema);
        List<String> locNames = new ArrayList<>();
        Set<String> locSeen = new HashSet<>();
        for (Element locType : children(locSchema, "complexType", "simpleType")) {
            String locName = locType.getAttribute("name");
            if (locName.isBlank() || !locSeen.add(locName))
                throw new IOException("Duplicate or unnamed global XSD type in " + aPath);
            if (locType != locRoot) locNames.add(locName);
        }
        return List.copyOf(locNames);
    }

    /**
     * Loads an explicitly named XSD type instead of the file's selected root.
     * Sibling contracts keep their own lexical type names and expanded QNames.
     *
     * @param aRequest source schema and naming conventions
     * @param aName declared global type name
     * @return canonical representation of the selected global type
     * @throws IOException if the type does not exist or cannot be projected
     */
    public AIcdCanonicalDefinition loadNamedType(AIcdDefinitionLoadRequest aRequest, String aName)
            throws IOException {
        Element locSchema = schema(aRequest.path());
        Element locType = namedType(locSchema, aName);
        if (locType == null) throw new IOException("Unknown named XSD type '" + aName + "' in " + aRequest.path());
        var locParsed = identities.fromFileName(aRequest, integer(locSchema.getAttribute("version")));
        String locIdentity = locSchema.getAttribute("targetNamespace");
        if (locIdentity.isBlank()) locIdentity = locParsed.logicalName();
        String locLogical = aName.replaceAll("([a-z0-9])([A-Z])", "$1-$2")
                .replaceAll("[^A-Za-z0-9]+", "-").toLowerCase(java.util.Locale.ROOT);
        List<AIcdEnumValueDefinition> locValues = enumValues(locType);
        String locDescription = documentation(locType);
        String locTitle = title(locType);
        if (!locValues.isEmpty()) return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locLogical, sourceKind(), aRequest.path() + "#@type/" + aName, locDescription, AIcdDataType.atom(AInDataTypeKind.ENUM, null), locValues, locTitle);
        if ("complexType".equals(locType.getLocalName())) {
            AIcdDataType locChoice = rootChoice(locType, aRequest, locSchema);
            if (locChoice != null) return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locLogical, sourceKind(), aRequest.path() + "#@type/" + aName, locDescription, locChoice, List.of(), locTitle);
            var locFields = complexProperties(locType, aRequest, locSchema, new HashSet<>());
            return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locLogical, sourceKind(), aRequest.path() + "#@type/" + aName, locDescription, AIcdDataType.object(locFields), List.of(), locTitle);
        }
        AIcdShape locShape = simpleShape(locType, aRequest, locSchema, new HashSet<>());
        var locValue = new AIcdPropertyDefinition("value", AIcSourceDataType.fromSourceHints(locShape.kind(), locShape.itemKind(), locShape.reference(), locShape.constraints(), locShape.itemConstraints()), ((true) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, locDescription, locTitle, null);
        return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locLogical, sourceKind(), aRequest.path() + "#@type/" + aName, locDescription, locValue.dataType(), List.of(), locTitle);
    }

    /**
     * Returns the extension base QName for a specific global complex type.
     *
     * @param aRequest source XSD containing the declaration
     * @param aName named global complex type
     * @return expanded base QName or {@code null} for an unextended type
     * @throws IOException for an invalid declaration or QName
     */
    public String namedTypeExtensionBaseQName(AIcdDefinitionLoadRequest aRequest, String aName)
            throws IOException {
        Element locSchema = schema(aRequest.path());
        Element locType = namedType(locSchema, aName);
        if (locType == null) throw new IOException("Unknown XSD type '" + aName + "' in " + aRequest.path());
        return extensionBaseQName(locSchema, locType, aRequest.path());
    }

    /** Discover all global element identities without projecting them into data types. */
    public List<AIcdXmlElementDeclaration> globalElementDeclarations(AIcdDefinitionLoadRequest aRequest)
            throws IOException {
        Element locRoot = schema(aRequest.path());
        String locNamespace = locRoot.getAttribute("targetNamespace");
        if (!locRoot.getAttribute("blockDefault").isBlank() || !locRoot.getAttribute("finalDefault").isBlank())
            throw new IOException("Unsupported XSD substitution/derivation defaults in " + aRequest.path());
        List<AIcdXmlElementDeclaration> locResult = new ArrayList<>();
        Set<String> locNames = new HashSet<>();
        for (Element locElement : children(locRoot, "element")) {
            String locName = locElement.getAttribute("name");
            if (locName.isBlank() || !locNames.add(locName))
                throw new IOException("Duplicate or unnamed global element '" + locName + "' in " + aRequest.path());
            if (!locElement.getAttribute("block").isBlank() || !locElement.getAttribute("final").isBlank())
                throw new IOException("Unsupported XSD substitution/derivation restriction for element '"
                        + locName + "' in " + aRequest.path());
            String locType = xmlQName(locElement, locElement.getAttribute("type"), locNamespace);
            String locHead = locElement.hasAttribute("substitutionGroup")
                    ? xmlQName(locElement, locElement.getAttribute("substitutionGroup"), locNamespace) : null;
            locResult.add(new AIcdXmlElementDeclaration(locName, locNamespace, locType, locHead,
                    Set.of("true", "1").contains(locElement.getAttribute("abstract")),
                    Set.of("true", "1").contains(locElement.getAttribute("nillable"))));
        }
        return List.copyOf(locResult);
    }

    /**
     * Reads the target namespace of a schema without deriving it from a Java
     * package, generated type name, or file-system location.
     *
     * @param aRequest source XSD request
     * @return declared target namespace, or the empty namespace when absent
     * @throws IOException if the schema cannot be read
     */
    public String schemaNamespace(AIcdDefinitionLoadRequest aRequest) throws IOException {
        return schema(aRequest.path()).getAttribute("targetNamespace");
    }

    /** Expanded QName of the XSD content type projected by load(). */
    public String rootTypeQName(AIcdDefinitionLoadRequest aRequest) throws IOException {
        Element locSchema = schema(aRequest.path());
        Element locType = rootType(locSchema);
        String locName = locType == null ? "__root__" : locType.getAttribute("name");
        return "{" + locSchema.getAttribute("targetNamespace") + "}"
                + (locName.isBlank() ? "__root__" : locName);
    }

    /**
     * Returns the expanded QName of the direct named extension base, if any.
     * Attribute/particle restrictions do not create a substitutable Java parent here:
     * narrowing the allowed field set cannot safely be expressed by interface override.
     *
     * @param aRequest the local XSD source whose selected root type is being generated
     * @return expanded QName of an extension base, or {@code null} without extension
     * @throws IOException for an invalid or unresolvable QName
     */
    public String rootExtensionBaseQName(AIcdDefinitionLoadRequest aRequest) throws IOException {
        Element locSchema = schema(aRequest.path());
        return extensionBaseQName(locSchema, rootType(locSchema), aRequest.path());
    }

    /** Resolves the extension QName for both primary and auxiliary type declarations. */
    private static String extensionBaseQName(Element aSchema, Element aType, Path aPath) throws IOException {
        Element locExtension = child(child(aType, "complexContent"), "extension");
        if (locExtension == null) return null;
        String locBase = locExtension.getAttribute("base");
        if (locBase.isBlank()) throw new IOException("Missing XML complexContent extension base in " + aPath);
        return xmlQName(locExtension, locBase, aSchema.getAttribute("targetNamespace"));
    }

    /** Resolve a QName attribute without losing its defining XML namespace. */
    private static String xmlQName(Element aContext, String aLexical, String aFallbackNamespace) throws IOException {
        if (aLexical.isBlank()) return "{" + aFallbackNamespace + "}__root__";
        int locColon = aLexical.indexOf(':');
        String locPrefix = locColon < 0 ? null : aLexical.substring(0, locColon);
        String locLocal = locColon < 0 ? aLexical : aLexical.substring(locColon + 1);
        String locNamespace = aContext.lookupNamespaceURI(locPrefix);
        if (locPrefix != null && locNamespace == null)
            throw new IOException("Undefined XML namespace prefix '" + locPrefix + "'");
        return "{" + (locNamespace == null ? aFallbackNamespace : locNamespace) + "}" + locLocal;
    }

    /** Selects the root declaration, without mistaking a nested enum for the whole document. */
    private static Element rootType(Element aSchema) {
        for (Element locElement : children(aSchema, "element")) {
            Element locInline = child(locElement, "complexType", "simpleType");
            if (locInline != null) return locInline;
            Element locNamed = namedType(aSchema, localName(locElement.getAttribute("type")));
            if (locNamed != null) return locNamed;
        }
        Element locComplex = child(aSchema, "complexType");
        return locComplex != null ? locComplex : child(aSchema, "simpleType");
    }

    /** Project conservative, same-schema complexContent extensions and attribute restrictions. */
    private List<AIcdPropertyDefinition> complexProperties(Element aType, AIcdDefinitionLoadRequest aRequest,
            Element aSchema, Set<String> aVisited) throws IOException {
        if (child(aType, "anyAttribute", "simpleContent") != null)
            throw new IOException("Unsupported XSD attribute group/wildcard/simple content in " + aRequest.path());
        Element locContent = child(aType, "complexContent");
        List<AIcdPropertyDefinition> locResult = new ArrayList<>();
        if (locContent == null) {
            elements(aType, false, aRequest, aSchema, locResult);
            attributes(aType, aRequest, aSchema, locResult);
            return locResult;
        }
        if ("true".equals(aType.getAttribute("mixed")) || "true".equals(locContent.getAttribute("mixed")))
            throw new IOException("Unsupported mixed XSD complexContent in " + aRequest.path());
        List<Element> locBranches = children(locContent, "extension", "restriction");
        if (locBranches.size() != 1)
            throw new IOException("Unsupported XSD complexContent derivation in " + aRequest.path());
        Element locBranch = locBranches.get(0);
        String locBaseName = locBranch.getAttribute("base");
        String locPrefix = locBaseName.contains(":") ? locBaseName.substring(0, locBaseName.indexOf(':')) : null;
        String locNamespace = locBranch.lookupNamespaceURI(locPrefix);
        String locTargetNamespace = aSchema.getAttribute("targetNamespace");
        if (locBaseName.isBlank() || (locPrefix != null && locNamespace == null))
            throw new IOException("Unknown XSD complexContent base QName '" + locBaseName + "' in " + aRequest.path());
        Element locBase = null;
        Element locBaseSchema = aSchema;
        AIcdDefinitionLoadRequest locBaseRequest = aRequest;
        if (locNamespace == null || locNamespace.equals(locTargetNamespace))
            locBase = namedType(aSchema, localName(locBaseName));
        if (locBase == null) {
            for (Element locImport : children(aSchema, "import", "include")) {
                if ("import".equals(locImport.getLocalName())
                        && !locImport.getAttribute("namespace").equals(locNamespace)) continue;
                if ("include".equals(locImport.getLocalName())
                        && locNamespace != null && !locNamespace.equals(locTargetNamespace)) continue;
                String locLocation = locImport.getAttribute("schemaLocation");
                if (locLocation.isBlank()) continue;
                URI locUri = URI.create(locLocation);
                if (locUri.isAbsolute() && !"file".equals(locUri.getScheme()))
                    throw new IOException("XSD extension imports must be local: " + locLocation);
                Path locPath = locUri.isAbsolute() ? Path.of(locUri)
                        : aRequest.path().toAbsolutePath().getParent().resolve(locLocation).normalize();
                Element locCandidate = schema(locPath);
                if (!Objects.equals(locNamespace == null ? locTargetNamespace : locNamespace,
                        locCandidate.getAttribute("targetNamespace"))) continue;
                Element locFound = namedType(locCandidate, localName(locBaseName));
                if (locFound == null) continue;
                locBase = locFound;
                locBaseSchema = locCandidate;
                locBaseRequest = new AIcdDefinitionLoadRequest(locPath, sourceKind(), aRequest.namingProfile());
                break;
            }
        }
        if (locBase == null || !"complexType".equals(locBase.getLocalName()))
            throw new IOException("Unknown or non-complex XSD derivation base '" + locBaseName + "' in " + aRequest.path());
        String locIdentity = locBaseRequest.path().toAbsolutePath().normalize() + "#" + locBase.getAttribute("name");
        if (!aVisited.add(locIdentity))
            throw new IOException("Circular XSD complexContent derivation at '" + locIdentity + "' in " + aRequest.path());
        locResult.addAll(complexProperties(locBase, locBaseRequest, locBaseSchema, aVisited));
        aVisited.remove(locIdentity);
        if (child(locBranch, "anyAttribute", "simpleContent", "complexContent") != null)
            throw new IOException("Unsupported XSD derivation child in " + aRequest.path());
        List<AIcdPropertyDefinition> locLocal = new ArrayList<>();
        elements(locBranch, false, aRequest, aSchema, locLocal);
        attributes(locBranch, aRequest, aSchema, locLocal);
        Map<String, AIcdPropertyDefinition> locByName = new java.util.LinkedHashMap<>();
        for (AIcdPropertyDefinition locField : locResult) {
            if (locByName.putIfAbsent(locField.sourceName(), locField) != null)
                throw new IOException("Duplicate inherited XML field in " + aRequest.path());
        }
        Set<String> locSeen = new HashSet<>();
        for (AIcdPropertyDefinition locField : locLocal)
            if (!locSeen.add(locField.sourceName()))
                throw new IOException("Duplicate derived XML field in " + aRequest.path());
        if ("extension".equals(locBranch.getLocalName())) {
            for (AIcdPropertyDefinition locField : locLocal)
                if (locByName.containsKey(locField.sourceName()))
                    throw new IOException("XSD extension redeclares an inherited field in " + aRequest.path());
            locResult.addAll(locLocal);
            return locResult;
        }
        /* Both xs:all and xs:sequence project to ordered canonical properties.
         * Rendering uses declaration order; lenient parsing may use QName lookup.
         * Strict XSD sequence validation is deliberately a separate concern. */
        Element locBaseSequence = child(locBase, "sequence", "all");
        Element locDerivedSequence = child(locBranch, "sequence", "all");
        if (child(locBase, "choice", "group", "complexContent") != null
                || child(locBranch, "choice", "group") != null)
            throw new IOException("Unsupported XSD complexContent particle restriction in " + aRequest.path());
        if (locDerivedSequence != null && locBaseSequence == null)
            throw new IOException("XSD restriction introduces an unsupported particle group in " + aRequest.path());
        if (locBaseSequence != null) {
            if (children(locBaseSequence).stream().anyMatch(aNode -> !"element".equals(aNode.getLocalName()))
                    || locDerivedSequence != null && children(locDerivedSequence).stream().anyMatch(aNode -> !"element".equals(aNode.getLocalName()))
                    || !"1".equals(locBaseSequence.getAttribute("minOccurs").isBlank() ? "1" : locBaseSequence.getAttribute("minOccurs"))
                    || !"1".equals(locBaseSequence.getAttribute("maxOccurs").isBlank() ? "1" : locBaseSequence.getAttribute("maxOccurs"))
                    || locDerivedSequence != null && (!"1".equals(locDerivedSequence.getAttribute("minOccurs").isBlank() ? "1" : locDerivedSequence.getAttribute("minOccurs"))
                    || !"1".equals(locDerivedSequence.getAttribute("maxOccurs").isBlank() ? "1" : locDerivedSequence.getAttribute("maxOccurs"))))
                throw new IOException("Unsupported XSD complexContent particle restriction in " + aRequest.path());
            List<String> locBaseNames = children(locBaseSequence, "element").stream()
                    .map(aNode -> aNode.getAttribute("name")).toList();
            int locIndex = 0;
            for (Element locItem : children(locDerivedSequence, "element")) {
                while (locIndex < locBaseNames.size() && !locBaseNames.get(locIndex).equals(locItem.getAttribute("name"))) locIndex++;
                if (locIndex == locBaseNames.size())
                    throw new IOException("Unsupported XSD particle restriction: reorders or introduces compositor elements in " + aRequest.path());
                locIndex++;
            }
        }
        for (AIcdPropertyDefinition locField : locLocal) {
            var locPrevious = locByName.get(locField.sourceName());
            if (locPrevious == null)
                throw new IOException("XSD restriction introduces new field '" + locField.sourceName() + "' in " + aRequest.path());
            if (!Objects.equals(locPrevious.xmlField(), locField.xmlField()))
                throw new IOException("XSD restriction changes attribute/element QName of '"
                        + locField.sourceName() + "' in " + aRequest.path());
            if (locField.presence() == AInFieldPresenceKind.FORBIDDEN && locField.dataType().kind() == AInDataTypeKind.ANY
                    && locField.dataType().referencedDefinition() == null) {
                /* An untyped prohibited attribute retains its base type, but cannot be present. */
                locField = new AIcdPropertyDefinition(locPrevious.sourceName(), locPrevious.dataType(), AInFieldPresenceKind.FORBIDDEN, locPrevious.nullable(), locPrevious.description(), locPrevious.title(), locPrevious.xmlField());
            }
            if (!Objects.equals(locPrevious.xmlField(), locField.xmlField()))
                throw new IOException("XSD restriction changes attribute/element QName of '"
                        + locField.sourceName() + "' in " + aRequest.path());
            if (!sameTypeShape(locPrevious.dataType(), locField.dataType()))
                throw new IOException("XSD restriction changes field type '" + locField.sourceName() + "' in " + aRequest.path());
            if (!Objects.equals(locPrevious.dataType().constraints().dataType(), locField.dataType().constraints().dataType()))
                throw new IOException("Unsupported XSD restriction changes scalar family of '" + locField.sourceName() + "' in " + aRequest.path());
            validateRestrictionFacets(locPrevious.dataType().constraints(), locField.dataType().constraints(), aRequest.path());
            if (!Objects.equals(locPrevious.dataType().constraints().pattern(), locField.dataType().constraints().pattern()))
                throw new IOException("Unsupported XSD restriction changes inherited pattern of '" + locField.sourceName() + "' in " + aRequest.path());
            if (locPrevious.presence() == AInFieldPresenceKind.REQUIRED && locField.presence() != AInFieldPresenceKind.REQUIRED)
                throw new IOException("XSD restriction relaxes required field '" + locField.sourceName() + "' in " + aRequest.path());
            if (locPrevious.presence() == AInFieldPresenceKind.FORBIDDEN && locField.presence() != AInFieldPresenceKind.FORBIDDEN)
                throw new IOException("XSD restriction un-forbids field '" + locField.sourceName() + "' in " + aRequest.path());
            locByName.put(locField.sourceName(), locField);
        }
        for (AIcdPropertyDefinition locPrevious : locResult) {
            if (locSeen.contains(locPrevious.sourceName())) continue;
            if (locPrevious.presence() == AInFieldPresenceKind.REQUIRED)
                throw new IOException("XSD restriction omits required attribute '" + locPrevious.sourceName() + "' in " + aRequest.path());
            locByName.put(locPrevious.sourceName(), new AIcdPropertyDefinition(locPrevious.sourceName(), locPrevious.dataType(), AInFieldPresenceKind.FORBIDDEN, locPrevious.nullable(), locPrevious.description(), locPrevious.title(), locPrevious.xmlField()));
        }
        return List.copyOf(locByName.values());
    }

    /**
     * Compare nested structural shapes and scalar families, including array elements.
     * This deliberately excludes narrowing facets, which are validated independently.
     *
     * @param aBase canonical type from the base declaration
     * @param aDerived canonical type from the restriction
     * @return true only when inherited getter types remain structurally compatible
     */
    private static boolean sameTypeShape(AIcdDataType aBase, AIcdDataType aDerived) {
        if (aBase.kind() != aDerived.kind()
                || !Objects.equals(aBase.constraints().dataType(), aDerived.constraints().dataType())) return false;
        return switch (aBase.kind()) {
            case ARRAY -> sameTypeShape(aBase.elementType(), aDerived.elementType());
            case REFERENCE -> Objects.equals(aBase.reference(), aDerived.reference());
            case OBJECT -> Objects.equals(aBase.properties(), aDerived.properties());
            case ONE_OF, ANY_OF -> aBase.alternatives().size() == aDerived.alternatives().size()
                    && java.util.stream.IntStream.range(0, aBase.alternatives().size())
                    .allMatch(aIndex -> sameTypeShape(aBase.alternatives().get(aIndex), aDerived.alternatives().get(aIndex)));
            default -> true;
        };
    }

    /**
     * Checks the precise XSD occurrence interval before any structural projection.
     * Repeated compositor groups containing exactly one mandatory nonrepeating
     * element are eligible for conversion into one repeated QName field. Groups
     * with multiple correlated fields must be rejected by the caller, since
     * independent arrays would erase the group repetition boundaries.
     * Full XSD grammar conformance remains the schema validator's responsibility.
     *
     * @param aParticle local element or particle compositor
     * @param aGroup whether the declaration is a group instead of a leaf element
     * @param aPath source schema for actionable diagnostics
     * @throws IOException for an invalid interval or an unrepresentable forbidden group
     */
    private static void validateOccurs(Element aParticle, boolean aGroup, Path aPath) throws IOException {
        String locMinimumText = aParticle.getAttribute("minOccurs");
        String locMaximumText = aParticle.getAttribute("maxOccurs");
        int locMinimum;
        int locMaximum;
        try {
            locMinimum = locMinimumText.isEmpty() ? 1 : Integer.parseInt(locMinimumText);
            locMaximum = locMaximumText.isEmpty() ? 1
                    : "unbounded".equals(locMaximumText) ? Integer.MAX_VALUE : Integer.parseInt(locMaximumText);
        } catch (NumberFormatException locFailure) {
            throw new IOException("Invalid XSD occurrence interval in " + aPath, locFailure);
        }
        if (locMinimum < 0 || locMaximum < 0 || locMaximum < locMinimum)
            throw new IOException("Invalid XSD occurrence interval in " + aPath);
        if (aGroup && locMaximum == 0)
            throw new IOException("Forbidden XSD compositor must preserve its child model in " + aPath);
    }

    /** A global declaration is always paired with the schema and source that define it. */
    private record AIcdGlobalDeclaration(Element declaration, AIcdDefinitionLoadRequest request,
            Element schema) { }

    /**
     * Resolves an expanded global QName via finite, local XSD import/include graphs.
     * Remote schemas, inconsistent namespace declarations and ambiguous global names
     * fail before any canonical XML field can be generated.
     *
     * @param aContext XML node containing the lexical QName
     * @param aQName prefixed or unprefixed XSD global declaration reference
     * @param aKind XML Schema global declaration kind
     * @param aRequest current schema load request
     * @param aSchema schema containing the referencing declaration
     * @return the single matching declaration with its owning schema
     * @throws IOException if the reference cannot be resolved unambiguously and locally
     */
    private AIcdGlobalDeclaration resolveGlobal(Element aContext, String aQName, String aKind,
            AIcdDefinitionLoadRequest aRequest, Element aSchema) throws IOException {
        if (aQName.isBlank() || aQName.indexOf(':') != aQName.lastIndexOf(':'))
            throw new IOException("Invalid XSD " + aKind + " QName '" + aQName + "' in " + aRequest.path());
        int locColon = aQName.indexOf(':');
        String locPrefix = locColon < 0 ? null : aQName.substring(0, locColon);
        String locLocal = locColon < 0 ? aQName : aQName.substring(locColon + 1);
        if (locLocal.isBlank())
            throw new IOException("Invalid XSD " + aKind + " QName '" + aQName + "' in " + aRequest.path());
        String locNamespace = aContext.lookupNamespaceURI(locPrefix);
        if (locPrefix != null && locNamespace == null)
            throw new IOException("Undefined XSD namespace prefix '" + locPrefix + "' in " + aRequest.path());
        String locTarget = locNamespace == null ? aSchema.getAttribute("targetNamespace") : locNamespace;
        List<AIcdGlobalDeclaration> locFound = new ArrayList<>();
        findGlobal(aRequest, aSchema, aKind, locTarget, locLocal, locFound, new HashSet<>());
        if (locFound.size() != 1)
            throw new IOException((locFound.isEmpty() ? "Unknown" : "Ambiguous") + " XSD " + aKind
                    + " reference '" + aQName + "' in " + aRequest.path());
        return locFound.get(0);
    }

    /** Traverse local schema references, using source paths to break import/include cycles. */
    private void findGlobal(AIcdDefinitionLoadRequest aRequest, Element aSchema, String aKind,
            String aNamespace, String aName, List<AIcdGlobalDeclaration> aFound,
            Set<Path> aVisited) throws IOException {
        Path locPath = aRequest.path().toAbsolutePath().normalize();
        if (!aVisited.add(locPath)) return;
        if (aNamespace.equals(aSchema.getAttribute("targetNamespace")))
            for (Element locDeclaration : children(aSchema, aKind))
                if (aName.equals(locDeclaration.getAttribute("name")))
                    aFound.add(new AIcdGlobalDeclaration(locDeclaration, aRequest, aSchema));
        for (Element locImport : children(aSchema, "import", "include")) {
            String locLocation = locImport.getAttribute("schemaLocation");
            if (locLocation.isBlank()) continue;
            URI locUri;
            try { locUri = URI.create(locLocation); }
            catch (IllegalArgumentException locFailure) {
                throw new IOException("Invalid XSD schemaLocation: " + locLocation, locFailure);
            }
            if (locUri.getFragment() != null || locUri.getQuery() != null
                    || locUri.getRawAuthority() != null
                    || locUri.isAbsolute() && !"file".equals(locUri.getScheme()))
                throw new IOException("XSD declaration imports must be local files: " + locLocation);
            Path locImportedPath;
            try {
                locImportedPath = (locUri.isAbsolute() ? Path.of(locUri)
                        : locPath.getParent().resolve(locUri.getPath())).toAbsolutePath().normalize();
            } catch (IllegalArgumentException locFailure) {
                throw new IOException("Invalid local XSD schemaLocation: " + locLocation, locFailure);
            }
            Element locImported = schema(locImportedPath);
            String locImportedNamespace = locImported.getAttribute("targetNamespace");
            if ("import".equals(locImport.getLocalName())) {
                if (!locImport.getAttribute("namespace").equals(locImportedNamespace))
                    throw new IOException("XSD import namespace disagrees with schemaLocation: " + locLocation);
            } else if (!aSchema.getAttribute("targetNamespace").equals(locImportedNamespace)) {
                throw new IOException("XSD include namespace disagrees with schemaLocation: " + locLocation);
            }
            findGlobal(new AIcdDefinitionLoadRequest(locImportedPath, sourceKind(), aRequest.namingProfile()),
                    locImported, aKind, aNamespace, aName, aFound, aVisited);
        }
    }

    /** Traverses compositors, keeping inline object fields inside their own property. */
    /**
     * Flattens a compositor only when its occurrence interval remains exact.
     *
     * <p>A repeated group consisting of one mandatory nonrepeating element is equivalent
     * to the same number of repeated sibling elements. For multiple correlated
     * fields and already repeating leaves, a flat field cannot retain the group
     * boundaries, so this helper rejects the projection rather than widening it.
     *
     * @param aOutput receiving canonical fields
     * @param aProjected declarations expanded from one compositor
     * @param aCompositor particle whose occurrence count applies to the group
     * @param aOptional whether a containing compositor was optional
     * @param aPath schema source for error diagnostics
     * @throws IOException when flattening would lose the particle structure
     */
    private static void appendCompositor(List<AIcdPropertyDefinition> aOutput,
            List<AIcdPropertyDefinition> aProjected, Element aCompositor,
            boolean aOptional, Path aPath) throws IOException {
        int locMinimum = aCompositor.hasAttribute("minOccurs")
                ? Integer.parseInt(aCompositor.getAttribute("minOccurs")) : 1;
        String locMax = aCompositor.getAttribute("maxOccurs");
        Integer locMaximum = "unbounded".equals(locMax) ? null
                : locMax.isEmpty() ? 1 : Integer.valueOf(locMax);
        if (locMinimum == 1 && Integer.valueOf(1).equals(locMaximum)) {
            aOutput.addAll(aProjected);
            return;
        }
        if (aProjected.size() != 1) throw new IOException(
                "XSD compositor cannot be flattened without losing group cardinality in " + aPath);
        var locField = aProjected.get(0);
        if (locField.presence() != AInFieldPresenceKind.REQUIRED
                || locField.dataType().kind() == AInDataTypeKind.ARRAY)
            throw new IOException("XSD compositor cannot be flattened without losing group cardinality in " + aPath);
        var locType = locMaximum == null || locMaximum > 1
                ? AIcdDataType.array(locField.dataType(), aOptional ? 0 : locMinimum, locMaximum)
                : locField.dataType();
        aOutput.add(new AIcdPropertyDefinition(locField.sourceName(), locType,
                aOptional || locMinimum == 0 ? AInFieldPresenceKind.ALLOWED : AInFieldPresenceKind.REQUIRED,
                locField.nullable(), locField.description(), locField.title(), locField.xmlField()));
    }

    private void elements(Element aParent, boolean aOptional, AIcdDefinitionLoadRequest aRequest,
            Element aSchema, List<AIcdPropertyDefinition> aProperties) throws IOException {
        elements(aParent, aOptional, aRequest, aSchema, aProperties, new HashSet<>());
    }

    /**
     * Resolve local named model groups once per active recursion branch. The group
     * is expanded only when its occurrence and optionality remain representable.
     */
    private void elements(Element aParent, boolean aOptional, AIcdDefinitionLoadRequest aRequest,
            Element aSchema, List<AIcdPropertyDefinition> aProperties,
            Set<String> aActiveGroups) throws IOException {
        for (Element locElement : children(aParent)) {
            String locKind = locElement.getLocalName();
            if (Set.of("sequence", "all", "choice").contains(locKind)) {
                validateOccurs(locElement, true, aRequest.path());
                if ("choice".equals(locKind)) throw new IOException("XSD choice is not represented by the canonical property model: " + aRequest.path());
                List<AIcdPropertyDefinition> locFields = new ArrayList<>();
                elements(locElement, aOptional, aRequest, aSchema, locFields, aActiveGroups);
                appendCompositor(aProperties, locFields, locElement, aOptional, aRequest.path());
            } else if ("element".equals(locKind)) {
                validateOccurs(locElement, false, aRequest.path());
                Element locDeclaration = locElement;
                AIcdDefinitionLoadRequest locDeclarationRequest = aRequest;
                Element locDeclarationSchema = aSchema;
                String locName = locElement.getAttribute("name");
                boolean locGlobalField = false;
                if (locElement.hasAttribute("ref")) {
                    String locRef = locElement.getAttribute("ref");
                    if (!locName.isBlank() || locElement.hasAttribute("type") || locElement.hasAttribute("nillable"))
                        throw new IOException("Invalid XSD element reference declaration in " + aRequest.path());
                    AIcdGlobalDeclaration locResolved = resolveGlobal(locElement, locRef, "element",
                            aRequest, aSchema);
                    locDeclaration = locResolved.declaration();
                    locDeclarationRequest = locResolved.request();
                    locDeclarationSchema = locResolved.schema();
                    locName = locDeclaration.getAttribute("name");
                    locGlobalField = true;
                }
                if (locName.isBlank()) throw new IOException("XSD element references require a named canonical property: " + aRequest.path());
                if (child(locDeclaration, "alternative") != null)
                    throw new IOException("Unsupported XSD conditional element type in " + aRequest.path() + ": " + locName);
                AIcdShape locShape = shape(locDeclaration, locDeclaration.getAttribute("type"), locDeclarationRequest, locDeclarationSchema, new HashSet<>());
                int locMinimum = locElement.hasAttribute("minOccurs") ? Integer.parseInt(locElement.getAttribute("minOccurs")) : 1;
                String locMaxText = locElement.getAttribute("maxOccurs");
                Integer locMaximum = "unbounded".equals(locMaxText) ? null
                        : locMaxText.isBlank() ? 1 : Integer.valueOf(locMaxText);
                boolean locRepeated = locMaximum == null || locMaximum > 1;
                if (locRepeated && locShape.kind() == AInDataTypeKind.ARRAY) throw new IOException("Nested XSD lists are not represented by the canonical property model: " + aRequest.path());
                AIcdDataType locDataType = AIcSourceDataType.fromSourceHints(locRepeated ? AInDataTypeKind.ARRAY : locShape.kind(),
                        locRepeated ? locShape.kind() : locShape.itemKind(), locShape.reference(),
                        locRepeated ? AIcdValueConstraints.empty() : locShape.constraints(),
                        locRepeated ? locShape.constraints() : locShape.itemConstraints());
                if (locRepeated)
                    locDataType = AIcdDataType.array(locDataType.elementType(), locMinimum, locMaximum);
                aProperties.add(new AIcdPropertyDefinition(locName, locDataType,
                        locMaximum != null && locMaximum == 0 ? AInFieldPresenceKind.FORBIDDEN
                        : !aOptional && locMinimum > 0 ? AInFieldPresenceKind.REQUIRED : AInFieldPresenceKind.ALLOWED,
                        Set.of("true", "1").contains(locDeclaration.getAttribute("nillable")),
                        documentation(locElement) != null ? documentation(locElement) : documentation(locDeclaration),
                        title(locElement) != null ? title(locElement) : title(locDeclaration),
                        new AIcdXmlFieldRepresentation(locGlobalField ? locDeclarationSchema.getAttribute("targetNamespace")
                                : fieldNamespace(locElement, aSchema, false),
                                locName, AInXmlValueKind.ELEMENT)));
            } else if ("group".equals(locKind)) {
                validateOccurs(locElement, true, aRequest.path());
                String locReference = locElement.getAttribute("ref");
                if (locReference.isBlank() || locElement.hasAttribute("name"))
                    throw new IOException("Unsupported XSD wildcard/group particle 'group' in " + aRequest.path());
                AIcdGlobalDeclaration locResolved = resolveGlobal(locElement, locReference, "group",
                        aRequest, aSchema);
                Element locDefinition = locResolved.declaration();
                String locIdentity = locResolved.request().path().toAbsolutePath().normalize()
                        + "#" + locDefinition.getAttribute("name");
                if (!aActiveGroups.add(locIdentity))
                    throw new IOException("Circular XSD group reference '" + locReference + "' in " + aRequest.path());
                try {
                    List<AIcdPropertyDefinition> locFields = new ArrayList<>();
                    elements(locDefinition, aOptional,
                            locResolved.request(), locResolved.schema(), locFields, aActiveGroups);
                    appendCompositor(aProperties, locFields, locElement, aOptional, aRequest.path());
                } finally {
                    aActiveGroups.remove(locIdentity);
                }
            } else if ("any".equals(locKind)) {
                throw new IOException("Unsupported XSD wildcard/group particle 'any' in " + aRequest.path());
            } else if ("annotation".equals(locKind)) {
                continue;
            } else if (Set.of("attribute", "attributeGroup", "anyAttribute", "simpleContent",
                    "complexContent").contains(locKind) && Set.of("complexType", "extension",
                    "restriction").contains(aParent.getLocalName())) {
                /* The enclosing complex-type parser processes these declarations. */
                continue;
            } else {
                throw new IOException("Unsupported XSD content model child '" + locKind
                        + "' in " + aRequest.path() + "; refusing a partial projection");
            }
        }
    }

    /** Projects root-level XML attributes into named data-object fields without erasing them. */
    private void attributes(Element aType, AIcdDefinitionLoadRequest aRequest, Element aSchema,
            List<AIcdPropertyDefinition> aProperties) throws IOException {
        attributes(aType, aRequest, aSchema, aProperties, new HashSet<>());
    }

    /** Expand local attributeGroup references while preventing recursive group cycles. */
    private void attributes(Element aType, AIcdDefinitionLoadRequest aRequest, Element aSchema,
            List<AIcdPropertyDefinition> aProperties, Set<String> aActiveGroups) throws IOException {
        if (child(aType, "anyAttribute") != null)
            throw new IOException("Unsupported XSD attribute wildcard in " + aRequest.path());
        for (Element locAttribute : children(aType, "attribute", "attributeGroup")) {
            if ("attributeGroup".equals(locAttribute.getLocalName())) {
                String locReference = locAttribute.getAttribute("ref");
                if (locReference.isBlank() || locAttribute.hasAttribute("name"))
                    throw new IOException("Invalid XSD attributeGroup reference in " + aRequest.path());
                AIcdGlobalDeclaration locResolved = resolveGlobal(locAttribute, locReference,
                        "attributeGroup", aRequest, aSchema);
                Element locGroup = locResolved.declaration();
                String locIdentity = locResolved.request().path().toAbsolutePath().normalize()
                        + "#" + locGroup.getAttribute("name");
                if (!aActiveGroups.add(locIdentity))
                    throw new IOException("Circular XSD attributeGroup reference '" + locReference + "' in " + aRequest.path());
                try {
                    attributes(locGroup, locResolved.request(), locResolved.schema(), aProperties, aActiveGroups);
                } finally {
                    aActiveGroups.remove(locIdentity);
                }
                continue;
            }
            Element locDeclaration = locAttribute;
            Element locDeclarationSchema = aSchema;
            AIcdDefinitionLoadRequest locDeclarationRequest = aRequest;
            String locReference = locAttribute.getAttribute("ref");
            if (!locReference.isBlank()) {
                if (locAttribute.hasAttribute("name") || locAttribute.hasAttribute("type")
                        || locAttribute.hasAttribute("form"))
                    throw new IOException("Invalid XSD attribute reference in " + aRequest.path());
                AIcdGlobalDeclaration locResolved = resolveGlobal(locAttribute, locReference,
                        "attribute", aRequest, aSchema);
                locDeclaration = locResolved.declaration();
                locDeclarationSchema = locResolved.schema();
                locDeclarationRequest = locResolved.request();
            }
            String locName = locDeclaration.getAttribute("name");
            if (locName.isBlank()) throw new IOException("Unnamed XSD attribute in " + aRequest.path());
            if (aProperties.stream().anyMatch(aProperty -> aProperty.sourceName().equals(locName)))
                throw new IOException("Duplicate XML element/attribute field '" + locName + "' in " + aRequest.path());
            AIcdShape locShape = shape(locDeclaration, locDeclaration.getAttribute("type"),
                    locDeclarationRequest, locDeclarationSchema, new HashSet<>());
            if (locShape.kind() == AInDataTypeKind.ARRAY || locShape.kind() == AInDataTypeKind.OBJECT)
                throw new IOException("XML attribute '" + locName + "' must have a scalar type in " + aRequest.path());
            String locUse = locAttribute.hasAttribute("use") ? locAttribute.getAttribute("use")
                    : locDeclaration.getAttribute("use");
            aProperties.add(new AIcdPropertyDefinition(locName,
                    AIcSourceDataType.fromSourceHints(locShape.kind(), locShape.itemKind(),
                            locShape.reference(), locShape.constraints(), locShape.itemConstraints()),
                    "prohibited".equals(locUse) ? AInFieldPresenceKind.FORBIDDEN
                            : "required".equals(locUse) ? AInFieldPresenceKind.REQUIRED : AInFieldPresenceKind.ALLOWED,
                    false, documentation(locAttribute) != null ? documentation(locAttribute) : documentation(locDeclaration),
                    title(locAttribute) != null ? title(locAttribute) : title(locDeclaration),
                    new AIcdXmlFieldRepresentation(locReference.isBlank()
                            ? fieldNamespace(locAttribute, aSchema, true)
                            : locDeclarationSchema.getAttribute("targetNamespace"),
                            locName, AInXmlValueKind.ATTRIBUTE)));
        }
    }

    /**
     * Resolves local XSD qualification rules separately for elements and attributes.
     * A local declaration without an explicit form follows its schema-wide default.
     * The canonical field name remains independent of the resulting expanded QName.
     */
    private static String fieldNamespace(Element aField, Element aSchema, boolean aAttribute) throws IOException {
        String locForm = aField.getAttribute("form");
        if (locForm.isEmpty()) locForm = aSchema.getAttribute(aAttribute ? "attributeFormDefault" : "elementFormDefault");
        if (locForm.isEmpty() || "unqualified".equals(locForm)) return "";
        if ("qualified".equals(locForm)) return aSchema.getAttribute("targetNamespace");
        throw new IOException("Invalid XSD " + (aAttribute ? "attribute" : "element")
                + " form '" + locForm + "'");
    }

    /** Resolves built-ins, local simple restrictions and imported canonical object/enum types. */
    private AIcdShape shape(Element aContext, String aName, AIcdDefinitionLoadRequest aRequest,
            Element aSchema, Set<String> aVisited) throws IOException {
        if (aName.isBlank()) {
            if (child(aContext, "complexType") != null) return new AIcdShape(AInDataTypeKind.OBJECT, null, null);
            Element locSimple = child(aContext, "simpleType");
            return locSimple == null ? new AIcdShape(AInDataTypeKind.ANY, null, null)
                    : simpleShape(locSimple, aRequest, aSchema, aVisited);
        }
        String locLocal = localName(aName);
        String locNamespace = aContext.lookupNamespaceURI(aName.contains(":") ? aName.substring(0, aName.indexOf(':')) : null);
        if (XS.equals(locNamespace) || (!aName.contains(":") && locNamespace == null && builtin(locLocal) != null)) {
            AIcdShape locBuiltin = builtin(locLocal);
            if (locBuiltin == null) throw new IOException("Unknown XSD built-in type '" + aName + "'.");
            return locBuiltin;
        }
        String locKey = aRequest.path().toAbsolutePath().normalize() + "#" + locNamespace + ":" + locLocal;
        if (!aVisited.add(locKey)) throw new IOException("Circular XSD simple type '" + aName + "'.");
        if (locNamespace == null || locNamespace.equals(aSchema.getAttribute("targetNamespace"))) {
            Element locType = namedType(aSchema, locLocal);
            if (locType != null) return "simpleType".equals(locType.getLocalName())
                    ? simpleShape(locType, aRequest, aSchema, aVisited) : new AIcdShape(AInDataTypeKind.OBJECT, null, null);
        }
        for (Element locImport : children(aSchema, "import", "include")) {
            if ("import".equals(locImport.getLocalName()) && !locImport.getAttribute("namespace").equals(locNamespace)) continue;
            if ("include".equals(locImport.getLocalName()) && locNamespace != null && !locNamespace.equals(aSchema.getAttribute("targetNamespace"))) continue;
            String locLocation = locImport.getAttribute("schemaLocation");
            if (locLocation.isBlank()) continue;
            URI locUri = URI.create(locLocation);
            if (locUri.isAbsolute() && !"file".equals(locUri.getScheme())) throw new IOException("XSD imports must resolve locally: " + locLocation);
            Path locPath = locUri.isAbsolute() ? Path.of(locUri) : aRequest.path().toAbsolutePath().getParent().resolve(locLocation).normalize();
            Element locImported = schema(locPath);
            Element locType = namedType(locImported, locLocal);
            if (locType == null) continue;
            var locRequest = new AIcdDefinitionLoadRequest(locPath, sourceKind(), aRequest.namingProfile());
            List<AIcdEnumValueDefinition> locEnums = enumValues(locType);
            if ("simpleType".equals(locType.getLocalName()) && locEnums.isEmpty()) return simpleShape(locType, locRequest, locImported, aVisited);
            var locParsed = identities.fromFileName(locRequest, integer(locImported.getAttribute("version")));
            var locReference = new AIcdDefinitionReference(locImported.getAttribute("targetNamespace"),
                    locParsed.version(), locParsed.logicalName(), AIcdDataType.atom(locEnums.isEmpty() ? AInDataTypeKind.OBJECT : AInDataTypeKind.ENUM, null));
            return new AIcdShape(AInDataTypeKind.REFERENCE, null, locReference);
        }
        throw new IOException("Undefined XSD type '" + aName + "' in " + aRequest.path());
    }

    /** Projects a simple restriction or list without claiming to enforce its validation facets. */
    private AIcdShape simpleShape(Element aType, AIcdDefinitionLoadRequest aRequest, Element aSchema, Set<String> aVisited) throws IOException {
        Element locRestriction = child(aType, "restriction");
        if (locRestriction != null) {
            AIcdShape locBase = shape(locRestriction, locRestriction.getAttribute("base"), aRequest, aSchema, aVisited);
            AIcdValueConstraints locConstraints = locBase.constraints();
            String locMin = locConstraints.minimum(), locMax = locConstraints.maximum(), locPattern = locConstraints.pattern();
            boolean locExclusiveMin = locConstraints.exclusiveMinimum(), locExclusiveMax = locConstraints.exclusiveMaximum();
            Integer locMinLength = locConstraints.minLength(), locMaxLength = locConstraints.maxLength();
            List<String> locEnum = new ArrayList<>();
            Set<String> locSeen = new HashSet<>();
            for (Element locFacet : children(locRestriction)) {
                String locKind = locFacet.getLocalName();
                if ("annotation".equals(locKind)) continue;
                String locCategory = Set.of("minInclusive", "minExclusive").contains(locKind) ? "lowerBound"
                        : Set.of("maxInclusive", "maxExclusive").contains(locKind) ? "upperBound" : locKind;
                if (!locSeen.add(locCategory) && !"enumeration".equals(locKind))
                    throw new IOException("Duplicate XSD restriction facet '" + locKind + "' in " + aRequest.path());
                String locValue = locFacet.getAttribute("value");
                switch (locKind) {
                    case "minInclusive", "minExclusive" -> { locMin = AIcScalarConstraints.decimal(locValue); locExclusiveMin = "minExclusive".equals(locKind); }
                    case "maxInclusive", "maxExclusive" -> { locMax = AIcScalarConstraints.decimal(locValue); locExclusiveMax = "maxExclusive".equals(locKind); }
                    case "length" -> { locMinLength = Integer.valueOf(locValue); locMaxLength = locMinLength; }
                    case "minLength" -> locMinLength = Integer.valueOf(locValue);
                    case "maxLength" -> locMaxLength = Integer.valueOf(locValue);
                    case "pattern" -> {
                        if (locConstraints.pattern() != null && !locConstraints.pattern().equals(locValue))
                            throw new IOException("Unsupported conjunction of inherited XSD pattern facets in " + aRequest.path());
                        locPattern = locValue;
                    }
                    case "enumeration" -> locEnum.add(locValue);
                    default -> throw new IOException("Unsupported XSD restriction facet '" + locKind + "' in " + aRequest.path());
                }
            }
            if (locSeen.contains("length") && (locSeen.contains("minLength") || locSeen.contains("maxLength")))
                throw new IOException("Conflicting XSD length facets in " + aRequest.path());
            AIcdValueConstraints locDerived = new AIcdValueConstraints(locConstraints.dataType(), locMin, locMax,
                    locExclusiveMin, locExclusiveMax, locMinLength, locMaxLength, locPattern,
                    locEnum.isEmpty() ? locConstraints.enumValues() : locEnum);
            validateRestrictionFacets(locConstraints, locDerived, aRequest.path());
            return new AIcdShape(locBase.kind(), locBase.itemKind(), locBase.reference(), locDerived, locBase.itemConstraints());
        }

        Element locList = child(aType, "list");
        if (locList != null) {
            AIcdShape locItem = shape(locList, locList.getAttribute("itemType"), aRequest, aSchema, aVisited);
            return new AIcdShape(AInDataTypeKind.ARRAY, locItem.kind(), locItem.reference(), AIcdValueConstraints.empty(), locItem.constraints());
        }
        throw new IOException("Unsupported XSD simple type in " + aRequest.path());
    }

    /** Ensure that the supported scalar facets never loosen a restriction's base type. */
    private static void validateRestrictionFacets(AIcdValueConstraints aBase, AIcdValueConstraints aDerived,
            Path aPath) throws IOException {
        if (aBase.minItems() != null && (aDerived.minItems() == null
                || aDerived.minItems() < aBase.minItems()))
            throw new IOException("XSD restriction relaxes inherited minOccurs in " + aPath);
        if (aBase.maxItems() != null && (aDerived.maxItems() == null
                || aDerived.maxItems() > aBase.maxItems()))
            throw new IOException("XSD restriction relaxes inherited maxOccurs in " + aPath);
        if (aBase.minimum() != null && (aDerived.minimum() == null
                || new BigDecimal(aDerived.minimum()).compareTo(new BigDecimal(aBase.minimum())) < 0
                || new BigDecimal(aDerived.minimum()).compareTo(new BigDecimal(aBase.minimum())) == 0
                    && aBase.exclusiveMinimum() && !aDerived.exclusiveMinimum()))
            throw new IOException("XSD restriction relaxes inherited minimum in " + aPath);
        if (aBase.maximum() != null && (aDerived.maximum() == null
                || new BigDecimal(aDerived.maximum()).compareTo(new BigDecimal(aBase.maximum())) > 0
                || new BigDecimal(aDerived.maximum()).compareTo(new BigDecimal(aBase.maximum())) == 0
                    && aBase.exclusiveMaximum() && !aDerived.exclusiveMaximum()))
            throw new IOException("XSD restriction relaxes inherited maximum in " + aPath);
        if (aDerived.minimum() != null && aDerived.maximum() != null) {
            int locComparison = new BigDecimal(aDerived.minimum()).compareTo(new BigDecimal(aDerived.maximum()));
            if (locComparison > 0 || locComparison == 0
                    && (aDerived.exclusiveMinimum() || aDerived.exclusiveMaximum()))
                throw new IOException("Inconsistent XSD numeric restriction bounds in " + aPath);
        }
        if (aBase.minLength() != null && (aDerived.minLength() == null
                || aDerived.minLength() < aBase.minLength()))
            throw new IOException("XSD restriction relaxes inherited minLength in " + aPath);
        if (aBase.maxLength() != null && (aDerived.maxLength() == null
                || aDerived.maxLength() > aBase.maxLength()))
            throw new IOException("XSD restriction relaxes inherited maxLength in " + aPath);
        if (aDerived.minLength() != null && aDerived.maxLength() != null
                && aDerived.minLength() > aDerived.maxLength())
            throw new IOException("Inconsistent XSD length restriction in " + aPath);
        if (!aBase.enumValues().isEmpty() && aDerived.enumValues().isEmpty())
            throw new IOException("XSD restriction removes inherited enumeration in " + aPath);
        if (!aBase.enumValues().isEmpty() && !aBase.enumValues().containsAll(aDerived.enumValues()))
            throw new IOException("XSD restriction widens inherited enumeration in " + aPath);
    }

    /** Maps XSD lexical built-ins onto the existing canonical value families. */
    private static AIcdShape builtin(String aName) {
        if (STRINGS.contains(aName)) return new AIcdShape(AInDataTypeKind.STRING, null, null, AIcScalarConstraints.defaults(aName), AIcdValueConstraints.empty());
        if (INTEGERS.contains(aName)) return new AIcdShape(AInDataTypeKind.INTEGER, null, null, AIcScalarConstraints.defaults(aName), AIcdValueConstraints.empty());
        if (Set.of("decimal", "float", "double").contains(aName)) return new AIcdShape(AInDataTypeKind.NUMBER, null, null, AIcScalarConstraints.defaults(aName), AIcdValueConstraints.empty());
        if ("boolean".equals(aName)) return new AIcdShape(AInDataTypeKind.BOOLEAN, null, null, AIcScalarConstraints.defaults(aName), AIcdValueConstraints.empty());
        if (Set.of("NMTOKENS", "IDREFS", "ENTITIES").contains(aName)) return new AIcdShape(AInDataTypeKind.ARRAY, AInDataTypeKind.STRING, null, AIcScalarConstraints.defaults(aName), AIcScalarConstraints.defaults("string"));
        if (Set.of("anyType", "anySimpleType", "anyAtomicType").contains(aName)) return new AIcdShape(AInDataTypeKind.ANY, null, null, AIcScalarConstraints.defaults("anyType".equals(aName) ? null : aName), AIcdValueConstraints.empty());
        return null;
    }

    /** Parses securely; schema imports are resolved explicitly rather than by the XML parser. */
    private static Element schema(Path aPath) throws IOException {
        try {
            DocumentBuilderFactory locFactory = DocumentBuilderFactory.newInstance();
            locFactory.setNamespaceAware(true);
            locFactory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            locFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
            locFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            Element locRoot = locFactory.newDocumentBuilder().parse(aPath.toFile()).getDocumentElement();
            if (!XS.equals(locRoot.getNamespaceURI()) || !"schema".equals(locRoot.getLocalName()))
                throw new IOException("Expected XML Schema root in " + aPath);
            if (child(locRoot, "redefine", "override", "defaultOpenContent") != null)
                throw new IOException("Unsupported XSD schema override/redefine/open content in " + aPath);
            return locRoot;
        } catch (Exception locFailure) { throw new IOException("Cannot parse XSD " + aPath, locFailure); }
    }

    /** Returns immediate XSD children, preserving declaration order. */
    private static List<Element> children(Element aElement, String... aNames) {
        List<Element> locResult = new ArrayList<>();
        if (aElement == null) return locResult;
        for (Node locNode = aElement.getFirstChild(); locNode != null; locNode = locNode.getNextSibling()) {
            if (locNode instanceof Element locChild && XS.equals(locChild.getNamespaceURI())
                    && (aNames.length == 0 || List.of(aNames).contains(locChild.getLocalName()))) locResult.add(locChild);
        }
        return locResult;
    }

    private static Element child(Element aElement, String... aNames) { return children(aElement, aNames).stream().findFirst().orElse(null); }
    private static String localName(String aName) { return aName.substring(aName.indexOf(':') + 1); }
    private static Element namedType(Element aSchema, String aName) {
        return children(aSchema, "complexType", "simpleType").stream().filter(aType -> aName.equals(aType.getAttribute("name"))).findFirst().orElse(null);
    }
    private static Integer integer(String aValue) {
        try { return aValue.isBlank() ? null : Integer.valueOf(aValue); } catch (NumberFormatException locFailure) { return null; }
    }
    private static String documentation(Element aElement) {
        Element locAnnotation = child(aElement, "annotation");
        Element locDocumentation = child(locAnnotation, "documentation");
        if (locDocumentation == null) return null;
        String locValue = locDocumentation.getTextContent().strip().replaceAll("\\s+", " ");
        return locValue.isEmpty() ? null : locValue;
    }
    /** Reads the Algites documentation title from the appinfo extension namespace. */
    private static String title(Element aElement) {
        if (aElement == null) return null;
        Element locAnnotation = child(aElement, "annotation");
        Element locAppinfo = child(locAnnotation, "appinfo");
        if (locAppinfo == null) return null;
        var locChildren = locAppinfo.getChildNodes();
        for (int locIndex = 0; locIndex < locChildren.getLength(); locIndex++) {
            if (locChildren.item(locIndex) instanceof Element locTitle
                    && "urn:eu:algites:documentation:1".equals(locTitle.getNamespaceURI())
                    && "title".equals(locTitle.getLocalName())) {
                String locValue = locTitle.getTextContent().strip();
                return locValue.isEmpty() ? null : locValue;
            }
        }
        return null;
    }

    private static List<AIcdEnumValueDefinition> enumValues(Element aType) {
        Element locRestriction = child(aType, "restriction");
        return children(locRestriction, "enumeration").stream().map(aValue -> new AIcdEnumValueDefinition(aValue.getAttribute("value"), documentation(aValue), title(aValue))).toList();
    }
    private record AIcdShape(AInDataTypeKind kind, AInDataTypeKind itemKind, AIcdDefinitionReference reference,
            AIcdValueConstraints constraints, AIcdValueConstraints itemConstraints) {
        private AIcdShape(AInDataTypeKind aKind, AInDataTypeKind aItemKind, AIcdDefinitionReference aReference) {
            this(aKind, aItemKind, aReference, AIcdValueConstraints.empty(), AIcdValueConstraints.empty());
        }
    }
}
