package eu.algites.tool.codegen.defs;

import java.util.ArrayList;
import java.util.List;

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
        return new AIcdGeneratedSource(locBase.typeName(), locBase.relativePath(), locSource);
    }

    /** Generate an annotated read contract without writing a concrete implementation. */
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest aRequest) {
        AIcdGeneratedSource locContract = new AIcSchemaInterfaceGenerator().generate(aRequest).contract();
        if (aRequest.target() != AInCodeGenerationTarget.PYTHON
                || aRequest.definition().kind() == AInDefinitionKind.ENUM) {
            return locContract;
        }
        String locMarker = "class " + locContract.typeName() + "(ABC):";
        String locSource = locContract.source();
        if (!locSource.contains(locMarker)) {
            throw new IllegalStateException("Cannot locate read-contract declaration: " + locContract.typeName());
        }
        locSource = locSource.replace("from decimal import Decimal\n",
                "from decimal import Decimal\n"
                + "from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n"
                + "from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n"
                + "from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\n");
        List<String> locMetadata = new ArrayList<>();
        locMetadata.add("    __data_object__ = AIcdDataObject(id="
                + AIcScalarGeneration.jquote(aRequest.definition().identity())
                + ", version=" + (aRequest.definition().version() == null ? -1 : aRequest.definition().version())
                + ", description=" + AIcScalarGeneration.jquote(
                    aRequest.definition().description() == null ? "" : aRequest.definition().description()) + ")");
        locMetadata.add("    __data_object_fields__ = (");
        AIcGenerationNames locNames = new AIcGenerationNames();
        List<String> locGetters = new ArrayList<>();
        for (AIcdPropertyDefinition locField : aRequest.definition().properties()) {
            String locProperty = locNames.propertyName(locField.sourceName(), aRequest.namingProfile());
            String locGetter = "get" + Character.toUpperCase(locProperty.charAt(0)) + locProperty.substring(1);
            locMetadata.add("        AIcdDataObjectField(name=" + AIcScalarGeneration.jquote(locField.sourceName())
                    + ", description=" + AIcScalarGeneration.jquote(
                        locField.description() == null ? "" : locField.description())
                    + ", presence_required=" + (locField.required() ? "True" : "False")
                    + ", allows_null=" + (locField.nullable() ? "True" : "False")
                    + ", getter_name=" + AIcScalarGeneration.jquote(locGetter) + "),");
            locGetters.add("    @abstractmethod\n    def " + locGetter + "(self):\n        raise NotImplementedError");
        }
        locMetadata.add("    )");
        locSource = locSource.replace(locMarker, "class " + locContract.typeName()
                + "(ABC, AIiDataObject):\n" + String.join("\n", locMetadata));
        int locLegacyMethod = locSource.indexOf("\n\n    @abstractmethod\n    def to_mapping(");
        if (locLegacyMethod >= 0) {
            locSource = locSource.substring(0, locLegacyMethod).stripTrailing() + "\n";
        }
        if (!locGetters.isEmpty()) {
            locSource += "\n" + String.join("\n\n", locGetters) + "\n";
        }
        return new AIcdGeneratedSource(locContract.typeName(), locContract.relativePath(), locSource);
    }
}
