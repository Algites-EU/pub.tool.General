package eu.algites.tool.codegen.sdo;

import java.util.Objects;

/**
 * Generated SDO source with its importable type and canonical origin.
 *
 * @param typeName name of the generated public type
 * @param relativePath path relative to the output source root
 * @param source generated source text
 * @param namespace logical namespace or Java package
 * @param moduleName importable module identifier
 * @param fullyQualifiedTypeName fully qualified generated type identity
 * @param typeRole generation role of the source type
 * @param sourceDefinitionId canonical identity of its source definition
 * @param sourceDefinitionVersion version of its source definition, when available
 */
public record AIcdGeneratedSdoSource(
        String typeName, String relativePath, String source,
        String namespace, String moduleName, String fullyQualifiedTypeName,
        String typeRole, String sourceDefinitionId, Integer sourceDefinitionVersion) {

    /** Validates immutable generated type metadata. */
    public AIcdGeneratedSdoSource {
        Objects.requireNonNull(typeName, "typeName");
        Objects.requireNonNull(relativePath, "relativePath");
        Objects.requireNonNull(source, "source");
        Objects.requireNonNull(namespace, "namespace");
        Objects.requireNonNull(moduleName, "moduleName");
        Objects.requireNonNull(fullyQualifiedTypeName, "fullyQualifiedTypeName");
        Objects.requireNonNull(typeRole, "typeRole");
        Objects.requireNonNull(sourceDefinitionId, "sourceDefinitionId");
    }

    /** Compatibility constructor for sources without type metadata. */
    public AIcdGeneratedSdoSource(String aTypeName, String aRelativePath, String aSource) {
        this(aTypeName, aRelativePath, aSource, "", "", "", "", "", null);
    }
}
