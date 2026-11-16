package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.lib.common.object.props.labels.AIaFieldLabel;
import eu.algites.lib.common.object.props.labels.AIiFieldLabelResolverFactory;
import eu.algites.lib.factory.cpdiscovery.AIaCategoryProviderFactoryDefinition;
import java.lang.reflect.Method;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Regression: generated field-label resolver annotations use the current CPDiscovery API. */
public final class AItcSdoFieldLabelFactoryEmissionTest {
    /** Verify that the factory SPI, category and provider ID survive SDO generation. */
    @Test
    public void testFactoryInterfaceEmittedForFieldLabelResolver() throws ReflectiveOperationException {
        Method locMethod = AIcSdoCodegenService.class.getDeclaredMethod(
                "fieldLabelAnnotation", Method.class, String.class);
        locMethod.setAccessible(true);
        String locSource = (String) locMethod.invoke(null, ReadContract.class.getDeclaredMethod("getValue"), "value");
        Assert.assertTrue(locSource.contains(
                "factoryInterface = eu.algites.lib.common.object.props.labels.AIiFieldLabelResolverFactory.class"));
        Assert.assertTrue(locSource.contains("factoryCategory = \"dynamic\""));
        Assert.assertTrue(locSource.contains("factoryProviderId = \"resolver-v1\""));
        Assert.assertFalse(locSource.contains("factoryClass"));
    }

    private interface ReadContract {
        @AIaFieldLabel(label = "Value", labelResolver = @AIaCategoryProviderFactoryDefinition(
                factoryInterface = AIiFieldLabelResolverFactory.class,
                factoryCategory = "dynamic", factoryProviderId = "resolver-v1"))
        String getValue();
    }
}
