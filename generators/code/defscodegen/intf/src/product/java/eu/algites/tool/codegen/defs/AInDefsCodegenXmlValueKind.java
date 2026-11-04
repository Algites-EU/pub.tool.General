package eu.algites.tool.codegen.defs;

/** Wire representation of a field in an XML document, independent of its semantic identifier. */
public enum AInDefsCodegenXmlValueKind {
    /** XML child element. */
    ELEMENT,
    /** XML attribute, with zero or one scalar value. */
    ATTRIBUTE
}
