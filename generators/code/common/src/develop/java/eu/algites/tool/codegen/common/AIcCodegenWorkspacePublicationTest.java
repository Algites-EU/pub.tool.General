package eu.algites.tool.codegen.common;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

/**
 * Dependency-free smoke tests for incremental and explicit-cleanup Java publication.
 * Run with javac/java against the production workspace class.
 *
 * @author linhart1
 */
public final class AIcCodegenWorkspacePublicationTest {
    /** Prevent utility construction. */
    private AIcCodegenWorkspacePublicationTest() { }

    /**
     * Verify normal replacement, no-index verification, and generator-scoped cleanup.
     * @param args first argument is the temporary test repository root
     * @throws Exception if publication, locking, source safety, or a check fails
     */
    public static void main(String[] args) throws Exception {
        Path repository = Path.of(args[0]).toAbsolutePath();
        Path artifact = repository.resolve("artifact");
        Files.createDirectories(artifact);
        Files.writeString(artifact.resolve("modustro-artifact.yml"), "identifier: test\n");
        Path output = artifact.resolve("src/product/java.gen/generated.java");
        Path foreign = artifact.resolve("src/product/java.gen/foreign.java");
        Files.createDirectories(output.getParent());
        Files.writeString(output, "stale\n");
        Files.writeString(foreign, "foreign\n");
        try (var ws = new AIcCodegenWorkspace(repository, artifact, "defscodegen")) {
            ws.publish(Map.of(output, "new\n"), false);
        }
        assertText(output, "new\n");
        assertText(foreign, "foreign\n");
        Path index = repository.resolve("build/artifact/defscodegen/generated-files-java.properties");
        Files.delete(index);
        try (var ws = new AIcCodegenWorkspace(repository, artifact, "defscodegen")) {
            ws.publish(Map.of(output, "new\n"), true);
        }
        // An independent generator is allowed to share the physical .gen root.
        try (var ws = new AIcCodegenWorkspace(repository, artifact, "sdocodegen")) {
            ws.publish(Map.of(foreign, "sdo\n"), false);
        }
        try (var ws = new AIcCodegenWorkspace(repository, artifact, "defscodegen")) {
            ws.publish(Map.of(output, "latest\n"), false, true);
        }
        assertText(output, "latest\n");
        assertText(foreign, "sdo\n");
        Path obsolete = artifact.resolve("src/product/java.gen/obsolete.java");
        try (var ws = new AIcCodegenWorkspace(repository, artifact, "defscodegen")) {
            ws.publish(Map.of(obsolete, "obsolete\n"), false);
        }
        try (var ws = new AIcCodegenWorkspace(repository, artifact, "defscodegen")) {
            ws.publish(Map.of(output, "latest\n"), false, true);
        }
        if (Files.exists(obsolete)) throw new AssertionError("Obsolete generator-owned output survived cleanup");
        assertText(foreign, "sdo\n");
        // A malicious file or parent symlink must never redirect publication.
        Path external = repository.resolve("external");
        Files.createDirectories(external);
        Path protectedFile = external.resolve("protected.java");
        Files.writeString(protectedFile, "unchanged\n");
        Path alias = artifact.resolve("src/product/java.gen/alias.java");
        Files.createSymbolicLink(alias, protectedFile);
        try (var ws = new AIcCodegenWorkspace(repository, artifact, "defscodegen")) {
            try {
                ws.publish(Map.of(alias, "wrong\n"), false);
                throw new AssertionError("Symlinked source should have been refused");
            } catch (java.io.IOException expected) {
                if (!expected.getMessage().contains("Symlink")) throw expected;
            }
        }
        Path linkedDirectory = artifact.resolve("src/product/java.gen/linked");
        Files.createSymbolicLink(linkedDirectory, external);
        try (var ws = new AIcCodegenWorkspace(repository, artifact, "sdocodegen")) {
            try {
                ws.publish(Map.of(linkedDirectory.resolve("protected.java"), "wrong\n"), false);
                throw new AssertionError("Symlinked parent should have been refused");
            } catch (java.io.IOException expected) {
                if (!expected.getMessage().contains("Symlink")) throw expected;
            }
        }
        assertText(protectedFile, "unchanged\n");
    }

    /**
     * Check exact source bytes.
     * @param file generated source to inspect
     * @param content expected source
     * @throws Exception when reading fails or expected output differs
     */
    private static void assertText(Path file, String content) throws Exception {
        if (!Files.readString(file, StandardCharsets.UTF_8).equals(content))
            throw new AssertionError("Unexpected generated source " + file);
    }
}
