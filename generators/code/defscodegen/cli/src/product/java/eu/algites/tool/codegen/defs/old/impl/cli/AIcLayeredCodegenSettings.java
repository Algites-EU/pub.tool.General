package eu.algites.tool.codegen.defs.old.impl.cli;

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
     * @param aPackage implementation resource package, including an optional .old suffix;
     *                 public profile overlays retain the unsuffixed package
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
        String locResourceRoot = "eu/algites/tool/codegen/" + aPackage.replace(".", "/") + "/";
        String locDefaultName = aGenerator + "-" + aTechnology + "-default.settings";
        String locOverrideName = aGenerator + "-" + aTechnology + ".settings";
        String locBase = "generators/code/" + aGenerator
                + "/intf/src/product/config/" + locResourceRoot;
        LinkedHashMap<String, String> locSettings = new LinkedHashMap<>();
        String locBuiltIn = readBuiltIn(locResourceRoot + locDefaultName,
                Path.of(locBase, locDefaultName));
        addLines(locSettings, locBuiltIn, locDefaultName);
        // Defaults follow the implementation namespace; public profile artifacts
        // keep their stable resource identity across internal namespace migrations.
        String locProfilePackage = aPackage.endsWith(".old")
                ? aPackage.substring(0, aPackage.length() - ".old".length()) : aPackage;
        String locProfileRoot = "eu/algites/tool/codegen/" + locProfilePackage.replace(".", "/") + "/";
        String locProfileBase = "generators/code/" + aGenerator
                + "/intf/src/product/config/" + locProfileRoot;
        String locUserFile = locSpecifiedFile == null ? ""
                : Files.readString(Path.of(locSpecifiedFile));
        Map<String, String> locRequested = profileSelections(locUserFile);
        locRequested.putAll(profileSelections(String.join("\n", locInvocation)));
        // Installed Algites, Standard Prefix and Standard Postfix settings are
        // alternatives. Never merge unrelated profiles merely because several
        // wheels/JARs happen to be on the classpath.
        var locOverlays = readOverlays(locProfileRoot + locOverrideName,
                Path.of(locProfileBase, locOverrideName));
        Map<Map<String, String>, List<Map.Entry<String, String>>> locFamilies =
                new LinkedHashMap<>();
        for (var locOverlay : locOverlays) {
            var locSignature = profileSelections(locOverlay.getValue());
            if (!locSignature.isEmpty())
                locFamilies.computeIfAbsent(locSignature, ignored -> new ArrayList<>())
                        .add(locOverlay);
        }
        List<Map<String, String>> locMatching = new ArrayList<>();
        for (var locSignature : locFamilies.keySet()) {
            if (locRequested.isEmpty()) {
                locMatching.add(locSignature);
                continue;
            }
            boolean locAgrees = locSignature.entrySet().stream().anyMatch(item ->
                    item.getValue().equals(locRequested.get(item.getKey())));
            boolean locConflicts = locSignature.entrySet().stream().anyMatch(item ->
                    locRequested.containsKey(item.getKey())
                    && !item.getValue().equals(locRequested.get(item.getKey())));
            if (locAgrees && !locConflicts) locMatching.add(locSignature);
        }
        if (locMatching.size() > 1) {
            List<String> locOrigins = new ArrayList<>();
            for (var locSignature : locMatching)
                for (var locOverlay : locFamilies.get(locSignature))
                    locOrigins.add(locOverlay.getKey());
            throw new AIxCodegenValidationException(
                    "Ambiguous Codegen naming profile overlays: " + String.join(", ", locOrigins),
                    "Select exactly one naming family using qualified profile IDs or --settings-file.");
        }
        if (locMatching.isEmpty() && !locRequested.isEmpty()) {
            boolean locPartiallyMatched = locFamilies.keySet().stream().anyMatch(signature ->
                    signature.entrySet().stream().anyMatch(item ->
                            item.getValue().equals(locRequested.get(item.getKey()))));
            if (locPartiallyMatched)
                throw new AIxCodegenValidationException(
                        "Conflicting naming profile selection: no single installed profile matches "
                        + "the explicitly selected profile IDs",
                        "Do not mix Algites, Standard Prefix and Standard Postfix profile IDs.");
        }
        if (locMatching.size() == 1)
            for (var locOverlay : locFamilies.get(locMatching.get(0)))
                addLines(locSettings, locOverlay.getValue(), locOverlay.getKey());
        if (locSpecifiedFile != null)
            addLines(locSettings, locUserFile, locSpecifiedFile);
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

    /**
     * Identifies the naming profile chosen by settings without introducing
     * vendor-specific profile names into the generic CLI settings loader.
     *
     * @param aContent newline-delimited qualified CLI options
     * @return all nonempty naming-profile identity selectors in the content
     */
    private static Map<String, String> profileSelections(String aContent) {
        Set<String> locPrefixes = Set.of(
                "--input-schema-naming-convention:",
                "--common-codegen-naming-convention:",
                "--defs-codegen-naming-convention:",
                "--sdo-codegen-naming-convention:",
                "--output-interface-technology-naming-convention:",
                "--output-enum-technology-naming-convention:",
                "--input-technology-naming-convention:",
                "--output-technology-naming-convention:");
        Map<String, String> locResult = new LinkedHashMap<>();
        for (String locLine : aContent.lines().toList()) {
            String locToken = locLine.strip();
            int locEquals = locToken.indexOf('=');
            if (locEquals <= 0 || locToken.startsWith("#")) continue;
            String locKey = locToken.substring(0, locEquals);
            String locValue = locToken.substring(locEquals + 1);
            if (!locValue.isEmpty() && locPrefixes.stream().anyMatch(locKey::startsWith))
                locResult.put(locKey, locValue);
        }
        return locResult;
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
     * Discovers available classpath profile overlays for subsequent selection.
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
