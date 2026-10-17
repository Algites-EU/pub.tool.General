package eu.algites.tool.codegen.sdo.impl.standard;

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
    @AIaDataObject(schemaId = "test:parent", schemaVersion = 1)
    public interface AIigParent extends AIiDataObject {
        @AIaDataObjectField(name = "Name", presenceRequired = true)
        String getName();
    }
    /** Handwritten derived contract; parent metadata must remain visible. */
    @AIaDataObject(schemaId = "test:child", schemaVersion = 1)
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
    @AIaDataObject(schemaId = "test:container", schemaVersion = 1)
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

    /** The YAML-backed Java generation uses the selected interface/class and parameter naming conventions. */
    @AIaDataObject(schemaId = "test:catalog-customer", schemaVersion = 1)
    public interface AIigCatalogCustomer_1 extends AIiDataObject {
        @AIaDataObjectField(name = "Name", presenceRequired = true)
        String getName();
    }

    /** A naming configuration affects generated names, file suffixes and setter argument identifiers. */
    @Test
    public void AIcYamlNamingControlsGeneratedSdo() throws Exception {
        var locCatalog = eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1.standard("java");
        var locResult = new AIcSdoCodegenService().generate(AIigCatalogCustomer_1.class, "d",
                locCatalog, locCatalog, locCatalog);
        Assert.assertEquals(locResult.mutableInterface().typeName(), "AIigdCatalogCustomer_1");
        Assert.assertEquals(locResult.implementation().typeName(), "AIcgdCatalogCustomer_1");
        Assert.assertTrue(locResult.mutableInterface().relativePath().endsWith("AIigdCatalogCustomer_1.java"));
        Assert.assertTrue(locResult.implementation().relativePath().endsWith("AIcgdCatalogCustomer_1.java"));
        Assert.assertTrue(locResult.mutableInterface().source().contains("setName(java.lang.String aName)"));
        Assert.assertTrue(locResult.implementation().source().contains("setName(java.lang.String aName)"));
    }

    /** Generated Java SmartDOs honor interface defaults and explicit getter overrides. */
    @AIaDataObject(schemaId = "test:read-policy", schemaVersion = 1)
    @eu.algites.lib.data.smartdataobject.AIaSmartDataObject(allowNonPresentRead = true)
    public interface AIigReadPolicy extends AIiDataObject {
        @AIaDataObjectField(name = "Soft", presenceRequired = true)
        String getSoft();

        @AIaDataObjectField(name = "Strict", presenceRequired = true)
        @eu.algites.lib.data.smartdataobject.AIaSmartDataObjectField(allowNonPresentRead = false)
        String getStrict();
    }

    @Test
    public void AIcGeneratedJavaHonorsSmartReadPolicy() throws Exception {
        var locGenerated = new AIcSdoCodegenService().generate(AIigReadPolicy.class, "d");
        Path locRoot = Files.createTempDirectory("sdo-policy-java-");
        Path locClasses = Files.createDirectory(locRoot.resolve("classes"));
        var locFiles = new java.util.ArrayList<String>();
        for (var locUnit : java.util.List.of(locGenerated.mutableInterface(), locGenerated.implementation())) {
            Path locFile = locRoot.resolve(locUnit.relativePath());
            Files.createDirectories(locFile.getParent());
            Files.writeString(locFile, locUnit.source());
            locFiles.add(locFile.toString());
        }
        var locArgs = new java.util.ArrayList<>(java.util.List.of(
                "-cp", System.getProperty("java.class.path"), "-d", locClasses.toString()));
        locArgs.addAll(locFiles);
        Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                locArgs.toArray(String[]::new)), 0);
        try (var locLoader = new URLClassLoader(new java.net.URL[] {locClasses.toUri().toURL()},
                getClass().getClassLoader())) {
            var locType = locLoader.loadClass("eu.algites.tool.codegen.sdo.AIcgdReadPolicy");
            var locInstance = locType.getConstructor().newInstance();
            Assert.assertNull(locType.getMethod("getSoft").invoke(locInstance));
            Assert.assertNull(locType.getMethod("get_Soft").invoke(locInstance));
            Assert.assertEquals(locType.getMethod("isPresent_Soft").invoke(locInstance), false);
            Assert.assertEquals(locType.getMethod("is_ByRawValuesValid").invoke(locInstance), false);
            var locException = Assert.expectThrows(InvocationTargetException.class,
                    () -> locType.getMethod("getStrict").invoke(locInstance));
            Assert.assertTrue(locException.getCause() instanceof IllegalStateException);
        }
    }

    @AIaDataObject(schemaId = "test:inferred-name", schemaVersion = 1)
    public interface AIigInferredName extends AIiDataObject {
        @AIaDataObjectField(presenceRequired = true)
        String getInferred();
    }

    @Test
    public void AIcInfersOmittedFieldNameFromGetter() {
        var locGenerated = new AIcSdoCodegenService().generate(AIigInferredName.class, "d");
        Assert.assertTrue(locGenerated.implementation().source().contains("get_EffectiveField(\"Inferred\")"));
        Assert.assertTrue(locGenerated.implementation().source().contains("set_RawField(\"Inferred\""));
    }

}
