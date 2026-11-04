package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * Exact expanded XML field name and representation, including XSD form defaults.
 * The wire QName never substitutes for the semantic generated accessor identifier.
 *
 * @param namespaceUri namespace URI, or empty string for an unqualified name
 * @param localName unprefixed original XML field name
 * @param valueKind XML ELEMENT or ATTRIBUTE representation
 */
public record AIcdDefsCodegenXmlWireName(String namespaceUri, String localName,
        AInDefsCodegenXmlValueKind valueKind) {
    /**
     * Validates a complete XML wire identity.
     * @throws NullPointerException for any missing component
     * @throws IllegalArgumentException for an empty or qualified local name
     */
    public AIcdDefsCodegenXmlWireName {
        Objects.requireNonNull(namespaceUri, "namespaceUri");
        Objects.requireNonNull(localName, "localName");
        Objects.requireNonNull(valueKind, "valueKind");
        if (localName.isEmpty() || localName.contains(":") || localName.startsWith("{")) {
            throw new IllegalArgumentException("XML QName requires a local name, not a prefixed QName");
        }
    }
}
