package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.lib.data.dataobject.AIaDataObject;
import eu.algites.lib.data.dataobject.AIaDataObjectField;
import eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField;
import eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.util.List;
import javax.tools.ToolProvider;
import org.testng.annotations.Test;

/** Ensures that the generated Java XML implementation can materialize nested typed SDOs. */
public final class AItcGeneratedXmlDeserializationTest {
    /** Nested item data type with a named XML child field. */
    @AIaDataObject(schemaId = "urn:test:item", schemaVersion = 1)
    @AIaXmlDataObject(definitionKind = AInXmlObjectDefinitionKind.TYPE,
            namespace = "urn:test", namespaceLocalName = "ItemType")
    public interface AIigItem_1 extends AIiXmlDataObject {
        /** Name of one nested item. */
        @AIaDataObjectField(fieldName = "Name")
        @AIaXmlDataObjectField(namespace = "urn:test", namespaceLocalName = "Name")
        String getName();
    }

    /** Root XML element containing a repeating nested item field. */
    @AIaDataObject(schemaId = "urn:test:order", schemaVersion = 1)
    @AIaXmlDataObject(definitionKind = AInXmlObjectDefinitionKind.ELEMENT,
            namespace = "urn:test", namespaceLocalName = "Order")
    public interface AIigOrder_1 extends AIiXmlDataObject {
        /** Repeating item values, represented in XML as sibling elements. */
        @AIaDataObjectField(fieldName = "Item")
        @AIaXmlDataObjectField(namespace = "urn:test", namespaceLocalName = "Item")
        List<? extends AIigItem_1> getItem();
    }

    /**
     * Compiles emitted Java contracts and concrete classes, then parses XML
     * without supplying an external nested-type map.
     *
     * @throws Exception if the Java compiler or typed materializer fails
     */
    @Test
    public void AIcGeneratedNestedXmlMaterializerCompilesAndRuns() throws Exception {
        var locGenerator = new AIcSdoCodegenService();
        var locRoot = Files.createTempDirectory("algites-xml-generated-");
        var locSources = new java.util.ArrayList<String>();
        for (Class<?> locRead : List.of(AIigItem_1.class, AIigOrder_1.class)) {
            var locResult = locGenerator.generate(locRead, "d");
            for (var locSource : List.of(locResult.mutableInterface(), locResult.implementation())) {
                var locPath = locRoot.resolve(locSource.relativePath());
                Files.createDirectories(locPath.getParent());
                Files.writeString(locPath, locSource.source());
                locSources.add(locPath.toString());
                if (locRead == AIigOrder_1.class && locSource == locResult.implementation()) {
                    if (!locSource.source().contains("java.util.Map.entry(\"Item\""))
                        throw new AssertionError("Missing concrete nested XML field map");
                }
            }
        }
        try (var locFiles = ToolProvider.getSystemJavaCompiler().getStandardFileManager(null, null, null)) {
            var locUnits = locFiles.getJavaFileObjectsFromStrings(locSources);
            var locOptions = List.of("-classpath", System.getProperty("java.class.path"),
                    "-d", locRoot.toString());
            if (!Boolean.TRUE.equals(ToolProvider.getSystemJavaCompiler().getTask(null,
                    locFiles, null, locOptions, null, locUnits).call())) {
                throw new AssertionError("Generated XML SDO Java sources failed compilation");
            }
        }
        try (var locLoader = new URLClassLoader(new java.net.URL[]{locRoot.toUri().toURL()},
                getClass().getClassLoader())) {
            var locOrder = locLoader.loadClass(getClass().getPackageName() + ".AIcgdOrder_1");
            Object locParsed = locOrder.getMethod("fromXml", String.class).invoke(null,
                    "<t:Order xmlns:t='urn:test'><t:Item><t:Name>alpha</t:Name></t:Item>" +
                    "<t:Item><t:Name>beta</t:Name></t:Item></t:Order>");
            var locItems = (List<?>) locOrder.getMethod("getItem").invoke(locParsed);
            if (locItems.size() != 2 ||
                    !locItems.get(0).getClass().getSimpleName().equals("AIcgdItem_1") ||
                    !locItems.get(0).getClass().getMethod("getName").invoke(locItems.get(0)).equals("alpha") ||
                    !locItems.get(1).getClass().getMethod("getName").invoke(locItems.get(1)).equals("beta")) {
                throw new AssertionError("Generated XML SDO did not preserve typed sibling items");
            }
        }
    }
}
