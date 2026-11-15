package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema;
import eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema;
import eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind;
import java.lang.reflect.Method;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Regression for SDO generation from XML contracts carrying only the moved
 * schema annotations: modern metadata must be propagated with the deprecated
 * compatibility representation and no generic annotation is required here.
 *
 * @author linhart1
 */
public final class AItcModernSdoXmlSchemaMetadataTest {
    /**
     * Verify that modern XML metadata remains usable without a legacy annotation.
     * @throws ReflectiveOperationException if the Java generator API changes
     */
    @Test
    public void testModernOnlyXmlAnnotationsEmittedInBothFormats() throws ReflectiveOperationException {
        Method type = AIcSdoCodegenService.class.getDeclaredMethod("xmlTypeAnnotation", Class.class);
        type.setAccessible(true);
        String declaration = (String) type.invoke(null, ModernOnlyXmlContract.class);
        Assert.assertTrue(declaration.contains("eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema("));
        Assert.assertTrue(declaration.contains("eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema("));
        Assert.assertTrue(declaration.contains("namespaceLocalName = \"Modern\""));

        Method field = AIcSdoCodegenService.class.getDeclaredMethod("xmlFieldAnnotation", Method.class);
        field.setAccessible(true);
        String getter = (String) field.invoke(null, ModernOnlyXmlContract.class.getDeclaredMethod("getCode"));
        Assert.assertTrue(getter.contains("eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema("));
        Assert.assertTrue(getter.contains("eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema("));
        Assert.assertTrue(getter.contains("namespaceLocalName = \"Code\""));
    }

    /** Read-only XML contract with only migrated annotations. */
    @AIaDataObjectXmlSchema(namespace = "urn:modern", namespaceLocalName = "Modern")
    private interface ModernOnlyXmlContract {
        /**
         * Read the externally named XML attribute.
         * @return attribute text
         */
        @AIaDataObjectFieldXmlSchema(namespace = "urn:modern", namespaceLocalName = "Code",
                valueKind = AInXmlValueKind.ATTRIBUTE)
        String getCode();
    }
}
