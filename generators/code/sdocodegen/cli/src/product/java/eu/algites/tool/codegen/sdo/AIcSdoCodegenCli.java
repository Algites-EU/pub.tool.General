package eu.algites.tool.codegen.sdo;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;

/** CLI adapter; consumes compiled annotated AIig contracts, never schemas. */
public final class AIcSdoCodegenCli {
    private AIcSdoCodegenCli() { }

    /** Generate independent mutable-contract and concrete implementation files. */
    public static void main(String[] aArguments) throws Exception {
        if (aArguments.length < 3 || aArguments.length > 5) {
            throw new IllegalArgumentException("Usage: <class> <mutable-root> <implementation-root> [marker] [--check]");
        }
        boolean locCheck = false;
        String locMarker = "d";
        for (int i = 3; i < aArguments.length; i++) {
            if (aArguments[i].equals("--check")) locCheck = true;
            else if (locMarker.equals("d")) locMarker = aArguments[i];
            else throw new IllegalArgumentException("Invalid generator argument: " + aArguments[i]);
        }
        Path locMutableRoot = Path.of(aArguments[1]).toAbsolutePath().normalize();
        Path locImplementationRoot = Path.of(aArguments[2]).toAbsolutePath().normalize();
        if (locMutableRoot.equals(locImplementationRoot)) {
            throw new IllegalArgumentException("Mutable interfaces and implementations must have separate output roots");
        }
        var locGenerated = new AIcSdoCodegenService().generate(Class.forName(aArguments[0]), locMarker);
        write(locMutableRoot, locGenerated.mutableInterface(), locCheck);
        write(locImplementationRoot, locGenerated.implementation(), locCheck);
    }

    private static void write(Path aRoot, AIcdGeneratedSdoSource aSource, boolean aCheck) throws Exception {
        Path locOutput = aRoot.resolve(aSource.relativePath()).normalize();
        if (!locOutput.startsWith(aRoot)) throw new IllegalArgumentException("Generated path escapes output root");
        if (aCheck) {
            if (!Files.isRegularFile(locOutput) || !Files.readString(locOutput).equals(aSource.source())) {
                throw new IllegalStateException("Missing/outdated generated SDO output: " + locOutput);
            }
        } else {
            Files.createDirectories(locOutput.getParent());
            if (!Files.isRegularFile(locOutput) || !Files.readString(locOutput).equals(aSource.source())) {
                Files.writeString(locOutput, aSource.source(), StandardCharsets.UTF_8);
            }
        }
        System.out.println(locOutput);
    }
}
