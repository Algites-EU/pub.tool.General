package eu.algites.tool.codegen.sdo.impl.cli;

import eu.algites.lib.data.dataobject.AIaDataObject;
import eu.algites.lib.data.dataobject.AIiDataObject;
import eu.algites.lib.data.smartdataobject.AIiSmartDataObject;
import eu.algites.lib.data.smartdataobject.jsondefs.AIiJsonSmartDataObject;
import eu.algites.lib.data.smartdataobject.yamldefs.AIiYamlSmartDataObject;
import eu.algites.lib.data.smartdataobject.xmldefs.AIiXmlSmartDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObjectNamespace;
import eu.algites.tool.codegen.sdo.impl.standard.AIcSdoCodegenService;
import org.testng.annotations.Test;

/**
 * Ensures binary input discovery shares the same contract eligibility rules as
 * generation and does not treat XML namespace markers as independent DataObjects.
 */
public final class AItcBinaryDataObjectSelectionTest {
    /**
     * XML namespace lineage marker, not a standalone DataObject; this is the
     * contract shape emitted by Defs Codegen for each XML schema namespace.
     */
    @AIaXmlDataObject(namespace = "urn:algites:test:namespace")
    public interface AIigXmlNamespaceMarker extends AIiXmlDataObjectNamespace { }

    /** Legitimate XML DataObject defined in the namespace above. */
    @AIaDataObject(schemaId = "urn:algites:test:object", schemaVersion = 1)
    @AIaXmlDataObject(namespace = "urn:algites:test:namespace")
    public interface AIigXmlContract extends AIigXmlNamespaceMarker { }

    /** Handwritten DataObject without Defs-generated metadata. */
    public interface AIigHandwrittenContract extends AIiDataObject { }

    /** User-defined mutable interface, which must not be processed a second time. */
    public interface AIigHandwrittenMutableContract extends AIiSmartDataObject { }

    /**
     * Verifies exclusion of namespace-only markers while preserving XML and
     * handwritten DataObject contracts as valid SDO inputs.
     */
    @Test
    public void verifyBinaryInputSelection() {
        if (AIcSdoCodegenService.isReadContract(AIigXmlNamespaceMarker.class))
            throw new AssertionError("XML namespace marker must not be an SDO generation input");
        if (!AIcSdoCodegenService.isReadContract(AIigXmlContract.class))
            throw new AssertionError("Annotated XML object must remain an SDO generation input");
        if (!AIcSdoCodegenService.isReadContract(AIigHandwrittenContract.class))
            throw new AssertionError("Handwritten DataObject must remain eligible");
        for (Class<?> locMutable : new Class<?>[] {
                AIiSmartDataObject.class,
                AIiJsonSmartDataObject.class,
                AIiYamlSmartDataObject.class,
                AIiXmlSmartDataObject.class,
                AIigHandwrittenMutableContract.class
        }) {
            if (AIcSdoCodegenService.isReadContract(locMutable))
                throw new AssertionError("Mutable SDO interface must not be a read contract: " + locMutable);
        }
        if (AIcSdoCodegenService.isReadContract(String.class))
            throw new AssertionError("Non-DataObject types must not be generated");
    }
}
