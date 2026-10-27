package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.lib.naming.convention.impl.standard.AIcNameConventionCatalog;
import eu.algites.tool.codegen.sdo.AIcdSdoGenerationResult;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/**
 * Supplies explicit naming catalogs to legacy handwritten-contract test fixtures.
 *
 * <p>Unlike the former generator defaults, this helper belongs only to the
 * TestNG source set. Production generation still rejects absent configuration.
 */
final class AItcConfiguredSdoCodegenService {
    private final AIcSdoCodegenService delegate = new AIcSdoCodegenService();
    private static final AIcNameConventionCatalog NAMING = load();

    /** Load the explicitly requested Algites test catalog, including method rules. */
    private static AIcNameConventionCatalog load() {
        try {
            return AIcNameConventionCatalog.loadAll(List.of(
                    "resource:algites-java-name-conventions.yml",
                    "resource:algites-java-codegen-method-conventions.yml"))
                    .withGeneratedMethodProfile("algites-java-codegen-standard_1");
        } catch (IOException aError) {
            throw new IllegalStateException("Missing Algites test naming resources", aError);
        }
    }

    /**
     * Select one unversioned or versioned naming family for the requested test contract.
     * @param aRead input fixture type
     * @param aMarker legacy marker, validated but not interpreted as a profile selector
     * @return two generated source units
     */
    AIcdSdoGenerationResult generate(Class<?> aRead, String aMarker) {
        boolean locVersioned = aRead.getSimpleName().matches(".*_[1-9][0-9]*$");
        String locSuffix = locVersioned ? "-versioned_1" : "_1";
        String locSourcePrefix = aRead.getSimpleName().startsWith("AIig")
                ? "algites-java-gen-intf" : "algites-java-intf";
        return delegate.generate(aRead, aMarker,
                select(locSourcePrefix + locSuffix),
                select("algites-java-gen-data-intf" + locSuffix),
                select("algites-java-gen-data-class" + locSuffix));
    }

    /**
     * Forward deliberately supplied role catalogs without changing test expectations.
     * @param aRead requested contract
     * @param aMarker implementation marker
     * @param aInput read-contract catalog
     * @param aMutable writable interface catalog
     * @param aConcrete implementation catalog
     * @return generated pair
     */
    AIcdSdoGenerationResult generate(Class<?> aRead, String aMarker,
            AIcNameConventionCatalog aInput, AIcNameConventionCatalog aMutable,
            AIcNameConventionCatalog aConcrete) {
        return delegate.generate(aRead, aMarker, aInput, aMutable, aConcrete);
    }

    /**
     * Compiles versioned test input sources with explicit writable output roles.
     * @param aRoot root of handwritten source fixtures
     * @param aSources requested source files
     * @param aMarker marker for validating invocation
     * @param aClasspath dependency classpath
     * @return generated pairs by original source path
     */
    Map<Path, AIcdSdoGenerationResult> generateFromSources(Path aRoot, List<Path> aSources,
            String aMarker, List<Path> aClasspath) {
        return delegate.generateFromSources(aRoot, aSources, aMarker, aClasspath,
                select("algites-java-gen-intf-versioned_1"),
                select("algites-java-gen-data-intf-versioned_1"),
                select("algites-java-gen-data-class-versioned_1"));
    }

    /**
     * Apply the selected profile consistently for all technology-specific contract roles.
     * @param aProfile explicit name composition for this test fixture
     * @return role-bound catalog
     */
    private static AIcNameConventionCatalog select(String aProfile) {
        return NAMING.withRoles(Map.of(
                "common", aProfile, "jsondefs", aProfile, "yamldefs", aProfile,
                "xmldefs_type", aProfile, "xmldefs_element", aProfile,
                "xmldefs_namespace", aProfile));
    }
}
