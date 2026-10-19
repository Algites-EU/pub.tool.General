package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdGeneratedSource;
import eu.algites.tool.codegen.defs.AIcdGeneratedTypeIdentity;
import eu.algites.tool.codegen.defs.AIcdXmlElementDeclaration;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;

/** Generate type-safe nominal wrappers for global XML elements in the business package. */
public final class AIcXmlElementContractGenerator {
    private static final String XS = "http://www.w3.org/2001/XMLSchema";
    private final AIcGenerationNames names = new AIcGenerationNames();

    /**
     * Generate one element interface with explicit content and substitutable element parents.
     * The qualified indexes are assembled across all XML definitions before generation.
     */
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest aRequest,
            AIcdXmlElementDeclaration aElement, Map<String, String> aContentTypes,
            Map<String, String> aElementTypes) {
        return generate(aRequest, aElement, aContentTypes, aElementTypes, java.util.Set.of());
    }

    /** Render element content including a named scalar or enum contract. */
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest aRequest,
            AIcdXmlElementDeclaration aElement, Map<String, String> aContentTypes,
            Map<String, String> aElementTypes, java.util.Set<String> aValueTypes) {
        Integer locVersion = aRequest.definition().version();
        String locName = names.referenceTypeName(xmlIdentifier(aElement.localName()), locVersion, aRequest.namingProfile(),
                AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE);
        String locStem = names.referenceTypeName(xmlIdentifier(aElement.localName()), locVersion, aRequest.namingProfile(),
                AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM);
        String locHead = aElement.substitutionHeadQName() == null ? null
                : aElementTypes.get(aElement.substitutionHeadQName());
        if (aElement.substitutionHeadQName() != null && locHead == null)
            throw new IllegalArgumentException("Unresolved XML substitution head " + aElement.substitutionHeadQName());
        String locBase = aContentTypes.get(aElement.typeQName());
        boolean locScalarContent = aValueTypes.contains(aElement.typeQName());
        String[] locBuiltin = null;
        if (aElement.typeQName().startsWith("{" + XS + "}"))
            locBuiltin = scalar(aElement.typeQName().substring(XS.length() + 2));
        else if (locBase == null)
            throw new IllegalArgumentException("No generated XML content contract for " + aElement.typeQName());
        else if (locScalarContent)
            locBuiltin = new String[] {locBase, locBase.substring(locBase.lastIndexOf('.') + 1)};
        if (aElement.typeQName().startsWith("{" + XS + "}") && locBuiltin == null)
            throw new IllegalArgumentException("Unsupported XML scalar: " + aElement.typeQName());
        LinkedHashSet<String> locParents = new LinkedHashSet<>();
        /* Python resolves multiple inheritance left-to-right. A substitution head can
         * already extend its content type, so the more specific head must come first. */
        if (locHead != null) locParents.add(locHead);
        if (locBase != null && !locScalarContent) locParents.add(locBase);
        if (locParents.isEmpty()) locParents.add("eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject");
        String locPackage = aRequest.packageName();
        String locAnnotation = "@eu.algites.lib.data.dataobject.AIaDataObject(schemaId = "
                + quote(aElement.namespace() + "#" + aElement.localName()) + ", schemaVersion = "
                + (locVersion == null ? -1 : locVersion) + ")";
        String locXmlAnnotation = "@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject("
                + "definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT, namespace = "
                + quote(aElement.namespace()) + ", namespaceLocalName = " + quote(aElement.localName()) + ")";
        String locGetter = "";
        if (locBuiltin != null) {
            String locSuffix = java.util.Arrays.stream(xmlIdentifier(aElement.localName()).split("-"))
                    .map(aToken -> Character.toUpperCase(aToken.charAt(0)) + aToken.substring(1))
                    .collect(java.util.stream.Collectors.joining());
            locGetter = "    /** Content value of this XML element. */\n"
                + "    @eu.algites.lib.data.dataobject.AIaDataObjectField(fieldName = "
                + quote(aElement.localName()) + ", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = "
                + aElement.nillable() + ")\n"
                + "    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField(namespace = "
                + quote(aElement.namespace()) + ", namespaceLocalName = " + quote(aElement.localName()) + ", order = 0)\n"
                + "    " + locBuiltin[0] + " get" + locSuffix + "();\n";
        }
        String locSource;
        String locFile;
        if (aRequest.target() == AInCodeGenerationTarget.JAVA) {
            locSource = "package " + locPackage + ";\n\n"
                + "/** Generated nominal contract of global XML element " + aElement.localName() + ". */\n"
                + locAnnotation + "\n" + locXmlAnnotation + "\npublic interface " + locName + " extends "
                + String.join(", ", locParents) + " {\n" + locGetter + "}\n";
            locFile = locStem + ".java";
        } else {
            List<String> locImports = new ArrayList<>();
            locImports.add("from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject");
            List<String> locBaseNames = new ArrayList<>();
            for (String locParent : locParents) {
                int locDot = locParent.lastIndexOf('.');
                if (locDot < 1) throw new IllegalArgumentException("Expected module-qualified Python type " + locParent);
                locImports.add("from " + locParent.substring(0, locDot) + " import " + locParent.substring(locDot + 1));
                locBaseNames.add(locParent.substring(locDot + 1));
            }
            if (locScalarContent) {
                int locDot = locBase.lastIndexOf('.');
                locImports.add("from " + locBase.substring(0, locDot) + " import " + locBase.substring(locDot + 1));
            }
            locImports.add("from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject");
            locImports.add("from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind");
            String locBody = "    __data_object__ = AIcdDataObject(schema_id="
                    + quote(aElement.namespace() + "#" + aElement.localName()) + ", schema_version="
                    + (locVersion == null ? -1 : locVersion) + ")\n"
                    + "    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.ELEMENT, namespace="
                    + quote(aElement.namespace()) + ", namespace_local_name=" + quote(aElement.localName()) + ")\n"
                    + "    __slots__ = ()\n";
            if (locBuiltin != null) {
                locImports.add("from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField");
                locImports.add("from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind");
                if (locBuiltin[1].equals("Decimal")) locImports.add("from decimal import Decimal");
                String locSuffix = java.util.Arrays.stream(xmlIdentifier(aElement.localName()).split("-"))
                    .map(aToken -> Character.toUpperCase(aToken.charAt(0)) + aToken.substring(1))
                    .collect(java.util.stream.Collectors.joining());
                locImports.add("from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField");
                locBody += "    __xml_data_object_fields__ = {" + quote(aElement.localName())
                    + ": AIaXmlDataObjectField(namespace=" + quote(aElement.namespace())
                    + ", namespace_local_name=" + quote(aElement.localName()) + ", order=0)}\n"
                    + "    __data_object_fields__ = (AIcdDataObjectField(field_name="
                    + quote(aElement.localName()) + ", presence=AInFieldPresenceKind.REQUIRED, allows_null="
                    + (aElement.nillable() ? "True" : "False") + ", getter_name="
                    + quote("get" + locSuffix) + "),)\n"
                    + "    def get" + locSuffix + "(self) -> " + locBuiltin[1]
                    + ":\n        raise NotImplementedError\n";
            }
            locSource = "from __future__ import annotations\n" + String.join("\n", locImports.stream().distinct().sorted().toList())
                    + "\n\nclass " + locName + "("
                    + String.join(", ", locBaseNames) + "):\n" + locBody;
            locFile = locStem + ".py";
        }
        String locPath = locPackage.replace('.', '/') + "/" + locFile;
        return new AIcdGeneratedSource(locName, locPath, locSource,
                List.of(AIcdGeneratedTypeIdentity.fromRequest(aRequest, locName, locPath,
                        AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE)));
    }

    /** Normalize XML local names through the canonical lower-kebab naming grammar. */
    public static String xmlIdentifier(String aName) {
        return aName.replaceAll("([A-Z]+)([A-Z][a-z])", "$1-$2")
                .replaceAll("([a-z0-9])([A-Z])", "$1-$2")
                .replaceAll("[^A-Za-z0-9]+", "-")
                .replaceAll("^-|-$", "").toLowerCase(java.util.Locale.ROOT);
    }

    /** Supported native XML scalar projections; unsupported families are rejected explicitly. */
    private static String[] scalar(String aXmlType) {
        return switch (aXmlType) {
            case "string", "token", "normalizedString", "date", "dateTime", "anyURI" -> new String[] {"String", "str"};
            case "integer", "int", "long" -> new String[] {"Long", "int"};
            case "decimal" -> new String[] {"java.math.BigDecimal", "Decimal"};
            case "double", "float" -> new String[] {"Double", "float"};
            case "boolean" -> new String[] {"Boolean", "bool"};
            default -> null;
        };
    }
    /** Escape quoted annotation literals for both target syntaxes. */
    private static String quote(String aValue) {
        return "\"" + aValue.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n") + "\"";
    }
}
