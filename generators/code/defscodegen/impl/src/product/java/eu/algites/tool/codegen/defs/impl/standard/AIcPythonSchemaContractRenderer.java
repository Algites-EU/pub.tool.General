package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdGeneratedSource;
import eu.algites.tool.codegen.defs.AIcdGeneratedTypeIdentity;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

/** Render native Python read contracts from normalized property metadata. */
final class AIcPythonSchemaContractRenderer {
    private final AIcGenerationNames names = new AIcGenerationNames();
    private static final Set<String> RESERVED = Set.of(
        "False", "None", "True", "and", "as", "assert", "async", "await", "break", "class", "continue",
        "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import",
        "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while",
        "with", "yield");

    AIcdGeneratedSource generate(AIcdCodeGenerationRequest aRequest) {
        var locDefinition = aRequest.definition();
        String locName = names.typeName(locDefinition, aRequest.namingProfile(), AInDefsNameRole.INTERFACE_TYPE);
        String locStem = names.fileStem(locDefinition, aRequest.namingProfile(), AInDefsNameRole.INTERFACE_TYPE_FILE_STEM);
        String locPath = aRequest.packageName().replace('.', '/') + "/" + locStem + ".py";
        TreeSet<String> locImports = new TreeSet<>();
        List<String> locFields = new ArrayList<>(), locMetadata = new ArrayList<>(), locLabels = new ArrayList<>(), locGetters = new ArrayList<>();
        boolean locTemporal = false;
        List<String> locXmlFields = new ArrayList<>();
        for (AIcdPropertyDefinition locProperty : locDefinition.dataType().properties()) {
            String locField = identifier(names.propertyName(locProperty.sourceName(), aRequest.namingProfile()));
            String locSuffix = Character.toUpperCase(locField.charAt(0)) + locField.substring(1);
            boolean locArray = locProperty.dataType().kind() == AInDataTypeKind.ARRAY;
            var locReference = locProperty.dataType().referencedDefinition();
            String locAnnotation = AIcRecursiveContractType.render(locProperty, aRequest, names, false, locImports);
            String locType = locAnnotation;
            if (locReference != null && !locArray) {
                var locRole = locReference.targetsEnum()
                        ? AInDefsNameRole.ENUM_TYPE : AInDefsNameRole.INTERFACE_TYPE;
                locType = names.referenceTypeName(locReference.logicalName(), locReference.version(), aRequest.namingProfile(), locRole);
            }
            if (locAnnotation.contains("AIcSchemaTemporalValue") || locAnnotation.contains("AIcSchemaDuration"))
                locTemporal = true;
            if (locProperty.nullable()) locAnnotation += " | None";
            locFields.add("    " + locField + ": " + locAnnotation);
            locFields.add("    " + names.schemaFieldNameConstant(locProperty.sourceName(), aRequest.namingProfile())
                    + ": ClassVar[str] = " + quote(locProperty.sourceName()));
            String locTitle = title(locProperty.title(), locProperty.sourceName());
            String locEntries = locProperty.description() == null || locProperty.description().isBlank() ? "()"
                    : "(AIaFieldLabel.Entry(roleCode=AIaFieldLabel.FIELD_DESCRIPTION, label=" + quote(locProperty.description()) + "),)";
            locMetadata.add("        AIcdDataObjectField(field_name=" + quote(locProperty.sourceName())
                    + ", presence=AInFieldPresenceKind." + locProperty.presence().name()
                    + ", allows_null=" + (locProperty.nullable() ? "True" : "False")
                    + ", getter_name=" + quote("get" + locSuffix) + "),");
            if (locProperty.xmlField() != null) {
                var locXml = locProperty.xmlField();
                locXmlFields.add("        " + quote(locProperty.sourceName())
                        + ": AIaXmlDataObjectField(namespace=" + quote(locXml.namespace())
                        + ", namespace_local_name=" + quote(locXml.namespaceLocalName())
                        + ", value_kind=AInXmlValueKind." + locXml.valueKind().name()
                        + ", order=" + locDefinition.dataType().properties().indexOf(locProperty)
                        + ", min_occurs=" + locXml.minOccurs()
                        + ", max_occurs=" + locXml.maxOccurs() + "),");
            }
            locLabels.add("        " + quote(locProperty.sourceName()) + ": AIaFieldLabel(label=" + quote(locTitle)
                    + ", labels=" + locEntries + "),");
            String locReturn = locReference != null && !locArray && !locReference.targetsEnum()
                    ? " -> " + locType + (locProperty.nullable() ? " | None" : "") : "";
            locGetters.add("    @AIaFieldLabel(label=" + quote(locTitle) + ", labels=" + locEntries + ")");
            locGetters.add("    @abstractmethod");
            locGetters.add("    def get" + locSuffix + "(self)" + locReturn + ":");
            locGetters.add("        raise NotImplementedError");
            locGetters.add("");
        }
        String locHelpers = locTemporal
                ? "from dataclasses import dataclass\n\n"
                    + "@dataclass(frozen=True, slots=True)\nclass AIcSchemaTemporalValue:\n"
                    + "    lexical: str\n    data_type: str\n\n"
                    + "@dataclass(frozen=True, slots=True)\nclass AIcSchemaDuration:\n"
                    + "    lexical: str\n\n" : "";
        String locXmlFieldImports = locXmlFields.isEmpty() ? "" :
                "from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField\n"
                + "from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind\n";
        String locXmlFieldMetadata = locXmlFields.isEmpty() ? "" :
                "    __xml_data_object_fields__ = {\n" + String.join("\n", locXmlFields) + "\n    }\n";
        String locXmlImports = "";
        String locXmlMetadata = "";
        if (aRequest.xmlTypeQName() != null) {
            String locQName = aRequest.xmlTypeQName();
            int locDelimiter = locQName.indexOf('}');
            locXmlImports = "from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject\n"
                    + "from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind\n";
            locXmlMetadata = "    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace="
                    + quote(locQName.substring(1, locDelimiter)) + ", namespace_local_name="
                    + quote(locQName.substring(locDelimiter + 1)) + ")\n";
        }
        String locSource = "from __future__ import annotations\n\nfrom abc import ABC, abstractmethod\n"
                + "from typing import Any, ClassVar, Mapping\nfrom decimal import Decimal\n"
                + "from " + baseModule(locDefinition.sourceKind()) + " import " + baseType(locDefinition.sourceKind()) + "\n"
                + "from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n"
                + "from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\n"
                + "from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind\n"
                + "from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel\n"
                + locXmlImports + locXmlFieldImports
                + String.join("\n", locImports) + "\n\n" + locHelpers
                + "class " + locName + "(" + baseType(locDefinition.sourceKind()) + ", ABC):\n"
                + "    __data_object__ = AIcdDataObject(schema_id=" + quote(locDefinition.identity())
                + ", schema_version=" + (locDefinition.version() == null ? -1 : locDefinition.version())
                + ", title=" + quote(title(locDefinition.title(), locDefinition.logicalName()))
                + ", description=" + quote(locDefinition.description() == null ? "" : locDefinition.description()) + ")\n"
                + locXmlMetadata + locXmlFieldMetadata
                + "    __data_object_fields__ = (\n" + String.join("\n", locMetadata)
                + "\n    )\n\n    __field_labels__ = {\n" + String.join("\n", locLabels)
                + "\n    }\n\n" + String.join("\n", locFields)
                + "\n\n    __slots__ = ()\n\n" + String.join("\n", locGetters) + "\n";
        return new AIcdGeneratedSource(locName, locPath, locSource,
                List.of(AIcdGeneratedTypeIdentity.fromRequest(aRequest, locName, locPath, AInDefsNameRole.INTERFACE_TYPE)));
    }

    /** Map a canonical source family to the stable Python DataObject marker. */
    static String baseType(eu.algites.tool.codegen.defs.AInDefinitionSourceKind aKind) {
        return switch (aKind) {
            case XMLDEFS -> "AIiXmlDataObject";
            case JSONDEFS -> "AIiJsonDataObject";
            case YAMLDEFS -> "AIiYamlDataObject";
        };
    }

    /** Return the importable Python module that owns the selected technology marker. */
    static String baseModule(eu.algites.tool.codegen.defs.AInDefinitionSourceKind aKind) {
        return switch (aKind) {
            case XMLDEFS -> "eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object";
            case JSONDEFS -> "eu.algites.lib.data.dataobject.jsondefs.aii_json_data_object";
            case YAMLDEFS -> "eu.algites.lib.data.dataobject.yamldefs.aii_yaml_data_object";
        };
    }

    private static String identifier(String aValue) {
        String locValue = aValue.replaceAll("[^a-zA-Z0-9_]", "_");
        if (locValue.isEmpty() || Character.isDigit(locValue.charAt(0))) locValue = "_" + locValue;
        return RESERVED.contains(locValue) ? locValue + "_" : locValue;
    }

    private static String title(String aTitle, String aName) {
        if (aTitle != null && !aTitle.isBlank()) return aTitle;
        String locWords = aName.replaceAll("([A-Z]+)([A-Z][a-z])", "$1 $2")
                .replaceAll("([a-z0-9])([A-Z])", "$1 $2").replace('_', ' ').replace('-', ' ')
                .trim().replaceAll("\\s+", " ");
        return locWords.isEmpty() ? aName : Character.toUpperCase(locWords.charAt(0)) + locWords.substring(1);
    }

    private static String quote(String aValue) {
        return "'" + aValue.replace("\\", "\\\\").replace("'", "\\'")
                .replace("\n", "\\n").replace("\r", "\\r") + "'";
    }
}
