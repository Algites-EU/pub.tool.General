package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalList;
import eu.algites.tool.codegen.defs.model.AIngSourceInputKind_1;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Native Java JSONDEFS/YAMLDEFS indexed-map parity regression. These scenarios
 * are identical to the Python native frontend's homogeneous-map rules.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenCanonicalIndexedMapParityTest {
    /**
     * Create minimal explicitly selected naming rules for synthetic types.
     * @return catalog-backed naming profile with no implicit language prefixes
     */
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        var fragment = Map.<String, Object>of("NameFragmentsSegmentValue", Map.of(
                "Kind", "identifier", "Convention", "upper_camel"));
        var composition = Map.<String, Object>of("Segments", List.of(fragment));
        return new AIcCodegenNamingProfileResolver.Profile("test", Map.of(),
                Map.of("synthetic_list_item_type", "compose"), Map.of(), Map.of(), 1,
                Map.of("compose", composition));
    }

    /**
     * Construct an indexed map whose explicit names share the same value schema.
     * @param differing whether one explicit property's schema is different
     * @return JSON Schema root
     */
    private static Map<String, Object> schema(boolean differing) {
        Map<String, Object> value = Map.of("type", "string");
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("type", "object");
        map.put("x-algites-defscodegen-key", Map.of("id", "UniqueStructureRoles", "field-name", "kind"));
        map.put("propertyNames", Map.of("type", "string"));
        map.put("additionalProperties", value);
        map.put("properties", Map.of("standard_getter", differing
                ? Map.of("type", "string", "minLength", 1) : value, "raw_getter", value));
        return Map.of("$id", "urn:parity", "title", "Naming", "type", "object",
                "properties", Map.of("StructureNaming", map));
    }

    /** Accept homogeneous explicit properties as one key-indexed collection. */
    @Test
    public void homogeneousExplicitPropertiesProduceSameKeyedList() {
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
            var original = schema(false);
            var withProperties = frontend.loadJsonOrYaml(original, "schema.json", kind);
            @SuppressWarnings("unchecked")
            Map<String, Object> altered = new LinkedHashMap<>(original);
            @SuppressWarnings("unchecked")
            var wrapper = new LinkedHashMap<String, Object>((Map<String, Object>) original.get("properties"));
            @SuppressWarnings("unchecked")
            var indexed = new LinkedHashMap<String, Object>((Map<String, Object>) wrapper.get("StructureNaming"));
            indexed.remove("properties");
            wrapper.put("StructureNaming", indexed);
            altered.put("properties", wrapper);
            Assert.assertEquals(frontend.loadJsonOrYaml(altered, "schema.json", kind), withProperties);
            var group = (AIcDefsCanonicalElementList) withProperties.structure();
            var indexedList = (AIcDefsCanonicalList) group.children().get(0);
            Assert.assertEquals(indexedList.keyDefinitions().get(0).identifier(), "UniqueStructureRoles");
            Assert.assertEquals(indexedList.keyDefinitions().get(0).fields(), List.of("kind"));
        }
    }

    /** Reject per-key constraints until they can be represented losslessly. */
    @Test
    public void differentValueConstraintsRemainUnsupported() {
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            try {
                new AIcDefsCodegenCanonicalSchemaFrontend(profile())
                        .loadJsonOrYaml(schema(true), "schema.json", kind);
                Assert.fail("Distinct explicit property constraint was silently discarded");
            } catch (UnsupportedOperationException expected) {
                Assert.assertTrue(expected.getMessage().contains("property constraints"));
            }
        }
    }
}
