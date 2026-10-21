package eu.algites.tool.codegen.defs.impl.standard;


import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.lib.naming.convention.impl.algites.AIcAlgitesNamingProfiles_1;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.tools.ToolProvider;
import javax.xml.XMLConstants;
import javax.xml.validation.SchemaFactory;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Equivalent three-format fixtures and executable generated-source regressions. */
public final class AItcSchemaParityTest {
    private static final List<String> STEMS = List.of("parity-root", "parity-child", "parity-leaf", "parity-status", "parity-builtins");
    private static final List<String> SUFFIXES = List.of("yamldef.schema.json", "jsondef.schema.json", "xsd");
    private static final List<AInDefinitionSourceKind> KINDS = List.of(AInDefinitionSourceKind.YAMLDEFS, AInDefinitionSourceKind.JSONDEFS, AInDefinitionSourceKind.XMLDEFS);

    private Path resource(String name) throws Exception {
        return Path.of(getClass().getClassLoader().getResource(name).toURI());
    }

    private AIcdCanonicalDefinition load(String stem, int format) throws Exception {
        return new AIcDefaultDefsCodegenService().load(new AIcdDefinitionLoadRequest(
                resource(stem + "_1." + SUFFIXES.get(format)), KINDS.get(format), AIcAlgitesNamingProfiles_1.javaProfile()));
    }

    private AIcdCanonicalDefinition normalized(AIcdCanonicalDefinition model) {
        return new AIcdCanonicalDefinition("urn:parity:" + model.logicalName() + ":1", model.version(), model.logicalName(), AInDefinitionSourceKind.JSONDEFS, model.logicalName() + "_1.schema", model.description(), model.dataType(), model.enumValues(), null);
    }

    /** Compares full generated sources, retaining comments and constraints; only provenance differs. */
    @Test
    public void AIcThreeFormatParity() throws Exception {
        var service = new AIcDefaultDefsCodegenService();
        for (String stem : STEMS) {
            var models = List.of(load(stem, 0), load(stem, 1), load(stem, 2));
            var merged = AIcCanonicalDefinitionMerger.AIcMerge(models);
            for (var model : models) Assert.assertTrue(merged.description().contains(model.identity()));
            for (var target : AInCodeGenerationTarget.values()) {
                var profile = target == AInCodeGenerationTarget.JAVA ? AIcAlgitesNamingProfiles_1.javaProfile() : AIcAlgitesNamingProfiles_1.pythonProfile();
                var outputs = models.stream().map(model -> service.generate(new AIcdCodeGenerationRequest(
                        normalized(model), target, "parity_generated", profile))).toList();
                Assert.assertEquals(outputs.get(0), outputs.get(1));
                Assert.assertEquals(outputs.get(0), outputs.get(2));
            }
            SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI).newSchema(resource(stem + "_1.xsd").toFile());
        }
        var builtins = load("parity-builtins", 2);
        Assert.assertEquals(builtins.dataType().properties().size(), 46);
        var unsigned = builtins.dataType().properties().stream().filter(p -> p.sourceName().equals("unsignedLong")).findFirst().orElseThrow();
        Assert.assertEquals(unsigned.dataType().constraints().maximum(), "18446744073709551615");
        var root = load("parity-root", 2);
        Assert.assertEquals(root.dataType().properties().size(), 28);
        Assert.assertFalse(root.dataType().properties().stream().anyMatch(p -> p.sourceName().equals("inner")));
        var children = root.dataType().properties().stream().filter(p -> p.sourceName().equals("children")).findFirst().orElseThrow();
        Assert.assertEquals(children.dataType().elementType().kind(), AInDataTypeKind.REFERENCE);
        Assert.assertEquals(children.dataType().referencedDefinition().logicalName(), "parity-child");
    }

    /** Confirms that every frontend produces the same documented schema-field-name constants. */
    @Test
    public void AIcSchemaFieldNameConstantsAcrossAllDefinitionKinds() throws Exception {
        var service = new AIcDefaultDefsCodegenService();
        for (int format = 0; format < KINDS.size(); format++) {
            var model = load("parity-root", format);
            var javaSource = service.generate(new AIcdCodeGenerationRequest(
                    model, AInCodeGenerationTarget.JAVA, "parity_generated", AIcAlgitesNamingProfiles_1.javaProfile())).source();
            Assert.assertTrue(javaSource.contains("public static final String SCHEMA_FIELD_NAME__OPTIONAL_TEXT = \"optionalText\";"));
            Assert.assertTrue(javaSource.contains("<strong>Field Name:</strong> {@code optionalText}<br/>"));
            Assert.assertTrue(javaSource.contains("<strong>Field Description:</strong> Optional text value."));

            var pythonSource = service.generate(new AIcdCodeGenerationRequest(
                    model, AInCodeGenerationTarget.PYTHON, "parity_generated", AIcAlgitesNamingProfiles_1.pythonProfile())).source();
            Assert.assertTrue(pythonSource.contains("SCHEMA_FIELD_NAME__OPTIONAL_TEXT = \"optionalText\""));
            Assert.assertTrue(pythonSource.contains("**Field Name:** ``optionalText``"));
            Assert.assertTrue(pythonSource.contains("**Field Description:** Optional text value."));
        }
    }

    /**
     * Ensures Defs-specific constant designation does not depend on a fixed uppercase
     * schema-field prefix inside the generator or in the general naming catalog.
     */
    @Test
    public void AIcSchemaFieldConstantUsesChosenConstantStyle() {
        AIcGenerationNames names = new AIcGenerationNames();
        Assert.assertEquals(names.schemaFieldNameConstant("optionalText", AIcAlgitesNamingProfiles_1.javaProfile()),
                "SCHEMA_FIELD_NAME__OPTIONAL_TEXT");
        AIiNameConventionCatalog custom = new AIiNameConventionCatalog() {
            /** Identifies the standard Java generation profile. */
            @Override public Set<String> names() { return Set.of("algites-java-gen-intf-versioned_1"); }

            /** Renders identifiers as UpperCamel, independently of schema-field semantics. */
            @Override public String format(String profile, String structure, Map<String, String> values, String source) {
                Assert.assertEquals(structure, "constant_name");
                String identifier = values.get("identifier").replaceAll("(?<=[a-z])(?=[A-Z])", "_");
                StringBuilder result = new StringBuilder();
                for (String word : identifier.split("_")) {
                    if (word.isEmpty()) continue;
                    result.append(Character.toUpperCase(word.charAt(0)))
                            .append(word.substring(1).toLowerCase(java.util.Locale.ROOT));
                }
                return result.toString();
            }

            /** Parsing is not used by the name-rendering scenario. */
            @Override public Map<String, String> parse(String profile, String structure, String name) {
                throw new UnsupportedOperationException();
            }

            /** Filename matching is not used by the name-rendering scenario. */
            @Override public boolean matches(String profile, String structure, String name) {
                throw new UnsupportedOperationException();
            }
        };
        Assert.assertEquals(names.schemaFieldNameConstant("optionalText", custom), "SchemaFieldName__OptionalText");
    }

    /** Compiles all generated Java classes and imports all generated Python classes with nested references. */
    @Test
    public void AIcGeneratedContractsExecute() throws Exception {
        var service = new AIcDefaultDefsCodegenService();
        Path root = Files.createTempDirectory("defs-parity-generated-");
        var javaFiles = new ArrayList<String>();
        for (String stem : STEMS) {
            for (var target : AInCodeGenerationTarget.values()) {
                var profile = target == AInCodeGenerationTarget.JAVA ? AIcAlgitesNamingProfiles_1.javaProfile() : AIcAlgitesNamingProfiles_1.pythonProfile();
                var output = service.generate(new AIcdCodeGenerationRequest(load(stem, 2), target, "parity_generated", profile));
                Path path = root.resolve(output.relativePath());
                Files.createDirectories(path.getParent());
                Files.writeString(path, output.source());
                if (target == AInCodeGenerationTarget.JAVA) javaFiles.add(path.toString());
            }
        }
        var args = new ArrayList<String>(List.of("-d", root.toString()));
        args.addAll(javaFiles);
        Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null, args.toArray(String[]::new)), 0);
        Files.writeString(root.resolve("parity_generated/__init__.py"), "");
        var process = new ProcessBuilder("python3", "-c", """
                import importlib, pathlib, typing
                from decimal import Decimal
                for path in pathlib.Path('parity_generated').glob('*.py'):
                    module=importlib.import_module('parity_generated.'+path.stem)
                    for cls in vars(module).values():
                        if isinstance(cls,type) and hasattr(cls,'from_mapping'): typing.get_type_hints(cls)
                from parity_generated.aicgd_parity_child_1 import AIcgdParityChild_1
                wire={'name':'parent','detail':{'label':'leaf','quantity':10**90}}
                assert AIcgdParityChild_1.from_mapping(wire).to_mapping()==wire
                from parity_generated.aicgd_parity_builtins_1 import _ai_convert
                assert _ai_convert('12345678901234567890.1234567890123456789','decimal','NUMBER')==Decimal('12345678901234567890.1234567890123456789')
                assert _ai_convert('01FF','hexBinary','STRING')==b'\\x01\\xff'
                """).directory(root.toFile()).redirectErrorStream(true).start();
        String output = new String(process.getInputStream().readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        Assert.assertEquals(process.waitFor(), 0, output);
    }

    /** Checks constraints independently of agreement between the schema readers. */
    @Test
    public void AIcExactJavaNumbersAndConstraints() throws Exception {
        Path root = Files.createTempDirectory("defs-exact-numbers-");
        Path schema = root.resolve("exact_1.jsondef.schema.json");
        Files.writeString(schema, """
                {"type":"object","properties":{"integer":{"type":"integer"},"decimal":{"type":"number"},
                "byte":{"type":"integer","x-modustro-datatype":"byte"},
                "text":{"type":"string","minLength":2,"maxLength":5,"pattern":"[A-Z]+"}},
                "required":["integer","decimal","byte","text"]}
                """);
        var service = new AIcDefaultDefsCodegenService();
        var model = service.load(new AIcdDefinitionLoadRequest(schema, AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles_1.javaProfile()));
        var output = service.generate(new AIcdCodeGenerationRequest(model, AInCodeGenerationTarget.JAVA, "exact_generated", AIcAlgitesNamingProfiles_1.javaProfile()));
        Path source = root.resolve(output.relativePath());
        Files.createDirectories(source.getParent());
        Files.writeString(source, output.source());
        Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null, "-d", root.toString(), source.toString()), 0);
        try (var loader = new URLClassLoader(new java.net.URL[]{root.toUri().toURL()})) {
            Class<?> type = loader.loadClass("exact_generated." + output.typeName());
            var constructor = type.getDeclaredConstructor(BigInteger.class, BigDecimal.class, BigInteger.class, String.class);
            BigInteger huge = BigInteger.TEN.pow(90);
            BigDecimal precise = new BigDecimal("12345678901234567890.1234567890123456789");
            Object value = constructor.newInstance(huge, precise, BigInteger.valueOf(127), "ABC");
            Assert.assertEquals(type.getMethod("integer").invoke(value), huge);
            Assert.assertEquals(type.getMethod("decimal").invoke(value), precise);
            Assert.expectThrows(java.lang.reflect.InvocationTargetException.class,
                    () -> constructor.newInstance(huge, precise, BigInteger.valueOf(128), "ABC"));
            Assert.expectThrows(java.lang.reflect.InvocationTargetException.class,
                    () -> constructor.newInstance(huge, precise, BigInteger.valueOf(1), "TOOLONG"));
        }
    }
    /** Resolves canonical URN identities and retains decimal facets without a double conversion. */
    @Test
    public void AIcCanonicalUrnAndExactFacets() throws Exception {
        Path root = Files.createTempDirectory("defs-urn-").resolve("yamldefs");
        Files.createDirectories(root);
        Files.writeString(root.resolve("leaf_1.yamldef.schema.json"), """
                {"$id":"urn:tests:leaf:1","$defs":{"value":{"$anchor":"Content","type":"number",
                "minimum":0.12345678901234567890123456789}},"type":"object","properties":{}}
                """);
        Path schema = root.resolve("root_1.yamldef.schema.json");
        Files.writeString(schema, """
                {"type":"object","properties":{"inline":{"$ref":"urn:tests:leaf:1#Content"},"leaf":{"$ref":"urn:tests:leaf:1"}}}
                """);
        var model = new AIcDefaultDefsCodegenService().load(new AIcdDefinitionLoadRequest(schema,
                AInDefinitionSourceKind.YAMLDEFS, AIcAlgitesNamingProfiles_1.javaProfile()));
        Assert.assertEquals(model.dataType().properties().get(0).dataType().constraints().minimum(), "0.12345678901234567890123456789");
        Assert.assertEquals(model.dataType().properties().get(1).dataType().referencedDefinition().logicalName(), "leaf");
    }

    /** Excludes transient generated/build copies while retaining legitimate devops/build source directories. */
    @Test
    public void AIcCanonicalReferencesIgnoreBuildWorkspaces() throws Exception {
        for (String locKind : java.util.List.of("yamldefs", "jsondefs")) {
            Path locRepository = Files.createTempDirectory("defs-owned-roots-");
            Files.writeString(locRepository.resolve("modustro-source-repository.yml"), "SourceRepository: {}\n");
            String locSuffix = locKind.equals("yamldefs") ? ".yamldef.schema.json" : ".jsondef.schema.json";
            Path locOwner = Files.createDirectories(locRepository.resolve("devops/build/owner/src/product/" + locKind + "/example"));
            String locId = "https://defs.example.test/api/" + locKind + "/example/leaf_1" + locSuffix;
            String locLeaf = "{\"$id\":\"" + locId + "\",\"type\":\"object\",\"properties\":{}}";
            Files.writeString(locOwner.resolve("leaf_1" + locSuffix), locLeaf);
            Path locTransient = Files.createDirectories(locRepository.resolve("build/run/owner/project/src/product/" + locKind + "/example"));
            Files.writeString(locTransient.resolve("leaf_1" + locSuffix), locLeaf);
            Path locConsumer = Files.createDirectories(locRepository.resolve("consumer/src/product/" + locKind));
            Path locRoot = locConsumer.resolve("root_1" + locSuffix);
            Files.writeString(locRoot, "{\"type\":\"object\",\"properties\":{\"leaf\":{\"$ref\":\"" + locId + "\"}}}");
            var locModel = new AIcDefaultDefsCodegenService().load(new AIcdDefinitionLoadRequest(locRoot,
                locKind.equals("yamldefs") ? AInDefinitionSourceKind.YAMLDEFS : AInDefinitionSourceKind.JSONDEFS,
                AIcAlgitesNamingProfiles_1.javaProfile()));
            Assert.assertEquals(locModel.dataType().properties().get(0).dataType().referencedDefinition().logicalName(), "leaf");
            String locUrn = "urn:tests:owned-leaf:1";
            Files.writeString(locOwner.resolve("leaf_1" + locSuffix), locLeaf.replace(locId, locUrn));
            Files.writeString(locRoot, "{\"type\":\"object\",\"properties\":{\"leaf\":{\"$ref\":\"" + locUrn + "\"}}}");
            Files.writeString(locTransient.resolve("leaf_1" + locSuffix), "{broken transient JSON");
            locModel = new AIcDefaultDefsCodegenService().load(new AIcdDefinitionLoadRequest(locRoot,
                locKind.equals("yamldefs") ? AInDefinitionSourceKind.YAMLDEFS : AInDefinitionSourceKind.JSONDEFS,
                AIcAlgitesNamingProfiles_1.javaProfile()));
            Assert.assertEquals(locModel.dataType().properties().get(0).dataType().referencedDefinition().logicalName(), "leaf");
        }
    }

}
