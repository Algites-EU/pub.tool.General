package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.model.AIngScalarKind_1;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalScalar;
import eu.algites.tool.codegen.defs.impl.standard.model.AIiDefsCanonicalStructure;
import java.lang.reflect.InvocationTargetException;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Guarantees that neither Java nor Python public DataObject getters receive
 * a substituted Object/Any type when their canonical scalar is unresolved.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenStrictTypedGetterTest {
    /**
     * Asserts that an unresolved scalar is rejected for both output languages.
     *
     * @throws Exception if the emitter cannot be reflected for this regression test
     */
    @Test
    public void AIcRejectUntypedPublicGetterInBothBackends() throws Exception {
        var profile = new AIcCodegenNamingProfileResolver.Profile(
                "test", Map.of(), Map.of(), Map.of(), Map.of(), 1, Map.of());
        var emitter = new AIcDefsCodegenCanonicalSourceEmitter(
                profile, Map.of(), "test.output");
        var method = AIcDefsCodegenCanonicalSourceEmitter.class.getDeclaredMethod(
                "typed", AIiDefsCanonicalStructure.class, Map.class, boolean.class, String.class);
        method.setAccessible(true);
        var unresolved = new AIcDefsCanonicalScalar(AIngScalarKind_1.ANY, "");
        String source = "sample.jsondef.schema.json#/$defs/Thing/properties/value";
        for (boolean javaTarget : new boolean[] {true, false}) {
            InvocationTargetException failure = Assert.expectThrows(InvocationTargetException.class,
                    () -> method.invoke(emitter, unresolved, Map.of(), javaTarget, source));
            Assert.assertTrue(failure.getCause() instanceof IllegalArgumentException);
            Assert.assertTrue(failure.getCause().getMessage().contains(source));
            Assert.assertTrue(failure.getCause().getMessage().contains("Object/Any is forbidden"));
        }
        var string = new AIcDefsCanonicalScalar(AIngScalarKind_1.STRING, "");
        Assert.assertEquals(method.invoke(emitter, string, Map.of(), true, source), "String");
        Assert.assertEquals(method.invoke(emitter, string, Map.of(), false, source), "str");
    }
}
