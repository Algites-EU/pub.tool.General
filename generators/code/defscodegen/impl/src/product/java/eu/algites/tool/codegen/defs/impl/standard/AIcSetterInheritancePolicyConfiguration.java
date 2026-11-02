package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;

import eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy;

/**
 * Selects the current invocation's Defs setter policy, retaining a safe default
 * for callers using the service API without a native CLI settings resolution.
 */
public final class AIcSetterInheritancePolicyConfiguration {
    private AIcSetterInheritancePolicyConfiguration() { }

    /**
     * Resolve the current native invocation's policy or the generic inheritance default.
     *
     * @return a concrete policy, never {@code DEFAULT}
     * @throws IllegalArgumentException if the invocation override is invalid
     */
    public static AInFieldSetterInheritancePolicy effectiveDefault() {
        String locValue = System.getProperty("algites.defscodegen.setterInheritancePolicy",
                AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER.name());
        try {
            AInFieldSetterInheritancePolicy locPolicy = AInFieldSetterInheritancePolicy.valueOf(locValue);
            if (locPolicy == AInFieldSetterInheritancePolicy.DEFAULT)
                throw new AIxCodegenValidationException("Unresolved setter inheritance policy: DEFAULT", "Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.");
            return locPolicy;
        } catch (IllegalArgumentException aFailure) {
            throw new AIxCodegenValidationException("Invalid setterInheritancePolicy: " + locValue, "Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.", null, null, aFailure);
        }
    }
}
