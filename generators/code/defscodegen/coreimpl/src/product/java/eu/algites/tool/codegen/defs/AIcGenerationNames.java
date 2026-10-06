package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.conversion.AIcDefaultNameConverter;
import eu.algites.lib.naming.convention.AIcdNamingProfile;
import eu.algites.lib.naming.convention.AIcdOutputNameRule;
import eu.algites.lib.naming.convention.AInInputNameKind;
import eu.algites.lib.naming.convention.AInOutputNameKind;


/** Shared output-name projection. */
final class AIcGenerationNames {
    private final AIcDefaultNameConverter converter = new AIcDefaultNameConverter();

    String typeName(AIcdCanonicalDefinition definition, AIcdNamingProfile profile, AInOutputNameKind kind) {
        AIcdOutputNameRule rule = profile.outputRules().get(kind);
        String converted = converter.convert(definition.logicalName(), profile.inputConventions().get(AInInputNameKind.DEFINITION), rule.convention());
        return rule.prefix() + rule.typeMarker() + converted + rule.suffix() + converter.renderVersion(definition.version(), profile.outputVersionPolicy());
    }

    String fileStem(AIcdCanonicalDefinition definition, AIcdNamingProfile profile, AInOutputNameKind kind) {
        AIcdOutputNameRule rule = profile.outputRules().get(kind);
        String converted = converter.convert(definition.logicalName(), profile.inputConventions().get(AInInputNameKind.DEFINITION), rule.convention());
        return rule.prefix() + rule.typeMarker() + converted + rule.suffix() + converter.renderVersion(definition.version(), profile.outputVersionPolicy());
    }

    String propertyName(String sourceName, AIcdNamingProfile profile) {
        AIcdOutputNameRule rule = profile.outputRules().get(AInOutputNameKind.PROPERTY);
        return rule.prefix() + rule.typeMarker() + converter.convert(sourceName, profile.inputConventions().get(AInInputNameKind.PROPERTY), rule.convention()) + rule.suffix();
    }

    String enumConstant(String sourceName, AIcdNamingProfile profile) {
        AIcdOutputNameRule rule = profile.outputRules().get(AInOutputNameKind.ENUM_CONSTANT);
        return rule.prefix() + rule.typeMarker() + converter.convert(sourceName, profile.inputConventions().get(AInInputNameKind.ENUM_VALUE), rule.convention()) + rule.suffix();
    }

    /**
     * Renders the stable generated constant name that exposes one canonical schema field name.
     *
     * @param sourceName canonical schema field name
     * @param profile naming profile used by the generated type
     * @return schema-field-name constant identifier
     */
    String schemaFieldNameConstant(String sourceName, AIcdNamingProfile profile) {
        AIcdOutputNameRule rule = profile.outputRules().get(AInOutputNameKind.ENUM_CONSTANT);
        String converted = converter.convert(sourceName,
                profile.inputConventions().get(AInInputNameKind.PROPERTY), rule.convention());
        String identifier = converted.replaceAll("[^A-Za-z0-9_]", "_")
                .replaceAll("_+", "_").replaceAll("^_+|_+$", "");
        if (identifier.isEmpty()) identifier = "FIELD";
        return "SCHEMA_FIELD_NAME__" + identifier;
    }

    String referenceTypeName(String logicalName, Integer version, AIcdNamingProfile profile, AInOutputNameKind kind) {
        AIcdOutputNameRule rule = profile.outputRules().get(kind);
        String converted = converter.convert(logicalName, profile.inputConventions().get(AInInputNameKind.DEFINITION), rule.convention());
        return rule.prefix() + rule.typeMarker() + converted + rule.suffix() + converter.renderVersion(version, profile.outputVersionPolicy());
    }
}
