package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Native Java frontend/emitter parity for top-level XML ELEMENT declarations.
 * Python's Defs CLI and the Java frontend must represent XSD element-scoped
 * identity constraints identically without altering a shared named TYPE.
 */
public final class AItcDefsCodegenCanonicalGlobalElementParityTest {
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        return new AIcCodegenNamingProfileResolver.Profile("test", Map.of(), Map.of(),
                Map.of(), Map.of(), 1, Map.of());
    }

    private static final String KEYED_ROOT = """
        <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
            xmlns:t="urn:profiles" targetNamespace="urn:profiles"
            elementFormDefault="qualified" attributeFormDefault="unqualified">
          <xs:complexType name="ProfileType">
            <xs:attribute name="Id" type="xs:string" use="required"/>
          </xs:complexType>
          <xs:complexType name="ProfilesType"><xs:sequence>
            <xs:element name="Profile" type="t:ProfileType" minOccurs="0"
                maxOccurs="unbounded"/>
          </xs:sequence></xs:complexType>
          <xs:element name="CredentialProfiles" type="t:ProfilesType">
            <xs:key name="UniqueProfileId">
              <xs:selector xpath="t:Profile"/><xs:field xpath="@Id"/>
            </xs:key>
          </xs:element>
        </xs:schema>
        """;

    @Test
    public void AIcGlobalElementCarriesIndexedListKeyWithoutMutatingNamedType() {
        var types = new AIcDefsCodegenCanonicalSchemaFrontend(profile())
                .loadXsd(KEYED_ROOT, "profiles.xsd", "1");
        Assert.assertEquals(types.size(), 3);
        var named = types.get(1);
        var root = types.get(2);
        Assert.assertEquals(root.name(), "CredentialProfiles");
        Assert.assertEquals(root.sourceBindings().get(AIngSourceInputKind_1.XMLDEFS)
                .get(0).representationKind(), "xs:element");
        var rootList = (AIcDefsCanonicalList) ((AIcDefsCanonicalElementList)
                root.structure()).children().get(0);
        var namedList = (AIcDefsCanonicalList) ((AIcDefsCanonicalElementList)
                named.structure()).children().get(0);
        Assert.assertEquals(rootList.name(), "Profile");
        Assert.assertTrue(namedList.keyDefinitions().isEmpty(),
                "A global-element key must not mutate the reused named TYPE");
        Assert.assertEquals(rootList.keyDefinitions().size(), 1);
        Assert.assertEquals(rootList.keyDefinitions().get(0).identifier(), "UniqueProfileId");
        Assert.assertEquals(rootList.keyDefinitions().get(0).selector(), "Profile");
        Assert.assertEquals(rootList.keyDefinitions().get(0).fields(), List.of("@Id"));
        Assert.assertEquals(rootList.xmlWire().namespaceUri(), "urn:profiles");
    }

    @Test
    public void AIcGlobalElementAndNamedTypeUseDistinctXsdSymbolSpaces() {
        var types = new AIcDefsCodegenCanonicalSchemaFrontend(profile()).loadXsd("""
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:t="urn:profiles" targetNamespace="urn:profiles">
              <xs:complexType name="Shared"/>
              <xs:element name="Shared" type="t:Shared"/>
            </xs:schema>
            """, "shared.xsd", "1");
        Assert.assertEquals(types.size(), 2);
        Assert.assertEquals(types.get(0).identity(), "{urn:profiles}Shared");
        Assert.assertEquals(types.get(1).identity(), "{urn:profiles}Shared#element");
        Assert.assertEquals(types.get(1).name(), "SharedElement");
        var element = types.get(1);
        var renderer = new AIcDefsCodegenCanonicalSourceEmitter(profile(), Map.of(
                element.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                        "AIigSharedElement_1", "AIigSharedElement_1", "aiig_shared_element_1")),
                "parity.test");
        var generated = renderer.render(List.of(element));
        Assert.assertEquals(generated.size(), 2);
        for (var output : generated) {
            Assert.assertTrue(output.sourceText().contains("AInXmlObjectDefinitionKind.ELEMENT"),
                    output.language());
            Assert.assertTrue(output.sourceText().contains("Shared"), output.language());
            Assert.assertTrue(output.sourceText().contains("urn:profiles"), output.language());
        }
    }

    @Test
    public void AIcSelectorPrefixMustResolveToTheActualXmlElementNamespace() {
        var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
        Assert.expectThrows(IllegalArgumentException.class, () -> frontend.loadXsd(
                KEYED_ROOT.replace("t:Profile\"", "missing:Profile\""),
                "missing-prefix.xsd", "1"));
        Assert.expectThrows(UnsupportedOperationException.class, () -> frontend.loadXsd(
                KEYED_ROOT.replace("t:Profile\"", "t:Profile[@Id]\""),
                "unsupported-xpath.xsd", "1"));
    }

    @Test
    public void AIcJsonYamlExplicitRootContractNameMatchesPythonFrontend() {
        var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS, AIngSourceInputKind_1.YAMLDEFS)) {
            var root = frontend.loadJsonOrYaml(Map.of("type", "object",
                    "x-algites-defscodegen-root-type-name", "CredentialDocument"),
                    "credentials.schema", kind, "", "1");
            Assert.assertEquals(root.name(), "CredentialDocument");
            Assert.expectThrows(IllegalArgumentException.class, () -> frontend.loadJsonOrYaml(
                    Map.of("type", "object", "x-algites-defscodegen-root-type-name", "invalid-name!"),
                    "credentials.schema", kind, "", "1"));
        }
    }

    /**
     * A root reference to an explicitly named local definition is a JSON Schema
     * validation alias, not an additional generated contract.
     */
    @Test
    public void AIcDirectNamedRootAliasProducesOnlyItsNamedDefinition() {
        var schema = Map.<String, Object>of(
                "$ref", "#/$defs/CredentialDocument",
                "x-algites-schema-id", "eu.algites.lib.security.credentials.core.credential-document",
                "$defs", Map.of("CredentialDocument", Map.of("type", "object",
                        "properties", Map.of("Profile", Map.of("type", "array",
                                "items", Map.of("type", "string"))))));
        var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS, AIngSourceInputKind_1.YAMLDEFS)) {
            var types = frontend.loadJsonOrYamlTypes(schema,
                    "credential-document_1.schema.json", kind, "CredentialDocument", "1");
            Assert.assertEquals(types.size(), 1);
            Assert.assertEquals(types.get(0).name(), "CredentialDocument");
            Assert.assertEquals(types.get(0).sourceBindings().get(kind).get(0).representationKind(),
                    "$defs");
        }
    }

    /** Naming rules used only for a complete root/list emission parity test. */
    private static AIcCodegenNamingProfileResolver.Profile emissionProfile() {
        var identifier = Map.<String, Object>of("NameFragmentsSegmentValue",
                Map.of("Kind", "identifier", "Convention", "upper_camel_case_1"));
        var get = Map.<String, Object>of("NameFragmentsSegmentValue",
                Map.of("Kind", "constant_string", "Value", "get"));
        var set = Map.<String, Object>of("NameFragmentsSegmentValue",
                Map.of("Kind", "constant_string", "Value", "set"));
        var list = Map.<String, Object>of("NameFragmentsSegmentValue",
                Map.of("Kind", "constant_string", "Value", "List"));
        var constant = Map.<String, Object>of("NameFragmentsSegmentValue",
                Map.of("Kind", "constant_string", "Value", "Const"));
        return new AIcCodegenNamingProfileResolver.Profile("test",
                Map.of("standard_getter", "get", "list_getter", "get-list",
                        "standard_setter", "set", "const_container_interface", "const"),
                Map.of(), Map.of(), Map.of(), 1,
                Map.of("get", Map.of("Segments", List.of(get, identifier)),
                        "get-list", Map.of("Segments", List.of(get, identifier, list)),
                        "set", Map.of("Segments", List.of(set, identifier)),
                        "const", Map.of("Segments", List.of(constant, identifier))));
    }

    /**
     * A global key must survive real model linking and complete Java/Python
     * source emission, including the canonical List getter naming convention.
     */
    @Test
    public void AIcIndexedGlobalElementEmitsTypedGetterAndKeyInBothLanguages() {
        var naming = emissionProfile();
        var linked = AIcDefsCodegenCanonicalModelLinker.link(
                new AIcDefsCodegenCanonicalSchemaFrontend(naming)
                        .loadXsd(KEYED_ROOT, "profiles.xsd", "1"));
        Map<String, AIcDefsCodegenCanonicalSourceEmitter.Names> names =
                new java.util.LinkedHashMap<>();
        for (var type : linked) {
            var javaName = "AIig" + type.name() + "_1";
            names.put(type.identity(), new AIcDefsCodegenCanonicalSourceEmitter.Names(
                    javaName, javaName, "aiig_" + type.name().toLowerCase(java.util.Locale.ROOT) + "_1"));
        }
        var outputs = new AIcDefsCodegenCanonicalSourceEmitter(naming, names, "parity.test")
                .render(linked);
        for (var language : List.of("java", "python")) {
            var root = outputs.stream().filter(item -> item.language().equals(language)
                    && item.typeIdentity().equals(linked.get(2).identity()))
                    .findFirst().orElseThrow();
            Assert.assertTrue(root.sourceText().contains("AInXmlObjectDefinitionKind.ELEMENT"), language);
            Assert.assertTrue(root.sourceText().contains("getProfileList"), language);
            Assert.assertTrue(root.sourceText().contains("UniqueProfileId"), language);
        }
    }

}
