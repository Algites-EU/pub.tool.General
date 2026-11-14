package eu.algites.tool.codegen.defs.impl.cli;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Coalesces identical common enums originating from multiple wire schema dialects.
 * Unlike DataObject interfaces, a named enum is shared by all representations;
 * schema identity and source location are provenance, not enum wire-value ABI.
 * Only provenance and documentation may differ: changes to values, methods,
 * constants other than the source-location fields, or versions remain errors.
 *
 * @author linhart1
 */
public final class AIcDefsCodegenEnumCoalescer {
    /** Provenance emitted by the schema definition Java/Python backends. */
    private static final Pattern ORIGIN = Pattern.compile(
            "Generated from canonical definition ([^\\n]*?)\\. Source: ([^\\n]*?)\\. Do not edit manually\\.");
    /** Metadata emitted by the current canonical enum emitter. */
    private static final Pattern CANONICAL_IDENTITY = Pattern.compile(
            "Canonical identity: ([^;\\n]+); version: ([0-9]+)\\.");
    /** Additional canonical-emitter provenance in Java Javadocs. */
    private static final Pattern JAVA_LEGACY_ALTERNATE = Pattern.compile(
            "(?m)^ \\* <p>Equivalent schema identity: (.*?)</p>\\n");
    /** Additional canonical-emitter provenance in Python enum docs. */
    private static final Pattern PYTHON_LEGACY_ALTERNATE = Pattern.compile(
            "(?m)\\n    Equivalent schema identity: (.*?); version: ([0-9]+)\\.(?=\\n|\"\"\")");
    /** Additional provenance already merged into Java Javadocs. */
    private static final Pattern JAVA_ALTERNATE = Pattern.compile(
            "(?m)^ \\* <p>Equivalent enum schema: (.*?) Source: (.*?)</p>\\n");
    /** Additional provenance already merged into Python enum documentation. */
    private static final Pattern PYTHON_ALTERNATE = Pattern.compile(
            "(?m)\\n    Equivalent enum schema: (.*?) Source: (.*?)(?=\\n|\"\"\")");
    /** Java source-specific fields that are not part of the shared enum's ABI. */
    private static final Pattern JAVA_SOURCE_FIELDS = Pattern.compile(
            "(?m)^\\s*public static final String CANONICAL_SOURCE_(?:ID|RESOURCE)\\s*=\\s*\"(?:\\\\.|[^\"\\\\])*\";\\s*$");
    /** Generated Javadoc blocks may differ by representation. */
    private static final Pattern JAVA_COMMENTS = Pattern.compile("/\\*.*?\\*/", Pattern.DOTALL);
    /** Generated Python enum's class/method docstrings may differ by dialect. */
    private static final Pattern PYTHON_DOCSTRINGS = Pattern.compile(
            "(?ms)^[ \\t]+\"\"\".*?\"\"\"");
    /** Stable order for the canonical source and its documented equivalents. */
    private static final Comparator<Origin> ORIGIN_ORDER = Comparator
            .comparing(Origin::resource).thenComparing(Origin::identity);

    /**
     * One format-specific definition of a shared enum.
     * @param identity versioned canonical definition identity
     * @param resource exact source schema and definition location
     */
    private record Origin(String identity, String resource) { }

    /** Prevent instantiation of this stateless merger. */
    private AIcDefsCodegenEnumCoalescer() { }

    /**
     * Merge two generated declarations of the same enum destination.
     * @param path repository-relative destination, used for diagnostics
     * @param existing first generated source
     * @param proposed second generated source
     * @return deterministic source with all equivalent source identities documented
     * @throws IllegalArgumentException when public members, wire codes or versions conflict
     */
    public static String merge(String path, String existing, String proposed) {
        if (existing.equals(proposed)) return existing;
        boolean java = path.endsWith(".java");
        boolean python = path.endsWith(".py");
        if (!(java && existing.contains("public enum ") && proposed.contains("public enum ")
                || python && existing.contains("class ") && proposed.contains("class ")
                        && existing.contains("Enum") && proposed.contains("Enum"))) {
            throw new IllegalArgumentException("Conflicting Defs outputs at " + path
                    + ": non-enum declaration collision");
        }
        List<Origin> a = origins(existing, python);
        List<Origin> b = origins(proposed, python);
        TreeSet<Origin> merged = new TreeSet<>(ORIGIN_ORDER);
        merged.addAll(a);
        merged.addAll(b);
        if (a.isEmpty() || b.isEmpty() || !program(existing, python).equals(program(proposed, python))) {
            throw new IllegalArgumentException("Conflicting Defs enum declarations at " + path
                    + ": " + (a.isEmpty() ? "missing canonical provenance" : a)
                    + " versus " + (b.isEmpty() ? "missing canonical provenance" : b)
                    + "; enum values, version or public API differ");
        }
        String version = null;
        for (Origin origin : merged) {
            int separator = origin.identity().lastIndexOf('/');
            String candidate = origin.identity().substring(separator + 1);
            if (!candidate.matches("[0-9]+") || version != null && !version.equals(candidate)) {
                throw new IllegalArgumentException("Conflicting Defs enum schema versions at "
                        + path + ": " + merged);
            }
            version = candidate;
        }
        Origin primary = merged.first();
        String result = (a.get(0).equals(primary) ? existing : proposed);
        result = (python ? PYTHON_ALTERNATE : JAVA_ALTERNATE).matcher(result).replaceAll("");
        result = (python ? PYTHON_LEGACY_ALTERNATE : JAVA_LEGACY_ALTERNATE)
                .matcher(result).replaceAll("");
        List<Origin> equivalents = new ArrayList<>(merged);
        equivalents.remove(primary);
        if (equivalents.isEmpty()) return result;
        StringBuilder extra = new StringBuilder();
        for (Origin source : equivalents) {
            String identity = source.identity();
            String bare = identity.substring(0, identity.lastIndexOf('/'));
            String number = identity.substring(identity.lastIndexOf('/') + 1);
            if (java && !source.resource().isEmpty()) {
                extra.append(" * <p>Equivalent enum schema: ").append(identity)
                        .append(" Source: ").append(source.resource()).append("</p>\n");
            } else if (java) {
                extra.append(" * <p>Equivalent schema identity: ").append(bare)
                        .append("; version: ").append(number).append(".</p>\n");
            } else if (!source.resource().isEmpty()) {
                extra.append("\n    Equivalent enum schema: ").append(identity)
                        .append(" Source: ").append(source.resource());
            } else {
                extra.append("\n    Equivalent schema identity: ").append(bare)
                        .append("; version: ").append(number).append('.');
            }
        }
        if (java) {
            int insertion = result.indexOf(" * @author ");
            if (insertion < 0) insertion = result.indexOf(" */");
            if (insertion < 0) throw new IllegalArgumentException("Missing Java enum Javadoc at " + path);
            return result.substring(0, insertion) + extra + result.substring(insertion);
        }
        Matcher original = ORIGIN.matcher(result);
        if (!original.find()) {
            original = CANONICAL_IDENTITY.matcher(result);
            if (!original.find()) throw new IllegalArgumentException("Missing Python enum provenance at " + path);
        }
        return result.substring(0, original.end()) + extra + result.substring(original.end());
    }

    /** Return all already documented source identities. */
    private static List<Origin> origins(String source, boolean python) {
        Matcher original = ORIGIN.matcher(source);
        List<Origin> values = new ArrayList<>();
        if (original.find()) {
            values.add(new Origin(original.group(1), original.group(2)));
        } else {
            Matcher canonical = CANONICAL_IDENTITY.matcher(source);
            if (!canonical.find()) return List.of();
            values.add(new Origin(canonical.group(1) + "/" + canonical.group(2), ""));
        }
        Matcher equivalent = (python ? PYTHON_ALTERNATE : JAVA_ALTERNATE).matcher(source);
        while (equivalent.find()) {
            Origin item = new Origin(equivalent.group(1), equivalent.group(2));
            if (!values.contains(item)) values.add(item);
        }
        if (python) {
            Matcher old = PYTHON_LEGACY_ALTERNATE.matcher(source);
            while (old.find()) {
                Origin item = new Origin(old.group(1) + "/" + old.group(2), "");
                if (!values.contains(item)) values.add(item);
            }
        } else {
            Matcher old = JAVA_LEGACY_ALTERNATE.matcher(source);
            String defaultVersion = values.get(0).identity().substring(
                    values.get(0).identity().lastIndexOf('/') + 1);
            while (old.find()) {
                String tag = old.group(1);
                int versionPos = tag.lastIndexOf("; version: ");
                String identity = versionPos < 0 ? tag : tag.substring(0, versionPos);
                String version = versionPos < 0 ? defaultVersion
                        : tag.substring(versionPos + "; version: ".length()).replaceAll("\\.$", "");
                Origin item = new Origin(identity + "/" + version, "");
                if (!values.contains(item)) values.add(item);
            }
        }
        return values;
    }

    /** Ignore documentation and wire-provenance locations, not executable fields. */
    private static String program(String source, boolean python) {
        String clean = python ? PYTHON_DOCSTRINGS.matcher(source).replaceAll("")
                : JAVA_COMMENTS.matcher(JAVA_SOURCE_FIELDS.matcher(source).replaceAll("")).replaceAll("");
        StringBuilder normalized = new StringBuilder();
        for (String line : clean.split("\\R")) {
            String value = line.strip();
            if (!value.isEmpty()) normalized.append(value).append('\n');
        }
        return normalized.toString();
    }
}
