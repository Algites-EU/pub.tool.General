package eu.algites.tool.codegen.sdo.impl.cli;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Merges native Codegen settings by their complete qualified option keys.
 *
 * <p>Defaults bundled with the generator are overlaid with the optional classpath
 * resource, the invocation settings file, and explicit command-line arguments.
 * Empty assignments remove inherited entries; the resulting entries are converted
 * to the existing internal CLI syntax only after all layers have been merged.
 */
public final class AIcLayeredCodegenSettings {
    private static final Set<String> FLAGS = Set.of(
            "--check", "--clean-only", "--allow-unversioned-schemas");
    private static final Set<String> REPEATABLE = Set.of(
            "--naming-conventions-file", "--dointf-classpath",
            "--dointf-input-artifact", "--dointf-input-class");
    private static final Set<String> QUALIFIED_ONE = Set.of(
            "--schema-input-dir", "--input-schema-naming-convention",
            "--technology-dointf-output-dir", "--technology-dointf-input-dir",
            "--technology-sdointf-output-dir", "--technology-sdoimpl-output-dir",
            "--output-enum-technology-naming-convention");
    private static final Set<String> QUALIFIED_NAMING = Set.of(
            "--output-interface-technology-naming-convention",
            "--input-technology-naming-convention", "--output-technology-naming-convention");

    private AIcLayeredCodegenSettings() { }

    /**
     * Resolve all configuration layers for a native generator entry point.
     *
     * @param aArgs explicit invocation options, including at most one settings-file selector
     * @param aGenerator standard generator name such as defscodegen or sdocodegen
     * @param aTechnology native target language, java or python
     * @param aPackage resource package leaf, defs or sdo
     * @return merged arguments compatible with the generator's existing batch parser
     * @throws IOException when an input file or resource cannot be read
     */
    public static String[] expand(String[] aArgs, String aGenerator,
                                  String aTechnology, String aPackage) throws IOException {
        String locSpecifiedFile = null;
        List<String> locInvocation = new ArrayList<>();
        for (String locArg : aArgs) {
            if (locArg.startsWith("--settings-file=")) {
                if (locSpecifiedFile != null)
                    throw new IllegalArgumentException("Only one --settings-file is permitted");
                locSpecifiedFile = locArg.substring("--settings-file=".length());
            } else locInvocation.add(locArg);
        }
        String locResourceRoot = "eu/algites/tool/codegen/" + aPackage + "/";
        String locDefaultName = aGenerator + "-" + aTechnology + "-default.settings";
        String locOverrideName = aGenerator + "-" + aTechnology + ".settings";
        String locBase = "generators/code/" + aGenerator
                + "/intf/src/product/config/" + locResourceRoot;
        LinkedHashMap<String, String> locSettings = new LinkedHashMap<>();
        Map<String, Integer> locLegacyIndices = new LinkedHashMap<>();
        String locBuiltIn = readBuiltIn(locResourceRoot + locDefaultName,
                Path.of(locBase, locDefaultName));
        addLines(locSettings, locLegacyIndices, locBuiltIn, locDefaultName);
        for (var locOverlay : readOverlays(locResourceRoot + locOverrideName,
                Path.of(locBase, locOverrideName)))
            addLines(locSettings, locLegacyIndices, locOverlay.getValue(), locOverlay.getKey());
        if (locSpecifiedFile != null)
            addLines(locSettings, locLegacyIndices,
                    Files.readString(Path.of(locSpecifiedFile)), locSpecifiedFile);
        for (String locArg : locInvocation)
            addOption(locSettings, locLegacyIndices, locArg);
        List<String> locExpanded = new ArrayList<>();
        for (var locSetting : locSettings.entrySet()) {
            String locKey = locSetting.getKey();
            String locValue = locSetting.getValue();
            int locColon = locKey.indexOf(':');
            String locBaseKey = locColon < 0 ? locKey : locKey.substring(0, locColon);
            if (FLAGS.contains(locBaseKey)) {
                if (!locValue.equalsIgnoreCase("true") && !locValue.equalsIgnoreCase("false"))
                    throw new IllegalArgumentException("Expected boolean for " + locKey + ": " + locValue);
                if (locValue.equalsIgnoreCase("true")) locExpanded.add(locBaseKey);
            } else if (locColon < 0 || REPEATABLE.contains(locBaseKey)) {
                locExpanded.add(locBaseKey + "=" + locValue);
            } else if (QUALIFIED_NAMING.contains(locBaseKey)) {
                int locLastColon = locKey.lastIndexOf(':');
                if (locLastColon <= locColon)
                    throw new IllegalArgumentException("Invalid qualified naming key: " + locKey);
                locExpanded.add(locBaseKey + "=" + locKey.substring(locColon + 1, locLastColon)
                        + ":" + locKey.substring(locLastColon + 1) + "=" + locValue);
            } else {
                locExpanded.add(locBaseKey + "=" + locKey.substring(locColon + 1) + ":" + locValue);
            }
        }
        return locExpanded.toArray(String[]::new);
    }

    private static String readBuiltIn(String aResource, Path aCheckout) throws IOException {
        try (InputStream locStream = AIcLayeredCodegenSettings.class.getClassLoader()
                .getResourceAsStream(aResource)) {
            if (locStream != null)
                return new String(locStream.readAllBytes(), StandardCharsets.UTF_8);
        }
        if (Files.isRegularFile(aCheckout)) return Files.readString(aCheckout);
        throw new IOException("Missing packaged Codegen settings: " + aResource);
    }

    /**
     * Reads every matching classpath settings file rather than selecting one.
     *
     * <p>ClassLoader lookup order places the first resource at highest priority.
     * Overlay files are therefore applied in reverse enumeration order, so the
     * first classpath occurrence wins when the same key appears more than once.
     * An optional checkout overlay participates as a lower-priority fallback.
     *
     * @param aResource package-relative resource name of the overlay
     * @param aCheckout checkout-relative fallback file
     * @return ordered source/content pairs, from lowest to highest priority
     * @throws IOException if resource enumeration or reading fails
     */
    private static List<Map.Entry<String, String>> readOverlays(
            String aResource, Path aCheckout) throws IOException {
        List<Map.Entry<String, String>> locResult = new ArrayList<>();
        if (Files.isRegularFile(aCheckout))
            locResult.add(Map.entry(aCheckout.toString(), Files.readString(aCheckout)));
        ClassLoader locLoader = Thread.currentThread().getContextClassLoader();
        if (locLoader == null) locLoader = AIcLayeredCodegenSettings.class.getClassLoader();
        Enumeration<java.net.URL> locCandidates = locLoader.getResources(aResource);
        List<java.net.URL> locOrdered = new ArrayList<>();
        Set<String> locSeen = new java.util.HashSet<>();
        while (locCandidates.hasMoreElements()) {
            java.net.URL locCandidate = locCandidates.nextElement();
            if (locSeen.add(locCandidate.toExternalForm())) locOrdered.add(locCandidate);
        }
        for (int locIndex = locOrdered.size() - 1; locIndex >= 0; locIndex--) {
            java.net.URL locCandidate = locOrdered.get(locIndex);
            try (InputStream locStream = locCandidate.openStream()) {
                locResult.add(Map.entry(locCandidate.toExternalForm(),
                        new String(locStream.readAllBytes(), StandardCharsets.UTF_8)));
            }
        }
        return locResult;
    }

    private static void addLines(Map<String, String> aMerged, Map<String, Integer> aCounters,
                                 String aContent, String aSource) {
        int locNumber = 0;
        for (String locLine : aContent.lines().toList()) {
            locNumber++;
            String locTrimmed = locLine.strip();
            if (locTrimmed.isEmpty() || locTrimmed.startsWith("#")) continue;
            if (locTrimmed.chars().anyMatch(Character::isWhitespace))
                throw new IllegalArgumentException("Malformed settings: " + aSource + ":" + locNumber);
            addOption(aMerged, aCounters, locTrimmed);
        }
    }

    private static void addOption(Map<String, String> aMerged, Map<String, Integer> aCounters,
                                  String aOption) {
        if (FLAGS.contains(aOption)) aOption += "=true";
        int locEquals = aOption.indexOf('=');
        if (!aOption.startsWith("--") || locEquals < 3)
            throw new IllegalArgumentException("Invalid Codegen setting: " + aOption);
        String locKey = aOption.substring(0, locEquals);
        String locValue = aOption.substring(locEquals + 1);
        if (locKey.equals("--settings-file"))
            throw new IllegalArgumentException("Nested settings-file is not allowed");
        if (locKey.indexOf(':') < 0) {
            if (REPEATABLE.contains(locKey)) {
                int locCounter = aCounters.merge(locKey, 1, Integer::sum);
                locKey += ":legacy-" + String.format("%08d", locCounter);
            } else if (QUALIFIED_ONE.contains(locKey)) {
                int locColon = locValue.indexOf(':');
                if (locColon > 0) {
                    locKey += ":" + locValue.substring(0, locColon);
                    locValue = locValue.substring(locColon + 1);
                }
            } else if (QUALIFIED_NAMING.contains(locKey)) {
                String[] locParts = locValue.split(":", 3);
                if (locParts.length == 3) {
                    for (String locElement : locParts[2].split(",")) {
                        int locAssignment = locElement.indexOf('=');
                        if (locAssignment <= 0)
                            throw new IllegalArgumentException("Invalid naming assignment: " + locElement);
                        addOption(aMerged, aCounters, locKey + ":" + locParts[0] + ":" + locParts[1]
                                + ":" + locElement.substring(0, locAssignment) + "="
                                + locElement.substring(locAssignment + 1));
                    }
                    return;
                }
            }
        }
        if (locValue.isEmpty()) aMerged.remove(locKey);
        else aMerged.put(locKey, locValue);
    }
}
