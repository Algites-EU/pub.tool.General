package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import java.util.Set;

/** Project nested schema shapes to actual repository-discovered named contracts. */
final class AIcRecursiveContractType {
    private AIcRecursiveContractType() { }

    /** The batch discovery path uses these same source-name tokens. */
    private static String kebab(String aName) {
        return aName.replaceAll("([a-z0-9])([A-Z])", "$1-$2")
                .replaceAll("[^A-Za-z0-9]+", "-").replaceAll("^-|-$", "")
                .toLowerCase(java.util.Locale.ROOT);
    }

    static String render(AIcdPropertyDefinition aProperty, AIcdCodeGenerationRequest aRequest,
            AIcGenerationNames aNames, boolean aJava, Set<String> aPythonImports) {
        String locPath = aRequest.definition().logicalName() + "-" + kebab(aProperty.sourceName());
        return renderNode(aProperty.dataType(), locPath, aRequest, aNames, aJava, aPythonImports);
    }

    private static String renderNode(AIcdDataType aType, String aPath,
            AIcdCodeGenerationRequest aRequest, AIcGenerationNames aNames, boolean aJava,
            Set<String> aPythonImports) {
        if (aType.kind() == AInDataTypeKind.ARRAY) {
            String locMember = renderNode(aType.elementType(), aPath + "-items", aRequest,
                    aNames, aJava, aPythonImports);
            return aJava ? "java.util.List<? extends " + locMember + ">" : "tuple[" + locMember + ", ...]";
        }
        boolean locReference = aType.kind() == AInDataTypeKind.REFERENCE;
        boolean locInline = aType.kind() == AInDataTypeKind.OBJECT
                || aType.kind() == AInDataTypeKind.ONE_OF || aType.kind() == AInDataTypeKind.ANY_OF
                || aType.kind() == AInDataTypeKind.ENUM;
        if (locInline && aRequest.definition().sourceKind() == AInDefinitionSourceKind.XMLDEFS) {
            if (aType.kind() == AInDataTypeKind.OBJECT && aType.properties().isEmpty())
                return AIcScalarGeneration.scalar(AInDataTypeKind.OBJECT, aType.constraints(), aJava);
            throw new IllegalArgumentException("Inline XML complex/choice member needs an explicitly generated XSD content contract: " + aPath);
        }
        if (locReference || locInline) {
            boolean locEnum = locReference
                    ? aType.reference().targetsEnum()
                    : aType.kind() == AInDataTypeKind.ENUM;
            String locLogicalName = locReference ? aType.reference().logicalName() : aPath;
            Integer locVersion = locReference ? aType.reference().version() : aRequest.definition().version();
            AInDefsNameRole locRole = locEnum ? AInDefsNameRole.ENUM_TYPE : AInDefsNameRole.INTERFACE_TYPE;
            AInDefsNameRole locFileRole = locEnum ? AInDefsNameRole.ENUM_TYPE_FILE_STEM
                    : AInDefsNameRole.INTERFACE_TYPE_FILE_STEM;
            String locType = aNames.referenceTypeName(locLogicalName, locVersion,
                    aRequest.namingProfile(), locRole);
            if (!aJava) {
                String locFile = aNames.referenceTypeName(locLogicalName, locVersion,
                        aRequest.namingProfile(), locFileRole);
                aPythonImports.add("from ." + locFile + " import " + locType);
            }
            return locType;
        }
        AInDataTypeKind locKind = switch (aType.kind()) {
            case STRING -> AInDataTypeKind.STRING;
            case INTEGER -> AInDataTypeKind.INTEGER;
            case NUMBER -> AInDataTypeKind.NUMBER;
            case BOOLEAN -> AInDataTypeKind.BOOLEAN;
            case ANY -> AInDataTypeKind.ANY;
            default -> throw new IllegalArgumentException("Unsupported recursive contract node: " + aType.kind());
        };
        return AIcScalarGeneration.scalar(locKind, aType.constraints(), aJava);
    }
}
