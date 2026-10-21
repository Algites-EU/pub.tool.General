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
 * @param minOccurs minimum XML occurrence count, or -1 when unknown
 * @param maxOccurs maximum XML occurrence count, or -1 when unbounded or unknown
 * @param wildcardNamespace original xs:any namespace expression; empty for ordinary fields
 * @param wildcardProcessContents xs:any validation policy
 */
public record AIcdXmlFieldRepresentation(
        String namespace, String namespaceLocalName, AInXmlValueKind valueKind, int minOccurs, int maxOccurs,
        String wildcardNamespace, String wildcardProcessContents) {
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
        Objects.requireNonNull(wildcardNamespace, "wildcardNamespace");
        Objects.requireNonNull(wildcardProcessContents, "wildcardProcessContents");
        if (!wildcardNamespace.isBlank() && (valueKind != AInXmlValueKind.ELEMENT
                || !java.util.Set.of("skip", "lax", "strict").contains(wildcardProcessContents)))
            throw new IllegalArgumentException("Invalid xs:any wildcard metadata");
        if (namespaceLocalName.isBlank()) throw new IllegalArgumentException("XML field local name is blank");
        if (minOccurs < -1 || maxOccurs < -1 || (minOccurs >= 0 && maxOccurs >= 0 && minOccurs > maxOccurs))
            throw new IllegalArgumentException("Invalid XML wire occurrence interval");
    }

    /**
     * Construct an ordinary XML field without wildcard metadata.
     *
     * @param aNamespace XML namespace URI
     * @param aLocalName XML QName local part
     * @param aValueKind element or attribute kind
     * @param aMinOccurs minimum occurrence count
     * @param aMaxOccurs maximum occurrence count
     */
    public AIcdXmlFieldRepresentation(String aNamespace, String aLocalName, AInXmlValueKind aValueKind,
            int aMinOccurs, int aMaxOccurs) {
        this(aNamespace, aLocalName, aValueKind, aMinOccurs, aMaxOccurs, "", "strict");
    }

    /**
     * Construct XML field identity without explicit wire occurrence constraints.
     *
     * @param aNamespace XML namespace URI
     * @param aLocalName XML QName local part
     * @param aValueKind element or attribute kind
     */
    public AIcdXmlFieldRepresentation(String aNamespace, String aLocalName, AInXmlValueKind aValueKind) {
        this(aNamespace, aLocalName, aValueKind, -1, -1, "", "strict");
    }
}
