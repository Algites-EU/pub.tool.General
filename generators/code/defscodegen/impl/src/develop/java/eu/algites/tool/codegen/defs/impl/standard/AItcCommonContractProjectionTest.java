package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.data.dataobject.AInFieldPresenceKind;
import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies common-role projections retain only compatible semantic members,
 * without rewriting the complete format-specific representations.
 */
public final class AItcCommonContractProjectionTest {
    /**
     * Constructs a scalar member without source-specific XML metadata.
     *
     * @param aName schema member name
     * @param aKind structural type of this field
     * @return optional canonical field
     */
    private static AIcdPropertyDefinition field(String aName, AInDataTypeKind aKind) {
        return new AIcdPropertyDefinition(aName, AIcdDataType.atom(aKind, AIcdValueConstraints.empty()),
                AInFieldPresenceKind.ALLOWED, false, "Field " + aName, aName, null);
    }

    /**
     * Wraps source fields into a standalone object representation.
     *
     * @param aKind source serialization family
     * @param aIdentity exact source-specific identity
     * @param aFields members of that representation
     * @return independently addressable schema model
     */
    private static AIcdCanonicalDefinition definition(AInDefinitionSourceKind aKind,
            String aIdentity, List<AIcdPropertyDefinition> aFields) {
        return new AIcdCanonicalDefinition(aIdentity, 1, "capability-definition", aKind,
                "src/product/" + aKind.name().toLowerCase() + "/example/capability-definition_1.schema",
                "Shared capability", AIcdDataType.object(aFields), List.of(), "Capability");
    }

    /** Only common fields are projected; the XML and YAML variants stay independent. */
    @Test
    public void AIcProjectOnlySharedCapabilityFields() {
        var locCapability = field("Capability", AInDataTypeKind.STRING);
        var locSchemaId = field("ConfigurationSchemaId", AInDataTypeKind.STRING);
        var locXml = definition(AInDefinitionSourceKind.XMLDEFS,
                "urn:algites:builder:model:capability-definition:1",
                List.of(locCapability, locSchemaId, field("AllowedScope", AInDataTypeKind.ANY)));
        var locYaml = definition(AInDefinitionSourceKind.YAMLDEFS,
                "urn:algites:builder:yamldef:model:capability-definition:1",
                List.of(locCapability, locSchemaId, field("AllowedScopes", AInDataTypeKind.ANY)));
        var locProjected = AIcCommonContractProjection.merge(List.of(locXml, locYaml));
        Assert.assertEquals(locProjected.dataType().properties().stream()
                .map(AIcdPropertyDefinition::sourceName).toList(),
                List.of("Capability", "ConfigurationSchemaId"));
        Assert.assertEquals(locYaml.dataType().properties().size(), 3);
        Assert.assertEquals(locProjected.identity(), locXml.identity());
    }

    /** Incompatible scalar types with the same member name are an explicit error. */
    @Test
    public void AIcRejectConflictingScalarMembers() {
        var locXml = definition(AInDefinitionSourceKind.XMLDEFS, "urn:algites:capability:1",
                List.of(field("Mode", AInDataTypeKind.STRING)));
        var locYaml = definition(AInDefinitionSourceKind.YAMLDEFS, "urn:algites:capability:1",
                List.of(field("Mode", AInDataTypeKind.INTEGER)));
        Assert.expectThrows(IllegalArgumentException.class,
                () -> AIcCommonContractProjection.merge(List.of(locXml, locYaml)));
    }

    /** Common URN aliasing must follow the actual source format, never an arbitrary token. */
    @Test
    public void AIcNormalizeOnlyAlgitesFormatIdentity() {
        var locYaml = definition(AInDefinitionSourceKind.YAMLDEFS,
                "urn:algites:builder:yamldef:model:capability-definition:1", List.of());
        Assert.assertEquals(AIcCommonContractProjection.canonicalIdentity(locYaml, "example.contracts",
                List.of("explicit", locYaml.identity(), 1)),
                List.of("explicit", "urn:algites:builder:model:capability-definition:1", 1));
        var locForeign = definition(AInDefinitionSourceKind.YAMLDEFS,
                "urn:foreign:yamldef:capability:1", List.of());
        Assert.assertEquals(AIcCommonContractProjection.canonicalIdentity(locForeign, "example.contracts",
                List.of("explicit", locForeign.identity(), 1)),
                List.of("explicit", locForeign.identity(), 1));
    }
    /**
     * A package-qualified XML namespace can denote the same root type as
     * JSONDEFS/YAMLDEFS with no declared logical identifier. Other namespaces
     * and nested definitions remain distinct, as do mismatched versions.
     */
    @Test
    public void AIcMatchOnlyExactQualifiedXmlImplicitRoot() {
        var locImplicit = List.of("implicit", "eu.algites.lib.naming.convention",
                "common-naming-conventions", 1, "");
        var locQualified = List.of("explicit",
                "eu.algites.lib.naming.convention.common-naming-conventions", 1);
        Assert.assertTrue(AIcSchemaContractBindingsGenerator.commonExplicitMatchesImplicit(
                locQualified, locImplicit));
        Assert.assertFalse(AIcSchemaContractBindingsGenerator.commonExplicitMatchesImplicit(
                List.of("explicit", "eu.other.convention.common-naming-conventions", 1), locImplicit));
        Assert.assertFalse(AIcSchemaContractBindingsGenerator.commonExplicitMatchesImplicit(
                List.of("explicit", locQualified.get(1), 2), locImplicit));
        Assert.assertFalse(AIcSchemaContractBindingsGenerator.commonExplicitMatchesImplicit(
                locQualified, List.of("implicit", "eu.algites.lib.naming.convention",
                        "common-naming-conventions", 1, "/properties/Nested")));
        Assert.assertFalse(AIcSchemaContractBindingsGenerator.commonExplicitMatchesImplicit(
                List.of("explicit", "urn:foreign:common-naming-conventions:1", 1), locImplicit));
    }
}
