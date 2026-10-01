package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.conversion.AIcdParsedVersionedName;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** Loads canonical definitions expressed as XML Schema definitions. */
public final class AIcXmlDefsFrontend implements AIiDefinitionFrontend {
    /** Creates the default XML/XSD definition frontend. */
    public AIcXmlDefsFrontend() {
    }
    private static final String XS = "http://www.w3.org/2001/XMLSchema";
    private final AIcDefinitionIdentityResolver identities = new AIcDefinitionIdentityResolver();

    /**
     * Returns the source family handled by this frontend.
     *
     * @return the XML definitions source kind
     */
    @Override
    public AInDefinitionSourceKind sourceKind() {
        return AInDefinitionSourceKind.XMLDEFS;
    }

    /**
     * Loads one XSD resource into the format-neutral canonical-definition model.
     *
     * @param request source path, source kind, and naming policy
     * @return the normalized canonical definition
     * @throws IOException if the XSD cannot be parsed
     */
    @Override
    public AIcdCanonicalDefinition load(AIcdDefinitionLoadRequest request) throws IOException {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            Document document = factory.newDocumentBuilder().parse(request.path().toFile());
            Element schema = document.getDocumentElement();
            Integer explicitVersion = intAttribute(schema, "version");
            AIcdParsedVersionedName parsed = identities.fromFileName(request, explicitVersion);
            String targetNamespace = schema.getAttribute("targetNamespace");
            String identity = targetNamespace == null || targetNamespace.isBlank() ? parsed.logicalName() : targetNamespace;
            String schemaDescription = documentation(schema);
            NodeList simpleTypes = schema.getElementsByTagNameNS(XS, "simpleType");
            if (simpleTypes.getLength() > 0) {
                Element type = (Element) simpleTypes.item(0);
                List<AIcdEnumValueDefinition> values = new ArrayList<>();
                NodeList enums = type.getElementsByTagNameNS(XS, "enumeration");
                for (int i = 0; i < enums.getLength(); i++) {
                    Element enumElement = (Element) enums.item(i);
                    values.add(new AIcdEnumValueDefinition(enumElement.getAttribute("value"), documentation(enumElement)));
                }
                if (!values.isEmpty()) {
                    String logical = type.getAttribute("name");
                    if (logical == null || logical.isBlank()) logical = parsed.logicalName();
                    return new AIcdCanonicalDefinition(identity, parsed.version(), logical, AInDefinitionKind.ENUM, sourceKind(), request.path().toString(), firstNonBlank(documentation(type), schemaDescription), List.of(), values);
                }
            }
            NodeList complexTypes = schema.getElementsByTagNameNS(XS, "complexType");
            if (complexTypes.getLength() > 0) {
                Element type = (Element) complexTypes.item(0);
                String logical = type.getAttribute("name");
                if (logical == null || logical.isBlank()) logical = parsed.logicalName();
                List<AIcdPropertyDefinition> properties = new ArrayList<>();
                NodeList elements = type.getElementsByTagNameNS(XS, "element");
                for (int i = 0; i < elements.getLength(); i++) {
                    Element element = (Element) elements.item(i);
                    String name = element.getAttribute("name");
                    String xsdType = element.getAttribute("type");
                    boolean required = !"0".equals(element.getAttribute("minOccurs"));
                    boolean nullable = "true".equals(element.getAttribute("nillable"));
                    properties.add(new AIcdPropertyDefinition(name, valueKind(xsdType), required, nullable, null, null, documentation(element)));
                }
                return new AIcdCanonicalDefinition(identity, parsed.version(), logical, AInDefinitionKind.OBJECT, sourceKind(), request.path().toString(), firstNonBlank(documentation(type), schemaDescription), properties, List.of());
            }
            return new AIcdCanonicalDefinition(identity, parsed.version(), parsed.logicalName(), AInDefinitionKind.SCALAR, sourceKind(), request.path().toString(), schemaDescription, List.of(), List.of());
        } catch (Exception ex) {
            if (ex instanceof IOException io) throw io;
            throw new IOException("Cannot parse XSD " + request.path(), ex);
        }
    }

    /**
     * Reads one integer-valued XML attribute.
     *
     * @param element source element
     * @param name attribute name
     * @return parsed integer, or {@code null} when absent or invalid
     */
    private static Integer intAttribute(Element element, String name) {
        String value = element.getAttribute(name);
        try {
            return value == null || value.isBlank() ? null : Integer.valueOf(value);
        } catch (NumberFormatException ex) {
            return null;
        }
    }

    /**
     * Reads the first XSD documentation text associated with an element.
     *
     * @param element XSD element
     * @return normalized documentation text, or {@code null} when no documentation exists
     */
    private static String documentation(Element element) {
        NodeList annotations = element.getChildNodes();
        for (int i = 0; i < annotations.getLength(); i++) {
            Node node = annotations.item(i);
            if (!(node instanceof Element annotation) || !XS.equals(annotation.getNamespaceURI()) || !"annotation".equals(annotation.getLocalName())) continue;
            NodeList docs = annotation.getElementsByTagNameNS(XS, "documentation");
            if (docs.getLength() == 0) return null;
            String value = docs.item(0).getTextContent();
            return value == null || value.isBlank() ? null : value.strip();
        }
        return null;
    }

    /**
     * Selects the first non-empty documentation value.
     *
     * @param preferred preferred value
     * @param fallback fallback value
     * @return preferred value when present, otherwise fallback
     */
    private static String firstNonBlank(String preferred, String fallback) {
        return preferred == null || preferred.isBlank() ? fallback : preferred;
    }

    /**
     * Maps an XSD type name to the normalized scalar/reference value kind.
     *
     * @param value XSD type name
     * @return normalized value kind
     */
    private static AInValueKind valueKind(String value) {
        if (value == null) return AInValueKind.ANY;
        if (value.endsWith(":string") || value.equals("string")) return AInValueKind.STRING;
        if (value.endsWith(":integer") || value.endsWith(":int") || value.equals("integer") || value.equals("int")) return AInValueKind.INTEGER;
        if (value.endsWith(":decimal") || value.endsWith(":double") || value.equals("decimal") || value.equals("double")) return AInValueKind.NUMBER;
        if (value.endsWith(":boolean") || value.equals("boolean")) return AInValueKind.BOOLEAN;
        return AInValueKind.REFERENCE;
    }
}
