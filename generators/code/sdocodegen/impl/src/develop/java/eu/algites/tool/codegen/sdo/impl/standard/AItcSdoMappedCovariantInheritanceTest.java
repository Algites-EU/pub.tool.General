package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.lib.common.list.AIiMultiMappedList;
import eu.algites.lib.data.dataobject.AIaDataObjectField;
import eu.algites.lib.data.dataobject.AIaKeyDefinition;
import eu.algites.lib.data.dataobject.AIiDataObject;
import eu.algites.lib.data.dataobject.AIaDataObject;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.sdo.AIcdSdoGenerationResult;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.tools.ToolProvider;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verify generic setter inheritance when a neutral descendant refines a
 * {@link List} into an indexed {@link AIiMultiMappedList}.
 *
 * <p>The regression is about generated source <em>compilation</em>, not merely
 * successful generation: the concrete getter must implement both the read-only
 * derived interface and the generic writable parent contract.
 *
 * @author linhart1
 */
public final class AItcSdoMappedCovariantInheritanceTest {
    /** Schema-neutral value read contract. */
    @AIaDataObject
    public interface AIigMappedBaseRule_1 extends AIiDataObject { }

    /** Neutral value-contract descendant refining the common rule. */
    public interface AIigMappedRule_1 extends AIigMappedBaseRule_1 { }

    /** Schema-neutral list; its mutable counterpart requires a type parameter. */
    @AIaDataObject
    public interface AIigMappedParent_1 extends AIiDataObject {
        /** @return all rules in schema order */
        @AIaDataObjectField(dataFieldName = "Rule")
        List<? extends AIigMappedBaseRule_1> getRuleList();
    }

    /** Neutral indexed collection refining the inherited list getter. */
    public interface AIigMappedChild_1 extends AIigMappedParent_1 {
        /** @return the same rules, with typed named indexes */
        @AIaKeyDefinition(name = "ByRuleName", fields = {"name"}, required = true)
        AIiMultiMappedList<? extends AIigMappedRule_1> getRuleList();
    }

    /** A sealed-choice-like marker without DataObject semantics or SDO output. */
    public interface AIigNameFragmentsSegmentChoice_1 { }

    /** Legacy-compatible helper with DO ancestry but no own/inherited SDO annotation. */
    public interface AIigNameFragmentsSegmentValueContent_1 extends AIiDataObject { }

    /** An ordinary DataObject referencing two auxiliary types without writable counterparts. */
    @AIaDataObject
    public interface AIigChoiceContainer_1 extends AIiDataObject {
        /** @return zero or more immutable choice values */
        @AIaDataObjectField(dataFieldName = "Segments")
        List<? extends AIigNameFragmentsSegmentChoice_1> getSegmentsList();

        /** @return an unannotated helper that must retain its read-only name */
        @AIaDataObjectField(dataFieldName = "Content")
        AIigNameFragmentsSegmentValueContent_1 getContent();
    }

    /**
     * An auxiliary Java choice and an unannotated DataObject helper cannot acquire
     * a phantom AIigd type merely because their names fit the selected profile.
     * The complete generated SDO pair must compile against the original helpers.
     *
     * @throws IOException if temporary regression files cannot be written
     */
    @Test
    public void testAuxiliaryChoiceTypesKeepReadOnlyReferences() throws IOException {
        var locService = new AIcSdoCodegenService();
        Assert.assertFalse(AIcSdoCodegenService.isSdoInput(AIigNameFragmentsSegmentChoice_1.class));
        Assert.assertFalse(AIcSdoCodegenService.isSdoInput(AIigNameFragmentsSegmentValueContent_1.class));
        var locResult = locService.generate(AIigChoiceContainer_1.class, "g",
                new Names("AIig"), new Names("AIigd"), new Names("AIcgd"),
                "impl.intf", "impl");
        String locMutable = locResult.mutableInterface().source();
        String locConcrete = locResult.implementation().source();
        String locReadChoice = AIigNameFragmentsSegmentChoice_1.class.getCanonicalName();
        String locReadContent = AIigNameFragmentsSegmentValueContent_1.class.getCanonicalName();
        for (String locSource : List.of(locMutable, locConcrete)) {
            Assert.assertTrue(locSource.contains(locReadChoice), locSource);
            Assert.assertTrue(locSource.contains(locReadContent), locSource);
            Assert.assertFalse(locSource.contains("AIigdNameFragmentsSegmentChoice_1"), locSource);
            Assert.assertFalse(locSource.contains("AIigdNameFragmentsSegmentValueContent_1"), locSource);
        }
        Path locTemp = Files.createTempDirectory("sdo-unannotated-choice-");
        try {
            List<Path> locFiles = new ArrayList<>();
            for (var locSource : List.of(locResult.mutableInterface(), locResult.implementation())) {
                Path locFile = locTemp.resolve(locSource.relativePath());
                Files.createDirectories(locFile.getParent());
                Files.writeString(locFile, locSource.source());
                locFiles.add(locFile);
            }
            Path locClasses = locTemp.resolve("classes");
            Files.createDirectories(locClasses);
            var locArguments = new ArrayList<String>(List.of("-proc:none", "-encoding", "UTF-8",
                    "-classpath", System.getProperty("java.class.path"),
                    "-d", locClasses.toString()));
            locArguments.addAll(locFiles.stream().map(Path::toString).toList());
            Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                    locArguments.toArray(String[]::new)), 0,
                    "SDO sources referencing immutable choice/helper types must compile");
        } finally {
            try (var locFiles = Files.walk(locTemp)) {
                for (Path locPath : locFiles.sorted(Comparator.reverseOrder()).toList())
                    Files.deleteIfExists(locPath);
            }
        }
    }

    /**
     * Minimal deterministic naming profile used only by this compiler regression.
     * It is intentionally independent of deployed naming resources.
     */
    private static final class Names implements AIiNameConventionCatalog {
        private final String prefix;

        /** @param aPrefix generated type prefix of this profile */
        private Names(String aPrefix) { prefix = aPrefix; }

        /** {@inheritDoc} */
        @Override public Set<String> names() { return Set.of("regression"); }

        /** {@inheritDoc} */
        @Override public String selectedRole(String aRole) { return "regression"; }

        /** {@inheritDoc} */
        @Override public String generatedMethodProfile() { return null; }

        /** {@inheritDoc} */
        @Override public String generatedMethodReference(String aRole) { return null; }

        /** {@inheritDoc} */
        @Override public String identifierConvention(String aProfile, String aRole) {
            return "upper_camel_case_1";
        }

        /** {@inheritDoc} */
        @Override public boolean matches(String aProfile, String aRole, String aName) { return true; }

        /** {@inheritDoc} */
        @Override public Map<String, String> parse(String aProfile, String aRole, String aName) {
            if ("getter_method_name".equals(aRole))
                return Map.of("identifier", aName.substring(3));
            if ("type_name".equals(aRole)) {
                String locBase = aName;
                for (String locPrefix : List.of("AIigd", "AIcgd", "AIig")) {
                    if (locBase.startsWith(locPrefix)) {
                        locBase = locBase.substring(locPrefix.length());
                        break;
                    }
                }
                if (locBase.endsWith("_1")) locBase = locBase.substring(0, locBase.length() - 2);
                return Map.of("identifier", locBase, "version", "1");
            }
            return Map.of("identifier", aName);
        }

        /** {@inheritDoc} */
        @Override public String format(String aProfile, String aRole,
                Map<String, String> aValues, String aSourceConvention) {
            String locName = aValues.getOrDefault("identifier", "");
            return switch (aRole) {
                case "type_name", "file_name_stem" -> prefix + locName + "_1";
                case "file_name_suffix" -> ".java";
                case "setter_method_name" -> "set" + locName;
                case "method_parameter_name" -> "a" + locName;
                default -> "get" + locName;
            };
        }
    }

    /** Schema-neutral parent with an optional semantic property. */
    @eu.algites.lib.data.dataobject.AIaDataObject
    public interface AIigUnifiedBase_1 extends AIiDataObject {
        /** @return optional identifier conventions */
        @AIaDataObjectField(dataFieldName = "IdentifierConventions",
                presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED)
        String getIdentifierConventions();
    }

    /** The same contract refined by XML and JSON metadata on a single type. */
    @eu.algites.lib.data.dataobject.AIaDataObject
    @eu.algites.lib.data.dataobject.xmlschema.AIaDataObjectXmlSchema(
            namespace = "urn:unified", namespaceLocalName = "UnifiedDerived",
            definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE)
    @eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(
            schemaId = "urn:unified", schemaVersion = 1)
    public interface AIigUnifiedDerived_1 extends AIigUnifiedBase_1 {
        /** @return required identifier conventions */
        @Override
        @eu.algites.lib.data.dataobject.xmlschema.AIaDataObjectFieldXmlSchema(
                namespaceLocalName = "IdentifierConventions",
                valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
        @AIaDataObjectField(dataFieldName = "IdentifierConventions",
                presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED)
        String getIdentifierConventions();
    }

    /**
     * The unified read-only contract must generate one SDO pair without old
     * format-specific parents, even when the child narrows an inherited field.
     */
    @Test
    public void testUnifiedReadContractWithModernFormatMetadata() {
        var result = new AIcSdoCodegenService().generate(
                AIigUnifiedDerived_1.class, "g", new Names("AIig"),
                new Names("AIigd"), new Names("AIcgd"), "impl.intf", "impl");
        String concrete = result.implementation().source();
        Assert.assertTrue(concrete.contains("impl.common.AIcSmartDataObject"), concrete);
        Assert.assertTrue(concrete.contains("AIaSmartDataObjectImplementationBinding"), concrete);
        Assert.assertTrue(!concrete.contains("xmlNestedTypes()"), concrete);
        Assert.assertTrue(!concrete.contains("AIcXmlSmartDataObject"), concrete);
        Assert.assertTrue(!concrete.contains("AIcJsonSmartDataObject"), concrete);
        Assert.assertTrue(result.mutableInterface().source().contains("IdentifierConventions"), "Missing inherited getter");
    }

    /**
     * Generate both sides of an inherited mapped getter, and compile the
     * generated interfaces <em>and</em> implementations together.
     *
     * @throws IOException if the temporary source/output directory is inaccessible
     */
    @Test
    public void testMappedCovariantGetterAndGenericParentCompile() throws IOException {
        var locService = new AIcSdoCodegenService();
        var locInput = new Names("AIig");
        var locMutable = new Names("AIigd");
        var locConcrete = new Names("AIcgd");
        Path locTemp = Files.createTempDirectory("sdo-mapped-covariance-");
        try {
            List<Path> locFiles = new ArrayList<>();
            for (Class<?> locRead : List.of(AIigMappedBaseRule_1.class,
                    AIigMappedRule_1.class, AIigMappedParent_1.class,
                    AIigMappedChild_1.class)) {
                AIcdSdoGenerationResult locResult = locService.generate(
                        locRead, "g", locInput, locMutable, locConcrete, "impl.intf", "impl");
                String locNewSdo = locResult.implementation().source();
                String locNewMutable = locResult.mutableInterface().source();
                Assert.assertTrue(locNewSdo.contains(
                        "extends eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject"),
                        "Concrete SDO must extend the shared format-independent runtime: " + locNewSdo);
                Assert.assertTrue(locNewSdo.contains(
                        "@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding("),
                        "Concrete implementation must explicitly bind its read contract: " + locNewSdo);
                Assert.assertTrue(locNewSdo.contains("readContracts = {" + locRead.getCanonicalName() + ".class}"),
                        "The binding cannot depend on naming-convention inference: " + locNewSdo);
                Assert.assertTrue(locNewMutable.contains(
                        "eu.algites.lib.data.smartdataobject.AIiSmartDataObject"),
                        "Mutable SDO must use the common contract marker: " + locNewMutable);
                Assert.assertTrue(!locNewSdo.contains("xmlNestedTypes()")
                        && !locNewSdo.contains("impl.jsondefs.AIcJsonSmartDataObject")
                        && !locNewSdo.contains("impl.xmldefs.AIcXmlSmartDataObject")
                        && !locNewSdo.contains("impl.yamldefs.AIcYamlSmartDataObject"),
                        "New SDO source cannot link the legacy per-format runtime: " + locNewSdo);
                if (locRead == AIigMappedParent_1.class) {
                    Assert.assertTrue(locNewMutable.contains("AIaDataObjectField(dataFieldName = \"Rule\""),
                            "New SDO annotations must not emit the deprecated fieldName: " + locNewMutable);
                }
                for (var locSource : List.of(locResult.mutableInterface(), locResult.implementation())) {
                    Path locFile = locTemp.resolve(locSource.relativePath());
                    Files.createDirectories(locFile.getParent());
                    Files.writeString(locFile, locSource.source());
                    locFiles.add(locFile);
                }
                if (locRead == AIigMappedChild_1.class) {
                    String locInterface = locResult.mutableInterface().source();
                    String locImplementation = locResult.implementation().source();
                    Assert.assertTrue(locInterface.contains(
                            "AIiMultiMappedList<? extends TRuleList>"), locInterface);
                    Assert.assertTrue(locInterface.contains("<TRuleList>"), locInterface);
                    Assert.assertTrue(locImplementation.contains(
                            "AIiMultiMappedList<? extends "), locImplementation);
                }
            }
            var locCompiler = ToolProvider.getSystemJavaCompiler();
            Assert.assertNotNull(locCompiler, "A JDK compiler is required for generated-source regression");
            Path locClasses = locTemp.resolve("classes");
            Files.createDirectories(locClasses);
            List<String> locArgs = new ArrayList<>(List.of("-encoding", "UTF-8", "-classpath",
                    System.getProperty("java.class.path"), "-d", locClasses.toString()));
            locArgs.addAll(locFiles.stream().map(Path::toString).toList());
            int locStatus = locCompiler.run(null, null, null, locArgs.toArray(String[]::new));
            Assert.assertEquals(locStatus, 0, "Generated mapped-list inheritance must compile");
        } finally {
            try (var locFiles = Files.walk(locTemp)) {
                for (Path locPath : locFiles.sorted(Comparator.reverseOrder()).toList())
                    Files.deleteIfExists(locPath);
            }
        }
    }
}
