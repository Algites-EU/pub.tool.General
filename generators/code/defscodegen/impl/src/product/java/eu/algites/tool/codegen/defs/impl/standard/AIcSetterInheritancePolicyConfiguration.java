package eu.algites.tool.codegen.defs.impl.standard;

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
                throw new IllegalArgumentException("Unresolved setter inheritance policy: DEFAULT");
            return locPolicy;
        } catch (IllegalArgumentException aFailure) {
            throw new IllegalArgumentException("Invalid setterInheritancePolicy: " + locValue, aFailure);
        }
    }
}
