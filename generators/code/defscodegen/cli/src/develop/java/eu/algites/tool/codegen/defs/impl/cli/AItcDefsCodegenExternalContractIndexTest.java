package eu.algites.tool.codegen.defs.impl.cli;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.ArrayList;
import java.util.Map;
import javax.tools.ToolProvider;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Java/Python paired contract index regressions: neither technology may choose
 * a mutable SDO or the generic contract instead of the derived XML Defs type.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenExternalContractIndexTest {
    /**
     * Verify inheritance-aware selection of a representation-specific contract
     * in both languages, without relying on a naming profile's class prefix.
     *
     * @throws Exception if test data cannot be created or source indexing fails
     */
    @Test
    public void testDerivedReadOnlySelectedInBothTechnologies() throws Exception {
        Path root = Files.createTempDirectory("defs-typed-parent-");
        String uri = "https://example.org/contracts/shared_1.xsd";
        String id = "{" + uri + "}SharedType";
        Path java = root.resolve("sample/src/product/java.gen/demo");
        Path python = root.resolve("sample/src/product/python.gen/demo");
        Files.createDirectories(java);
        Files.createDirectories(python);
        javaSource(java, "GenericInterface", uri, "", false);
        javaSource(java, "XmlInterface", uri, "demo.GenericInterface", false);
        javaSource(java, "MutableInterface", uri,
                "demo.XmlInterface, demo.AIiSmartDataObject", true);
        pythonSource(python, "generic_interface", "GenericInterface", uri, "object", false);
        Files.writeString(python.resolve("xml_interface.py"),
                "from demo.generic_interface import GenericInterface\n"
                + pythonDefinition("XmlInterface", uri, "GenericInterface", false));
        Files.writeString(python.resolve("mutable_interface.py"),
                "from demo.xml_interface import XmlInterface\n"
                + pythonDefinition("MutableInterface", uri, "XmlInterface", true));
        var result = AIcDefsCodegenExternalContractIndex.resolve(List.of(root));
        Assert.assertEquals(result.get(id).javaType(), "demo.XmlInterface");
        Assert.assertEquals(result.get(id).pythonModule(), "demo.xml_interface");
        Assert.assertEquals(result.get(id).pythonType(), "XmlInterface");
    }

    /**
     * Independently reject ambiguous unrelated Java and Python contracts.
     *
     * @throws Exception if test data cannot be created or source indexing fails
     */
    @Test
    public void testUnrelatedContractsRemainAmbiguousForEachTechnology() throws Exception {
        Path root = Files.createTempDirectory("defs-unrelated-contracts-");
        String uri = "https://example.org/contracts/shared_1.xsd";
        Path java = root.resolve("sample/src/product/java.gen/demo");
        Path python = root.resolve("sample/src/product/python.gen/demo");
        Files.createDirectories(java);
        Files.createDirectories(python);
        javaSource(java, "FirstContract", uri, "", false);
        javaSource(java, "SecondContract", uri, "", false);
        try {
            AIcDefsCodegenExternalContractIndex.resolve(List.of(root));
            Assert.fail("Unrelated Java contracts were silently merged");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("unrelated candidates"));
            Assert.assertTrue(expected.getMessage().contains("java"));
        }
        Files.delete(java.resolve("FirstContract.java"));
        Files.delete(java.resolve("SecondContract.java"));
        pythonSource(python, "first_contract", "FirstContract", uri, "object", false);
        pythonSource(python, "second_contract", "SecondContract", uri, "object", false);
        try {
            AIcDefsCodegenExternalContractIndex.resolve(List.of(root));
            Assert.fail("Unrelated Python contracts were silently merged");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("unrelated candidates"));
            Assert.assertTrue(expected.getMessage().contains("python"));
        }
    }

    /**
     * An unrelated Security artifact with duplicate type projections cannot
     * block a naming artifact that does not reference that Security type.
     * Required duplicates remain errors instead of being resolved arbitrarily.
     *
     * @throws Exception if test files cannot be written or indexed
     */
    @Test
    public void testUnreferencedSecurityDuplicatesAreNotValidated() throws Exception {
        Path root = Files.createTempDirectory("defs-security-irrelevant-");
        Path java = root.resolve("security/src/product/java.gen/demo");
        Files.createDirectories(java);
        String security = "https://example.org/security/credential-profiles_1.xsd";
        String naming = "https://example.org/naming/common_1.xsd";
        javaSource(java, "GeneralSecurity", security, "", false);
        javaSource(java, "XmlSecurity", security, "", false);
        javaSource(java, "NamingParent", naming, "", false);
        String parentId = "{" + naming + "}SharedType";
        var onlyRequired = AIcDefsCodegenExternalContractIndex.resolve(
                List.of(root), Set.of(parentId));
        Assert.assertEquals(onlyRequired.size(), 1);
        Assert.assertEquals(onlyRequired.get(parentId).javaType(), "demo.NamingParent");
        try {
            AIcDefsCodegenExternalContractIndex.resolve(List.of(root),
                    Set.of("{" + security + "}SharedType"));
            Assert.fail("Referenced unrelated Security contracts must remain ambiguous");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("unrelated candidates"));
        }
    }

    /**
     * A conflict between two copies of an unrelated symbol cannot block an
     * independent artifact. Requiring that symbol reports both source files.
     *
     * @throws Exception if test files cannot be written or indexed
     */
    @Test
    public void testIdenticalSymbolUnrelatedDuplicatesFilteredBeforeValidation() throws Exception {
        Path root = Files.createTempDirectory("defs-qname-lazy-validation-");
        for (String role : List.of("first", "second")) {
            Path directory = root.resolve(role + "/src/product/java.gen/demo");
            Files.createDirectories(directory);
            javaSource(directory, "AIigFieldBindingType_1", "urn:unrelated",
                    role.equals("first") ? "demo.ParentOne" : "demo.ParentTwo", false);
        }
        Path needed = root.resolve("needed/src/product/java.gen/demo");
        Files.createDirectories(needed);
        javaSource(needed, "NeededParent", "urn:needed", "", false);
        Assert.assertEquals(AIcDefsCodegenExternalContractIndex.resolve(List.of(root), Set.of()).size(), 0);
        var selected = AIcDefsCodegenExternalContractIndex.resolve(
                List.of(root), Set.of("{urn:needed}SharedType"));
        Assert.assertEquals(selected.get("{urn:needed}SharedType").javaType(), "demo.NeededParent");
        try {
            AIcDefsCodegenExternalContractIndex.resolve(
                    List.of(root), Set.of("{urn:unrelated}SharedType"));
            Assert.fail("A referenced duplicate must not be silently accepted");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("ParentOne"));
            Assert.assertTrue(expected.getMessage().contains("ParentTwo"));
            Assert.assertTrue(expected.getMessage().contains("AIigFieldBindingType_1.java"));
        }
    }

    /**
     * Verify arbitrary naming conventions are accepted for root JSONDEFS types.
     * This includes Python classes with no explicit base-class parentheses.
     *
     * @throws Exception if test data cannot be created or source indexing fails
     */
    @Test
    public void testCustomNamingAndPythonNoBaseParentheses() throws Exception {
        Path root = Files.createTempDirectory("defs-custom-naming-");
        Path java = root.resolve("src/product/java.gen/demo");
        Path python = root.resolve("src/product/python.gen/demo");
        Files.createDirectories(java);
        Files.createDirectories(python);
        String url = "https://example.org/schema/demo.json";
        Files.writeString(java.resolve("CustomInterface.java"),
                "package demo;\n@AIaDataObject()\n"
                + "@AIaJsonDataObject(schemaId=\"demo\", schemaUrl=\"" + url + "\")\n"
                + "public interface CustomInterface {}\n");
        Files.writeString(python.resolve("custom_module.py"),
                "class CompletelyDifferentName:\n"
                + "    __data_object__ = M()\n"
                + "    __json_data_object__ = J(schema_id='demo', schema_url='" + url + "')\n");
        var result = AIcDefsCodegenExternalContractIndex.resolve(List.of(root));
        Assert.assertEquals(result.get(url).javaType(), "demo.CustomInterface");
        Assert.assertEquals(result.get(url).pythonModule(), "demo.custom_module");
        Assert.assertEquals(result.get(url).pythonType(), "CompletelyDifferentName");
    }

    /**
     * Compile a published-style contract into binary .class files and resolve
     * XML TYPE metadata and read-only inheritance without Java source files.
     * This is the Java counterpart to the Python JAR dependency regression.
     *
     * @throws Exception on fixture creation, compilation or indexing failure
     */
    @Test
    public void testCompiledJavaContractsWithoutSourceTree() throws Exception {
        var compiler = ToolProvider.getSystemJavaCompiler();
        Assert.assertNotNull(compiler, "A full JDK is needed for binary-contract testing");
        Path workspace = Files.createTempDirectory("defs-compiled-parent-");
        Path sources = workspace.resolve("fixture-sources");
        Path binaries = workspace.resolve("binary-dependency");
        Files.createDirectories(binaries);
        Map<String, String> units = Map.of(
            "annotations/AIaDataObject.java",
                "package annotations; import java.lang.annotation.*; "
                + "@Retention(RetentionPolicy.RUNTIME) public @interface AIaDataObject {}",
            "annotations/Kind.java",
                "package annotations; public enum Kind { TYPE, ELEMENT }",
            "annotations/AIaXmlDataObject.java",
                "package annotations; import java.lang.annotation.*; "
                + "@Retention(RetentionPolicy.RUNTIME) public @interface AIaXmlDataObject { "
                + "Kind definitionKind(); String namespace(); String namespaceLocalName(); }",
            "example/contracts/ReadOnlyCommon.java",
                "package example.contracts; @annotations.AIaDataObject() "
                + "public interface ReadOnlyCommon {}",
            "example/contracts/XmlReadOnly.java",
                "package example.contracts; @annotations.AIaDataObject() "
                + "@annotations.AIaXmlDataObject(definitionKind=annotations.Kind.TYPE, "
                + "namespace=\"urn:published\", namespaceLocalName=\"SharedType\") "
                + "public interface XmlReadOnly extends ReadOnlyCommon {}",
            "example/contracts/MutableSdo.java",
                "package example.contracts; @annotations.AIaDataObject() "
                + "@annotations.AIaXmlDataObject(definitionKind=annotations.Kind.TYPE, "
                + "namespace=\"urn:published\", namespaceLocalName=\"SharedType\") "
                + "public interface MutableSdo extends XmlReadOnly { "
                + "void setName(String value); }"
        );
        List<String> arguments = new ArrayList<>(List.of("-d", binaries.toString()));
        for (var entry : units.entrySet()) {
            Path source = sources.resolve(entry.getKey());
            Files.createDirectories(source.getParent());
            Files.writeString(source, entry.getValue());
            arguments.add(source.toString());
        }
        Assert.assertEquals(compiler.run(null, null, null,
                arguments.toArray(String[]::new)), 0, "Java fixture compilation");
        var index = AIcDefsCodegenExternalContractIndex.resolve(
                List.of(binaries), Set.of("{urn:published}SharedType"));
        Assert.assertEquals(index.size(), 1);
        Assert.assertEquals(index.get("{urn:published}SharedType").javaType(),
                "example.contracts.XmlReadOnly");
        Assert.assertNull(index.get("{urn:published}SharedType").pythonType());
    }

    /**
     * New schema metadata annotations must work without the generic annotation
     * on representation-specific contracts, including direct Python sources.
     *
     * @throws Exception if generated fixture files cannot be indexed
     */
    @Test
    public void testModernSchemaPackagesWithoutRepeatedGenericAnnotation() throws Exception {
        Path root = Files.createTempDirectory("defs-modern-schema-source-");
        Path java = root.resolve("src/product/java.gen/demo");
        Path python = root.resolve("src/product/python.gen/demo");
        Files.createDirectories(java);
        Files.createDirectories(python);
        String url = "https://example.org/jsondefs/common_1.jsondef.schema.json";
        Files.writeString(java.resolve("JsonSpecific.java"),
                "package demo;\n"
                + "@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema("
                + "schemaId=\"common\",schemaUrl=\"" + url + "\")\n"
                + "public interface JsonSpecific {}\n");
        Files.writeString(java.resolve("XmlSpecific.java"),
                "package demo;\n"
                + "@eu.algites.lib.data.dataobject.xmlschema.AIaDataObjectXmlSchema("
                + "definitionKind=K.TYPE, namespace=\"urn:modern\", "
                + "namespaceLocalName=\"Common\")\n"
                + "public interface XmlSpecific {}\n");
        Files.writeString(python.resolve("json_specific.py"),
                "class JsonSpecific:\n"
                + "    __json_schema__ = AIaDataObjectJsonSchema("
                + "schema_id='common', schema_url='" + url + "')\n");
        Files.writeString(python.resolve("xml_specific.py"),
                "class XmlSpecific:\n"
                + "    __xml_schema__ = AIaDataObjectXmlSchema("
                + "definition_kind=K.TYPE, namespace='urn:modern', namespace_local_name='Common')\n");
        var result = AIcDefsCodegenExternalContractIndex.resolve(List.of(root));
        Assert.assertEquals(result.get(url).javaType(), "demo.JsonSpecific");
        Assert.assertEquals(result.get(url).pythonType(), "JsonSpecific");
        Assert.assertEquals(result.get("{urn:modern}Common").javaType(), "demo.XmlSpecific");
        Assert.assertEquals(result.get("{urn:modern}Common").pythonType(), "XmlSpecific");
    }

    /**
     * Real binary annotations in their new packages need no AIaDataObject.
     *
     * @throws Exception on fixture creation, compilation or indexing failure
     */
    @Test
    public void testModernCompiledSchemaPackagesWithoutGenericAnnotation() throws Exception {
        var compiler = ToolProvider.getSystemJavaCompiler();
        Assert.assertNotNull(compiler);
        Path root = Files.createTempDirectory("defs-modern-schema-binary-");
        Path src = root.resolve("src"), classes = root.resolve("classes");
        Files.createDirectories(src); Files.createDirectories(classes);
        Map<String, String> units = Map.of(
                "demo/Kind.java", "package demo; public enum Kind { TYPE, ELEMENT }",
                "demo/AIaDataObjectJsonSchema.java", "package demo; import java.lang.annotation.*; "
                    + "@Retention(RetentionPolicy.RUNTIME) public @interface AIaDataObjectJsonSchema "
                    + "{ String schemaId(); String schemaUrl(); }",
                "demo/AIaDataObjectXmlSchema.java", "package demo; import java.lang.annotation.*; "
                    + "@Retention(RetentionPolicy.RUNTIME) public @interface AIaDataObjectXmlSchema "
                    + "{ Kind definitionKind(); String namespace(); String namespaceLocalName(); }",
                "demo/JsonSpecific.java", "package demo; "
                    + "@AIaDataObjectJsonSchema(schemaId=\"common\", "
                    + "schemaUrl=\"https://example.org/common_1.json\") "
                    + "public interface JsonSpecific {}",
                "demo/XmlSpecific.java", "package demo; "
                    + "@AIaDataObjectXmlSchema(definitionKind=Kind.TYPE, namespace=\"urn:modern\", "
                    + "namespaceLocalName=\"Common\") public interface XmlSpecific {}");
        List<String> command = new ArrayList<>(List.of("-d", classes.toString()));
        for (var entry : units.entrySet()) {
            Path file = src.resolve(entry.getKey());
            Files.createDirectories(file.getParent());
            Files.writeString(file, entry.getValue());
            command.add(file.toString());
        }
        Assert.assertEquals(compiler.run(null, null, null, command.toArray(String[]::new)), 0);
        var result = AIcDefsCodegenExternalContractIndex.resolve(List.of(classes));
        Assert.assertEquals(result.get("https://example.org/common_1.json").javaType(), "demo.JsonSpecific");
        Assert.assertEquals(result.get("{urn:modern}Common").javaType(), "demo.XmlSpecific");
    }

    /**
     * Create a generated-looking annotated Java interface.
     * @param directory Java generated-source package directory
     * @param name test interface name
     * @param uri XSD namespace/schema URL
     * @param parent optional comma-separated interface parents
     * @param writable whether to add the mutable SDO method
     * @throws IOException on filesystem errors
     */
    private static void javaSource(Path directory, String name, String uri,
            String parent, boolean writable) throws IOException {
        Files.writeString(directory.resolve(name + ".java"),
                "package demo;\n@AIaDataObject()\n"
                + "@AIaXmlDataObject(definitionKind=K.TYPE, namespace=\"" + uri
                + "\", namespaceLocalName=\"SharedType\")\n"
                + "public interface " + name + (parent.isEmpty() ? "" : " extends " + parent)
                + " {" + (writable ? "void setName(String value);" : "") + "}\n");
    }

    /**
     * Create an annotated Python generated-source class.
     * @param directory Python generated module directory
     * @param stem Python module stem
     * @param name Python class name
     * @param uri XSD namespace/schema URL
     * @param parent Python base class
     * @param writable whether to add the mutable SDO method
     * @throws IOException on filesystem errors
     */
    private static void pythonSource(Path directory, String stem, String name,
            String uri, String parent, boolean writable) throws IOException {
        Files.writeString(directory.resolve(stem + ".py"),
                pythonDefinition(name, uri, parent, writable));
    }

    /**
     * Build a Python annotated DataObject declaration.
     * @param name generated class name
     * @param uri XSD namespace/schema URL
     * @param parent Python base class
     * @param writable whether the class exposes writable setters
     * @return valid generated-style Python class source
     */
    private static String pythonDefinition(String name, String uri, String parent, boolean writable) {
        return "class " + name + "(" + parent + "):\n"
                + "    __data_object__ = M()\n"
                + "    __xml_data_object__ = X(definition_kind=K.TYPE, namespace='"
                + uri + "', namespace_local_name='SharedType')\n"
                + (writable ? "    def setName(self, value): ...\n" : "");
    }
}
