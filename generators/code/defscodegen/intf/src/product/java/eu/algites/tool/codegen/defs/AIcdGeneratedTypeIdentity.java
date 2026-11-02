package eu.algites.tool.codegen.defs;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;

import java.util.Objects;

/**
 * Importable identity of one generated type, with its canonical source and generation role.
 *
 * @param typeName simple name of the generated public type
 * @param namespace target namespace or package
 * @param moduleName source module that exposes the generated type
 * @param fullyQualifiedTypeName fully qualified importable type name
 * @param typeRole role of the generated type
 * @param technologyKind programming language of the generated source
 * @param sourceDefinitionId canonical originating definition identity
 * @param sourceDefinitionVersion originating definition version, when available
 */
public record AIcdGeneratedTypeIdentity(
        String typeName,
        String namespace,
        String moduleName,
        String fullyQualifiedTypeName,
        AInDefsNameRole typeRole,
        AInCodeGenerationTarget technologyKind,
        String sourceDefinitionId,
        Integer sourceDefinitionVersion) {

    /** Validates an immutable generated type identity. */
    public AIcdGeneratedTypeIdentity {
        Objects.requireNonNull(typeName, "typeName");
        Objects.requireNonNull(namespace, "namespace");
        Objects.requireNonNull(moduleName, "moduleName");
        Objects.requireNonNull(fullyQualifiedTypeName, "fullyQualifiedTypeName");
        Objects.requireNonNull(typeRole, "typeRole");
        Objects.requireNonNull(technologyKind, "technologyKind");
        Objects.requireNonNull(sourceDefinitionId, "sourceDefinitionId");
    }

    /** Builds a language-aware importable identity from the canonical request. */
    public static AIcdGeneratedTypeIdentity fromRequest(
            AIcdCodeGenerationRequest aRequest, String aTypeName,
            String aRelativePath, AInDefsNameRole aRole) {
        String locNamespace = aRequest.packageName();
        String locModule = locNamespace;
        if (aRequest.target() == AInCodeGenerationTarget.PYTHON) {
            String locFile = aRelativePath.substring(aRelativePath.lastIndexOf('/') + 1);
            if (!locFile.endsWith(".py")) throw new AIxCodegenValidationException("Expected Python path", "Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.");
            locModule += "." + locFile.substring(0, locFile.length() - 3);
        }
        return new AIcdGeneratedTypeIdentity(
                aTypeName, locNamespace, locModule, locModule + "." + aTypeName,
                aRole, aRequest.target(), aRequest.definition().identity(), aRequest.definition().version());
    }
}
