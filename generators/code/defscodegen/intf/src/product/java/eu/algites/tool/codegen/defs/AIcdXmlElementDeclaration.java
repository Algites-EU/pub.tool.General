package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * One global XML element declaration, distinct from its content data type.
 * Substitution is a relation between qualified element identities, not data types.
 *
 * @param localName element local name
 * @param namespace target XML namespace
 * @param typeQName declared content type expanded QName
 * @param substitutionHeadQName expanded QName of the direct substitution head, if any
 * @param abstractElement true if the global element cannot occur directly
 * @param nillable whether explicit XML nil is permitted
 */
public record AIcdXmlElementDeclaration(String localName, String namespace,
        String typeQName, String substitutionHeadQName, boolean abstractElement,
        boolean nillable) {
    /** Validate the global element's stable identity. */
    public AIcdXmlElementDeclaration {
        Objects.requireNonNull(localName, "localName");
        Objects.requireNonNull(namespace, "namespace");
        Objects.requireNonNull(typeQName, "typeQName");
        if (localName.isBlank()) throw new IllegalArgumentException("XML element name is empty");
    }
    /** Expanded QName used for namespace-safe substitution lookup. */
    public String qName() { return "{" + namespace + "}" + localName; }
}
