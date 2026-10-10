package eu.algites.tool.codegen.defs;

/**
 * Reference to another canonical definition.
 *
 * @param identity canonical reference identity or source reference
 * @param version referenced canonical definition version
 * @param logicalName referenced logical definition name
 * @param targetKind normalized target definition kind when known
 */
public record AIcdDefinitionReference(String identity, Integer version, String logicalName, AInDefinitionKind targetKind) {
}
