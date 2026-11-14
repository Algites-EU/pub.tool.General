package eu.algites.tool.codegen.common;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

/**
 * Emit start and end timestamps for one artifact/target technology invocation.
 * The monotonic clock measures elapsed time even if wall-clock time changes.
 * No bootstrap script is involved: both standalone generator CLIs use this log.
 *
 * @author linhart1
 */
public final class AIcCodegenRunLog implements AutoCloseable {
    /** Generator identifying this invocation in concurrent bootstrap output. */
    private final String generator;
    /** Repository-relative artifact label. */
    private final String artifact;
    /** Java or Python generation target. */
    private final String technology;
    /** Monotonic start time. */
    private final long startedNanos;

    /**
     * Start a single generator/target invocation and write the first log line.
     *
     * @param aGenerator generator name, e.g. {@code Defs Codegen}
     * @param aTechnology output technology, {@code java} or {@code python}
     * @param aRepository repository root containing the selected artifact
     * @param aArtifact the selected artifact's physical root
     */
    public AIcCodegenRunLog(String aGenerator, String aTechnology,
            Path aRepository, Path aArtifact) {
        generator = aGenerator;
        technology = aTechnology;
        Path repository = aRepository.toAbsolutePath().normalize();
        Path selected = aArtifact.toAbsolutePath().normalize();
        String locLabel = selected.startsWith(repository)
                ? repository.relativize(selected).toString().replace('\\', '/')
                : selected.toString();
        // Gradle can run the SDO CLI with --repository-root pointing directly
        // at the artifact. An empty relative path must never produce an empty
        // artifact label; use the enclosing Modustro source-repository marker.
        if (locLabel.isBlank()) {
            Path locParent = selected;
            while (locParent != null && !Files.isRegularFile(
                    locParent.resolve("modustro-source-repository.yml")))
                locParent = locParent.getParent();
            locLabel = locParent == null ? selected.getFileName().toString()
                    : locParent.relativize(selected).toString().replace('\\', '/');
        }
        artifact = locLabel;
        startedNanos = System.nanoTime();
        log("START", 0L);
    }

    /**
     * Open a timing log for an SDO invocation after its layered CLI settings
     * have been expanded; the artifact is inferred from its actual output root.
     *
     * @param aGenerator generating command name
     * @param aTechnology generator target language
     * @param aArguments expanded qualified CLI arguments
     * @param aOutputOption output root option, without leading {@code --}
     * @return opened logger, to be closed in a {@code finally} block
     * @throws IOException if the selected output is outside the repository
     */
    public static AIcCodegenRunLog fromArguments(String aGenerator,
            String aTechnology, String[] aArguments, String aOutputOption) throws IOException {
        String repository = ".";
        String output = null;
        for (String option : aArguments) {
            if (option.startsWith("--repository-root="))
                repository = option.substring("--repository-root=".length());
            if (option.startsWith("--" + aOutputOption + "="))
                output = option.substring(aOutputOption.length() + 3);
        }
        Path root = Path.of(repository).toAbsolutePath().normalize();
        Path artifact = output == null ? root : AIcCodegenWorkspace.artifactRoot(
                root, root.resolve(output));
        return new AIcCodegenRunLog(aGenerator, aTechnology, root, artifact);
    }

    /**
     * Write a terminal log line, including elapsed milliseconds and seconds.
     * Even an exception from generation closes this logger.
     */
    @Override public void close() {
        log("END", System.nanoTime() - startedNanos);
    }

    /**
     * Emit one timestamped human- and machine-readable event.
     *
     * @param aEvent start/end marker
     * @param aElapsedNanos monotonic elapsed duration in nanoseconds
     */
    private void log(String aEvent, long aElapsedNanos) {
        Instant now = Instant.now();
        String timestamp = ZonedDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
        String duration = aEvent.equals("END")
                ? " durationMs=" + aElapsedNanos / 1_000_000L
                  + " durationSec=" + String.format(Locale.ROOT, "%.3f", aElapsedNanos / 1e9)
                : "";
        System.out.println(generator + " " + aEvent + " artifact=" + artifact
                + " technology=" + technology + " at=" + timestamp
                + " epochMillis=" + now.toEpochMilli() + duration);
        System.out.flush();
    }
}
