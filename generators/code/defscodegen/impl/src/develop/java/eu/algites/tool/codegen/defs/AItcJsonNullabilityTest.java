package eu.algites.tool.codegen.defs;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Protects JSON null semantics in the Java definition frontend. */
public final class AItcJsonNullabilityTest {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    /** A missing type restriction accepts null unless another keyword excludes it. */
    @Test
    public void AIcNullabilityPredicates() throws Exception {
        String[] locAccept = {
                "{}", "{\"type\":[\"string\",\"null\"]}",
                "{\"enum\":[\"success\",\"error\",null]}",
                "{\"const\":null}",
                "{\"anyOf\":[{\"type\":\"string\"},{\"type\":\"null\"}]}",
                "{\"oneOf\":[{\"type\":\"string\"},{\"type\":\"null\"}]}"
        };
        String[] locReject = {
                "{\"type\":\"string\"}", "{\"enum\":[\"success\"]}",
                "{\"type\":[\"string\",\"null\"],\"enum\":[\"allowed\"]}",
                "{\"const\":\"constant\"}",
                "{\"allOf\":[{}, {\"type\":\"string\"}]}",
                "{\"oneOf\":[{}, {}]}",
                "{\"not\":{\"type\":\"null\"}}"
        };
        for (String locSchema : locAccept) {
            Assert.assertTrue(AIcJsonSchemaNullability.acceptsNull(MAPPER.readTree(locSchema)), locSchema);
        }
        for (String locSchema : locReject) {
            Assert.assertFalse(AIcJsonSchemaNullability.acceptsNull(MAPPER.readTree(locSchema)), locSchema);
        }
    }
}
