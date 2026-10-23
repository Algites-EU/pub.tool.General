package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.lib.data.dataobject.AIaDataObject;
import eu.algites.lib.data.dataobject.AIaDataObjectField;
import eu.algites.lib.data.dataobject.AIiDataObject;
import eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import javax.tools.ToolProvider;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Compiles real generated writable contract hierarchies, including unrelated
 * future declarations, to prevent invalid erasure or lost generic bounds.
 */
public final class AItcSetterInheritancePolicyTest {
    /** Base value contract accepted by the original writable holder. */
    @AIaDataObject(schemaId = "test:generic-value-a", schemaVersion = 1)
    public interface AIigA extends AIiDataObject { }

    /** Refinement of a value contract that could be published in another artifact. */
    @AIaDataObject(schemaId = "test:generic-value-b", schemaVersion = 1)
    public interface AIigB extends AIigA { }

    /** Writable holder that must allow later specializations of its list elements. */
    @AIaDataObject(schemaId = "test:generic-holder-c", schemaVersion = 1)
    public interface AIigC extends AIiDataObject {
        /** Return values typed to the read-only parent contract. */
        @AIaDataObjectField(fieldName = "A", setterInheritancePolicy =
                AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        List<? extends AIigA> getA();
    }

    /** Writable holder that narrows the element type while inheriting all setters. */
    @AIaDataObject(schemaId = "test:generic-holder-d", schemaVersion = 1)
    public interface AIigD extends AIigC {
        /** Return values restricted to the refined read-only value contract. */
        @Override
        @AIaDataObjectField(fieldName = "A", setterInheritancePolicy =
                AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
        List<? extends AIigB> getA();
    }

    /** Read contract with two independent parents requiring mutable multiple inheritance. */
    @AIaDataObject(schemaId = "test:generic-holder-diamond", schemaVersion = 1)
    public interface AIigDiamond extends AIigC, AIigB { }

    /** Holder whose setter type must remain unchanged in descendants. */
    @AIaDataObject(schemaId = "test:fixed-holder", schemaVersion = 1)
    public interface AIigFixed extends AIiDataObject {
        /** Read the fixed element type published by this interface. */
        @AIaDataObjectField(fieldName = "A", setterInheritancePolicy =
                AInFieldSetterInheritancePolicy.INHERIT_AS_FIXED_PARAMETER)
        List<? extends AIigA> getA();
    }

    /** An invalid attempt to narrow an inherited fixed setter parameter. */
    @AIaDataObject(schemaId = "test:invalid-fixed-holder", schemaVersion = 1)
    public interface AIigInvalidFixed extends AIigFixed {
        /** Attempt a read refinement that would contradict the inherited fixed setter. */
        @Override
        @AIaDataObjectField(fieldName = "A")
        List<? extends AIigB> getA();
    }

    /**
     * Generate and compile complete mutable and concrete Java contracts,
     * preserving the correct writable subtype hierarchy and method erasures.
     *
     * @throws Exception if generated source cannot be written or compiled
     */
    @Test
    public void AIcCompilesSpecializedSettersAndDiamond() throws Exception {
        var locGenerator = new AIcSdoCodegenService();
        var locRoot = Files.createTempDirectory("sdo-setter-generics-");
        var locOutput = Files.createDirectories(locRoot.resolve("classes"));
        var locSources = new ArrayList<String>();
        for (Class<?> locRead : List.of(AIigA.class, AIigB.class, AIigC.class,
                AIigD.class, AIigDiamond.class)) {
            var locResult = locGenerator.generate(locRead, "d");
            for (var locUnit : List.of(locResult.mutableInterface(), locResult.implementation())) {
                Path locFile = locRoot.resolve(locUnit.relativePath());
                Files.createDirectories(locFile.getParent());
                Files.writeString(locFile, locUnit.source());
                locSources.add(locFile.toString());
            }
            if (locRead == AIigD.class) {
                Assert.assertTrue(locResult.mutableInterface().source().contains("TA extends"));
                Assert.assertTrue(locResult.mutableInterface().source().contains("AIigdC<TA>"));
                Assert.assertTrue(locResult.mutableInterface().source().contains("List<? extends TA> getA()"));
                Assert.assertTrue(locResult.mutableInterface().source().contains("List<? extends TA>"));
                Assert.assertTrue(locResult.implementation().source().contains("AIigdD<"));
            }
            if (locRead == AIigDiamond.class) {
                String locText = locResult.mutableInterface().source();
                Assert.assertTrue(locText.contains("AIigdC<TA>"));
                Assert.assertTrue(locText.contains("AIigdB"));
            }
        }
        var locArguments = new ArrayList<>(List.of(
                "-cp", System.getProperty("java.class.path"), "-d", locOutput.toString()));
        locArguments.addAll(locSources);
        Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                locArguments.toArray(String[]::new)), 0);
    }

    /**
     * A fixed setter cannot be silently narrowed by a distant descendant;
     * validation must fail before emitting an incompatible Java overload.
     */
    @Test
    public void AIcRejectsInvalidRefinementOfFixedSetter() {
        Assert.expectThrows(IllegalArgumentException.class,
                () -> new AIcSdoCodegenService().generate(AIigInvalidFixed.class, "d"));
    }
}
