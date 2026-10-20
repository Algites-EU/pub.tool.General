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
        @AIaDataObjectField(fieldName = "Name", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED)
        String getName();
    }
    /** Handwritten derived contract; parent metadata must remain visible. */
    @AIaDataObject(schemaId = "test:child", schemaVersion = 1)
    public interface AIigChild extends AIigParent {
        @AIaDataObjectField(fieldName = "Count", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED)
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
            Class<?> locType = locLoader.loadClass(locChild.implementation().fullyQualifiedTypeName());
            Assert.assertTrue(locLoader.loadClass(locParent.implementation().fullyQualifiedTypeName()).isAssignableFrom(locType));
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

    /** Java sources alone are sufficient: reflection is performed on in-memory compiled contracts. */
    @Test
    public void AIcGenerateFromUncompiledSourcesWithInheritance() throws Exception {
        Path locRoot = Files.createTempDirectory("sdo-uncompiled-");
        Path locPackage = locRoot.resolve("example/contract");
        Files.createDirectories(locPackage);
        Path locBase = locPackage.resolve("AIigBase_1.java");
        Path locChild = locPackage.resolve("AIigChild_1.java");
        Files.writeString(locBase, """
                package example.contract;
                @eu.algites.lib.data.dataobject.AIaDataObject(schemaId = "example.base", schemaVersion = 1)
                public interface AIigBase_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
                    @eu.algites.lib.data.dataobject.AIaDataObjectField(fieldName = "Name")
                    String getName();
                }
                """);
        Files.writeString(locChild, """
                package example.contract;
                @eu.algites.lib.data.dataobject.AIaDataObject(schemaId = "example.child", schemaVersion = 1)
                public interface AIigChild_1 extends AIigBase_1 {
                    @eu.algites.lib.data.dataobject.AIaDataObjectField(fieldName = "Count")
                    Integer getCount();
                }
                """);
        var locGenerated = new AIcSdoCodegenService().generateFromSources(locRoot,
                java.util.List.of(locBase, locChild), "d", java.util.List.of());
        Assert.assertEquals(locGenerated.size(), 2);
        Assert.assertTrue(locGenerated.get(locChild.toRealPath()).mutableInterface().source()
                .contains("AIigdBase_1"));
        Assert.assertTrue(locGenerated.get(locChild.toRealPath()).implementation().source()
                .contains("AIcgdBase_1"));
    }

    /** A Java compile error must fail with a useful diagnostic instead of using stale classes. */
    @Test
    public void AIcRejectInvalidSourceInsteadOfLoadingStaleClass() throws Exception {
        Path locRoot = Files.createTempDirectory("sdo-invalid-source-");
        Path locSource = locRoot.resolve("AIigBroken_1.java");
        Files.writeString(locSource, "public interface AIigBroken_1 { this is not Java; }");
        Assert.expectThrows(IllegalArgumentException.class,
                () -> new AIcSdoCodegenService().generateFromSources(locRoot,
                        java.util.List.of(locSource), "d", java.util.List.of()));
    }

    /** A nested read contract is exposed covariantly as a mutable SDO contract. */
    @AIaDataObject(schemaId = "test:container", schemaVersion = 1)
    public interface AIigContainer extends AIiDataObject {
        @AIaDataObjectField(fieldName = "Child", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED)
        AIigChild getChild();
    }

    /** Compiles real generated source and checks nested getter/setter reflection signatures. */
    @Test
    public void AIcCovariantNestedDataObject() throws Exception {
        var locGenerator = new AIcSdoCodegenService();
        Path locRoot = Files.createTempDirectory("sdo-nested-java-");
        Path locClasses = Files.createDirectory(locRoot.resolve("classes"));
        var locFiles = new java.util.ArrayList<String>();
        var locParentSources = locGenerator.generate(AIigParent.class, "d");
        var locChildSources = locGenerator.generate(AIigChild.class, "d");
        var locContainerSources = locGenerator.generate(AIigContainer.class, "d");
        for (var locSources : java.util.List.of(locParentSources, locChildSources, locContainerSources)) {
            for (var locSource : java.util.List.of(locSources.mutableInterface(), locSources.implementation())) {
                Path locFile = locRoot.resolve(locSource.relativePath());
                Files.createDirectories(locFile.getParent());
                Files.writeString(locFile, locSource.source());
                locFiles.add(locFile.toString());
            }
            if (locSources == locContainerSources) {
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
            var locMutableChild = locLoader.loadClass(locChildSources.mutableInterface().fullyQualifiedTypeName());
            var locContainer = locLoader.loadClass(locContainerSources.implementation().fullyQualifiedTypeName());
            var locChild = locLoader.loadClass(locChildSources.implementation().fullyQualifiedTypeName())
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
        @AIaDataObjectField(fieldName = "Name", allowsNull = true)
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
        @AIaDataObjectField(fieldName = "Name", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED)
        String getName();
    }

    /** A YAML naming catalog configures the common read-contract role independently of schema technology. */
    @Test
    public void AIcYamlNamingControlsGeneratedSdo() throws Exception {
        var locCatalog = eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1.standard("java");
        var locInputNames = locCatalog.withRoles(java.util.Map.of(
                "common", "algites-java-gen-intf-versioned_1"));
        var locMutableNames = locCatalog.withRoles(java.util.Map.of(
                "common", "algites-java-gen-data-intf-versioned_1"));
        var locConcreteNames = locCatalog.withRoles(java.util.Map.of(
                "common", "algites-java-gen-data-class-versioned_1"));
        var locResult = new AIcSdoCodegenService().generate(AIigCatalogCustomer_1.class, "d",
                locInputNames, locMutableNames, locConcreteNames);
        Assert.assertEquals(locResult.mutableInterface().typeName(), "AIigdCatalogCustomer_1");
        Assert.assertEquals(locResult.implementation().typeName(), "AIcgdCatalogCustomer_1");
        Assert.assertTrue(locResult.mutableInterface().relativePath().endsWith("AIigdCatalogCustomer_1.java"));
        Assert.assertTrue(locResult.implementation().relativePath().endsWith("AIcgdCatalogCustomer_1.java"));
        Assert.assertTrue(locResult.mutableInterface().source().contains("setName(java.lang.String aName)"));
        Assert.assertTrue(locResult.implementation().source().contains("setName(java.lang.String aName)"));
    }

    /** A technology-only YAML DataObject generates its SDO types without any common role binding. */
    @AIaDataObject(schemaId = "test:yaml-customer", schemaVersion = 1,
            namingConvention = "algites-java-gen-yaml-intf-versioned_1")
    public interface AIig_yCatalogCustomer_1
            extends eu.algites.lib.data.dataobject.yamldefs.AIiYamlDataObject {
        /** Returns the customer name described by the handwritten YAML contract. */
        @AIaDataObjectField(fieldName = "Name",
                presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED)
        String getName();
    }

    /** Technology-specific output role selection must not implicitly require a common interface. */
    @Test
    public void AIcYamlTechnologyRoleDoesNotRequireCommon() throws Exception {
        var locCatalog = eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1.standard("java");
        var locInputNames = locCatalog.withRoles(java.util.Map.of(
                "yamldefs", "algites-java-gen-yaml-intf-versioned_1"));
        var locMutableNames = locCatalog.withRoles(java.util.Map.of(
                "yamldefs", "algites-java-gen-data-yaml-intf-versioned_1"));
        var locConcreteNames = locCatalog.withRoles(java.util.Map.of(
                "yamldefs", "algites-java-gen-data-yaml-class-versioned_1"));
        var locResult = new AIcSdoCodegenService().generate(AIig_yCatalogCustomer_1.class, "d",
                locInputNames, locMutableNames, locConcreteNames);
        Assert.assertEquals(locResult.mutableInterface().typeName(), "AIigd_yCatalogCustomer_1");
        Assert.assertEquals(locResult.implementation().typeName(), "AIcgd_yCatalogCustomer_1");
        Assert.assertTrue(locResult.mutableInterface().source().contains(
                "namingConvention = \"algites-java-gen-data-yaml-intf-versioned_1\""));
        Assert.assertTrue(locResult.implementation().source().contains(
                "namingConvention = \"algites-java-gen-data-yaml-class-versioned_1\""));
    }

    /** Generated Java SmartDOs honor interface defaults and explicit getter overrides. */
    @AIaDataObject(schemaId = "test:read-policy", schemaVersion = 1)
    @eu.algites.lib.data.smartdataobject.AIaSmartDataObject(allowNonPresentRead = true)
    public interface AIigReadPolicy extends AIiDataObject {
        @AIaDataObjectField(fieldName = "Soft", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED)
        String getSoft();

        @AIaDataObjectField(fieldName = "Strict", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED)
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
            var locType = locLoader.loadClass(locGenerated.implementation().fullyQualifiedTypeName());
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
        @AIaDataObjectField(presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED)
        String getInferred();
    }

    @Test
    public void AIcInfersOmittedFieldNameFromGetter() {
        var locGenerated = new AIcSdoCodegenService().generate(AIigInferredName.class, "d");
        Assert.assertTrue(locGenerated.implementation().source().contains("get_EffectiveField(\"Inferred\")"));
        Assert.assertTrue(locGenerated.implementation().source().contains("set_RawField(\"Inferred\""));
    }


    /** Handwritten contract with both explicit and synthesized localization metadata. */
    @AIaDataObject(schemaId = "test:localization", schemaVersion = 1)
    public interface AIiLocalizedDocument_1 extends AIiDataObject {
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(
                label = "Document title",
                labels = {@eu.algites.lib.common.object.props.labels.AIaFieldLabel.Entry(
                        roleCode = "field.description", label = "Displayed document title.")})
        @AIaDataObjectField(fieldName = "DocumentTitle")
        String getDocumentTitle();

        @AIaDataObjectField(fieldName = "CertificatePrivateKey")
        String getCertificatePrivateKey();

        /** Field using a dynamically selected, discoverable label provider. */
        @eu.algites.lib.common.object.props.labels.AIaFieldLabel(
                labelResolver = @eu.algites.lib.factory.cpdiscovery.AIaCategoryProviderFactoryDefinition(
                    factoryClass = eu.algites.lib.common.object.props.labels.AIiFieldLabelResolverFactory.class,
                    factoryCategory = "localized"))
        @AIaDataObjectField(fieldName = "Localized")
        String getLocalized();
    }

    /** Verify that SDO interfaces keep custom resolvers and synthesize missing field labels. */
    @Test
    public void AIcPreservesFieldLabelMetadata() {
        String locSource = new AIcSdoCodegenService()
                .generate(AIiLocalizedDocument_1.class, "d").mutableInterface().source();
        Assert.assertTrue(locSource.contains("Document title"));
        Assert.assertTrue(locSource.contains("factoryCategory = \"localized\""));
        Assert.assertTrue(locSource.contains("AIiFieldLabelResolverFactory.class"));
        Assert.assertTrue(locSource.contains("field.description"));
        Assert.assertTrue(locSource.contains("Displayed document title."));
        Assert.assertTrue(locSource.contains("Certificate private key"));
    }


    /** Read contract with an explicit JSON Schema lineage and one annotated property. */
    @AIaDataObject(schemaId = "test:technology-json", schemaVersion = 1)
    public interface AIigTechnologyJson_1 extends eu.algites.lib.data.dataobject.jsondefs.AIiJsonDataObject {
        /** Read the stable JSON field identifier. */
        @AIaDataObjectField(fieldName = "Key")
        String getKey();
    }

    /** Read contract with an explicit YAML definition lineage. */
    @AIaDataObject(schemaId = "test:technology-yaml", schemaVersion = 1)
    public interface AIigTechnologyYaml_1 extends eu.algites.lib.data.dataobject.yamldefs.AIiYamlDataObject {
        /** Read the stable YAML field identifier. */
        @AIaDataObjectField(fieldName = "Key")
        String getKey();
    }

    /** Global XML element contract with a separate XML QName annotation. */
    @AIaDataObject(schemaId = "test:technology-xml", schemaVersion = 1)
    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject(
            definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT,
            namespace = "urn:test:xml", namespaceLocalName = "test")
    public interface AIigTechnologyXml_1 extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject {
        /** XML element field with independent wire QName metadata. */
        @AIaDataObjectField(fieldName = "Key")
        @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField(
                namespace = "urn:test:xml", namespaceLocalName = "key")
        String getKey();
    }

    /** Verify all technology markers and concrete inheritance roots survive generation. */
    @Test
    public void AIcPreservesTechnologySpecificSdoLineages() {
        var locGenerator = new AIcSdoCodegenService();
        for (var locCase : java.util.List.of(
                new Object[] {AIigTechnologyJson_1.class, "Json"},
                new Object[] {AIigTechnologyYaml_1.class, "Yaml"},
                new Object[] {AIigTechnologyXml_1.class, "Xml"})) {
            Class<?> locRead = (Class<?>) locCase[0];
            String locTechnology = (String) locCase[1];
            var locOutput = locGenerator.generate(locRead, "d");
            Assert.assertTrue(locOutput.mutableInterface().source().contains(
                    "AIi" + locTechnology + "SmartDataObject"));
            Assert.assertTrue(locOutput.implementation().source().contains(
                    "AIc" + locTechnology + "SmartDataObject"));
        }
        var locXml = locGenerator.generate(AIigTechnologyXml_1.class, "d").mutableInterface().source();
        Assert.assertTrue(locXml.contains("AIaXmlDataObject("));
        Assert.assertTrue(locXml.contains("namespaceLocalName = \"test\""));
        Assert.assertTrue(locXml.contains("AIaXmlDataObjectField("));
        Assert.assertTrue(locXml.contains("namespaceLocalName = \"key\""));
        Assert.assertFalse(locXml.contains("AIaOpenChoice"));
    }
}
