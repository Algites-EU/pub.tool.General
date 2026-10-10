package eu.algites.tool.codegen.sdo;

/** Schema-independent source generator for a compiled, annotated read-only AIig interface. */
public interface AIiSdoCodegenService {
    /** Produce mutable and concrete types; implementation marker is normally d or sdo. */
    AIcdSdoGenerationResult generate(Class<?> aReadContract, String aImplementationMarker);
}
