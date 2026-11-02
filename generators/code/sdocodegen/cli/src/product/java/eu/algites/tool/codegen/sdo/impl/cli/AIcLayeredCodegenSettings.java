package eu.algites.tool.codegen.sdo.impl.cli;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;

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
 * Empty assignments remove inherited entries; qualified option keys remain unchanged
 * throughout parsing and execution.
 */
public final class AIcLayeredCodegenSettings {
    private static final Set<String> FLAGS = Set.of(
            "--check", "--clean-only", "--allow-unversioned-schemas");
    private AIcLayeredCodegenSettings() { }

    /**
     * Resolve all configuration layers for a native generator entry point.
     *
     * @param aArgs explicit invocation options, including at most one settings-file selector
     * @param aGenerator standard generator name such as defscodegen or sdocodegen
     * @param aTechnology native target language, java or python
     * @param aPackage resource package leaf, defs or sdo
     * @return merged, fully qualified arguments with no obsolete value conversion
     * @throws IOException when an input file or resource cannot be read
     */
    public static String[] expand(String[] aArgs, String aGenerator,
                                  String aTechnology, String aPackage) throws IOException {
        String locSpecifiedFile = null;
        List<String> locInvocation = new ArrayList<>();
        for (String locArg : aArgs) {
            if (locArg.startsWith("--settings-file=")) {
                if (locSpecifiedFile != null)
                    throw new AIxCodegenValidationException("Only one --settings-file is permitted", "Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.");
                locSpecifiedFile = locArg.substring("--settings-file=".length());
            } else locInvocation.add(locArg);
        }
        String locResourceRoot = "eu/algites/tool/codegen/" + aPackage + "/";
        String locDefaultName = aGenerator + "-" + aTechnology + "-default.settings";
        String locOverrideName = aGenerator + "-" + aTechnology + ".settings";
        String locBase = "generators/code/" + aGenerator
                + "/intf/src/product/config/" + locResourceRoot;
        LinkedHashMap<String, String> locSettings = new LinkedHashMap<>();
        String locBuiltIn = readBuiltIn(locResourceRoot + locDefaultName,
                Path.of(locBase, locDefaultName));
        addLines(locSettings, locBuiltIn, locDefaultName);
        for (var locOverlay : readOverlays(locResourceRoot + locOverrideName,
                Path.of(locBase, locOverrideName)))
            addLines(locSettings, locOverlay.getValue(), locOverlay.getKey());
        if (locSpecifiedFile != null)
            addLines(locSettings,
                    Files.readString(Path.of(locSpecifiedFile)), locSpecifiedFile);
        for (String locArg : locInvocation)
            addOption(locSettings, locArg);
        List<String> locExpanded = new ArrayList<>();
        for (var locSetting : locSettings.entrySet()) {
            String locKey = locSetting.getKey();
            String locValue = locSetting.getValue();
            int locColon = locKey.indexOf(':');
            String locBaseKey = locColon < 0 ? locKey : locKey.substring(0, locColon);
            if (FLAGS.contains(locBaseKey)) {
                if (!locValue.equalsIgnoreCase("true") && !locValue.equalsIgnoreCase("false"))
                    throw new AIxCodegenValidationException("Expected boolean for " + locKey + ": " + locValue, "Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.");
                if (locValue.equalsIgnoreCase("true")) locExpanded.add(locBaseKey);
            } else {
                locExpanded.add(locKey + "=" + locValue);
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

    private static void addLines(Map<String, String> aMerged,
                                 String aContent, String aSource) {
        int locNumber = 0;
        for (String locLine : aContent.lines().toList()) {
            locNumber++;
            String locTrimmed = locLine.strip();
            if (locTrimmed.isEmpty() || locTrimmed.startsWith("#")) continue;
            if (locTrimmed.chars().anyMatch(Character::isWhitespace))
                throw new AIxCodegenValidationException("Malformed settings: " + aSource + ":" + locNumber, "Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.");
            addOption(aMerged, locTrimmed);
        }
    }

    private static void addOption(Map<String, String> aMerged,
                                  String aOption) {
        if (FLAGS.contains(aOption)) aOption += "=true";
        int locEquals = aOption.indexOf('=');
        if (!aOption.startsWith("--") || locEquals < 3)
            throw new AIxCodegenValidationException("Invalid Codegen setting: " + aOption, "Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.");
        String locKey = aOption.substring(0, locEquals);
        String locValue = aOption.substring(locEquals + 1);
        if (locKey.equals("--settings-file"))
            throw new AIxCodegenValidationException("Nested settings-file is not allowed", "Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.");
        if (locValue.isEmpty()) aMerged.remove(locKey);
        else aMerged.put(locKey, locValue);
    }
}
