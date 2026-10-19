package eu.algites.tool.codegen.defs;

import eu.algites.lib.data.dataobject.AInFieldPresenceKind;
import java.util.Objects;

/**
 * Named member of an object with exactly one recursive structural type.
 * Presence and explicit nullability are orthogonal to the structural type.
 * No scalar/array/reference compatibility descriptors are stored alongside the type.
 *
 * @param sourceName canonical source member name, independent of generated identifier
 * @param dataType fully recursive member type, including all nested constraints and references
 * @param presence whether the member must occur, may occur or has other presence semantics
 * @param nullable whether an explicitly present null is accepted
 * @param description optional source documentation
 * @param title optional short source title
 * @param xmlField XML QName and attribute/element kind, or null for non-XML members
 */
public record AIcdPropertyDefinition(
        String sourceName,
        AIcdDataType dataType,
        AInFieldPresenceKind presence,
        boolean nullable,
        String description,
        String title,
        AIcdXmlFieldRepresentation xmlField) {
    /** Rejects missing canonical identity and type; resolves omitted presence to ALLOWED. */
    public AIcdPropertyDefinition {
        Objects.requireNonNull(sourceName, "sourceName");
        Objects.requireNonNull(dataType, "dataType");
        presence = presence == null ? AInFieldPresenceKind.ALLOWED : presence;
    }
}
