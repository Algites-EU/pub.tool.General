package eu.algites.tool.codegen.common;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.TreeSet;
import java.util.UUID;
import java.util.stream.Stream;

/**
 * Transactional per-artifact workspace for native Java Codegens. Every process
 * uses a distinct UUID directory and holds its run lock for the entire lifetime.
 * A separate per-artifact publication lock synchronizes with Python's POSIX
 * record lock and never serializes unrelated artifacts.
 *
 * @author linhart1
 */
public final class AIcCodegenWorkspace implements AutoCloseable {
    /** Repository root, required to contain every owned destination. */
    private final Path repository;
    /** Declared artifact root. */
    private final Path artifact;
    /** Workspace base under build/. */
    private final Path base;
    /** Private directory for one invocation. */
    private final Path run;
    /** Active file descriptor preventing concurrent cleanup. */
    private final FileChannel runChannel;
    /** Active per-invocation lock. */
    private final FileLock runLock;

    /**
     * Allocate a private workspace for exactly one artifact and Codegen.
     *
     * @param aRepository repository root
     * @param aArtifact declared artifact directory, possibly the repository itself for tests
     * @param aGenerator defscodegen or sdocodegen
     * @throws IOException on inaccessible build directory or failed run lock
     */
    public AIcCodegenWorkspace(Path aRepository, Path aArtifact, String aGenerator) throws IOException {
        if (!Set.of("defscodegen", "sdocodegen").contains(aGenerator))
            throw new IllegalArgumentException("Unknown generator: " + aGenerator);
        repository = aRepository.toRealPath();
        artifact = aArtifact.toRealPath();
        if (!artifact.startsWith(repository))
            throw new IllegalArgumentException("Artifact outside repository: " + artifact);
        base = repository.resolve("build").resolve(repository.relativize(artifact)).resolve(aGenerator);
        Files.createDirectories(base);
        run = base.resolve(UUID.randomUUID().toString());
        Files.createDirectory(run);
        Files.createDirectories(run.resolve("tmp"));
        Files.createDirectories(run.resolve("staging"));
        runChannel = FileChannel.open(run.resolve(".run.lock"), StandardOpenOption.CREATE,
                StandardOpenOption.WRITE);
        runLock = runChannel.lock();
    }

    /**
     * Return the private work directory for this invocation.
     * @return unique UUID work directory under build/artifact/generator
     */
    public Path workDir() { return run; }

    /**
     * Detect the nearest declared artifact owning an output root.
     * @param aRepository repository root
     * @param aDestination generated output tree
     * @return containing artifact or repository for standalone fixtures
     * @throws IOException if the repository path does not exist
     */
    public static Path artifactRoot(Path aRepository, Path aDestination) throws IOException {
        Path repository = aRepository.toRealPath();
        Path output = aDestination.toAbsolutePath().normalize();
        if (!output.startsWith(repository)) throw new IllegalArgumentException("Output outside repository: " + output);
        for (Path cursor = output; cursor != null && cursor.startsWith(repository); cursor = cursor.getParent()) {
            if (Files.isRegularFile(cursor.resolve("modustro-artifact.yml"))) return cursor;
            if (cursor.equals(repository)) break;
        }
        return repository;
    }

    /**
     * Stage the complete generated set and publish it under a short artifact lock.
     * Normal publication replaces only requested destination files, including
     * after unpacking source archives without their build/ index. Optional
     * cleanup removes obsolete files recorded as owned by this generator.
     * Files belonging to other generators in the same *.gen tree are preserved.
     * Failures roll back all already changed paths.
     *
     * @param aContents absolute destination to source-text mapping
     * @param aCheck true to verify without changing files
     * @throws IOException on failed validation, write, or rollback
     */
    public void publish(Map<Path, String> aContents, boolean aCheck) throws IOException {
        publish(aContents, aCheck, false);
    }

    /**
     * Publish generated sources while optionally removing obsolete generator-owned outputs.
     * A missing ownership index does not block overwriting the requested generated paths.
     * @param aContents complete destination-to-source mapping for this invocation
     * @param aCheck verify the expected files without writing anything
     * @param aCleanupOutputFolderBeforeGeneration remove stale indexed outputs from this generator
     * @throws IOException on unsafe paths, file I/O or incomplete rollback
     */
    public void publish(Map<Path, String> aContents, boolean aCheck,
            boolean aCleanupOutputFolderBeforeGeneration) throws IOException {
        // Temporary self-hosted bootstrap mode isolates the ownership index
        // by run UUID; historical indexes cannot block a fresh generation.
        String bootstrapId = "1".equals(System.getenv("MODUSTRO_BOOTSTRAP_FRESH_GENERATION"))
                ? System.getenv("MODUSTRO_BOOTSTRAP_RUN_ID") : null;
        Path state;
        if (bootstrapId != null && !bootstrapId.isBlank()) {
            try { UUID.fromString(bootstrapId); }
            catch (IllegalArgumentException badId) {
                throw new IOException("Invalid bootstrap run ID", badId);
            }
            state = base.resolve("bootstrap-invocations").resolve(bootstrapId)
                    .resolve("generated-files-java.properties");
            Files.createDirectories(state.getParent());
        } else {
            state = base.resolve("generated-files-java.properties");
        }
        Map<String, String> requested = new LinkedHashMap<>();
        for (var entry : aContents.entrySet()) {
            Path target = entry.getKey().toAbsolutePath().normalize();
            validateGeneratedPath(target);
            String key = repository.relativize(target).toString().replace('\\', '/');
            if (requested.putIfAbsent(key, entry.getValue()) != null)
                throw new IOException("Duplicated generated source path: " + key);
        }
        try (FileChannel channel = FileChannel.open(base.resolve(".publish.lock"),
                StandardOpenOption.CREATE, StandardOpenOption.WRITE);
             FileLock ignored = channel.lock()) {
            Properties previous = new Properties();
            if (Files.isRegularFile(state)) {
                try (InputStream stream = Files.newInputStream(state)) { previous.load(stream); }
            }
            Map<String, String> hashes = new LinkedHashMap<>();
            for (var entry : requested.entrySet()) hashes.put(entry.getKey(), sha(entry.getValue()));
            for (String key : previous.stringPropertyNames()) {
                Path target = repository.resolve(key).normalize();
                validateGeneratedPath(target);
            }
            for (var entry : requested.entrySet()) {
                Path target = repository.resolve(entry.getKey());
                if (Files.isSymbolicLink(target))
                    throw new IOException("Refusing symlinked generated source " + target);
                if (aCheck && (!Files.isRegularFile(target)
                        || !sha(Files.readString(target)).equals(hashes.get(entry.getKey()))))
                    throw new IOException("Missing or outdated generated source: " + target);
            }
            if (aCheck) return;
            // Reuse byte-identical generated source files and their mtimes.
            Set<String> changedKeys = new TreeSet<>();
            for (var entry : requested.entrySet()) {
                Path destination = repository.resolve(entry.getKey());
                if (!Files.isRegularFile(destination)
                        || !sha(Files.readString(destination)).equals(hashes.get(entry.getKey())))
                    changedKeys.add(entry.getKey());
            }
            if (aCleanupOutputFolderBeforeGeneration)
                for (String key : previous.stringPropertyNames())
                    if (!requested.containsKey(key)) changedKeys.add(key);
            Path staging = run.resolve("staging");
            Path backups = run.resolve("tmp").resolve("rollback");
            Files.createDirectories(backups);
            Properties next = new Properties();
            if (!aCleanupOutputFolderBeforeGeneration)
                previous.forEach((key, value) -> next.setProperty((String) key, (String) value));
            hashes.forEach(next::setProperty);
            Path nextIndex = staging.resolve("generated-files-java.properties");
            try (OutputStream stream = Files.newOutputStream(nextIndex)) {
                next.store(stream, "Native Java Codegen ownership index");
            }
            for (var entry : requested.entrySet()) {
                Path destination = staging.resolve(entry.getKey());
                Files.createDirectories(destination.getParent());
                Files.writeString(destination, entry.getValue(), StandardCharsets.UTF_8);
            }
            List<String> changed = new ArrayList<>(changedKeys);
            Map<Path, Path> copied = new LinkedHashMap<>();
            for (String key : changed) {
                Path destination = repository.resolve(key);
                if (Files.isSymbolicLink(destination))
                    throw new IOException("Refusing symlinked generated source: " + destination);
                if (Files.isRegularFile(destination)) {
                    Path backup = backups.resolve(key);
                    Files.createDirectories(backup.getParent());
                    Files.copy(destination, backup, StandardCopyOption.COPY_ATTRIBUTES);
                    copied.put(destination, backup);
                }
            }
            List<Path> committed = new ArrayList<>();
            byte[] oldIndex = Files.isRegularFile(state) ? Files.readAllBytes(state) : null;
            try {
                for (String key : changed) {
                    Path destination = repository.resolve(key);
                    if (requested.containsKey(key)) {
                        Files.createDirectories(destination.getParent());
                        Files.move(staging.resolve(key), destination, StandardCopyOption.REPLACE_EXISTING);
                    } else Files.deleteIfExists(destination);
                    committed.add(destination);
                }
                Files.move(nextIndex, state, StandardCopyOption.REPLACE_EXISTING);
            } catch (Exception failure) {
                IOException rollbackFailure = null;
                for (int index = committed.size() - 1; index >= 0; index--) {
                    Path destination = committed.get(index);
                    try {
                        if (copied.containsKey(destination))
                            Files.move(copied.get(destination), destination, StandardCopyOption.REPLACE_EXISTING);
                        else Files.deleteIfExists(destination);
                    } catch (IOException rollback) {
                        if (rollbackFailure == null) rollbackFailure = new IOException("Codegen rollback incomplete", rollback);
                        else rollbackFailure.addSuppressed(rollback);
                    }
                }
                try {
                    if (oldIndex == null) Files.deleteIfExists(state);
                    else Files.write(state, oldIndex);
                } catch (IOException rollback) {
                    if (rollbackFailure == null) rollbackFailure = rollback;
                    else rollbackFailure.addSuppressed(rollback);
                }
                if (rollbackFailure != null) {
                    rollbackFailure.addSuppressed(failure);
                    throw rollbackFailure;
                }
                if (failure instanceof IOException io) throw io;
                throw new IOException("Codegen publication failed", failure);
            }
        }
    }

    /**
     * Reject output paths outside the declared artifact or through a symlink.
     * @param aTarget expected absolute generated source path
     * @throws IOException if the destination is not a safe *.gen source file
     */
    private void validateGeneratedPath(Path aTarget) throws IOException {
        Path target = aTarget.toAbsolutePath().normalize();
        if (!target.startsWith(artifact) || !target.startsWith(repository)
                || java.util.Arrays.stream(artifact.relativize(target).toString()
                        .replace('\\', '/').split("/"))
                        .noneMatch(part -> part.endsWith(".gen")))
            throw new IOException("Unsafe generated source destination " + target);
        for (Path current = target; current.startsWith(artifact);
                current = current.getParent()) {
            if (Files.isSymbolicLink(current))
                throw new IOException("Symlink in generated source path " + current);
        }
    }

    /**
     * Remove stale UUID workspaces without removing a concurrently running invocation.
     * @param aRepository repository root
     * @param aArtifact artifact containing the stale invocations
     * @param aGenerator one of the two Codegen names
     * @throws IOException on filesystem failure
     */
    public static void cleanupInactive(Path aRepository, Path aArtifact, String aGenerator)
            throws IOException {
        Path base = aRepository.toRealPath().resolve("build")
                .resolve(aRepository.toRealPath().relativize(aArtifact.toRealPath()))
                .resolve(aGenerator);
        if (!Files.isDirectory(base)) return;
        try (Stream<Path> children = Files.list(base)) {
            for (Path child : children.toList()) {
                if (!Files.isDirectory(child) || Files.isSymbolicLink(child)) continue;
                try { UUID.fromString(child.getFileName().toString()); }
                catch (IllegalArgumentException ignored) { continue; }
                try (var channel = FileChannel.open(child.resolve(".run.lock"),
                        StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
                    FileLock lock;
                    try { lock = channel.tryLock(); }
                    catch (java.nio.channels.OverlappingFileLockException ignored) { continue; }
                    if (lock == null) continue;
                    try (lock) { deleteTree(child); }
                }
            }
        }
    }

    /**
     * Remove only the caller's UUID work tree and release the invocation lock.
     * @throws IOException if unlocking or deleting the private directory fails
     */
    @Override public void close() throws IOException {
        IOException failure = null;
        // Retain the run lock until after deleting the private directory.
        // Otherwise an overlapping artifact cleanup can acquire this lock
        // and remove the same directory before our own cleanup finishes.
        try { deleteTree(run); }
        catch (IOException error) { failure = error; }
        try { runLock.release(); runChannel.close(); }
        catch (IOException error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
        if (failure != null) throw failure;
    }

    /**
     * Hash generated UTF-8 source deterministically.
     * @param aSource source text
     * @return lowercase SHA-256 hexadecimal digest
     */
    private static String sha(String aSource) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(aSource.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    /**
     * Delete a private work tree without following symbolic links.
     * @param aRoot private staging root
     * @throws IOException on deletion failure
     */
    private static void deleteTree(Path aRoot) throws IOException {
        if (!Files.exists(aRoot)) return;
        try (Stream<Path> walk = Files.walk(aRoot)) {
            for (Path path : walk.sorted(java.util.Comparator.reverseOrder()).toList())
                Files.deleteIfExists(path);
        }
    }
}
