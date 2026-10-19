package eu.algites.tool.codegen.sdo.impl.standard;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URI;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import javax.tools.DiagnosticCollector;
import javax.tools.FileObject;
import javax.tools.ForwardingJavaFileManager;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;

/** Compile a generated contract source tree in memory for reflection-based SDO generation. */
final class AIcSdoContractSourceLoader implements AutoCloseable {
    private final Path root;
    private final URLClassLoader dependencies;
    private final ClassLoader loader;

    private AIcSdoContractSourceLoader(Path aRoot, URLClassLoader aDependencies, ClassLoader aLoader) {
        root = aRoot;
        dependencies = aDependencies;
        loader = aLoader;
    }

    /** Compiles generated read interfaces and enums together; stale DTO classes are never inputs. */
    static AIcSdoContractSourceLoader compile(Path aSourceRoot, List<Path> aDependencyPaths) {
        Objects.requireNonNull(aSourceRoot, "source root");
        Objects.requireNonNull(aDependencyPaths, "dependency classpath");
        try {
            Path locRoot = aSourceRoot.toRealPath();
            if (!Files.isDirectory(locRoot)) throw new IllegalArgumentException("Not a source root: " + locRoot);
            List<Path> locSources;
            try (var locStream = Files.walk(locRoot)) {
                locSources = locStream.filter(Files::isRegularFile)
                        .filter(aFile -> aFile.getFileName().toString().matches("(?:AIig|AIi|AIng)[A-Za-z0-9_$]+\\.java"))
                        .sorted().toList();
            }
            if (locSources.isEmpty()) throw new IllegalArgumentException("No Java contract sources: " + locRoot);
            var locCompiler = ToolProvider.getSystemJavaCompiler();
            if (locCompiler == null) throw new IllegalStateException(
                    "Java source-based SDO codegen requires a JDK (javax.tools.JavaCompiler), not a JRE");
            var locClasspath = new ArrayList<String>();
            String locRuntimePath = System.getProperty("java.class.path", "");
            if (!locRuntimePath.isBlank()) locClasspath.add(locRuntimePath);
            var locUrls = new ArrayList<URL>();
            for (Path locDependency : aDependencyPaths) {
                Path locPath = locDependency.toRealPath();
                locClasspath.add(locPath.toString());
                locUrls.add(locPath.toUri().toURL());
            }
            var locDiagnostics = new DiagnosticCollector<JavaFileObject>();
            Map<String, byte[]> locBytecode = new LinkedHashMap<>();
            try (StandardJavaFileManager locStandard = locCompiler.getStandardFileManager(
                    locDiagnostics, java.util.Locale.ROOT, StandardCharsets.UTF_8);
                 var locManager = new AIcMemoryFileManager(locStandard, locBytecode)) {
                var locUnits = new ArrayList<JavaFileObject>();
                for (Path locSource : locSources) locUnits.add(new AIcSourceFile(locSource));
                var locOptions = new ArrayList<>(List.of("-proc:none", "-encoding", "UTF-8"));
                if (!locClasspath.isEmpty()) {
                    locOptions.add("-classpath");
                    locOptions.add(String.join(java.io.File.pathSeparator, locClasspath));
                }
                boolean locSuccess = Boolean.TRUE.equals(locCompiler.getTask(null, locManager,
                        locDiagnostics, locOptions, null, locUnits).call());
                if (!locSuccess) {
                    StringBuilder locMessage = new StringBuilder("Cannot compile DO sources for SDO reflection:\n");
                    locDiagnostics.getDiagnostics().forEach(aDiagnostic -> locMessage.append(aDiagnostic).append('\n'));
                    throw new IllegalArgumentException(locMessage.toString());
                }
            }
            URLClassLoader locDependencies = new URLClassLoader(locUrls.toArray(URL[]::new),
                    AIcSdoContractSourceLoader.class.getClassLoader());
            ClassLoader locLoader = new ClassLoader(locDependencies) {
                @Override
                protected synchronized Class<?> loadClass(String aName, boolean aResolve) throws ClassNotFoundException {
                    Class<?> locFound = findLoadedClass(aName);
                    if (locFound == null) {
                        byte[] locData = locBytecode.get(aName);
                        locFound = locData == null ? super.loadClass(aName, false)
                                : defineClass(aName, locData, 0, locData.length);
                    }
                    if (aResolve) resolveClass(locFound);
                    return locFound;
                }
            };
            return new AIcSdoContractSourceLoader(locRoot, locDependencies, locLoader);
        } catch (IOException locError) {
            throw new IllegalArgumentException("Cannot read Java source tree or dependencies: " + aSourceRoot, locError);
        }
    }

    /** Reject files outside the configured source root, including symlink escapes. */
    Path validate(Path aSource) {
        try {
            Path locFile = (aSource.isAbsolute() ? aSource : root.resolve(aSource)).toRealPath();
            if (!locFile.startsWith(root) || !locFile.getFileName().toString().endsWith(".java")
                    || !Files.isRegularFile(locFile))
                throw new IllegalArgumentException("Invalid DO contract source: " + aSource);
            return locFile;
        } catch (IOException locError) {
            throw new IllegalArgumentException("Cannot read DO contract source: " + aSource, locError);
        }
    }

    /** Locate the compiled contract using its package-root-relative Java source path. */
    Class<?> load(Path aSource) {
        Path locFile = validate(aSource);
        String locName = root.relativize(locFile).toString().replace('\\', '.')
                .replace('/', '.').replaceFirst("\\.java$", "");
        try {
            return Class.forName(locName, false, loader);
        } catch (ClassNotFoundException locError) {
            throw new IllegalArgumentException("Compiled DO source has no matching contract class: " + locFile, locError);
        }
    }

    @Override
    public void close() {
        try { dependencies.close(); }
        catch (IOException locError) { throw new IllegalStateException("Cannot close Java contract classpath", locError); }
    }

    private static final class AIcSourceFile extends SimpleJavaFileObject {
        private final Path source;
        AIcSourceFile(Path aSource) { super(aSource.toUri(), Kind.SOURCE); source = aSource; }
        @Override
        public CharSequence getCharContent(boolean aIgnoreEncodingErrors) throws IOException {
            return Files.readString(source, StandardCharsets.UTF_8);
        }
    }

    private static final class AIcMemoryFileManager extends ForwardingJavaFileManager<StandardJavaFileManager> {
        private final Map<String, byte[]> output;
        AIcMemoryFileManager(StandardJavaFileManager aDelegate, Map<String, byte[]> aOutput) {
            super(aDelegate);
            output = aOutput;
        }
        @Override
        public JavaFileObject getJavaFileForOutput(Location aLocation, String aName,
                JavaFileObject.Kind aKind, FileObject aSibling) {
            return new SimpleJavaFileObject(URI.create("mem:///" + aName.replace('.', '/') + aKind.extension), aKind) {
                @Override
                public OutputStream openOutputStream() {
                    return new ByteArrayOutputStream() {
                        @Override
                        public void close() throws IOException {
                            super.close();
                            if (output.putIfAbsent(aName, toByteArray()) != null)
                                throw new IOException("Duplicate compiled class: " + aName);
                        }
                    };
                }
            };
        }
    }
}
