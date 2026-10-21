package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdGeneratedSource;
import eu.algites.tool.codegen.defs.AIcdGeneratedTypeIdentity;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Generate a finite closed choice plus public branch record sources in its own package. */
public final class AIcClosedChoiceGenerator {
    private final AIcGenerationNames names = new AIcGenerationNames();
    private record AIcdVariant(String label, String type, String file, String identity) { }
    private record AIcdNamedVariant(String recordName, String fileName, String type, String typeFile) { }

    /** Render the closed choice and each value record; callers must write all outputs. */
    public List<AIcdGeneratedSource> generate(AIcdCodeGenerationRequest aRequest) {
        AIcdDataType locChoice = aRequest.definition().dataType();
        if (locChoice.kind() != AInDataTypeKind.ONE_OF && locChoice.kind() != AInDataTypeKind.ANY_OF)
            throw new IllegalArgumentException("Not a closed choice");
        boolean locJava = aRequest.target() == AInCodeGenerationTarget.JAVA;
        String locMode = locChoice.kind() == AInDataTypeKind.ONE_OF ? "oneOf" : "anyOf";
        String locName = names.typeName(aRequest.definition(), aRequest.namingProfile(), AInDefsNameRole.INTERFACE_TYPE);
        String locStem = names.fileStem(aRequest.definition(), aRequest.namingProfile(), AInDefsNameRole.INTERFACE_TYPE_FILE_STEM);
        String locPackage = aRequest.packageName(), locPrefix = locPackage.replace('.', '/') + "/";
        String locExtension = locJava ? ".java" : ".py";
        List<AIcdVariant> locVariants = new ArrayList<>();
        int locIndex = 0;
        for (AIcdDataType locAlternative : locChoice.alternatives()) {
            String locLabel, locType, locFile, locIdentity;
            if (locAlternative.kind() == AInDataTypeKind.REFERENCE) {
                var locRef = locAlternative.reference();
                var locRole = locRef.targetsEnum()
                        ? AInDefsNameRole.ENUM_TYPE : AInDefsNameRole.INTERFACE_TYPE;
                var locFileRole = locRole == AInDefsNameRole.ENUM_TYPE
                        ? AInDefsNameRole.ENUM_TYPE_FILE_STEM : AInDefsNameRole.INTERFACE_TYPE_FILE_STEM;
                locLabel = locRef.logicalName();
                locType = names.referenceTypeName(locRef.logicalName(), locRef.version(), aRequest.namingProfile(), locRole);
                locFile = names.referenceTypeName(locRef.logicalName(), locRef.version(), aRequest.namingProfile(), locFileRole);
                locIdentity = locRef.identity();
            } else if (java.util.Set.of(AInDataTypeKind.STRING, AInDataTypeKind.INTEGER,
                    AInDataTypeKind.NUMBER, AInDataTypeKind.BOOLEAN, AInDataTypeKind.ANY).contains(locAlternative.kind())) {
                locLabel = "Alternative" + (locIndex + 1);
                locType = switch (locAlternative.kind()) {
                    case STRING -> locJava ? "String" : "str";
                    case INTEGER -> locJava ? "Long" : "int";
                    case NUMBER -> locJava ? "java.math.BigDecimal" : "Decimal";
                    case BOOLEAN -> locJava ? "Boolean" : "bool";
                    default -> locJava ? "Object" : "object";
                };
                locFile = null;
                locIdentity = aRequest.definition().identity() + "#/" + locMode + "/" + locIndex;
            } else if (locAlternative.kind() == AInDataTypeKind.ARRAY) {
                AIcdDataType locItem = locAlternative.elementType();
                String locItemType = switch (locItem.kind()) {
                    case STRING -> locJava ? "String" : "str";
                    case INTEGER -> locJava ? "Long" : "int";
                    case NUMBER -> locJava ? "java.math.BigDecimal" : "Decimal";
                    case BOOLEAN -> locJava ? "Boolean" : "bool";
                    default -> throw new IllegalArgumentException(
                            "Closed choice array requires a supported scalar element type: " + locItem.kind());
                };
                locLabel = "Alternative" + (locIndex + 1);
                locType = (locJava ? "java.util.List<" : "list[") + locItemType + (locJava ? ">" : "]");
                locFile = null;
                locIdentity = aRequest.definition().identity() + "#/" + locMode + "/" + locIndex;
            } else if (locAlternative.kind() == AInDataTypeKind.OBJECT) {
                locLabel = "alternative" + (locIndex + 1);
                String locBranchName = aRequest.definition().logicalName()
                        + (locMode.equals("oneOf") ? "-one-of-" : "-any-of-") + locIndex;
                locType = names.referenceTypeName(locBranchName, aRequest.definition().version(),
                        aRequest.namingProfile(), AInDefsNameRole.INTERFACE_TYPE);
                locFile = names.referenceTypeName(locBranchName, aRequest.definition().version(),
                        aRequest.namingProfile(), AInDefsNameRole.INTERFACE_TYPE_FILE_STEM);
                locIdentity = aRequest.definition().identity() + "#/" + locMode + "/" + locIndex;
            } else throw new IllegalArgumentException("Unsupported closed choice alternative " + locAlternative.kind());
            locVariants.add(new AIcdVariant(locLabel, locType, locFile, locIdentity));
            locIndex++;
        }
        if (locVariants.stream().map(AIcdVariant::identity).distinct().count() != locVariants.size())
            throw new IllegalArgumentException("Repeated closed-choice alternative");
        Map<String, Integer> locCounts = new HashMap<>();
        locVariants.forEach(aVariant -> locCounts.merge(aVariant.label().toLowerCase(java.util.Locale.ROOT), 1, Integer::sum));
        List<AIcdNamedVariant> locNamed = new ArrayList<>();
        for (AIcdVariant locVariant : locVariants) {
            String locLabel = locVariant.label();
            if (locCounts.get(locLabel.toLowerCase(java.util.Locale.ROOT)) > 1)
                locLabel += "-h" + digest(locVariant.identity()).substring(0, 8);
            String locLogical = aRequest.definition().logicalName() + "-" + locLabel;
            String locRecord = names.referenceTypeName(locLogical, aRequest.definition().version(),
                    aRequest.namingProfile(), AInDefsNameRole.DATA_TYPE);
            String locFile = names.referenceTypeName(locLogical, aRequest.definition().version(),
                    aRequest.namingProfile(), AInDefsNameRole.DATA_TYPE_FILE_STEM);
            locNamed.add(new AIcdNamedVariant(locRecord, locFile, locVariant.type(), locVariant.file()));
        }
        String locXmlMetadata = "";
        if (aRequest.xmlTypeQName() != null) {
            int locEnd = aRequest.xmlTypeQName().indexOf('}');
            locXmlMetadata = "@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject("
                    + "definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, "
                    + "namespace = " + AIcScalarGeneration.jquote(aRequest.xmlTypeQName().substring(1, locEnd))
                    + ", namespaceLocalName = " + AIcScalarGeneration.jquote(aRequest.xmlTypeQName().substring(locEnd + 1))
                    + ")\n";
        }
        String locMain = locJava
                ? "package " + locPackage + ";\n\n/** Generated closed " + locMode + " schema contract. */\n"
                    + locXmlMetadata
                    + "public sealed interface " + locName +
                        (aRequest.definition().sourceKind() == AInDefinitionSourceKind.XMLDEFS
                            ? " extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject" : "")
                        + " permits "
                    + String.join(", ", locNamed.stream().map(AIcdNamedVariant::recordName).toList()) + " {\n}\n"
                : "from __future__ import annotations\n"
                    + (aRequest.definition().sourceKind() == AInDefinitionSourceKind.XMLDEFS
                        ? "from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject\n" : "")
                    + (aRequest.xmlTypeQName() != null
                        ? "from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject\n"
                          + "from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind\n" : "")
                    + "\nclass " + locName
                    + (aRequest.definition().sourceKind() == AInDefinitionSourceKind.XMLDEFS ? "(AIiXmlDataObject)" : "")
                    + ":\n"
                    + (aRequest.xmlTypeQName() == null ? "" :
                        "    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='"
                        + aRequest.xmlTypeQName().substring(1, aRequest.xmlTypeQName().indexOf('}'))
                        + "', namespace_local_name='"
                        + aRequest.xmlTypeQName().substring(aRequest.xmlTypeQName().indexOf('}') + 1)
                        + "')\n")
                    + "    \"\"\"Generated closed " + locMode + " choice.\"\"\"\n"
                    + "    __closed_choice_mode__ = '" + locMode + "'\n    __slots__ = ()\n";
        List<AIcdGeneratedSource> locResults = new ArrayList<>();
        locResults.add(source(aRequest, locName, locPrefix + locStem + locExtension, locMain, AInDefsNameRole.INTERFACE_TYPE));
        /* JSON/YAML inline branch contracts are created by schema discovery. XSD choices
         * are canonicalized from particles, so produce their branch interfaces here. */
        if (aRequest.definition().sourceKind() == AInDefinitionSourceKind.XMLDEFS) {
            for (int locBranch = 0; locBranch < locChoice.alternatives().size(); locBranch++) {
                AIcdDataType locAlternative = locChoice.alternatives().get(locBranch);
                if (locAlternative.kind() != AInDataTypeKind.OBJECT)
                    throw new IllegalArgumentException("XML choice requires object branch with XML QName");
                String locLogical = aRequest.definition().logicalName()
                        + (locMode.equals("oneOf") ? "-one-of-" : "-any-of-") + locBranch;
                AIcdCanonicalDefinition locDefinition = new AIcdCanonicalDefinition(aRequest.definition().identity() + "#/" + locMode + "/" + locBranch, aRequest.definition().version(), locLogical, aRequest.definition().sourceKind(), aRequest.definition().sourceResource(), aRequest.definition().description(), locAlternative, List.of(), null);
                AIcdCodeGenerationRequest locRequest = new AIcdCodeGenerationRequest(locDefinition,
                        aRequest.target(), aRequest.packageName(), aRequest.namingProfile());
                locResults.add(new AIcSchemaContractInterfaceGenerator().generate(locRequest));
            }
        }
        for (AIcdNamedVariant locVariant : locNamed) {
            String locSource = locJava
                    ? "package " + locPackage + ";\n\n/** Explicit typed alternative. */\n"
                        + "public record " + locVariant.recordName() + "(" + locVariant.type() + " value) implements "
                        + locName + " {\n    /** Validate the selected value. */\n    public "
                        + locVariant.recordName() + " { java.util.Objects.requireNonNull(value, \"value\"); }\n}\n"
                    : "from __future__ import annotations\nfrom dataclasses import dataclass\n"
                        + "from ." + locStem + " import " + locName + "\n"
                        + (locVariant.typeFile() != null
                            ? "from ." + locVariant.typeFile() + " import " + locVariant.type() + "\n"
                            : "Decimal".equals(locVariant.type()) ? "from decimal import Decimal\n" : "")
                        + "\n"
                        + "@dataclass(frozen=True, slots=True)\nclass " + locVariant.recordName() + "(" + locName + "):\n"
                        + "    \"\"\"One explicitly selected alternative.\"\"\"\n"
                        + "    value: " + locVariant.type() + "\n"
                        + "    def __post_init__(self):\n"
                        + "        if not isinstance(self.value, "
                        + (locVariant.type().startsWith("list[") ? "list" : locVariant.type()) + "):\n"
                        + "            raise TypeError(\"Invalid closed-choice alternative\")\n";
            locResults.add(source(aRequest, locVariant.recordName(),
                    locPrefix + locVariant.fileName() + locExtension, locSource, AInDefsNameRole.DATA_TYPE));
        }
        return List.copyOf(locResults);
    }

    /** Wrap a generated compilation unit with its canonical origin. */
    private static AIcdGeneratedSource source(AIcdCodeGenerationRequest aRequest, String aName,
            String aPath, String aSource, AInDefsNameRole aRole) {
        return new AIcdGeneratedSource(aName, aPath, aSource,
                List.of(AIcdGeneratedTypeIdentity.fromRequest(aRequest, aName, aPath, aRole)));
    }
    /** Stable local disambiguator derived from the canonical reference identity. */
    private static String digest(String aIdentity) {
        try {
            byte[] locBytes = MessageDigest.getInstance("SHA-256").digest(aIdentity.getBytes(StandardCharsets.UTF_8));
            return java.util.HexFormat.of().formatHex(locBytes);
        } catch (NoSuchAlgorithmException aError) { throw new AssertionError(aError); }
    }
}
