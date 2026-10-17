package eu.algites.tool.codegen.defs.impl.standard;



import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdGeneratedSource;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefinitionKind;
/** First-stage API: only read-only contracts and shared enums are emitted. */
public final class AIcSchemaContractInterfaceGenerator {
    /** Generate the own part of an object contract, inheriting all parent getters and metadata. */
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest aRequest, String aParentType,
            String aParentModule) {
        AIcdGeneratedSource locBase = generate(aRequest);
        if (aParentType == null) return locBase;
        if (aRequest.definition().kind() != AInDefinitionKind.OBJECT) {
            throw new IllegalArgumentException("Only object contracts can inherit");
        }
        String locSource = locBase.source();
        if (aRequest.target() == AInCodeGenerationTarget.PYTHON) {
            String locDeclaration = "class " + locBase.typeName() + "(ABC, AIiDataObject):";
            if (!locSource.contains(locDeclaration)) throw new IllegalStateException("Cannot locate Python contract");
            locSource = locSource.replace(locDeclaration, "class " + locBase.typeName() + "(" + aParentType + "):");
            locSource = locSource.replace("from __future__ import annotations\n",
                    "from __future__ import annotations\nfrom " + aParentModule + " import " + aParentType + "\n");
        } else {
            String locDeclaration = "public interface " + locBase.typeName()
                    + " extends eu.algites.lib.data.dataobject.AIiDataObject {";
            if (!locSource.contains(locDeclaration)) throw new IllegalStateException("Cannot locate Java contract");
            locSource = locSource.replace(locDeclaration,
                    "public interface " + locBase.typeName() + " extends " + aParentModule + "." + aParentType + " {");
        }
        return new AIcdGeneratedSource(locBase.typeName(), locBase.relativePath(), locSource, locBase.generatedTypes());
    }

    /** Generate an annotated read contract without writing a concrete implementation. */
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest aRequest) {
        AIcdGeneratedSource locContract = new AIcSchemaInterfaceGenerator().generate(aRequest).contract();
        if (aRequest.target() != AInCodeGenerationTarget.PYTHON
                || aRequest.definition().kind() == AInDefinitionKind.ENUM) {
            return locContract;
        }
        String locSource = locContract.source();
        String locMarker = "class " + locContract.typeName() + "(ABC, AIiDataObject):";
        if (!locSource.contains(locMarker)) {
            throw new IllegalStateException("Cannot locate read-contract declaration: " + locContract.typeName());
        }
        /* SmartDataObject supplies serialization; remove only the base contract's mapping method. */
        String locMappingMethod = "\n\n    @abstractmethod\n    def to_mapping(";
        int locMappingIndex = locSource.indexOf(locMappingMethod);
        if (locMappingIndex >= 0) {
            locSource = locSource.substring(0, locMappingIndex).stripTrailing() + "\n";
        }
        /* The metadata and getter declarations already belong to the shared base contract.
         * Mark inherited getter signatures as abstract rather than duplicating them. */
        locSource = locSource.replaceAll(
                "(?m)^(    def get[A-Za-z0-9_]+\\(self\\)(?: -> [^:]+)?:)$",
                "    @abstractmethod\n$1");
        return new AIcdGeneratedSource(locContract.typeName(), locContract.relativePath(), locSource, locContract.generatedTypes());
    }
}
