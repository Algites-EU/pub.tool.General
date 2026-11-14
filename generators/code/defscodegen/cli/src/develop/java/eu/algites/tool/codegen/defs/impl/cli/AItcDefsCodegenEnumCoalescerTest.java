package eu.algites.tool.codegen.defs.impl.cli;

import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Regression coverage for merging shared enums defined in several schema dialects.
 * No generated enum may silently lose a wire value or a source version.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenEnumCoalescerTest {
    /** Ensure Java and Python merge stable equivalent enums with distinct provenance. */
    @Test
    public void equivalentFormatDefinitionsHaveOneStableEnum() {
        String java = "/**\n * A field.\n * <p>Generated from canonical definition sample#/$defs/Status/1."
                + " Source: schemas/jsondefs/example_1.jsondef.schema.json#/$defs/Status."
                + " Do not edit manually.</p>\n * @author linhart1\n */\n"
                + "public enum Status {\n    A, B;\n"
                + "    public static final String CANONICAL_SOURCE_ID = \"sample#/$defs/Status\";\n"
                + "    public static final Integer CANONICAL_SOURCE_VERSION = 1;\n"
                + "    public static final String CANONICAL_SOURCE_RESOURCE = "
                + "\"schemas/jsondefs/example_1.jsondef.schema.json#/$defs/Status\";\n}\n";
        String xml = java.replace("A field.", "Same enum, different XML description.")
                .replace("schemas/jsondefs/example_1.jsondef.schema.json#/$defs/Status",
                         "schemas/xmldefs/example_1.xsd#/Status")
                .replace("sample#/$defs/Status", "sample#/Status");
        String first = AIcDefsCodegenEnumCoalescer.merge("Status.java", java, xml);
        String second = AIcDefsCodegenEnumCoalescer.merge("Status.java", xml, java);
        Assert.assertEquals(first, second);
        Assert.assertTrue(first.contains("Equivalent enum schema:"));
        Assert.assertTrue(first.contains("schemas/xmldefs/example_1.xsd"));
        Assert.assertEquals(AIcDefsCodegenEnumCoalescer.merge("Status.java", first, xml), first);
        try {
            AIcDefsCodegenEnumCoalescer.merge("Status.java", java, xml.replace("A, B;", "A, C;"));
            Assert.fail("Different enum members were accepted");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("schemas/xmldefs/"));
        }
        try {
            AIcDefsCodegenEnumCoalescer.merge("Status.java", java,
                    xml.replace("CANONICAL_SOURCE_VERSION = 1", "CANONICAL_SOURCE_VERSION = 2"));
            Assert.fail("Different enum versions were accepted");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("Status.java"));
        }
    }

    /** Python representation docs are not executable enum values. */
    @Test
    public void pythonFormatProvenanceDoesNotDuplicateCommonEnums() {
        String python = "from enum import Enum\nclass Status(str, Enum):\n"
                + "    \"\"\"JSON value.\n\n"
                + "    Generated from canonical definition sample#/$defs/Status/1."
                + " Source: schemas/jsondefs/example_1.jsondef.schema.json#/$defs/Status."
                + " Do not edit manually.\n    \"\"\"\n"
                + "    A = 'a'\n    B = 'b'\n";
        String xml = python.replace("JSON value.", "Equivalent XML value.")
                .replace("schemas/jsondefs/example_1.jsondef.schema.json#/$defs/Status",
                         "schemas/xmldefs/example_1.xsd#/Status")
                .replace("sample#/$defs/Status", "sample#/Status");
        String merged = AIcDefsCodegenEnumCoalescer.merge("status.py", python, xml);
        Assert.assertEquals(merged, AIcDefsCodegenEnumCoalescer.merge("status.py", xml, python));
        Assert.assertTrue(merged.contains("Equivalent enum schema:"));
        try {
            AIcDefsCodegenEnumCoalescer.merge("status.py", python, xml.replace("B = 'b'", "B = 'c'"));
            Assert.fail("Different Python enum wire codes were accepted");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("status.py"));
        }
    }
    /** Real canonical emitter uses canonical identity tags rather than source-resource constants. */
    @Test
    public void canonicalEmittedEnumsMergeByPublicValues() {
        String json = "/**\n * <p>Canonical identity: urn:records#/$defs/Status; version: 1.</p>\n"
                + " */\npublic enum Status {\n    READY, HOLD;\n}\n";
        String xml = json.replace("urn:records#/$defs/Status", "{urn:records}Status")
                .replace("READY, HOLD", "READY, HOLD");
        String first = AIcDefsCodegenEnumCoalescer.merge("Status.java", json, xml);
        String second = AIcDefsCodegenEnumCoalescer.merge("Status.java", xml, json);
        Assert.assertEquals(first, second);
        Assert.assertTrue(first.contains("Equivalent schema identity:"));
        Assert.assertEquals(AIcDefsCodegenEnumCoalescer.merge("Status.java", first, xml), first);
        try {
            AIcDefsCodegenEnumCoalescer.merge("Status.java", json,
                    xml.replace("READY, HOLD", "READY, ERROR"));
            Assert.fail("Different canonical enum values were accepted");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("Status.java"));
        }
    }
}
