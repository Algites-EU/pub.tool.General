package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.lib.naming.convention.impl.standard.AIcNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * Test-only explicit selection of the Algites source and output naming conventions.
 *
 * <p>Neither the production Defs frontends nor the naming library may silently
 * choose Algites profiles. These fixtures intentionally include the source-family
 * catalogs, an output-family catalog and explicit semantic role bindings, so
 * legacy integration tests exercise the strict production contract.
 */
final class AItcConfiguredNamingProfiles {
    private AItcConfiguredNamingProfiles() { }

    /**
     * Load the declared catalogs and select every output role needed by integration fixtures.
     *
     * @param aTarget output technology
     * @return resolved catalog with explicit generator-role mappings
     */
    static AIiNameConventionCatalog profile(AInCodeGenerationTarget aTarget) {
        String locLanguage = aTarget == AInCodeGenerationTarget.PYTHON ? "python" : "java";
        try {
            AIcNameConventionCatalog locCatalog = AIcNameConventionCatalog.loadAll(List.of(
                    "resource:algites-" + locLanguage + "-name-conventions.yml",
                    "resource:algites-jsondef-name-conventions.yml",
                    "resource:algites-yamldef-name-conventions.yml",
                    "resource:algites-xmldef-name-conventions.yml"));
            Map<AInDefsNameRole, String> locRoles = new EnumMap<>(AInDefsNameRole.class);
            for (AInDefsNameRole locRole : List.of(AInDefsNameRole.DATA_TYPE,
                    AInDefsNameRole.DATA_TYPE_FILE_STEM))
                locRoles.put(locRole, "algites-" + locLanguage + "-gen-data-class-versioned_1");
            for (AInDefsNameRole locRole : List.of(AInDefsNameRole.ENUM_TYPE,
                    AInDefsNameRole.ENUM_TYPE_FILE_STEM))
                locRoles.put(locRole, "algites-" + locLanguage + "-gen-enum-versioned_1");
            for (AInDefsNameRole locRole : List.of(AInDefsNameRole.INTERFACE_TYPE,
                    AInDefsNameRole.INTERFACE_TYPE_FILE_STEM))
                locRoles.put(locRole, "algites-" + locLanguage + "-gen-intf-versioned_1");
            for (AInDefsNameRole locRole : List.of(AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE,
                    AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM))
                locRoles.put(locRole, "algites-" + locLanguage + "-gen-xml-element-intf-versioned_1");
            for (AInDefsNameRole locRole : List.of(AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE,
                    AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM))
                locRoles.put(locRole, "algites-" + locLanguage + "-gen-xml-namespace-intf_1");
            return new AIcSelectedNamingCatalog(locCatalog, locRoles);
        } catch (IOException locError) {
            throw new UncheckedIOException("Cannot load explicitly configured test naming profiles", locError);
        }
    }

    /** @return explicitly selected Java fixture profile */
    static AIiNameConventionCatalog javaProfile() {
        return profile(AInCodeGenerationTarget.JAVA);
    }

    /** @return explicitly selected Python fixture profile */
    static AIiNameConventionCatalog pythonProfile() {
        return profile(AInCodeGenerationTarget.PYTHON);
    }

    /**
     * Create a definition request with a configured source-family convention.
     *
     * @param aPath schema source path
     * @param aKind schema format
     * @param aCatalog source-capable naming catalog
     * @return source request whose naming convention is explicitly selected
     */
    static AIcdDefinitionLoadRequest load(Path aPath, AInDefinitionSourceKind aKind,
            AIiNameConventionCatalog aCatalog) {
        String locFamily = switch (aKind) {
            case JSONDEFS -> "jsondef";
            case YAMLDEFS -> "yamldef";
            case XMLDEFS -> "xmldef";
        };
        String locConvention = "algites-" + locFamily + "-schema-versioned_1";
        if (!aCatalog.names().contains(locConvention))
            throw new IllegalArgumentException("Test catalog is missing declared source convention: "
                    + locConvention);
        return new AIcdDefinitionLoadRequest(aPath, aKind, aCatalog, locConvention);
    }
}
