package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.tool.codegen.defs.model.impl.AIcgdElement_1;
import eu.algites.tool.codegen.defs.model.impl.AIcgdSourceBindings_1;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verify lifecycle of the format-neutral typed source-binding field. The
 * current canonical model uses one contract, not separate per-format types.
 *
 * @author linhart1
 */
public final class AItcSdoNamedMappedCollectionTest {
    /**
     * Verify the writable model retains typed source bindings until unset.
     * The old generated technology-specific named-map getter is obsolete.
     */
    @Test
    public void AIcSourceBindingsUsesUnifiedTypedFieldAndDetachesOnUnset() {
        AIcgdElement_1 element = new AIcgdElement_1();
        AIcgdSourceBindings_1 first = new AIcgdSourceBindings_1();
        element.setSourceBindings(first);
        Assert.assertSame(element.getSourceBindings(), first);
        Assert.assertTrue(element._isPresent_SourceBindings());
        element._unset_SourceBindings();
        Assert.assertFalse(element._isPresent_SourceBindings());
        Assert.assertNotSame(element.getSourceBindings(), first);
    }
}
