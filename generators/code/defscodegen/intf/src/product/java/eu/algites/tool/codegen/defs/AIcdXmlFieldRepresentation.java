package eu.algites.tool.codegen.defs;

import eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind;
import java.util.Objects;

/**
 * XML wire identity of one canonical property, independent of its Java/Python name.
 * The empty namespace denotes an unqualified local XML element or attribute.
 * This projection intentionally does not conflate an XML attribute with an element
 * of the same local name; their kind and namespace remain part of the identity.
 *
 * @param namespace expanded XML namespace URI, possibly empty
 * @param namespaceLocalName required local part of the XML QName
 * @param valueKind XML element or attribute representation
 */
public record AIcdXmlFieldRepresentation(
        String namespace, String namespaceLocalName, AInXmlValueKind valueKind) {
    /**
     * Validates that every represented field has a complete QName and wire kind.
     *
     * @throws NullPointerException if any component is null
     * @throws IllegalArgumentException if the local name is blank
     */
    public AIcdXmlFieldRepresentation {
        Objects.requireNonNull(namespace, "namespace");
        Objects.requireNonNull(namespaceLocalName, "namespaceLocalName");
        Objects.requireNonNull(valueKind, "valueKind");
        if (namespaceLocalName.isBlank()) throw new IllegalArgumentException("XML field local name is blank");
    }
}
