package eu.algites.tool.codegen.sdo;

/** Schema-independent source generator for annotated read-only AIig interfaces. */
public interface AIiSdoCodegenService {
    /** Produce mutable and concrete types; implementation marker is normally d or sdo. */
    AIcdSdoGenerationResult generate(Class<?> aReadContract, String aImplementationMarker);

    /**
     * Generate from newly written Java contract sources, without requiring a prior
     * Gradle/Java compile task. Implementations compile the sources in memory and
     * inspect the resulting annotated interfaces using the same reflection path.
     *
     * @param aSourceRoot package root containing the generated read contracts and enums
     * @param aContractSources AIig source files relative to or inside the source root
     * @param aImplementationMarker output implementation naming marker
     * @param aDependencyClassPath optional binary dependencies used when compiling the sources
     * @return results keyed by normalized absolute contract source paths
     */
    java.util.Map<java.nio.file.Path, AIcdSdoGenerationResult> generateFromSources(
            java.nio.file.Path aSourceRoot, java.util.List<java.nio.file.Path> aContractSources,
            String aImplementationMarker, java.util.List<java.nio.file.Path> aDependencyClassPath);
}
