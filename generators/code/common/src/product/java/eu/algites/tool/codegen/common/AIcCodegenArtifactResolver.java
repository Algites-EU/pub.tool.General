package eu.algites.tool.codegen.common;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

/**
 * Resolves explicitly selected Java input artifacts from the local Modustro Maven store.
 *
 * <p>This component is shared by Defs and SDO code generation and does not
 * depend on either generator. Source-mode bootstrap must prepare the selected
 * dependencies beforehand; missing artifacts fail instead of using remote or
 * unrelated cached binaries.
 *
 * @author linhart1
 */
public final class AIcCodegenArtifactResolver {
    private AIcCodegenArtifactResolver() { }

    /**
     * Resolve a semicolon-delimited artifact list, preserving the selector order.
     *
     * <p>Each item accepts either a Maven {@code groupId:artifactId:version}
     * coordinate or a Modustro {@code artifactId@version} selector. Prefixes
     * {@code maven:} and {@code modustro:} may make the format explicit.
     * The Maven group cannot be inferred from a bare Modustro identifier: it
     * is instead discovered in the local repository and ambiguity is rejected.
     *
     * @param aSelectors nonempty semicolon-delimited artifact specifications
     * @return unique, existing input JAR paths in declaration order
     * @throws IOException if the repository cannot be scanned
     * @throws IllegalArgumentException if selectors are invalid, missing, or ambiguous
     */
    public static List<Path> resolveJava(String aSelectors) throws IOException {
        if (aSelectors == null || aSelectors.isBlank())
            throw new IllegalArgumentException("Java artifact selectors must not be empty");
        Path locHome = Path.of(System.getProperty("user.home"), ".modustro", "artifact-repos", "java", "maven");
        List<Path> locResults = new ArrayList<>();
        for (String locRaw : aSelectors.split(";", -1)) {
            String locValue = locRaw.strip();
            if (locValue.isEmpty()) throw new IllegalArgumentException("Empty Java artifact selector");
            if (locValue.startsWith("maven:")) locValue = locValue.substring(6);
            else if (locValue.startsWith("modustro:")) locValue = locValue.substring(9);
            String locName;
            String locVersion;
            Path locResult;
            if (locValue.contains("@")) {
                int locSeparator = locValue.lastIndexOf('@');
                locName = locValue.substring(0, locSeparator);
                locVersion = locValue.substring(locSeparator + 1);
                if (locName.isBlank() || locVersion.isBlank())
                    throw new IllegalArgumentException("Invalid Modustro selector: " + locRaw);
                List<Path> locMatches;
                if (!Files.isDirectory(locHome)) locMatches = List.of();
                else try (Stream<Path> locWalk = Files.walk(locHome)) {
                    String locFilename = locName + "-" + locVersion + ".jar";
                    locMatches = locWalk.filter(Files::isRegularFile)
                            .filter(aPath -> aPath.getFileName().toString().equals(locFilename))
                            .filter(aPath -> aPath.getParent().getFileName().toString().equals(locVersion))
                            .filter(aPath -> aPath.getParent().getParent().getFileName().toString().equals(locName))
                            .toList();
                }
                if (locMatches.size() != 1)
                    throw new IllegalArgumentException("Expected one local Modustro JAR for "
                            + locRaw + ", found " + locMatches);
                locResult = locMatches.get(0);
            } else {
                String[] locParts = locValue.split(":", -1);
                if (locParts.length != 3 || locParts[0].isBlank()
                        || locParts[1].isBlank() || locParts[2].isBlank())
                    throw new IllegalArgumentException("Expected Maven group:artifact:version: " + locRaw);
                locName = locParts[1];
                locVersion = locParts[2];
                locResult = locHome.resolve(locParts[0].replace('.', '/'))
                        .resolve(locName).resolve(locVersion)
                        .resolve(locName + "-" + locVersion + ".jar");
                if (!Files.isRegularFile(locResult))
                    throw new IllegalArgumentException("Missing local Maven input JAR: " + locResult);
            }
            if ("source".equals(System.getenv("MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE"))
                    && locName.startsWith("pub.")) {
                String locReady = System.getenv("MODUSTRO_BOOTSTRAP_PREPARED_ARTIFACTS");
                if (locReady == null || !List.of(locReady.split(",", -1)).contains(locName))
                    throw new IllegalArgumentException("Undeclared source input artifact " + locName
                            + "; add it to the Modustro build-time dependency graph");
            }
            if (locResults.contains(locResult))
                throw new IllegalArgumentException("Duplicate Java artifact selector: " + locRaw);
            locResults.add(locResult.toAbsolutePath().normalize());
        }
        return List.copyOf(locResults);
    }
}
