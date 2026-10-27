package eu.algites.tool.codegen.defs.impl.standard;


import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import java.util.Map;

/** Resolves all rendered names from the selected YAML NameCompositions. */
final class AIcGenerationNames {
    /** Require a semantic naming-role binding supplied by the active generator profile. */
    private static String selected(AIiNameConventionCatalog aCatalog, AInDefsNameRole aRole) {
        if (!(aCatalog instanceof AIcSelectedNamingCatalog locSelected))
            throw new IllegalArgumentException("No output naming profile configured for role " + aRole);
        return locSelected.selected(aRole);
    }

    private static String type(AIiNameConventionCatalog aCatalog, String aIdentifier, Integer aVersion,
            AInDefsNameRole aRole, String aStructure) {
        String locProfile = selected(aCatalog, aRole);
        /* Derived schema-pointer ordinals must not imitate a filename version suffix. */
        String locIdentifier = aIdentifier.replaceAll("(?<=[a-z])-(?=[0-9]+(?:-|$))", "");
        Map<String, String> locVariables = aVersion == null
                ? Map.of("identifier", locIdentifier)
                : Map.of("identifier", locIdentifier, "version", aVersion.toString());
        return aCatalog.format(locProfile, aStructure, locVariables, "lower_kebab_case_1");
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

    /**
     * Formats a source field according to the selected naming structure.
     *
     * <p>JSON/YAML field names may include punctuation, such as {@code $schema}.
     * Only those non-identifier lexical forms are normalized. Errors reported
     * by the configured naming profile are always propagated unchanged.
     *
     * @param aProfile explicitly selected naming catalog
     * @param aName original field key from the data schema
     * @param aStructure named target structure (field/getter/setter/constant)
     * @param aSourceConvention expected source lexical naming convention
     * @param aRole required target semantic role
     * @return name formatted according to the configured naming composition
     */
    private static String property(AIiNameConventionCatalog aProfile, String aName, String aStructure,
            String aSourceConvention, AInDefsNameRole aRole) {
        String locRole = selected(aProfile, aRole);
        String locSourceName = aName;
        String locSourceConvention = aSourceConvention;
        if (!recognizedSourceField(aName)) {
            /* Normalize wire-level punctuation, never a missing or broken naming profile. */
            locSourceName = aName.replaceAll("[^A-Za-z0-9]+", "-").replaceAll("^-|-$", "")
                    .toLowerCase(java.util.Locale.ROOT);
            if (locSourceName.isEmpty() || Character.isDigit(locSourceName.charAt(0)))
                locSourceName = "field-" + locSourceName;
            locSourceConvention = "lower_kebab_case_1";
        }
        return aProfile.format(locRole, aStructure, Map.of("identifier", locSourceName), locSourceConvention);
    }

    /** Return whether the field key matches one of the supported source lexical conventions. */
    private static boolean recognizedSourceField(String aName) {
        return aName.matches("[A-Z][A-Za-z0-9]*")
                || aName.matches("[a-z][A-Za-z0-9]*")
                || aName.matches("[a-z][a-z0-9]*(?:_[a-z0-9]+)+")
                || aName.matches("[a-z][a-z0-9]*(?:-[a-z0-9]+)+");
    }

    /**
     * Identifies a legal schema field's original lexical form, not the requested output syntax.
     *
     * <p>The naming profile owns the conversion to its identifier style. A source field
     * containing punctuation still follows the existing normalization path in property().
     */
    private static String sourceFieldConvention(String aName) {
        if (aName.matches("[A-Z][A-Za-z0-9]*")) return "upper_camel_case_1";
        if (aName.matches("[a-z][A-Za-z0-9]*")) return "lower_camel_case_1";
        if (aName.matches("[a-z][a-z0-9]*(?:_[a-z0-9]+)+")) return "lower_snake_case_1";
        if (aName.matches("[a-z][a-z0-9]*(?:-[a-z0-9]+)+")) return "lower_kebab_case_1";
        return "upper_camel_case_1";
    }

    String propertyName(String aName, AIiNameConventionCatalog aProfile) {
        return property(aProfile, aName, "field_name", sourceFieldConvention(aName), AInDefsNameRole.INTERFACE_TYPE);
    }

    /** Resolve a getter name exclusively through the selected naming profile. */
    String getterName(String aName, AIiNameConventionCatalog aProfile) {
        return getterName(aName, aProfile, AInDefsNameRole.INTERFACE_TYPE);
    }

    /** Resolve getters using the naming profile of their actual generated contract role. */
    String getterName(String aName, AIiNameConventionCatalog aProfile, AInDefsNameRole aRole) {
        return property(aProfile, aName, "getter_method_name", sourceFieldConvention(aName), aRole);
    }

    /** Resolve a setter name exclusively through the selected naming profile. */
    String setterName(String aName, AIiNameConventionCatalog aProfile) {
        return property(aProfile, aName, "setter_method_name", sourceFieldConvention(aName), AInDefsNameRole.INTERFACE_TYPE);
    }

    String enumConstant(String aName, AIiNameConventionCatalog aProfile) {
        return property(aProfile, aName, "enum_item_name", "lower_snake_case_1", AInDefsNameRole.INTERFACE_TYPE);
    }

    /**
     * Renders both semantic parts through the selected constant naming convention.
     *
     * <p>The schema-field designation belongs to Defs Codegen, not the language-wide
     * constant naming structure. An empty component between the rendered parts
     * preserves the existing two-separator schema-field constant contract.
     *
     * @param aName canonical schema field name
     * @param aProfile selected name convention catalog
     * @return the schema field constant identifier
     */
    String schemaFieldNameConstant(String aName, AIiNameConventionCatalog aProfile) {
        String locPrefix = property(aProfile, String.join("_", "schema", "field", "name"), "constant_name",
                "lower_snake_case_1", AInDefsNameRole.INTERFACE_TYPE);
        String locField = property(aProfile, aName, "constant_name",
                sourceFieldConvention(aName), AInDefsNameRole.INTERFACE_TYPE);
        return String.join("_", locPrefix, "", locField);
    }
}
