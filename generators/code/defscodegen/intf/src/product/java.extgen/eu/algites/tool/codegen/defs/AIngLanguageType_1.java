package eu.algites.tool.codegen.defs;

/**
 * One supported output programming language.
 *
 * <p>Canonical identity: eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/LanguageType; version: 1.</p>
 * <p>Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd}LanguageType; version: 1.</p>
 */
public enum AIngLanguageType_1 {
    /** Exact wire value java. */
    JAVA("java"),
    /** Exact wire value python. */
    PYTHON("python");

    private final String wireCode;

    /** @param aWireCode original typed schema code */
    AIngLanguageType_1(String aWireCode) { wireCode = aWireCode; }

    /** @return the exact typed schema wire value */
    public String code() { return wireCode; }
}
