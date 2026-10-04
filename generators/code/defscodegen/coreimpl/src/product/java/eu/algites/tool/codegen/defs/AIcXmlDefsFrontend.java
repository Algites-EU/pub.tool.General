package eu.algites.tool.codegen.defs;

import java.io.IOException;
import java.net.URI;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
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
        if (locDescription == null) locDescription = documentation(locSchema);
        if (!locValues.isEmpty()) return new AIcdCanonicalDefinition(locIdentity, locParsed.version(),
                locParsed.logicalName(), AInDefinitionKind.ENUM, sourceKind(), aRequest.path().toString(),
                locDescription, List.of(), locValues);
        List<AIcdPropertyDefinition> locProperties = new ArrayList<>();
        if (locType != null && "complexType".equals(locType.getLocalName())) {
            elements(locType, false, aRequest, locSchema, locProperties);
            return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locParsed.logicalName(),
                    AInDefinitionKind.OBJECT, sourceKind(), aRequest.path().toString(), locDescription,
                    locProperties, List.of());
        }
        Element locElement = child(locSchema, "element");
        AIcdShape locShape = locType != null ? simpleShape(locType, aRequest, locSchema, new HashSet<>())
                : locElement != null ? shape(locElement, locElement.getAttribute("type"), aRequest, locSchema, new HashSet<>())
                : new AIcdShape(AInValueKind.ANY, null, null);
        var locProperty = new AIcdPropertyDefinition("value", locShape.kind(), true,
                locElement != null && Set.of("true", "1").contains(locElement.getAttribute("nillable")),
                locShape.itemKind(), locShape.reference(), locDescription, locShape.constraints(), locShape.itemConstraints());
        return new AIcdCanonicalDefinition(locIdentity, locParsed.version(), locParsed.logicalName(),
                AInDefinitionKind.SCALAR, sourceKind(), aRequest.path().toString(), locDescription, List.of(locProperty), List.of());
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

    /** Traverses compositors, keeping inline object fields inside their own property. */
    private void elements(Element aParent, boolean aOptional, AIcdDefinitionLoadRequest aRequest,
            Element aSchema, List<AIcdPropertyDefinition> aProperties) throws IOException {
        for (Element locElement : children(aParent)) {
            String locKind = locElement.getLocalName();
            if (Set.of("sequence", "all", "choice").contains(locKind)) {
                if ("choice".equals(locKind)) throw new IOException("XSD choice is not represented by the canonical property model: " + aRequest.path());
                elements(locElement, aOptional || "0".equals(locElement.getAttribute("minOccurs")), aRequest, aSchema, aProperties);
            } else if ("element".equals(locKind)) {
                if (!locElement.hasAttribute("name")) throw new IOException("XSD element references require a named canonical property: " + aRequest.path());
                AIcdShape locShape = shape(locElement, locElement.getAttribute("type"), aRequest, aSchema, new HashSet<>());
                boolean locRepeated = locElement.hasAttribute("maxOccurs") && !"1".equals(locElement.getAttribute("maxOccurs"));
                if (locRepeated && locShape.kind() == AInValueKind.ARRAY) throw new IOException("Nested XSD lists are not represented by the canonical property model: " + aRequest.path());
                aProperties.add(new AIcdPropertyDefinition(locElement.getAttribute("name"),
                        locRepeated ? AInValueKind.ARRAY : locShape.kind(),
                        !aOptional && !"0".equals(locElement.getAttribute("minOccurs")),
                        Set.of("true", "1").contains(locElement.getAttribute("nillable")),
                        locRepeated ? locShape.kind() : locShape.itemKind(), locShape.reference(), documentation(locElement),
                        locRepeated ? AIcdValueConstraints.empty() : locShape.constraints(),
                        locRepeated ? locShape.constraints() : locShape.itemConstraints()));
            }
        }
    }

    /** Resolves built-ins, local simple restrictions and imported canonical object/enum types. */
    private AIcdShape shape(Element aContext, String aName, AIcdDefinitionLoadRequest aRequest,
            Element aSchema, Set<String> aVisited) throws IOException {
        if (aName.isBlank()) {
            if (child(aContext, "complexType") != null) return new AIcdShape(AInValueKind.OBJECT, null, null);
            Element locSimple = child(aContext, "simpleType");
            return locSimple == null ? new AIcdShape(AInValueKind.ANY, null, null)
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
                    ? simpleShape(locType, aRequest, aSchema, aVisited) : new AIcdShape(AInValueKind.OBJECT, null, null);
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
                    locParsed.version(), locParsed.logicalName(), locEnums.isEmpty() ? AInDefinitionKind.OBJECT : AInDefinitionKind.ENUM);
            return new AIcdShape(AInValueKind.REFERENCE, null, locReference);
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
            for (Element locFacet : children(locRestriction)) {
                String locValue = locFacet.getAttribute("value");
                switch (locFacet.getLocalName()) {
                    case "minInclusive", "minExclusive" -> { locMin = AIcScalarConstraints.decimal(locValue); locExclusiveMin = "minExclusive".equals(locFacet.getLocalName()); }
                    case "maxInclusive", "maxExclusive" -> { locMax = AIcScalarConstraints.decimal(locValue); locExclusiveMax = "maxExclusive".equals(locFacet.getLocalName()); }
                    case "length" -> { locMinLength = Integer.valueOf(locValue); locMaxLength = locMinLength; }
                    case "minLength" -> locMinLength = Integer.valueOf(locValue);
                    case "maxLength" -> locMaxLength = Integer.valueOf(locValue);
                    case "pattern" -> locPattern = locValue;
                    case "enumeration" -> locEnum.add(locValue);
                    default -> { }
                }
            }
            return new AIcdShape(locBase.kind(), locBase.itemKind(), locBase.reference(),
                    new AIcdValueConstraints(locConstraints.dataType(), locMin, locMax, locExclusiveMin, locExclusiveMax,
                            locMinLength, locMaxLength, locPattern, locEnum.isEmpty() ? locConstraints.enumValues() : locEnum), locBase.itemConstraints());
        }
        Element locList = child(aType, "list");
        if (locList != null) {
            AIcdShape locItem = shape(locList, locList.getAttribute("itemType"), aRequest, aSchema, aVisited);
            return new AIcdShape(AInValueKind.ARRAY, locItem.kind(), locItem.reference(), AIcdValueConstraints.empty(), locItem.constraints());
        }
        throw new IOException("Unsupported XSD simple type in " + aRequest.path());
    }

    /** Maps XSD lexical built-ins onto the existing canonical value families. */
    private static AIcdShape builtin(String aName) {
        if (STRINGS.contains(aName)) return new AIcdShape(AInValueKind.STRING, null, null, AIcScalarConstraints.defaults(aName), AIcdValueConstraints.empty());
        if (INTEGERS.contains(aName)) return new AIcdShape(AInValueKind.INTEGER, null, null, AIcScalarConstraints.defaults(aName), AIcdValueConstraints.empty());
        if (Set.of("decimal", "float", "double").contains(aName)) return new AIcdShape(AInValueKind.NUMBER, null, null, AIcScalarConstraints.defaults(aName), AIcdValueConstraints.empty());
        if ("boolean".equals(aName)) return new AIcdShape(AInValueKind.BOOLEAN, null, null, AIcScalarConstraints.defaults(aName), AIcdValueConstraints.empty());
        if (Set.of("NMTOKENS", "IDREFS", "ENTITIES").contains(aName)) return new AIcdShape(AInValueKind.ARRAY, AInValueKind.STRING, null, AIcScalarConstraints.defaults(aName), AIcScalarConstraints.defaults("string"));
        if (Set.of("anyType", "anySimpleType", "anyAtomicType").contains(aName)) return new AIcdShape(AInValueKind.ANY, null, null, AIcScalarConstraints.defaults("anyType".equals(aName) ? null : aName), AIcdValueConstraints.empty());
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
            return locFactory.newDocumentBuilder().parse(aPath.toFile()).getDocumentElement();
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
    private static List<AIcdEnumValueDefinition> enumValues(Element aType) {
        Element locRestriction = child(aType, "restriction");
        return children(locRestriction, "enumeration").stream().map(aValue -> new AIcdEnumValueDefinition(aValue.getAttribute("value"), documentation(aValue))).toList();
    }
    private record AIcdShape(AInValueKind kind, AInValueKind itemKind, AIcdDefinitionReference reference,
            AIcdValueConstraints constraints, AIcdValueConstraints itemConstraints) {
        private AIcdShape(AInValueKind aKind, AInValueKind aItemKind, AIcdDefinitionReference aReference) {
            this(aKind, aItemKind, aReference, AIcdValueConstraints.empty(), AIcdValueConstraints.empty());
        }
    }
}
