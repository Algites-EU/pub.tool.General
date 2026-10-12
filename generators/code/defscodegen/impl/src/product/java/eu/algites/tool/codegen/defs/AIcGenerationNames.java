package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import java.util.Map;

/** Resolves all rendered names from the selected YAML NameCompositions. */
final class AIcGenerationNames {
    private static String technology(AIiNameConventionCatalog aCatalog) {
        if (aCatalog.names().stream().anyMatch(aName -> aName.startsWith("algites-java-"))) return "java";
        if (aCatalog.names().stream().anyMatch(aName -> aName.startsWith("algites-python-"))) return "python";
        throw new IllegalArgumentException("No recognized standard technology naming roles in catalog");
    }

    private static String role(AInDefsNameRole aRole) {
        return switch (aRole) {
            case ENUM_TYPE, ENUM_TYPE_FILE_STEM -> "enum";
            case INTERFACE_TYPE, INTERFACE_TYPE_FILE_STEM -> "intf";
            case DATA_TYPE, DATA_TYPE_FILE_STEM -> "data-class";
            default -> throw new IllegalArgumentException("Not a generated type role: " + aRole);
        };
    }

    private static String type(AIiNameConventionCatalog aCatalog, String aIdentifier, Integer aVersion,
            AInDefsNameRole aRole, String aStructure) {
        String locPrefix = "algites-" + technology(aCatalog) + "-gen-" + role(aRole);
        String locProfile = locPrefix + (aVersion == null ? "" : "-versioned");
        /* Derived schema-pointer ordinals must not imitate a filename version suffix. */
        String locIdentifier = aIdentifier.replaceAll("(?<=[a-z])-(?=[0-9]+(?:-|$))", "");
        Map<String, String> locVariables = aVersion == null
                ? Map.of("identifier", locIdentifier)
                : Map.of("identifier", locIdentifier, "version", aVersion.toString());
        return aCatalog.format(locProfile, aStructure, locVariables, "lower_kebab_case");
    }

    String typeName(AIcdCanonicalDefinition aDefinition, AIiNameConventionCatalog aProfile, AInDefsNameRole aKind) {
        return type(aProfile, aDefinition.logicalName(), aDefinition.version(), aKind, "main_container_name");
    }

    String fileStem(AIcdCanonicalDefinition aDefinition, AIiNameConventionCatalog aProfile, AInDefsNameRole aKind) {
        return type(aProfile, aDefinition.logicalName(), aDefinition.version(), aKind, "file_name_stem");
    }

    String referenceTypeName(String aName, Integer aVersion, AIiNameConventionCatalog aProfile, AInDefsNameRole aKind) {
        return type(aProfile, aName, aVersion, aKind,
                aKind.name().endsWith("FILE_STEM") ? "file_name_stem" : "main_container_name");
    }

    private static String property(AIiNameConventionCatalog aProfile, String aName, String aStructure,
            String aSourceConvention) {
        String locRole = "algites-" + technology(aProfile) + "-gen-intf-versioned";
        try {
            return aProfile.format(locRole, aStructure, Map.of("identifier", aName), aSourceConvention);
        } catch (IllegalArgumentException aError) {
            /* JSON-Schema allows properties such as $schema that are not source identifiers. */
            String locNormalized = aName.replaceAll("[^A-Za-z0-9]+", "-").replaceAll("^-|-$", "")
                    .toLowerCase(java.util.Locale.ROOT);
            if (locNormalized.isEmpty() || Character.isDigit(locNormalized.charAt(0)))
                locNormalized = "field-" + locNormalized;
            return aProfile.format(locRole, aStructure, Map.of("identifier", locNormalized), "lower_kebab_case");
        }
    }

    String propertyName(String aName, AIiNameConventionCatalog aProfile) {
        return property(aProfile, aName, "field_name", "upper_camel_case");
    }

    String enumConstant(String aName, AIiNameConventionCatalog aProfile) {
        return property(aProfile, aName, "enum_item_name", "lower_snake_case");
    }

    String schemaFieldNameConstant(String aName, AIiNameConventionCatalog aProfile) {
        String locIdentifier = property(aProfile, aName, "constant_name", "upper_camel_case")
                .replaceAll("[^A-Za-z0-9_]", "_").replaceAll("_+", "_").replaceAll("^_+|_+$", "");
        return "SCHEMA_FIELD_NAME__" + (locIdentifier.isEmpty() ? "FIELD" : locIdentifier);
    }
}
