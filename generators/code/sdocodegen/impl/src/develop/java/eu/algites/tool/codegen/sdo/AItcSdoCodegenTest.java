package eu.algites.tool.codegen.sdo;

import eu.algites.lib.data.dataobject.AIaDataObject;
import eu.algites.lib.data.dataobject.AIaDataObjectField;
import eu.algites.lib.data.dataobject.AIiDataObject;
import java.lang.reflect.InvocationTargetException;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.tools.ToolProvider;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Independent JVM tests of the schema-free generated SmartDataObject hierarchy. */
public final class AItcSdoCodegenTest {
    /** Handwritten read-only base contract. */
    @AIaDataObject(id = "test:parent", version = 1)
    public interface AIigParent extends AIiDataObject {
        @AIaDataObjectField(name = "Name", presenceRequired = true)
        String getName();
    }
    /** Handwritten derived contract; parent metadata must remain visible. */
    @AIaDataObject(id = "test:child", version = 1)
    public interface AIigChild extends AIigParent {
        @AIaDataObjectField(name = "Count", presenceRequired = true)
        Integer getCount();
    }

    /** New types must preserve the exact inheritance and work with real pub.lib.General runtime. */
    @Test
    public void AIcGeneratesAndCompilesInheritedTypes() throws Exception {
        var locGenerator = new AIcSdoCodegenService();
        var locParent = locGenerator.generate(AIigParent.class, "d");
        var locChild = locGenerator.generate(AIigChild.class, "d");
        Path locDirectory = Files.createTempDirectory("sdocodegen-java-test");
        Path locOutput = locDirectory.resolve("classes");
        Files.createDirectories(locOutput);
        java.util.List<String> locFiles = new java.util.ArrayList<>();
        for (var locResult : java.util.List.of(locParent, locChild)) {
            for (var locUnit : java.util.List.of(locResult.mutableInterface(), locResult.implementation())) {
                Path locFile = locDirectory.resolve(locUnit.relativePath());
                Files.createDirectories(locFile.getParent());
                Files.writeString(locFile, locUnit.source());
                locFiles.add(locFile.toString());
            }
        }
        java.util.List<String> locOptions = new java.util.ArrayList<>(java.util.List.of(
                "-cp", System.getProperty("java.class.path"), "-d", locOutput.toString()));
        locOptions.addAll(locFiles);
        Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                locOptions.toArray(String[]::new)), 0);
        try (var locLoader = new URLClassLoader(new java.net.URL[] { locOutput.toUri().toURL() },
                getClass().getClassLoader())) {
            Class<?> locType = locLoader.loadClass("eu.algites.tool.codegen.sdo.AIcgdChild");
            Assert.assertTrue(locLoader.loadClass("eu.algites.tool.codegen.sdo.AIcgdParent").isAssignableFrom(locType));
            Object locInstance = locType.getConstructor().newInstance();
            Assert.assertEquals(locType.getMethod("is_ByRawValuesValid").invoke(locInstance), false);
            locType.getMethod("setName", String.class).invoke(locInstance, "Alpha");
            locType.getMethod("setCount", Integer.class).invoke(locInstance, 7);
            Assert.assertEquals(locType.getMethod("getName").invoke(locInstance), "Alpha");
            Assert.assertEquals(locType.getMethod("getCount").invoke(locInstance), 7);
            Assert.assertEquals(locType.getMethod("is_ByRawValuesValid").invoke(locInstance), true);
            locType.getMethod("unset_Count").invoke(locInstance);
            Assert.assertEquals(locType.getMethod("is_ByRawValuesValid").invoke(locInstance), false);
        }
    }

    /** A nested read contract is exposed covariantly as a mutable SDO contract. */
    @AIaDataObject(id = "test:container", version = 1)
    public interface AIigContainer extends AIiDataObject {
        @AIaDataObjectField(name = "Child", presenceRequired = true)
        AIigChild getChild();
    }

    /** Compiles real generated source and checks nested getter/setter reflection signatures. */
    @Test
    public void AIcCovariantNestedDataObject() throws Exception {
        var locGenerator = new AIcSdoCodegenService();
        Path locRoot = Files.createTempDirectory("sdo-nested-java-");
        Path locClasses = Files.createDirectory(locRoot.resolve("classes"));
        var locFiles = new java.util.ArrayList<String>();
        for (var locContract : java.util.List.of(AIigParent.class, AIigChild.class, AIigContainer.class)) {
            var locSources = locGenerator.generate(locContract, "d");
            for (var locSource : java.util.List.of(locSources.mutableInterface(), locSources.implementation())) {
                Path locFile = locRoot.resolve(locSource.relativePath());
                Files.createDirectories(locFile.getParent());
                Files.writeString(locFile, locSource.source());
                locFiles.add(locFile.toString());
            }
            if (locContract == AIigContainer.class) {
                Assert.assertTrue(locSources.mutableInterface().source().contains("AIigdChild getChild()"));
                Assert.assertTrue(locSources.mutableInterface().source().contains("setChild("));
                Assert.assertTrue(locSources.mutableInterface().source().contains("AIigdChild get_Child()"));
            }
        }
        var locArgs = new java.util.ArrayList<>(java.util.List.of(
                "-cp", System.getProperty("java.class.path"), "-d", locClasses.toString()));
        locArgs.addAll(locFiles);
        Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                locArgs.toArray(String[]::new)), 0);
        try (var locLoader = new URLClassLoader(new java.net.URL[] {locClasses.toUri().toURL()},
                getClass().getClassLoader())) {
            var locMutableChild = locLoader.loadClass("eu.algites.tool.codegen.sdo.AIigdChild");
            var locContainer = locLoader.loadClass("eu.algites.tool.codegen.sdo.AIcgdContainer");
            var locChild = locLoader.loadClass("eu.algites.tool.codegen.sdo.AIcgdChild")
                    .getConstructor().newInstance();
            Assert.assertEquals(locContainer.getMethod("getChild").getReturnType(), locMutableChild);
            Assert.assertEquals(locContainer.getMethod("setChild", locMutableChild).getParameterTypes()[0], locMutableChild);
            var locInstance = locContainer.getConstructor().newInstance();
            locContainer.getMethod("setChild", locMutableChild).invoke(locInstance, locChild);
            Assert.assertEquals(locContainer.getMethod("getChild").invoke(locInstance), locChild);
            Assert.assertEquals(locContainer.getMethod("get_Child").invoke(locInstance), locChild);
        }
    }

    /** Python implementation is exercised by the same Gradle verification task. */
    @Test
    public void AIcPythonImplementationAndRuntime() throws Exception {
        Path locRoot = Path.of("").toAbsolutePath();
        String locRelative = "generators/code/sdocodegen/impl/src/develop/python/test_sdocodegen.py";
        while (locRoot != null && !Files.isRegularFile(locRoot.resolve(locRelative))) {
            locRoot = locRoot.getParent();
        }
        if (locRoot == null) throw new IllegalStateException("Cannot locate SDO Python test suite");
        var locPython = System.getenv().getOrDefault("ALGITES_PYTHON_EXECUTABLE", "python3");
        var locProcess = new ProcessBuilder(locPython, "-m", "pytest", "-q",
                locRoot.resolve(locRelative).toString()).directory(locRoot.toFile()).redirectErrorStream(true);
        var locPaths = new java.util.ArrayList<String>();
        for (String locArtifact : java.util.List.of("intf", "impl")) {
            locPaths.add(locRoot.resolve("generators/code/sdocodegen/" + locArtifact + "/src/product/python").toString());
        }
        /* The cross-stage integration test reads Defs sources from this checkout; no production dependency is introduced. */
        for (String locArtifact : java.util.List.of("intf", "impl")) {
            locPaths.add(locRoot.resolve("generators/code/defscodegen/" + locArtifact + "/src/product/python").toString());
        }
        String locDependencies = System.getenv("MODUSTRO_SDO_PYTHON_DEPENDENCIES");
        if (locDependencies != null && !locDependencies.isBlank()) locPaths.add(locDependencies);
        String locPrevious = System.getenv("PYTHONPATH");
        if (locPrevious != null && !locPrevious.isBlank()) locPaths.add(locPrevious);
        locProcess.environment().put("PYTHONPATH", String.join(java.io.File.pathSeparator, locPaths));
        locProcess.environment().put("PYTHONPYCACHEPREFIX", locRoot.resolve("build/run/sdo-parity/pycache").toString());
        Process locStarted = locProcess.start();
        String locOutput = new String(locStarted.getInputStream().readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        Assert.assertEquals(locStarted.waitFor(), 0, locOutput);
    }

    /** Reject ambiguous inherited metadata before writing any generated file. */
    @Test
    public void AIcRejectsConflictingInheritance() {
        Assert.expectThrows(IllegalArgumentException.class,
                () -> new AIcSdoCodegenService().generate(AIigBadChild.class, "d"));
    }

    /** Intentionally incompatible redeclaration of an inherited field. */
    public interface AIigBadChild extends AIigParent {
        @Override
        @AIaDataObjectField(name = "Name", allowsNull = true)
        String getName();
    }

    /** An alternate implementation marker changes both names without changing the read contract. */
    @Test
    public void AIcSupportsDifferentImplementationMarker() {
        var locResult = new AIcSdoCodegenService().generate(AIigParent.class, "sdo");
        Assert.assertEquals(locResult.mutableInterface().typeName(), "AIigsdoParent");
        Assert.assertEquals(locResult.implementation().typeName(), "AIcgsdoParent");
        Assert.expectThrows(IllegalArgumentException.class,
                () -> new AIcSdoCodegenService().generate(AIigParent.class, "../"));
    }
}
