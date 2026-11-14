package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Regression guard against lossy JSONDEFS/YAMLDEFS/XMLDEFS source ingestion. */
public final class AItcDefsCodegenCanonicalLosslessTest {
    /**
     * Creates the minimum explicit Common naming profile for simple schema cases.
     * @return resolved naming profile
     */
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        return new AIcCodegenNamingProfileResolver.Profile("test",
                Map.of("standard_getter", "unused", "standard_setter", "unused"),
                Map.of(), Map.of(), Map.of(), 1, Map.of());
    }

    /** Rejects validation rules absent from the current seven-kind contract. */
    @Test
    public void AIcJsonConstraintsMustNotBeSilentlyDiscarded() {
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            for (var keyword : List.of("minLength", "pattern", "minimum", "multipleOf",
                    "uniqueItems", "minProperties", "readOnly", "writeOnly")) {
                Object value = switch (keyword) {
                    case "pattern" -> "^[A-Z]$";
                    case "uniqueItems", "readOnly", "writeOnly" -> Boolean.TRUE;
                    default -> 1;
                };
                boolean rejected = false;
                try {
                    new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                            new AIcdDefsCodegenSourceDocument(kind, "invalid.schema",
                                    Map.of("type", "string", keyword, value))));
                } catch (UnsupportedOperationException expected) {
                    rejected = expected.getMessage().contains(keyword);
                }
                if (!rejected) Assert.fail("Constraint must be rejected: " + keyword);
            }
        }
    }

    /** XSD list, wildcard and nillable semantics require explicit support. */
    @Test
    public void AIcUnsupportedXsdIsNotRewrittenToAny() {
        for (var fragment : List.of(
                "<xs:simpleType name='Tokens'><xs:list itemType='xs:string'/></xs:simpleType>",
                "<xs:complexType name='Any'><xs:sequence><xs:any/></xs:sequence></xs:complexType>",
                "<xs:complexType name='N'><xs:sequence><xs:element name='A' nillable='true' type='xs:string'/></xs:sequence></xs:complexType>")) {
            String xml = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
                    + fragment + "</xs:schema>";
            boolean rejected = false;
            try {
                new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                        new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                                "invalid.xsd", xml)));
            } catch (IllegalArgumentException | UnsupportedOperationException expected) {
                rejected = true;
            }
            if (!rejected) Assert.fail("Unsupported XSD input cannot be widened to ANY");
        }
    }
}
