package eu.algites.tool.codegen.sdo.impl.cli;

/**
 * Interprets portable naming catalog location prefixes in a native Java Codegen.
 *
 * <p>The naming library already recognizes {@code resource:} locations as
 * classloader-based resources. The public Codegen settings use the clearer
 * {@code classpath:} spelling; the older spelling remains an exact alias.
 */
final class AIcNamingCatalogSource {
    private AIcNamingCatalogSource() { }

    /**
     * Converts the portable classpath prefix to the naming library's resource
     * selector without changing filesystem paths or legacy resource selectors.
     *
     * @param aSource catalog location from resolved Codegen settings
     * @return location understood by the naming catalog loader
     */
    static String normalize(String aSource) {
        return aSource.startsWith("classpath:")
                ? "resource:" + aSource.substring("classpath:".length())
                : aSource;
    }
}
