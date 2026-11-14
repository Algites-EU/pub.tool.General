package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.tools.ToolProvider;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Regression checks for the new Java-native canonical source emission boundary. */
public final class AItcDefsCodegenCanonicalSourceEmitterTest {
    /**
     * Provides resolved getter and setter compositions matching the generator
     * contract without relying on unrelated legacy naming-catalog APIs.
     *
     * @return test Common/Defs naming profile with explicit lexical segments
     */
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        var getter = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "get")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "identifier", "Convention", "upper_camel_case_1"))));
        var setter = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "set")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "identifier", "Convention", "upper_camel_case_1"))));
        var choice = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "variable", "Name", "owner_type", "Regexp", ".+")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "Variant")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "variable", "Name", "position", "Regexp", "[0-9]+"))));
        var property = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "variable", "Name", "owner_type", "Regexp", ".+")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "Property")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "identifier", "Convention", "upper_camel_case_1"))));
        var item = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "item")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "variable", "Name", "position", "Regexp", "[0-9]+"))));
        var constants = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "CONST")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "identifier", "Convention", "upper_camel_case_1"))));
        return new AIcCodegenNamingProfileResolver.Profile("test",
                Map.of("standard_getter", "test-get", "list_getter", "test-get", "standard_setter", "test-set",
                       "positional_item_synthetic_getter", "test-item",
                       "const_container_interface", "test-const"),
                Map.of("synthetic_choice_variant_type", "test-choice",
                       "synthetic_property_type", "test-property"), Map.of(), Map.of(), 1,
                Map.of("test-get", getter, "test-set", setter, "test-choice", choice,
                       "test-item", item, "test-property", property, "test-const", constants));
    }

    /**
     * Builds a three-type namespace containing object references, arrays, and
     * a lexical enum independent of the old frontend or code generation backend.
     *
     * @return linked canonical type graph
     */
    private static List<AIcDefsCanonicalType> types() {
        Map<String, Object> fields = new LinkedHashMap<>();
        fields.put("value", Map.of("type", "string"));
        fields.put("next", Map.of("$ref", "#/$defs/Node"));
        fields.put("children", Map.of("type", "array", "items", Map.of("$ref", "#/$defs/Node")));
        Map<String, Object> defs = new LinkedHashMap<>();
        defs.put("Node", Map.of("type", "object", "properties", fields, "required", List.of("value")));
        defs.put("Status", Map.of("type", "string", "enum", List.of("ready", "on-hold")));
        Map<String, Object> source = new LinkedHashMap<>();
        source.put("$id", "urn:test");
        source.put("$defs", defs);
        return new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                        "test.json", source))).types();
    }

    /**
     * Verifies full model-to-source output, generated Java compilation, and
     * consistent typed getter/setter signatures for the Python target.
     *
     * @throws Exception if temporary source IO or the Java compiler fails
     */
    @Test
    public void AIcNativeJavaEmitterProducesCompilableIndependentSource() throws Exception {
        var types = types();
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> names = new LinkedHashMap<>();
        for (var type : types) {
            names.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    "AIig" + type.name() + "_1", "AIig" + type.name() + "_1",
                    "aiig_" + type.name().toLowerCase(java.util.Locale.ROOT) + "_1"));
        }
        var output = new AIcDefsCodegenCanonicalSourceEmitter(profile(), names, "test.output")
                .render(types);
        Assert.assertEquals(output.size(), 4);
        var root = Files.createTempDirectory("canonical-java-output-");
        try {
            var javaFiles = new ArrayList<String>();
            for (var entry : output) {
                var file = root.resolve(entry.relativePath());
                if (entry.language().equals("java")) {
                    Files.createDirectories(file.getParent());
                    Files.writeString(file, entry.sourceText(), StandardCharsets.UTF_8);
                    javaFiles.add(file.toString());
                } else if (entry.relativePath().endsWith("aiig_node_1.py")) {
                    Assert.assertTrue(entry.sourceText().contains("def getNext(self) -> AIigNode_1"));
                    Assert.assertTrue(!entry.sourceText().contains("def setNext(self, value: AIigNode_1)"));
                }
            }
            var node = Files.readString(root.resolve("test/output/AIigNode_1.java"));
            Assert.assertTrue(node.contains("java.util.List<? extends AIigNode_1> getChildren()"));
            Assert.assertTrue(node.contains("AIigNode_1 getNext()"));
            javaFiles.add(0, "-d");
            javaFiles.add(1, root.resolve("classes").toString());
            Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                    javaFiles.toArray(String[]::new)), 0);
        } finally {
            try (var walk = Files.walk(root)) {
                walk.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
                    try { Files.delete(path); }
                    catch (java.io.IOException failure) { throw new RuntimeException(failure); }
                });
            }
        }
    }

    /**
     * Verify that the native Java emitter retains scalar and list restrictions
     * on CHOICE alternative getters in both its Java and Python outputs.
     *
     * @throws Exception if the canonical pipeline cannot link the test schema
     */
    @Test
    public void AIcNativeChoiceAlternativesKeepFieldFacetAnnotations() throws Exception {
        Map<String, Object> alternatives = new LinkedHashMap<>();
        alternatives.put("record", Map.of("type", "object", "properties", Map.of(
                "items", Map.of("type", "array", "minItems", 2, "maxItems", 5,
                        "items", Map.of("type", "string")),
                "code", Map.of("type", "string", "minLength", 3))));
        alternatives.put("text", Map.of("type", "string", "minLength", 2, "maxLength", 10));
        Map<String, Object> source = Map.of("$id", "urn:choice-facets", "type", "object",
                "x-algites-defscodegen-choice", true, "properties", alternatives,
                "minProperties", 1, "maxProperties", 1, "additionalProperties", false);
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                        "choice.json", source))).types();
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> names = new LinkedHashMap<>();
        int index = 0;
        for (var type : AIcDefsCodegenCanonicalSourceEmitter.declarations(types)) {
            int ordinal = index++;
            names.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    "AIigChoice" + ordinal, "AIigChoice" + ordinal,
                    "aiig_choice" + ordinal));
        }
        var output = new AIcDefsCodegenCanonicalSourceEmitter(profile(), names, "choice.facets")
                .render(types);
        String javaText = output.stream().filter(item -> item.language().equals("java"))
                .map(AIcDefsCodegenCanonicalSourceEmitter.Output::sourceText)
                .collect(java.util.stream.Collectors.joining("\n"));
        String pythonText = output.stream().filter(item -> item.language().equals("python"))
                .map(AIcDefsCodegenCanonicalSourceEmitter.Output::sourceText)
                .collect(java.util.stream.Collectors.joining("\n"));
        Assert.assertTrue(javaText.contains("AIaDataObjectFieldListConstraints(minItems = 2, maxItems = 5)"));
        Assert.assertTrue(javaText.contains("AIaDataObjectFieldStringConstraints(minLength = 3)"));
        Assert.assertTrue(javaText.contains("AIaDataObjectFieldStringConstraints(minLength = 2, maxLength = 10)"));
        Assert.assertTrue(pythonText.contains("AIaDataObjectFieldListConstraints(min_items = 2, max_items = 5)"));
        Assert.assertTrue(pythonText.contains("AIaDataObjectFieldStringConstraints(min_length = 3)"));
        Assert.assertTrue(pythonText.contains("AIaDataObjectFieldStringConstraints(min_length = 2, max_length = 10)"));
    }

    /**
     * Verifies published document URLs independently from logical schema IDs.
     * A referenced $defs type must not be indexed as the document root.
     */
    @Test
    public void AIcNativePublishedSchemaUrlIsOnlyOnRoot() {
        String url = "https://example.org/api/jsondefs/sample_1.jsondef.schema.json";
        Map<String, Object> schema = new LinkedHashMap<>();
        schema.put("$id", url);
        schema.put("x-algites-schema-id", "example.sample");
        schema.put("x-algites-schema-version", 1);
        schema.put("title", "Sample");
        schema.put("type", "object");
        schema.put("properties", Map.of("Value", Map.of("type", "string")));
        schema.put("$defs", Map.of("Extra", Map.of("type", "object", "properties",
                Map.of("Label", Map.of("type", "string")))));
        var documents = List.of(new AIcdDefsCodegenSourceDocument(
                AIngSourceInputKind_1.JSONDEFS, "sample.json", schema));
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { })
                .process(documents).types();
        var declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(types);
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> names = new LinkedHashMap<>();
        for (var type : declarations) {
            names.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    "AIig" + type.name(), "AIig" + type.name(),
                    "aiig_" + type.name().toLowerCase(java.util.Locale.ROOT)));
        }
        var output = new AIcDefsCodegenCanonicalSourceEmitter(profile(), names, "test.output",
                Map.of(), Map.of("sample.json", url)).render(types);
        for (var item : output) {
            if (item.typeIdentity().equals("example.sample")) {
                if (item.language().equals("java")) {
                    Assert.assertTrue(item.sourceText().contains("schemaId = \"example.sample\""));
                    Assert.assertTrue(item.sourceText().contains("schemaUrl = \"" + url + "\""));
                } else {
                    Assert.assertTrue(item.sourceText().contains("schema_id=\"example.sample\""));
                    Assert.assertTrue(item.sourceText().contains("schema_url=\"" + url + "\""));
                }
            } else {
                Assert.assertTrue(!item.sourceText().contains("schemaUrl = "));
                Assert.assertTrue(!item.sourceText().contains("schema_url="));
            }
        }
    }

    /**
     * Reject the former two-output interface mode rather than emitting a
     * secondary nominal interface whose source format differs from the common
     * DataObject. Independent wire metadata must remain on one contract.
     */
    @Test
    public void AIcRejectsSeparateTechnologyContractOutput() {
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> unified = new LinkedHashMap<>();
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> alternate = new LinkedHashMap<>();
        for (var type : types()) {
            var simple = type.name();
            unified.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    "AIig" + simple + "_1", "AIig" + simple + "_1",
                    "aiig_" + simple.toLowerCase(java.util.Locale.ROOT) + "_1"));
            alternate.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    "AIigAlternative" + simple + "_1", "AIigAlternative" + simple + "_1",
                    "aiig_alternative_" + simple.toLowerCase(java.util.Locale.ROOT) + "_1"));
        }
        var common = AIcDefsCodegenCanonicalSourceEmitter.commonOnly(
                profile(), unified, "test.output", Map.of(), Map.of());
        var sources = common.render(types());
        Assert.assertTrue(sources.stream().anyMatch(entry ->
                entry.language().equals("java") && entry.relativePath().endsWith("AIigNode_1.java")));
        Assert.assertTrue(sources.stream().anyMatch(entry ->
                entry.language().equals("python") && entry.relativePath().endsWith("aiig_node_1.py")));
        Assert.assertThrows(IllegalArgumentException.class, () ->
                new AIcDefsCodegenCanonicalSourceEmitter(profile(), alternate,
                        "test.output", Map.of(), Map.of(), unified));
    }

    /** The emitter rejects silently renamed or missing canonical contracts. */
    @Test
    public void AIcNativeJavaEmitterRequiresExactOutputNameCoverage() {
        boolean rejected = false;
        try {
            new AIcDefsCodegenCanonicalSourceEmitter(profile(), Map.of(), "test.output").render(types());
        } catch (IllegalArgumentException expected) {
            rejected = true;
        }
        Assert.assertTrue(rejected);
    }

    /**
     * Ensures the native Java compiler emits a sealed interface with directly
     * permitted, final record variants in the same package and Java module.
     *
     * @throws Exception if staging or compilation of the generated sources fails
     */
    @Test
    public void AIcNativeJavaEmitterCompilesClosedScalarChoice() throws Exception {
        Map<String, Object> alternatives = new LinkedHashMap<>();
        alternatives.put("text", Map.of("type", "string"));
        alternatives.put("number", Map.of("type", "integer"));
        var source = Map.<String, Object>of("$id", "urn:choices", "type", "object",
                "x-algites-defscodegen-choice", true, "properties", alternatives,
                "minProperties", 1, "maxProperties", 1, "additionalProperties", false);
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                        "choice.json", source))).types();
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> symbols = new LinkedHashMap<>();
        symbols.put(types.get(0).identity(),
                new AIcDefsCodegenCanonicalSourceEmitter.Names("AIigChoice", "AIigChoice", "aiig_choice"));
        var group = (eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList) types.get(0).structure();
        int index = 0;
        for (var child : group.children()) {
            var variant = (eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType)
                    ((eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement) child).structure();
            String symbol = "AIigVariant" + ++index;
            symbols.put(variant.identity(),
                    new AIcDefsCodegenCanonicalSourceEmitter.Names(symbol, symbol, "aiig_variant" + index));
        }
        var outputs = new AIcDefsCodegenCanonicalSourceEmitter(profile(), symbols, "test.output").render(types);
        Assert.assertEquals(outputs.size(), 6);
        var javaFiles = new ArrayList<String>();
        var folder = Files.createTempDirectory("canonical-choice-");
        try {
            for (var output : outputs) {
                if (!output.language().equals("java")) continue;
                var file = folder.resolve(output.relativePath());
                Files.createDirectories(file.getParent());
                Files.writeString(file, output.sourceText());
                javaFiles.add(file.toString());
            }
            String sourceCode = Files.readString(folder.resolve("test/output/AIigChoice.java"));
            Assert.assertTrue(sourceCode.contains("sealed interface AIigChoice permits AIigVariant1, AIigVariant2"));
            Assert.assertTrue(Files.readString(folder.resolve("test/output/AIigVariant1.java"))
                    .contains("record AIigVariant1(String value) implements AIigChoice"));
            javaFiles.add(0, "-d");
            javaFiles.add(1, folder.resolve("classes").toString());
            Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                    javaFiles.toArray(String[]::new)), 0);
        } finally {
            try (var walk = Files.walk(folder)) {
                walk.sorted(java.util.Comparator.reverseOrder()).forEach(file -> {
                    try { Files.delete(file); }
                    catch (java.io.IOException error) { throw new RuntimeException(error); }
                });
            }
        }
    }

    /**
     * Verifies a structured explicit CHOICE branch becomes a nominal record with
     * ordered, typed fields, while its Python counterpart retains the getters.
     *
     * @throws Exception if source creation or compilation fails
     */
    @Test
    public void AIcNativeJavaEmitterCompilesStructuredChoice() throws Exception {
        Map<String, Object> fields = new LinkedHashMap<>();
        fields.put("name", Map.of("type", "string"));
        fields.put("age", Map.of("type", "integer"));
        Map<String, Object> alternatives = new LinkedHashMap<>();
        alternatives.put("person", Map.of("type", "object", "properties", fields,
                "required", List.of("name")));
        alternatives.put("number", Map.of("type", "integer"));
        var source = Map.<String, Object>of("$id", "urn:choices", "type", "object",
                "x-algites-defscodegen-choice", true, "properties", alternatives,
                "minProperties", 1, "maxProperties", 1, "additionalProperties", false);
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                        "structured-choice.json", source))).types();
        var declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(types);
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> names = new LinkedHashMap<>();
        int index = 0;
        for (var type : declarations) {
            String symbol = "AIigT" + index;
            names.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    symbol, symbol, "aiig_t" + index));
            index++;
        }
        var entries = new AIcDefsCodegenCanonicalSourceEmitter(profile(), names, "test.output").render(types);
        Assert.assertEquals(entries.size(), 6);
        var root = Files.createTempDirectory("canonical-structured-choice-");
        try {
            var javaFiles = new ArrayList<String>();
            for (var entry : entries) {
                if (entry.language().equals("java")) {
                    var file = root.resolve(entry.relativePath());
                    Files.createDirectories(file.getParent());
                    Files.writeString(file, entry.sourceText());
                    javaFiles.add(file.toString());
                    if (entry.relativePath().endsWith("AIigT1.java")) {
                        Assert.assertTrue(entry.sourceText().contains(
                                "record AIigT1(String field1, Long field2) implements AIigT0"));
                        Assert.assertTrue(entry.sourceText().contains("String getName() { return field1; }"));
                        Assert.assertTrue(entry.sourceText().contains("Long getAge() { return field2; }"));
                        Assert.assertTrue(entry.sourceText().contains("requireNonNull(field1"));
                    }
                } else if (entry.relativePath().endsWith("aiig_t1.py")) {
                    Assert.assertTrue(entry.sourceText().contains("def getName(self) -> str"));
                    Assert.assertTrue(entry.sourceText().contains("def getAge(self) -> int | None"));
                }
            }
            javaFiles.add(0, "-d");
            javaFiles.add(1, root.resolve("classes").toString());
            Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                    javaFiles.toArray(String[]::new)), 0);
        } finally {
            try (var walk = Files.walk(root)) {
                walk.sorted(java.util.Comparator.reverseOrder()).forEach(file -> {
                    try { Files.delete(file); }
                    catch (java.io.IOException failure) { throw new RuntimeException(failure); }
                });
            }
        }
    }

    /**
     * JSON Schema oneOf alone is validation-only, not a structural CHOICE.
     * A root without any independently declared object or enum structure must
     * therefore not emit arbitrary sealed variants from the assertion branches.
     */
    @Test
    public void AIcNativeJavaEmitterRejectsOneOfOnlyWithoutStructuralType() {
        var source = Map.<String, Object>of("$id", "urn:choices", "oneOf", List.of(
                Map.of("type", "object", "properties", Map.of("items", Map.of(
                        "type", "array", "minItems", 2, "items", Map.of("type", "string")))),
                Map.of("type", "integer")));
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                        "structured-choice.json", source))).types();
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> names = new LinkedHashMap<>();
        int index = 0;
        for (var type : AIcDefsCodegenCanonicalSourceEmitter.declarations(types)) {
            String symbol = "AIigT" + index;
            names.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    symbol, symbol, "aiig_t" + index));
            index++;
        }
        boolean rejected = false;
        try {
            new AIcDefsCodegenCanonicalSourceEmitter(profile(), names, "test.output").render(types);
        } catch (UnsupportedOperationException expected) {
            rejected = expected.getMessage().contains("Only object and top-level enum supported");
        }
        Assert.assertTrue(rejected);
    }
    /**
     * Checks unbounded integer and boolean enum codes against the canonical
     * type system for both language targets, without numeric string coercion.
     *
     * @throws Exception if emitted Java source does not compile
     */
    @Test
    public void AIcNativeJavaEmitterKeepsTypedEnumWireValues() throws Exception {
        var sources = List.of(
                Map.<String, Object>of("$id", "urn:integer-enum", "title", "Codes", "type", "integer",
                        "enum", List.of(new java.math.BigInteger("123456789012345678901234567890"),
                                java.math.BigInteger.valueOf(-22))),
                Map.<String, Object>of("$id", "urn:boolean-enum", "title", "Flags", "type", "boolean",
                        "enum", List.of(true, false)));
        var root = Files.createTempDirectory("canonical-enum-types-");
        try {
            for (int i = 0; i < sources.size(); i++) {
                var declarations = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { })
                        .process(List.of(new AIcdDefsCodegenSourceDocument(
                                AIngSourceInputKind_1.JSONDEFS, "enum" + i + ".json", sources.get(i)))).types();
                var names = Map.of(declarations.get(0).identity(),
                        new AIcDefsCodegenCanonicalSourceEmitter.Names(
                                "AIigCodes" + i, "AIigCodes" + i, "aiig_codes" + i));
                var emitted = new AIcDefsCodegenCanonicalSourceEmitter(profile(), names,
                        "test.output").render(declarations);
                var java = emitted.stream().filter(e -> e.language().equals("java")).findFirst().orElseThrow();
                var python = emitted.stream().filter(e -> e.language().equals("python")).findFirst().orElseThrow();
                if (i == 0) {
                    Assert.assertTrue(java.sourceText().contains("java.math.BigInteger code()"));
                    Assert.assertTrue(java.sourceText().contains("123456789012345678901234567890"));
                    Assert.assertTrue(python.sourceText().contains("123456789012345678901234567890"));
                } else {
                    Assert.assertTrue(java.sourceText().contains("Boolean code()"));
                    Assert.assertTrue(python.sourceText().contains("VALUE_1 = True"));
                    Assert.assertTrue(python.sourceText().contains("def code(self) -> bool"));
                }
                var file = root.resolve(java.relativePath());
                Files.createDirectories(file.getParent());
                Files.writeString(file, java.sourceText());
            }
            var files = List.of(root.resolve("test/output/AIigCodes0.java").toString(),
                    root.resolve("test/output/AIigCodes1.java").toString());
            Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                    "-d", root.resolve("classes").toString(), files.get(0), files.get(1)), 0);
        } finally {
            try (var walk = Files.walk(root)) {
                walk.sorted(java.util.Comparator.reverseOrder()).forEach(file -> {
                    try { Files.delete(file); }
                    catch (java.io.IOException failure) { throw new RuntimeException(failure); }
                });
            }
        }
    }

    /**
     * Verifies that the fully Java-native compiler uses each target's explicit
     * output composition, calls the required validation service for both
     * targets, and returns complete Java and Python source units.
     */
    @Test
    public void AIcNativeCompilerUsesNamingAndValidatesBothTargets() {
        var original = profile();
        var naming = new LinkedHashMap<String, Map<String, Object>>(original.nameCompositions());
        var className = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "AIig")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "identifier", "Convention", "upper_camel_case_1")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "_")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "variable", "Name", "version", "Regexp", "[0-9]+"))));
        var moduleName = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "aiig_")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "identifier", "Convention", "lower_snake_case_1")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "_")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "variable", "Name", "version", "Regexp", "[0-9]+"))));
        naming.put("test-class", className);
        naming.put("test-module", moduleName);
        var resolved = new AIcCodegenNamingProfileResolver.Profile(original.commonProfileId(),
                original.commonRoles(), original.defsRoles(), original.sdoRoles(), original.schemaMetadata(),
                original.indexesStartingFrom(), naming);
        var compositions = Map.of("interface", "test-class", "interface_file", "test-class",
                "enum", "test-class", "enum_file", "test-class");
        var pythonCompositions = Map.of("interface", "test-class", "interface_file", "test-module",
                "enum", "test-class", "enum_file", "test-module");
        var validationCalls = new java.util.concurrent.atomic.AtomicInteger();
        var compiler = new AIcDefsCodegenCanonicalCompiler(resolved, resolved,
                payload -> {
                    Assert.assertTrue(payload.containsKey("types"));
                    validationCalls.incrementAndGet();
                }, compositions, pythonCompositions, Map.of("*", "7"), "test.compiler");
        var schema = Map.<String, Object>of("$id", "urn:compiler", "$defs", Map.of(
                "Person", Map.of("type", "object", "properties", Map.of(
                        "full-name", Map.of("type", "string"))),
                "Status", Map.of("type", "string", "enum", List.of("ready", "closed"))));
        var outputs = compiler.compile(List.of(new AIcdDefsCodegenSourceDocument(
                AIngSourceInputKind_1.JSONDEFS, "compiler.json", schema)));
        Assert.assertEquals(validationCalls.get(), 2);
        Assert.assertEquals(outputs.size(), 4);
        Assert.assertTrue(outputs.stream().anyMatch(value -> value.language().equals("java")
                && value.relativePath().endsWith("AIigPerson_7.java")
                && value.sourceText().contains("getFullName()")));
        Assert.assertTrue(outputs.stream().anyMatch(value -> value.language().equals("python")
                && value.relativePath().endsWith("aiig_person_7.py")
                && value.sourceText().contains("getFullName")));
    }

    /**
     * Checks cross-catalog name reference normalization and refusal to override
     * existing naming definitions with incompatible external catalog entries.
     */
    @Test
    public void AIcNativeCompilerImportsSourcecodeNamingFragments() {
        var prefix = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "constant_string", "Value", "AIig"))));
        var whole = Map.<String, Object>of("Segments", List.of(
                Map.of("NameFragmentsSegmentReference", Map.of("Ref", "test-prefix")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "identifier", "Convention", "upper_camel_case_1")),
                Map.of("NameFragmentsSegmentValue", Map.of("Kind", "variable", "Name", "version", "Regexp", "[0-9]+"))));
        var catalog = Map.<String, Object>of("NameFragments", Map.of("test-prefix", prefix),
                "NameCompositions", Map.of("test-full", whole));
        var merged = AIcCodegenNamingProfileResolver.withExternalSourcecodeConventions(profile(), catalog);
        Assert.assertEquals(merged.composedName("test-full", "some_name", Map.of("version", "3")),
                "AIigSomeName3");
        boolean conflict = false;
        try {
            AIcCodegenNamingProfileResolver.withExternalSourcecodeConventions(profile(),
                    Map.of("NameCompositions", Map.of("test-get", whole)));
        } catch (IllegalArgumentException expected) {
            conflict = true;
        }
        Assert.assertTrue(conflict);
    }


    /**
     * Verifies XSD direct repeated particles generate typed Java and Python list
     * accessors without changing their canonical LIST group-child structure.
     *
     * @throws Exception when temporary compilation fails
     */
    @Test
    public void AIcNativeJavaEmitterSupportsDirectUnboundedXsdList() throws Exception {
        String xsd = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                  <xs:complexType name="Order"><xs:sequence>
                    <xs:element name="line" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
                  </xs:sequence></xs:complexType>
                </xs:schema>
                """;
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                        "order.xsd", xsd))).types();
        Assert.assertEquals(types.size(), 1);
        var symbols = Map.of(types.get(0).identity(),
                new AIcDefsCodegenCanonicalSourceEmitter.Names("AIigOrder", "AIigOrder", "aiig_order"));
        var outputs = new AIcDefsCodegenCanonicalSourceEmitter(profile(), symbols, "test.output").render(types);
        var javaOutput = outputs.stream().filter(item -> item.language().equals("java")).findFirst().orElseThrow();
        var python = outputs.stream().filter(item -> item.language().equals("python")).findFirst().orElseThrow();
        Assert.assertTrue(javaOutput.sourceText().contains("java.util.List<? extends String> getLine()"));
        Assert.assertTrue(!javaOutput.sourceText().contains("void setLine(java.util.List<String> aValue)"));
        Assert.assertTrue(python.sourceText().contains("def getLine(self) -> list[str]"));
        Assert.assertTrue(!python.sourceText().contains("def setLine(self, value: list[str])"));
        var folder = Files.createTempDirectory("canonical-repeated-list-");
        try {
            var file = folder.resolve(javaOutput.relativePath());
            Files.createDirectories(file.getParent());
            Files.writeString(file, javaOutput.sourceText(), StandardCharsets.UTF_8);
            Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                    "-d", folder.toString(), file.toString()), 0);
        } finally {
            try (var walk = Files.walk(folder)) {
                walk.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
                    try { Files.delete(path); }
                    catch (java.io.IOException failure) { throw new RuntimeException(failure); }
                });
            }
        }
    }

    /**
     * Nontrivial XSD collection bounds must be retained in both emitted languages.
     * The property presence and the number of list items are separate metadata.
     */
    @Test
    public void AIcNativeJavaEmitterPreservesBoundedXsdList() {
        String xsd = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                  <xs:complexType name="Order"><xs:sequence>
                    <xs:element name="line" type="xs:string" minOccurs="1" maxOccurs="5"/>
                  </xs:sequence></xs:complexType>
                </xs:schema>
                """;
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                        "order.xsd", xsd))).types();
        var symbols = Map.of(types.get(0).identity(),
                new AIcDefsCodegenCanonicalSourceEmitter.Names("AIigOrder", "AIigOrder", "aiig_order"));
        var output = new AIcDefsCodegenCanonicalSourceEmitter(profile(), symbols, "test.output").render(types);
        String java = output.stream().filter(item -> item.language().equals("java"))
                .findFirst().orElseThrow().sourceText();
        String python = output.stream().filter(item -> item.language().equals("python"))
                .findFirst().orElseThrow().sourceText();
        Assert.assertTrue(java.contains("minItemCount = 1, maxItemCount = 5"), java);
        Assert.assertTrue(java.contains("AIaDataObjectFieldListConstraints(minItems = 1, maxItems = 5)"), java);
        Assert.assertTrue(python.contains("min_item_count=1, max_item_count=5"), python);
        Assert.assertTrue(python.contains("AIaDataObjectFieldListConstraints(min_items = 1, max_items = 5)"), python);
    }

    /** Verify JSON array lengths without converting an optional property to required. */
    @Test
    public void AIcNativeJavaEmitterRetainsJsonItemBoundsAndOptionality() {
        var array = Map.<String, Object>of("type", "array", "minItems", 2, "maxItems", 4,
                "items", Map.of("type", "string"));
        var schema = Map.<String, Object>of("$id", "urn:java-item-bounds", "title", "Bounded",
                "type", "object", "properties", Map.of("items", array));
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                        "bounds.json", schema))).types();
        var symbols = Map.of(types.get(0).identity(),
                new AIcDefsCodegenCanonicalSourceEmitter.Names("AIigBounded", "AIigBounded", "aiig_bounded"));
        var output = new AIcDefsCodegenCanonicalSourceEmitter(profile(), symbols, "test.output").render(types);
        String java = output.stream().filter(item -> item.language().equals("java"))
                .findFirst().orElseThrow().sourceText();
        String python = output.stream().filter(item -> item.language().equals("python"))
                .findFirst().orElseThrow().sourceText();
        Assert.assertTrue(java.contains("minItemCount = 2, maxItemCount = 4"), java);
        Assert.assertTrue(python.contains("min_item_count=2, max_item_count=4"), python);
        Assert.assertTrue(java.contains("presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED"), java);
        Assert.assertTrue(python.contains("presence=AInFieldPresenceKind.ALLOWED"), python);
    }

    /**
     * Verifies that the native Java renderer avoids Unicode pre-translation
     * of control characters in source literals and in Javadoc comments.
     *
     * @throws Exception when generated sources cannot be compiled
     */
    @Test
    public void AIcNativeJavaEmitterSafelyQuotesControlCharacterEnum() throws Exception {
        var source = Map.<String, Object>of("$id", "urn:quoted", "type", "string",
                "enum", List.of("a" + (char) 1 + "b", "literal" + (char) 92 + "u000a"));
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                        "quoted.json", source))).types();
        var symbols = Map.of(types.get(0).identity(),
                new AIcDefsCodegenCanonicalSourceEmitter.Names("AIigQuoted", "AIigQuoted", "aiig_quoted"));
        var output = new AIcDefsCodegenCanonicalSourceEmitter(profile(), symbols, "test.output").render(types);
        var javaOutput = output.stream().filter(item -> item.language().equals("java")).findFirst().orElseThrow();
        Assert.assertTrue(javaOutput.sourceText().contains("[U+0001]"));
        Assert.assertTrue(javaOutput.sourceText().contains("\\001"));
        Assert.assertTrue(!javaOutput.sourceText().contains("\\u0001"));
        var folder = Files.createTempDirectory("canonical-quoted-enum-");
        try {
            var file = folder.resolve(javaOutput.relativePath());
            Files.createDirectories(file.getParent());
            Files.writeString(file, javaOutput.sourceText(), StandardCharsets.UTF_8);
            Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                    "-d", folder.toString(), file.toString()), 0);
        } finally {
            try (var walk = Files.walk(folder)) {
                walk.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
                    try { Files.delete(path); }
                    catch (java.io.IOException failure) { throw new RuntimeException(failure); }
                });
            }
        }
    }

    /**
     * Keys on top-level XML elements must be rejected, not accidentally
     * omitted while the frontend is collecting only named complex types.
     */
    @Test
    public void AIcNativeJavaFrontendRejectsGlobalXmlKeyConstraints() {
        for (String constraint : List.of("key", "unique", "keyref")) {
            String xsd = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">"
                    + "<xs:complexType name=\"Container\"><xs:sequence>"
                    + "<xs:element name=\"entry\" type=\"xs:string\" maxOccurs=\"unbounded\"/>"
                    + "</xs:sequence></xs:complexType>"
                    + "<xs:element name=\"root\" type=\"Container\"><xs:" + constraint
                    + " name=\"identity\"><xs:selector xpath=\"./entry\"/>"
                    + "<xs:field xpath=\".\"/></xs:" + constraint + "></xs:element></xs:schema>";
            boolean rejected = false;
            try {
                new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                        new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                                "keys.xsd", xsd)));
            } catch (IllegalArgumentException expected) {
                Throwable cause = expected.getCause();
                rejected = expected.getMessage().contains("keys.xsd") && cause != null
                        && cause instanceof UnsupportedOperationException
                        && (cause.getMessage().contains("identity constraints")
                            || cause.getMessage().contains("keyref/identityConstraint"));
            }
            Assert.assertTrue(rejected);
        }
    }

    /**
     * Verifies local composite xs:key / xs:unique remain contextual definitions
     * on the owning element while the referenced LIST retains its original type.
     * The scoped Java annotations and Python runtime metadata must agree, and
     * the referenced list still implements the public multi-mapped-list API.
     *
     * @throws Exception when source staging or javac compilation fails
     */
    @Test
    public void AIcNativeJavaEmitterSupportsCompositeIndexedList() throws Exception {
        String xsd = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:t="urn:employees"
                           targetNamespace="urn:employees">
                  <xs:complexType name="Employee"><xs:sequence>
                    <xs:element name="department" type="xs:string"/>
                    <xs:element name="identity"><xs:complexType><xs:sequence>
                      <xs:element name="code" type="xs:string"/>
                    </xs:sequence></xs:complexType></xs:element>
                  </xs:sequence></xs:complexType>
                  <xs:complexType name="Organization"><xs:sequence>
                    <xs:element name="staff"><xs:complexType><xs:sequence>
                      <xs:element name="employee" type="t:Employee" minOccurs="0" maxOccurs="unbounded"/>
                    </xs:sequence></xs:complexType>
                      <xs:key name="ByDepartmentAndCode"><xs:selector xpath="./employee"/>
                        <xs:field xpath="department"/><xs:field xpath="./identity/code"/>
                      </xs:key>
                      <xs:unique name="UniqueDepartment"><xs:selector xpath="employee"/>
                        <xs:field xpath="department"/>
                      </xs:unique>
                    </xs:element>
                  </xs:sequence></xs:complexType>
                </xs:schema>
                """;
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                        "staff.xsd", xsd))).types();
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> symbols = new LinkedHashMap<>();
        int index = 0;
        for (var type : AIcDefsCodegenCanonicalSourceEmitter.declarations(types)) {
            String name = "AIigIndex" + index;
            symbols.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    name, name, "aiig_index" + index));
            index++;
        }
        var sources = new AIcDefsCodegenCanonicalSourceEmitter(profile(), symbols, "test.output").render(types);
        String allJava = sources.stream().filter(file -> file.language().equals("java"))
                .map(AIcDefsCodegenCanonicalSourceEmitter.Output::sourceText)
                .reduce("", String::concat);
        String allPython = sources.stream().filter(file -> file.language().equals("python"))
                .map(AIcDefsCodegenCanonicalSourceEmitter.Output::sourceText)
                .reduce("", String::concat);
        Assert.assertTrue(allJava.contains("AIiMultiMappedList<? extends AIigIndex"));
        Assert.assertTrue(allJava.contains("String KEY_ID__BY_DEPARTMENT_AND_CODE = \"ByDepartmentAndCode\";"));
        Assert.assertTrue(allJava.contains("name = CONSTOrganization.KEY_ID__BY_DEPARTMENT_AND_CODE"));
        Assert.assertTrue(allJava.contains("name = CONSTOrganization.KEY_ID__UNIQUE_DEPARTMENT"));
        Assert.assertTrue(allJava.contains("selector = \"employee\""));
        Assert.assertTrue(allJava.contains("fields = {CONSTOrganization.FIELD_NAME__DEPARTMENT, CONSTOrganization.FIELD_NAME__IDENTITY_CODE}, required = true"));
        Assert.assertTrue(allJava.contains("fields = {CONSTOrganization.FIELD_NAME__DEPARTMENT}, required = false"));
        Assert.assertTrue(allPython.contains("__scoped_key_definitions__"));
        Assert.assertTrue(allPython.contains("KEY_ID__BY_DEPARTMENT_AND_CODE = \"ByDepartmentAndCode\""));
        Assert.assertTrue(allPython.contains("(\"employee\", \"ByDepartmentAndCode\", (\"department\", \"identity.code\""));
        Assert.assertTrue(allPython.contains("(\"employee\", \"UniqueDepartment\", (\"department\""));
        String colliding = xsd.replace("name=\"UniqueDepartment\"",
                "name=\"By_DepartmentAndCode\"");
        var collisionTypes = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                        "staff-collision.xsd", colliding))).types();
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> collidingSymbols = new LinkedHashMap<>();
        int collisionIndex = 0;
        for (var type : AIcDefsCodegenCanonicalSourceEmitter.declarations(collisionTypes)) {
            String symbol = "AIigIndex" + collisionIndex;
            collidingSymbols.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    symbol, symbol, "aiig_index" + collisionIndex));
            collisionIndex++;
        }
        boolean keyCollisionRejected = false;
        try {
            new AIcDefsCodegenCanonicalSourceEmitter(profile(), collidingSymbols,
                    "test.output").render(collisionTypes);
        } catch (IllegalArgumentException expected) {
            keyCollisionRejected = expected.getMessage().contains("Conflicting key ID constant");
        }
        Assert.assertTrue(keyCollisionRejected);
        var folder = Files.createTempDirectory("canonical-indexed-list-");
        try {
            List<String> command = new ArrayList<>();
            command.add("-d"); command.add(folder.resolve("classes").toString());
            for (var output : sources) {
                if (!output.language().equals("java")) continue;
                var file = folder.resolve(output.relativePath());
                Files.createDirectories(file.getParent());
                Files.writeString(file, output.sourceText());
                command.add(file.toString());
            }
            var common = java.nio.file.Path.of("pub.lib.General/common/util/src/product/java/");
            var metadata = java.nio.file.Path.of("pub.lib.General/data/dataobject/intf/src/product/java/");
            for (var filename : List.of("AIiMultiMappedList.java", "AIiKeyDefinition.java")) {
                command.add(common.resolve("eu/algites/lib/common/list/").resolve(filename).toString());
            }
            for (var filename : List.of("AIaKeyDefinition.java", "AIaKeyDefinitions.java")) {
                command.add(metadata.resolve("eu/algites/lib/data/dataobject/").resolve(filename).toString());
            }
            Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                    command.toArray(String[]::new)), 0);
        } finally {
            try (var walk = Files.walk(folder)) {
                walk.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
                    try { Files.delete(path); }
                    catch (java.io.IOException error) { throw new RuntimeException(error); }
                });
            }
        }
    }

    /**
     * A named keyed JSON map is a collection-valued field, not a second
     * DataObject which directly inherits a Java collection interface.
     */
    @Test
    public void AIcNamedIndexedMapUsesFieldCollectionInsteadOfTypeInheritance() {
        var source = new LinkedHashMap<String, Object>();
        source.put("$id", "https://example.org/named-map_1.json");
        source.put("type", "object");
        source.put("properties", Map.of("Entries", Map.of("$ref", "#/$defs/Entries")));
        source.put("$defs", Map.of("Entries", Map.of(
                "type", "object", "additionalProperties", Map.of("type", "string"),
                "x-algites-defscodegen-key", Map.of("id", "ByName", "field-name", "name"))));
        var types = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { })
                .process(List.of(new AIcdDefsCodegenSourceDocument(
                        AIngSourceInputKind_1.JSONDEFS, "indexed.json", source))).types();
        var declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(types);
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> names = new LinkedHashMap<>();
        for (int n = 0; n < declarations.size(); n++) {
            var type = declarations.get(n);
            names.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    "AIigIndex" + n, "AIigIndex" + n, "aiig_index" + n));
        }
        var output = new AIcDefsCodegenCanonicalSourceEmitter(profile(), names, "test.output")
                .render(types);
        var alias = declarations.stream().filter(type -> type.name().equals("Entries"))
                .findFirst().orElseThrow();
        Assert.assertTrue(output.stream().noneMatch(item -> item.typeIdentity().equals(alias.identity())));
        var java = output.stream().filter(item -> item.language().equals("java")
                && item.typeIdentity().equals(types.get(0).identity()))
                .findFirst().orElseThrow().sourceText();
        var python = output.stream().filter(item -> item.language().equals("python")
                && item.typeIdentity().equals(types.get(0).identity()))
                .findFirst().orElseThrow().sourceText();
        Assert.assertTrue(java.contains("AIiMultiMappedList<? extends AIigIndex"));
        Assert.assertTrue(java.contains("getEntries()"));
        Assert.assertTrue(python.contains("AIiMultiMappedList[AIigIndex"));
        Assert.assertTrue(python.contains("def getEntries("));
    }
}
