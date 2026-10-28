package eu.algites.tool.codegen.sdo.impl.cli;

import eu.algites.lib.naming.convention.impl.standard.AIcNameConventionCatalog;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Collects every matching classpath naming catalog before merging the definitions.
 *
 * <p>Catalog sources may be filesystem paths or classpath resource identifiers.
 * Resources from JARs are materialized together with their referenced naming
 * standard in a temporary directory, then merged by the established naming
 * catalog loader. Identical definitions can be shared, while conflicting
 * naming IDs remain an error rather than receiving silent precedence.
 */
final class AIcNamingCatalogCollector {
    private static final String PREFIX = "eu/algites/lib/naming/convention/";
    private static final Pattern FILE_NAME = Pattern.compile("[A-Za-z0-9][A-Za-z0-9_.-]*\\.yml");
    private static final Pattern STANDARD = Pattern.compile(
            "(?m)^\\s*StandardConventionsFile:\\s*[\"']?([A-Za-z0-9][A-Za-z0-9_.-]*\\.yml)");

    private AIcNamingCatalogCollector() { }

    /**
     * Read all configured catalogs, including every classpath occurrence of each name.
     *
     * @param aSources filesystem paths or classpath/resource locators in settings order
     * @return one merged naming catalog retaining all compatible definitions
     * @throws IOException when a catalog or its sibling standard cannot be read
     */
    static AIcNameConventionCatalog load(List<String> aSources) throws IOException {
        Path locTemporary = Files.createTempDirectory("algites-naming-catalogs-");
        try {
            List<String> locExpanded = new ArrayList<>();
            ClassLoader locLoader = Thread.currentThread().getContextClassLoader();
            if (locLoader == null) locLoader = AIcNamingCatalogCollector.class.getClassLoader();
            for (String locSource : aSources) {
                if (!locSource.startsWith("resource:") && !locSource.startsWith("classpath:")) {
                    locExpanded.add(locSource);
                    continue;
                }
                String locName = locSource.substring(locSource.indexOf(':') + 1);
                if (!FILE_NAME.matcher(locName).matches())
                    throw new IllegalArgumentException("Invalid classpath naming catalog: " + locName);
                Enumeration<URL> locResources = locLoader.getResources(PREFIX + locName);
                List<URL> locUrls = new ArrayList<>();
                Set<String> locSeen = new HashSet<>();
                while (locResources.hasMoreElements()) {
                    URL locUrl = locResources.nextElement();
                    if (locSeen.add(locUrl.toExternalForm())) locUrls.add(locUrl);
                }
                if (locUrls.isEmpty())
                    throw new IOException("Missing classpath naming catalog: " + locName);
                for (int locIndex = locUrls.size() - 1; locIndex >= 0; locIndex--) {
                    URL locUrl = locUrls.get(locIndex);
                    Path locFolder = Files.createTempDirectory(locTemporary, "catalog-");
                    String locText;
                    try (InputStream locStream = locUrl.openStream()) {
                        locText = new String(locStream.readAllBytes(), StandardCharsets.UTF_8);
                    }
                    Files.writeString(locFolder.resolve(locName), locText);
                    Matcher locStandard = STANDARD.matcher(locText);
                    if (locStandard.find()) {
                        String locSiblingName = locStandard.group(1);
                        /* The shared standard grammar belongs to naming/convention/intf,
                         * not to the profile JAR providing the referring catalog.
                         * Resolving it through the classloader also supports separate
                         * Maven artifacts and exploded class directories. */
                        String locSharedResource = PREFIX + locSiblingName;
                        try (InputStream locStream = locLoader.getResourceAsStream(locSharedResource)) {
                            if (locStream == null)
                                throw new IOException("Missing shared standard naming resource: "
                                        + locSharedResource + " (required by " + locUrl + ")");
                            Files.copy(locStream, locFolder.resolve(locSiblingName));
                        }
                    }
                    locExpanded.add(locFolder.resolve(locName).toString());
                }
            }
            return AIcNameConventionCatalog.loadAll(locExpanded);
        } finally {
            try (var locPaths = Files.walk(locTemporary)) {
                for (Path locPath : locPaths.sorted(java.util.Comparator.reverseOrder()).toList())
                    Files.deleteIfExists(locPath);
            }
        }
    }
}
