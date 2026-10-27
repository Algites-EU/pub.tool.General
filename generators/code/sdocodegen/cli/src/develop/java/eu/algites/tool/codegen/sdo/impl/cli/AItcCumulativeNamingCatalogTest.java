package eu.algites.tool.codegen.sdo.impl.cli;

import eu.algites.lib.naming.convention.impl.standard.AIcNameConventionCatalog;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;

import org.testng.annotations.Test;

/** Regression for cumulative naming-catalog lookup across directories and JARs. */
public final class AItcCumulativeNamingCatalogTest {
    /**
     * Validates that all resources with one name contribute definitions and that
     * each JAR-backed catalog retains access to its sibling standard definitions.
     *
     * @throws Exception when a catalog resource cannot be merged or validated
     */
    @Test
    public void verifyCumulativeNamingCatalogs() throws Exception {
        Path locRoot = Files.createTempDirectory("algites-cumulative-catalog-");
        String locResource = "eu/algites/lib/naming/convention/";
        Path locDirectory = locRoot.resolve("directory");
        Path locCatalog = locDirectory.resolve(locResource + "multi.yml");
        Files.createDirectories(locCatalog.getParent());
        Files.writeString(locCatalog, schema("directory"));
        Path locJar = locRoot.resolve("resources.jar");
        try (JarOutputStream locOutput = new JarOutputStream(Files.newOutputStream(locJar))) {
            locOutput.putNextEntry(new JarEntry(locResource + "multi.yml"));
            locOutput.write(("StandardConventionsFile: standard-conventions.yml\n"
                    + schema("archive")).getBytes(StandardCharsets.UTF_8));
            locOutput.closeEntry();
            locOutput.putNextEntry(new JarEntry(locResource + "standard-conventions.yml"));
            locOutput.write("IdentifierConventions: {}\n".getBytes(StandardCharsets.UTF_8));
            locOutput.closeEntry();
        }
        ClassLoader locBefore = Thread.currentThread().getContextClassLoader();
        try (URLClassLoader locClassPath = new URLClassLoader(new URL[] {
                locDirectory.toUri().toURL(), locJar.toUri().toURL()}, locBefore)) {
            Thread.currentThread().setContextClassLoader(locClassPath);
            AIcNameConventionCatalog locMerged = AIcNamingCatalogCollector.load(
                    List.of("classpath:multi.yml"));
            if (!locMerged.names().contains("directory-id")
                    || !locMerged.names().contains("archive-id"))
                throw new AssertionError("Multiple classpath naming resources were not merged: "
                        + locMerged.names());
        } finally {
            Thread.currentThread().setContextClassLoader(locBefore);
            try (var locFiles = Files.walk(locRoot)) {
                for (Path locFile : locFiles.sorted(java.util.Comparator.reverseOrder()).toList())
                    Files.deleteIfExists(locFile);
            }
        }
    }

    private static String schema(String aName) {
        return "NameFragments:\n"
                + "  " + aName + ":\n"
                + "    Segments: [{Kind: constant_string, Value: " + aName + "}]\n"
                + "NameConventions:\n"
                + "  " + aName + "-id:\n"
                + "    ContainerStructureType: interface\n"
                + "    StructureNaming:\n"
                + "      file_name_stem: " + aName + "\n"
                + "      file_name_suffix: " + aName + "\n";
    }
}
