package eu.algites.tool.codegen.sdo.impl.standard;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;


import eu.algites.tool.codegen.sdo.AIcdGeneratedSdoSource;
import eu.algites.tool.codegen.sdo.AIcdSdoGenerationResult;
import eu.algites.tool.codegen.sdo.AIiSdoCodegenService;
import eu.algites.lib.data.dataobject.AIaDataObjectField;
import eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy;
import eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault;
import eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObjectNamespace;
import eu.algites.lib.factory.cpdiscovery.AIaCategoryProviderFactoryDefinition;
import eu.algites.lib.common.object.props.labels.AIaFieldLabel;
import eu.algites.lib.data.dataobject.AIiDataObject;
import eu.algites.lib.data.smartdataobject.AIiSmartDataObject;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import java.lang.reflect.Method;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.lang.reflect.WildcardType;
import java.lang.reflect.Modifier;
import java.util.Arrays;
import eu.algites.lib.data.dataobject.AIaDataObject;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.LinkedHashSet;
import java.util.ArrayList;
import java.util.Objects;

/** Generate mutable contracts and concrete SmartDataObjects from annotated read-only DataObject contracts. */
public final class AIcSdoCodegenService implements AIiSdoCodegenService {
    /**
     * Effective semantic field used by SDO generation. The value getter may be
     * covariantly specialized by a format projection whose method intentionally
     * has no {@link AIaDataObjectField}. The original getter remains the sole
     * source for format-neutral restrictions, labels, and defaults.
     *
     * @param method most-specific getter to implement, including XML projections
     * @param field schema-neutral field definition
     * @param dataMethod original method declaring the schema-neutral field
     */
    private record AIcdGetter(Method method, AIaDataObjectField field, Method dataMethod) {
        private AIcdGetter(Method method, AIaDataObjectField field) {
            this(method, field, method);
        }
    }

    /** {@inheritDoc} */
    @Override
    public AIcdSdoGenerationResult generate(Class<?> aReadContract, String aImplementationMarker) {
        return generate(aReadContract, aImplementationMarker, null, null, null);
    }

    /** {@inheritDoc} */
    @Override
    public Map<Path, AIcdSdoGenerationResult> generateFromSources(Path aSourceRoot,
            List<Path> aContractSources, String aImplementationMarker, List<Path> aDependencyClassPath) {
        return generateFromSources(aSourceRoot, aContractSources, aImplementationMarker,
                aDependencyClassPath, null, null, null);
    }

    /**
     * Compiles generated read contracts in memory and delegates all metadata and
     * inheritance handling to the existing reflection-based generation path.
     */
    public Map<Path, AIcdSdoGenerationResult> generateFromSources(Path aSourceRoot,
            List<Path> aContractSources, String aImplementationMarker, List<Path> aDependencyClassPath,
            AIiNameConventionCatalog aInputNames, AIiNameConventionCatalog aMutableNames,
            AIiNameConventionCatalog aConcreteNames) {
        return generateFromSources(aSourceRoot, aContractSources, aImplementationMarker,
                aDependencyClassPath, aInputNames, aMutableNames, aConcreteNames, "", "");
    }

    /**
     * Generates SDOs from source contracts with independently selectable JPMS-safe output packages.
     *
     * @param aSourceRoot root containing importable read-only Java contracts
     * @param aContractSources exact sources to generate; dependencies are not independently generated
     * @param aImplementationMarker implementation marker (validated, not used to select naming)
     * @param aDependencyClassPath classpath used to resolve base contracts and field types
     * @param aInputNames input naming catalog with selected semantic roles
     * @param aMutableNames mutable-interface naming catalog with selected semantic roles
     * @param aConcreteNames implementation naming catalog with selected semantic roles
     * @param aMutableSubpackage subpackage appended to generated mutable interfaces; empty means same package
     * @param aConcreteSubpackage subpackage appended to generated implementations; empty means same package
     * @return source-to-result mapping for the explicitly selected contracts
     */
    public Map<Path, AIcdSdoGenerationResult> generateFromSources(Path aSourceRoot,
            List<Path> aContractSources, String aImplementationMarker, List<Path> aDependencyClassPath,
            AIiNameConventionCatalog aInputNames, AIiNameConventionCatalog aMutableNames,
            AIiNameConventionCatalog aConcreteNames,
            String aMutableSubpackage, String aConcreteSubpackage) {
        return generateFromSources(aSourceRoot, aContractSources, aImplementationMarker,
                aDependencyClassPath, aInputNames, aMutableNames, aConcreteNames,
                aMutableSubpackage, aConcreteSubpackage, null);
    }

    /**
     * Generates only requested semantic roles from an annotated Java source tree.
     *
     * <p>Source filenames are not used to identify a contract. Reflection over
     * the compiled type determines its DataObject role, so manually authored
     * interfaces can use a naming profile entirely unlike Algites defaults.
     *
     * @param aSourceRoot source root containing Java packages
     * @param aContractSources candidate interface sources, irrespective of their names
     * @param aImplementationMarker implementation marker retained for API compatibility
     * @param aDependencyClassPath dependencies needed to compile and inspect the sources
     * @param aInputNames naming catalog for input roles
     * @param aMutableNames naming catalog for SDO interfaces
     * @param aConcreteNames naming catalog for SDO implementations
     * @param aMutableSubpackage generated interface package suffix
     * @param aConcreteSubpackage generated implementation package suffix
     * @param aEnabledRoles permitted semantic roles, or null to require every candidate
     * @return generated pairs indexed by their canonical source paths
     */
    public Map<Path, AIcdSdoGenerationResult> generateFromSources(Path aSourceRoot,
            List<Path> aContractSources, String aImplementationMarker, List<Path> aDependencyClassPath,
            AIiNameConventionCatalog aInputNames, AIiNameConventionCatalog aMutableNames,
            AIiNameConventionCatalog aConcreteNames,
            String aMutableSubpackage, String aConcreteSubpackage, Set<String> aEnabledRoles) {
        Objects.requireNonNull(aContractSources, "contract sources");
        if (aContractSources.isEmpty()) return Map.of();
        try (var locCompiled = AIcSdoContractSourceLoader.compile(aSourceRoot, aDependencyClassPath)) {
            Map<Path, AIcdSdoGenerationResult> locResults = new LinkedHashMap<>();
            for (Path locSource : aContractSources) {
                Path locCanonical = locCompiled.validate(locSource);
                Class<?> locClass = locCompiled.load(locCanonical);
                // The neutral annotation may be declared on this interface or
                // inherited from another neutral read-only DataObject. Pure
                // marker interfaces and schema-only projections do not
                // become independent writable SDO inputs.
                if (!isSdoInput(locClass)
                        || (aEnabledRoles != null
                            && !aEnabledRoles.contains(dataObjectRole(locClass)))) continue;
                if (locResults.putIfAbsent(locCanonical, generate(locClass, aImplementationMarker,
                        aInputNames, aMutableNames, aConcreteNames,
                        aMutableSubpackage, aConcreteSubpackage)) != null)
                    throw new AIxCodegenValidationException("Duplicate read contract source: " + locCanonical, "Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.");
            }
            return Map.copyOf(locResults);
        }
    }

    /** Generates SDO classes using the selected YAML naming catalogs for each of the three roles. */
    public AIcdSdoGenerationResult generate(Class<?> aReadContract, String aImplementationMarker,
            AIiNameConventionCatalog aInputNames, AIiNameConventionCatalog aMutableNames,
            AIiNameConventionCatalog aConcreteNames) {
        return generate(aReadContract, aImplementationMarker, aInputNames, aMutableNames,
                aConcreteNames, "", "");
    }

    /**
     * Generates one SDO pair in optionally distinct Java packages.
     *
     * @param aReadContract a reflected public DataObject contract
     * @param aImplementationMarker optional legacy naming marker
     * @param aInputNames input catalog carrying semantic role bindings
     * @param aMutableNames output mutable-interface catalog carrying role bindings
     * @param aConcreteNames output implementation catalog carrying role bindings
     * @param aMutableSubpackage package suffix for mutable interfaces
     * @param aConcreteSubpackage package suffix for implementations
     * @return pair of generated sources with exact output paths
     */
    public AIcdSdoGenerationResult generate(Class<?> aReadContract, String aImplementationMarker,
            AIiNameConventionCatalog aInputNames, AIiNameConventionCatalog aMutableNames,
            AIiNameConventionCatalog aConcreteNames,
            String aMutableSubpackage, String aConcreteSubpackage) {
        if (aInputNames == null || aMutableNames == null || aConcreteNames == null)
            throw new AIxCodegenValidationException("Missing explicit SDO input/mutable/implementation naming profiles", "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        Objects.requireNonNull(aReadContract, "read contract");
        String locMarker = Objects.requireNonNull(aImplementationMarker, "marker");
        if (!locMarker.matches("[a-z][a-z0-9]*")) {
            throw new AIxCodegenValidationException("Invalid implementation marker: " + locMarker, "Inspect the selected DataObject contract and SDO naming profile; correct the incompatible declaration, then regenerate the SDO sources.");
        }
        if (eu.algites.lib.common.list.AIiBoundedList.class.isAssignableFrom(aReadContract))
            throw new AIxCodegenValidationException("A collection is not a DataObject: " + aReadContract,
                    "Generate bounded and multi-mapped lists as collection values, not SDO classes.");
        if (!aReadContract.isInterface() || !AIiDataObject.class.isAssignableFrom(aReadContract)
                || !isReadContract(aReadContract)) {
            throw new AIxCodegenValidationException("Expected an interface extending AIiDataObject: " + aReadContract, "Inspect the selected DataObject contract and SDO naming profile; correct the incompatible declaration, then regenerate the SDO sources.");
        }
        // Recognize the shared annotation on this interface or on any of its
        // read-only DataObject ancestors. A separate XML/JSON/YAML projection
        // is never an independent SDO input merely because it inherits one.
        if (!isSdoInput(aReadContract)) {
            throw new AIxCodegenValidationException(
                    "SDO input must declare or inherit schema-neutral @AIaDataObject "
                    + "without being a technology-specific projection: " + aReadContract.getName(),
                    "Pass an annotated read-only DataObject interface or its neutral descendant; "
                    + "do not pass technology-specific projections or compiler ABI seeds.");
        }
        var locParents = Arrays.stream(aReadContract.getInterfaces())
                .filter(AIcSdoCodegenService::isReadContract).toList();
        LinkedHashMap<String, AIcdGetter> locAll = inheritedFields(aReadContract, aInputNames);
        // Join the schema-neutral structural fields and the XML-only wire
        // projections once, before producing methods or nested-type metadata.
        // The SDO runtime consumes the resulting generated descriptors: it must
        // not rediscover XML child types from unrelated inherited getters.
        if (hasXmlSchema(aReadContract))
            applyXmlFieldProjections(aReadContract, locAll, aInputNames);
        Map<String, String> locEffectiveDataNames = effectiveDataNames(aReadContract, aInputNames);
        /* Mutable interfaces keep the complete read-only hierarchy, but generated
         * concrete SDO implementations never inherit other generated implementations.
         * Each implementation derives directly from the shared SmartDataObject
         * runtime and must therefore emit accessors for every inherited field.
         */
        LinkedHashMap<String, AIcdGetter> locOwn = locAll;
        String locPackage = aReadContract.getPackageName();
        String locMutablePackage = appendedPackage(locPackage, aMutableSubpackage);
        String locConcretePackage = appendedPackage(locPackage, aConcreteSubpackage);
        String locContractRole = dataObjectRole(aReadContract);
        String locMutableConvention = aMutableNames == null ? "" : aMutableNames.selectedRole(locContractRole);
        String locConcreteConvention = aConcreteNames == null ? "" : aConcreteNames.selectedRole(locContractRole);
        AIaDataObject locSourceAnnotation = commonDataObjectMetadata(aReadContract);
        var locJsonAnnotation = aReadContract.getDeclaredAnnotation(
                eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema.class);
        var locYamlAnnotation = aReadContract.getDeclaredAnnotation(
                eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema.class);
        String locSchemaId = locJsonAnnotation != null ? locJsonAnnotation.schemaId()
                : locYamlAnnotation != null ? locYamlAnnotation.schemaId() : "";
        int locSchemaVersion = locJsonAnnotation != null ? locJsonAnnotation.schemaVersion()
                : locYamlAnnotation != null ? locYamlAnnotation.schemaVersion() : -1;
        String locSourceConvention = aInputNames.selectedRole(locContractRole);
        if (locSourceConvention == null || locSourceConvention.isBlank())
            throw new AIxCodegenValidationException("Missing explicit input naming convention for " + locContractRole, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        Map<String, String> locParsedNames = aInputNames.parse(locSourceConvention,
                "type_name", aReadContract.getSimpleName());
        if (locSchemaId.isBlank()) {
            String locIdentifier = locParsedNames.get("identifier");
            if (locIdentifier == null || locIdentifier.isBlank())
                throw new AIxCodegenValidationException("Input naming profile has no identifier: " + locSourceConvention, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
            locSchemaId = locPackage + "." + aInputNames.convertIdentifierByDeclaredStyle(
                    locIdentifier, aInputNames.identifierConvention(locSourceConvention, "type_name"),
                    "lower_kebab_case_1");
        }
        if (locSchemaVersion < 0) {
            String locVersion = locParsedNames.get("version");
            if (locVersion == null || !locVersion.matches("[1-9][0-9]*"))
                throw new AIxCodegenValidationException("Handwritten DataObject requires a schemaVersion or selected versioned naming convention: " + aReadContract, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
            locSchemaVersion = Integer.parseInt(locVersion);
        }
        String locAnnotationLiteral = "@eu.algites.lib.data.dataobject.AIaDataObject("
                + "title = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.title())
                + "\", description = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.description())
                + "\", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy."
                + (locSourceAnnotation == null || locSourceAnnotation.setterInheritancePolicy()
                    == AInFieldSetterInheritancePolicy.DEFAULT
                        ? defaultSetterPolicy().name()
                        : locSourceAnnotation.setterInheritancePolicy().name()) + ")\n";
        String locConcreteAnnotationLiteral = locAnnotationLiteral;
        // The source-technology annotation, not AIaDataObject, owns schema identifiers.
        String locFormatAnnotationLiteral = formatTypeAnnotation(locJsonAnnotation, locYamlAnnotation);
        String locXmlAnnotationLiteral = xmlTypeAnnotation(aReadContract);
        String locSmartAnnotationLiteral = smartTypeAnnotation(
                aReadContract.getDeclaredAnnotation(eu.algites.lib.data.smartdataobject.AIaSmartDataObject.class));
        String locMutable = typeName(aReadContract, locMarker, true, aInputNames, aMutableNames, aConcreteNames);
        String locConcrete = typeName(aReadContract, locMarker, false, aInputNames, aMutableNames, aConcreteNames);
        LinkedHashMap<String, AIcdGetter> locInherited = new LinkedHashMap<>();
        for (Class<?> locAncestor : locParents)
            merge(locInherited, inheritedFields(locAncestor, aInputNames));
        List<AIcdGetter> locAncestorDeclarations = inheritedDeclarations(aReadContract, aInputNames);
        LinkedHashMap<String, String> locTypeVariables = new LinkedHashMap<>();
        LinkedHashMap<String, String> locFieldPolicies = new LinkedHashMap<>();
        for (var locEntry : locAll.entrySet()) {
            String locFieldName = locEntry.getKey();
            AIcdGetter locDefinition = locEntry.getValue();
            AInFieldSetterInheritancePolicy locPolicy = setterPolicy(locDefinition);
            AIcdGetter locInheritedField = locInherited.get(locFieldName);
            if (locInheritedField != null) {
                AInFieldSetterInheritancePolicy locParentPolicy = setterPolicy(locInheritedField);
                if (locParentPolicy != locPolicy) {
                    if (locDefinition.field().setterInheritancePolicy() != AInFieldSetterInheritancePolicy.DEFAULT)
                        throw new AIxCodegenValidationException("Setter inheritance policy of " + locFieldName
                                + " conflicts with published parent contract " + locInheritedField.method().getDeclaringClass(), "Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.");
                    locPolicy = locParentPolicy;
                }
                if (locParentPolicy == AInFieldSetterInheritancePolicy.INHERIT_AS_FIXED_PARAMETER
                        && !locInheritedField.method().getGenericReturnType().getTypeName().equals(
                                locDefinition.method().getGenericReturnType().getTypeName()))
                    throw new AIxCodegenValidationException("Cannot narrow a fixed inherited setter parameter: " + locFieldName, "Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.");
            }
            locFieldPolicies.put(locFieldName, locPolicy.name());
            if (locPolicy == AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER
                    && supportsGenericSetterValue(locDefinition.method()))
                locTypeVariables.put(locFieldName, "T" + locFieldName);
        }
        List<String> locTypeBounds = new ArrayList<>();
        for (var locEntry : locTypeVariables.entrySet()) {
            AIcdGetter locDefinition = locAll.get(locEntry.getKey());
            locTypeBounds.add(locEntry.getValue() + " extends " + genericSetterElementBound(
                    locDefinition.method(), locMarker, aInputNames, aMutableNames,
                    aConcreteNames, aMutableSubpackage));
        }
        String locGenericDeclaration = locTypeBounds.isEmpty() ? "" : "<" + String.join(", ", locTypeBounds) + ">";
        List<String> locParentDeclarations = new ArrayList<>();
        for (Class<?> locAncestor : locParents) {
            List<String> locParentArguments = new ArrayList<>();
            for (var locAncestorField : inheritedFields(locAncestor, aInputNames).entrySet()) {
                if (setterPolicy(locAncestorField.getValue()) != AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER
                        || !supportsGenericSetterValue(locAncestorField.getValue().method())) continue;
                String locVariable = locTypeVariables.get(locAncestorField.getKey());
                if (locVariable == null) throw new AIxCodegenValidationException("Missing inherited setter type argument for "
                        + locAncestorField.getKey() + " in " + aReadContract, "Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.");
                locParentArguments.add(locVariable);
            }
            String locParentType = qualifiedName(locAncestor, typeName(locAncestor, locMarker, true,
                    aInputNames, aMutableNames, aConcreteNames), aMutableSubpackage);
            locParentDeclarations.add(locParentType + (locParentArguments.isEmpty() ? ""
                    : "<" + String.join(", ", locParentArguments) + ">"));
        }
        String locMutableParents = locParentDeclarations.stream()
                .reduce("", (aLeft, aRight) -> aLeft + ", " + aRight);
        String locConcreteParent = implementationBase(aReadContract);
        String locConcreteArguments = locTypeVariables.isEmpty() ? "" : "<" + String.join(", ",
                locTypeVariables.keySet().stream().map(aName -> {
                    return genericSetterElementBound(locAll.get(aName).method(),
                            locMarker, aInputNames, aMutableNames,
                            aConcreteNames, aMutableSubpackage);
                }).toList()) + ">";
        StringBuilder locInterface = new StringBuilder("package " + locMutablePackage + ";\n\n"
                + "/** Generated mutable contract derived from " + aReadContract.getSimpleName() + ". */\n"
                + locAnnotationLiteral
                + locFormatAnnotationLiteral
                + locXmlAnnotationLiteral
                + locSmartAnnotationLiteral
                + "public interface " + locMutable + locGenericDeclaration + " extends " + aReadContract.getCanonicalName()
                + locMutableParents
                + ", " + mutableBase(aReadContract) + " {\n");
        StringBuilder locImplementation = new StringBuilder("package " + locConcretePackage + ";\n\n"
                + "/** Generated mutable implementation of " + aReadContract.getSimpleName() + ". */\n"
                + locConcreteAnnotationLiteral
                + locFormatAnnotationLiteral
                + locXmlAnnotationLiteral
                + "@eu.algites.lib.data.smartdataobject.impl.common.AIaSmartDataObjectImplementationBinding("
                + "readContracts = {" + aReadContract.getCanonicalName() + ".class})\n"
                + "public class " + locConcrete + " extends " + locConcreteParent
                + " implements " + locMutablePackage + "." + locMutable + locConcreteArguments
                + " {\n"
                + "    /** Create an object whose raw fields are initially absent. */\n"
                + "    public " + locConcrete + "() { super(); }\n"
                + "    /** Reconstruct an identity-preserving typed SmartDataObject graph. */\n"
                + "    public " + locConcrete
                + "(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }\n");
        String locSyntheticKeyName = aInputNames.generatedMethodLiteral(
                "multi_mapped_list_key_synthetic_getter");
        Method locSyntheticKeyGetter = syntheticGetter(aReadContract, locSyntheticKeyName);
        if (locSyntheticKeyGetter != null) {
            if (hasXmlSchema(aReadContract))
                throw new AIxCodegenValidationException("Virtual JSON/YAML map-entry keys cannot be XML fields: "
                        + aReadContract.getName(), "Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.");
            locImplementation.append("    /** Actual parent JSON/YAML object property name; never an embedded field. */\n")
                    .append("    private String parentPropertyKey;\n")
                    .append("    /** Construct an entry with its parent object's property name.\n")
                    .append("     * @param aPropertyKey nonempty name of the parent object property\n")
                    .append("     * @throws IllegalArgumentException if the key is absent\n")
                    .append("     */\n")
                    .append("    public ").append(locConcrete).append("(String aPropertyKey) {\n")
                    .append("        super();\n")
                    .append("        this.parentPropertyKey = requireParentPropertyKey(aPropertyKey);\n")
                    .append("    }\n")
                    .append("    /** Construct an entry populated from an identity-preserving field graph.\n")
                    .append("     * @param aMapping typed field graph\n")
                    .append("     * @param aPropertyKey actual parent property key\n")
                    .append("     */\n")
                    .append("    public ").append(locConcrete)
                    .append("(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping, String aPropertyKey) {\n")
                    .append("        super(aMapping);\n")
                    .append("        this.parentPropertyKey = requireParentPropertyKey(aPropertyKey);\n")
                    .append("    }\n")
                    .append("    /** Require a nonempty external parent property name.\n")
                    .append("     * @param aKey candidate property name\n")
                    .append("     * @return the validated key\n")
                    .append("     */\n")
                    .append("    private static String requireParentPropertyKey(String aKey) {\n")
                    .append("        if (aKey == null || aKey.isEmpty())\n")
                    .append("            throw new IllegalArgumentException(\"Missing JSON/YAML parent property key\");\n")
                    .append("        return aKey;\n")
                    .append("    }\n")
                    .append("    /** Return the actual external key, not a synthesized object field.\n")
                    .append("     * @return the containing property name\n")
                    .append("     * @throws IllegalStateException if the entry has no containing map key\n")
                    .append("     */\n")
                    .append("    @Override public String ").append(locSyntheticKeyName).append("() {\n")
                    .append("        if (parentPropertyKey == null)\n")
                    .append("            throw new IllegalStateException(\"Map entry has no parent property key\");\n")
                    .append("        return parentPropertyKey;\n")
                    .append("    }\n");
        }
        String locSyntheticValueName = aInputNames.generatedMethodLiteral(
                "multi_mapped_list_value_synthetic_getter");
        Method locSyntheticValueGetter = syntheticValueGetter(aReadContract, locSyntheticValueName);
        if (locSyntheticValueGetter != null) {
            if (locSyntheticKeyGetter == null)
                throw new AIxCodegenValidationException(
                        "A virtual map-entry value getter requires a virtual key getter: " + aReadContract.getName(),
                        "Declare both nonserialized synthetic getters in the read-only JSON/YAML contract.");
            String locValueType = locSyntheticValueGetter.getGenericReturnType().getTypeName();
            locImplementation.append("    /** Virtual map-entry value, never an embedded serialized field. */\n")
                    .append("    private ").append(locValueType).append(" parentPropertyValue;\n")
                    .append("    /** Construct an entry retaining both its external property key and its typed value.\n")
                    .append("     * @param aPropertyKey nonempty property name\n")
                    .append("     * @param aPropertyValue non-null typed property value\n")
                    .append("     * @throws NullPointerException if the value is absent\n")
                    .append("     */\n")
                    .append("    public ").append(locConcrete).append("(String aPropertyKey, ")
                    .append(locValueType).append(" aPropertyValue) {\n")
                    .append("        this(aPropertyKey);\n")
                    .append("        this.parentPropertyValue = java.util.Objects.requireNonNull(aPropertyValue, \"property value\");\n")
                    .append("    }\n")
                    .append("    /** Reconstruct a virtual map entry from a typed field graph.\n")
                    .append("     * @param aMapping original field values\n")
                    .append("     * @param aPropertyKey nonempty parent property key\n")
                    .append("     * @param aPropertyValue non-null typed property value\n")
                    .append("     */\n")
                    .append("    public ").append(locConcrete)
                    .append("(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping, String aPropertyKey, ")
                    .append(locValueType).append(" aPropertyValue) {\n")
                    .append("        this(aMapping, aPropertyKey);\n")
                    .append("        this.parentPropertyValue = java.util.Objects.requireNonNull(aPropertyValue, \"property value\");\n")
                    .append("    }\n")
                    .append("    /** Return the synthetic property value without serializing a duplicate field.\n")
                    .append("     * @return the exact typed value associated with the containing key\n")
                    .append("     * @throws IllegalStateException if the value has not been supplied\n")
                    .append("     */\n")
                    .append("    @Override public ").append(locValueType).append(" ")
                    .append(locSyntheticValueName).append("() {\n")
                    .append("        if (parentPropertyValue == null)\n")
                    .append("            throw new IllegalStateException(\"Map entry has no virtual property value\");\n")
                    .append("        return parentPropertyValue;\n")
                    .append("    }\n");
        }
        for (var locField : locOwn.values()) {
            Method locGetter = locField.method();
            String locName = semanticFieldId(locField.method(), aInputNames);
            String locType = mutableValueType(locGetter, locMarker, aInputNames, aMutableNames,
                    aConcreteNames, aMutableSubpackage);
            String locVariable = locTypeVariables.get(locName);
            String locInterfaceType = locVariable == null ? locType
                    : genericMutableValueType(locGetter, locVariable);

            String locSuffix = Character.toUpperCase(locName.charAt(0)) + locName.substring(1);
            AIiNameConventionCatalog locAccessorCatalog = Objects.requireNonNull(aMutableNames, "mutable naming profile");
            String locSetterProfile = locMutableConvention;
            String locIdentifierConvention = "upper_camel_case_1";
            String locSetterName = locAccessorCatalog.format(locSetterProfile, "setter_method_name",
                    Map.of("identifier", locName), locIdentifierConvention);
            String locMethodProfile = locAccessorCatalog.generatedMethodProfile();
            String locRawGetter = locMethodProfile == null ? "get_" + locSuffix
                    : locAccessorCatalog.generatedMethodReference("raw_getter") == null ? null
                    : locAccessorCatalog.format(locMethodProfile, "raw_getter",
                            Map.of("identifier", locName), locIdentifierConvention);
            String locPresenceChecker = locMethodProfile == null ? "isPresent_" + locSuffix
                    : locAccessorCatalog.generatedMethodReference("raw_presence_checker_method") == null ? null
                    : locAccessorCatalog.format(locMethodProfile, "raw_presence_checker_method",
                            Map.of("identifier", locName), locIdentifierConvention);
            String locUnsetter = locMethodProfile == null ? "unset_" + locSuffix
                    : locAccessorCatalog.generatedMethodReference("raw_unsetter") == null ? null
                    : locAccessorCatalog.format(locMethodProfile, "raw_unsetter",
                            Map.of("identifier", locName), locIdentifierConvention);
            boolean locCollection = java.util.Collection.class.isAssignableFrom(locGetter.getReturnType());
            boolean locMapped = eu.algites.lib.common.list.AIiMultiMappedList.class
                    .isAssignableFrom(locGetter.getReturnType());
            String locEmptySetter = !locField.field().isEmptyAllowed() ? null
                    : locMethodProfile == null || locAccessorCatalog.generatedMethodReference("raw_empty_setter") == null
                    ? null : locAccessorCatalog.format(locMethodProfile, "raw_empty_setter",
                            Map.of("identifier", locName), locIdentifierConvention);
            String locEmptyChecker = !locField.field().isEmptyAllowed() ? null
                    : locMethodProfile == null || locAccessorCatalog.generatedMethodReference("raw_empty_checker_method") == null
                    ? null : locAccessorCatalog.format(locMethodProfile, "raw_empty_checker_method",
                            Map.of("identifier", locName), locIdentifierConvention);
            if (locField.field().isEmptyAllowed() && (locEmptySetter == null || locEmptyChecker == null))
                throw new AIxCodegenValidationException("Missing empty-state SDO naming roles for " + locName,
                        "Configure raw_empty_setter and raw_empty_checker_method in the selected SDO naming profile.");
            var locGeneratedNames = new java.util.ArrayList<String>();
            if (!locCollection) locGeneratedNames.add(locSetterName);
            for (String locGenerated : new String[] {locRawGetter, locPresenceChecker, locUnsetter,
                    locEmptySetter, locEmptyChecker}) {
                if (locGenerated == null) continue;
                if (!javax.lang.model.SourceVersion.isIdentifier(locGenerated)
                        || javax.lang.model.SourceVersion.isKeyword(locGenerated))
                    throw new AIxCodegenValidationException("Invalid generated SDO method identifier: " + locGenerated, "Rename the indicated type, method or field to match the selected naming convention and update every reference to the renamed declaration.");
                locGeneratedNames.add(locGenerated);
            }
            if (new java.util.HashSet<>(locGeneratedNames).size() != locGeneratedNames.size()
                    || locGeneratedNames.contains(locGetter.getName()))
                throw new AIxCodegenValidationException("Conflicting generated field methods for " + locName, "Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.");
            if (aConcreteNames != null && !aConcreteNames.matches(
                    locConcreteConvention, "setter_method_name", locSetterName))
                throw new AIxCodegenValidationException("SDO setter name does not match concrete naming profile: " + locSetterName, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
            String locParameter = locAccessorCatalog.format(locSetterProfile, "method_parameter_name",
                    Map.of("identifier", locName), locIdentifierConvention);
            if (aConcreteNames != null && !aConcreteNames.matches(
                    locConcreteConvention, "method_parameter_name", locParameter))
                throw new AIxCodegenValidationException("SDO parameter name does not match concrete naming profile: " + locParameter, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
            String locLiteral = "\"" + escape(locName) + "\"";
            String locBoxed = boxed(locGetter.getReturnType(), locType);
            locInterface.append("    /** Typed writable access to field ")
                    .append(locName).append(" under the published setter policy. */\n");
            locInterface.append("    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = \"")
                    .append(escape(locEffectiveDataNames.get(locName))).append("\", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.")
                    .append(locField.field().presence().name()).append(", allowsNull = ")
                    .append(locField.field().allowsNull())
                    .append(", order = ").append(locField.field().order())
                    .append(", minItemCount = ").append(locField.field().minItemCount())
                    .append(", maxItemCount = ").append(locField.field().maxItemCount())
                    .append(", isEmptyAllowed = ").append(locField.field().isEmptyAllowed())
                    .append(", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.")
                    .append(locFieldPolicies.get(locName)).append(")\n");
            locInterface.append("    ").append(fieldConstraintsAnnotations(locField.dataMethod()));
            locInterface.append("    ").append(fieldLabelAnnotation(locField.dataMethod(), locName));
            locInterface.append("    ").append(xmlFieldAnnotation(locGetter));
            for (var locKey : locField.dataMethod().getAnnotationsByType(
                    eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition.class)) {
                String locPaths = java.util.Arrays.stream(locKey.fields())
                        .map(aPath -> "\"" + escape(aPath) + "\"")
                        .collect(java.util.stream.Collectors.joining(", "));
                locInterface.append("    @eu.algites.lib.data.dataobject.AIaDataObjectListKeyDefinition(name = \"")
                        .append(escape(locKey.name())).append("\", selector = \"")
                        .append(escape(locKey.selector())).append("\", fields = {")
                        .append(locPaths).append("}, required = ").append(locKey.required()).append(")\n");
            }
            locInterface.append("    ").append(defaultValueAnnotation(locField.dataMethod()));
            locInterface.append("    ").append(smartFieldAnnotation(locField.dataMethod()));
            locInterface.append("    @Override ").append(locInterfaceType).append(' ')
                    .append(locGetter.getName()).append("();\n");
            if (!locCollection) locInterface.append("    void ").append(locSetterName).append('(')
                    .append(locInterfaceType).append(' ').append(locParameter).append(");\n");
            if (locRawGetter != null)
                locInterface.append("    ").append(locInterfaceType).append(' ').append(locRawGetter).append("();\n");
            if (locPresenceChecker != null)
                locInterface.append("    boolean ").append(locPresenceChecker).append("();\n");
            if (locUnsetter != null)
                locInterface.append("    void ").append(locUnsetter).append("();\n");
            if (locEmptySetter != null)
                locInterface.append("    void ").append(locEmptySetter).append("();\n");
            if (locEmptyChecker != null)
                locInterface.append("    boolean ").append(locEmptyChecker).append("();\n");
            locImplementation.append("    @Override public ").append(locType).append(' ').append(locGetter.getName())
                    .append("() { return (").append(locBoxed).append(") ");
            locImplementation.append(locCollection ? "get_OrCreateCollectionField(" : "get_EffectiveField(")
                    .append(locLiteral).append(locCollection ? ", " + locMapped : "");
            locImplementation.append("); }\n");
            if (!locCollection) locImplementation.append("    @Override public void ")
                    .append(locSetterName).append('(').append(locType).append(' ')
                    .append(locParameter).append(") { set_RawField(").append(locLiteral).append(", ")
                    .append(locParameter).append("); }\n");
            /* A representation-specific getter may narrow a common Object (or
             * another non-generic value) getter. The common mutable interface
             * then has a concrete setter such as setVersionConventions(Object),
             * which overloading with the narrow setter does not implement.
             * Generate the inherited signature explicitly; raw-field validation
             * remains the responsibility of the SmartDataObject runtime.
             * Generic parent setters need no source bridge: javac handles their
             * erased signatures from the specialized type arguments.
             */
            Set<String> locEmittedSignatures = new LinkedHashSet<>();
            locEmittedSignatures.add(locSetterName + "(" + locType + ")");
            for (AIcdGetter locAncestorField : locAncestorDeclarations) {
                if (locCollection) continue;
                Method locAncestorGetter = locAncestorField.method();
                if (!locName.equals(semanticFieldId(locAncestorGetter, aInputNames))) continue;
                if (setterPolicy(locAncestorField) == AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER
                        && supportsGenericSetterValue(locAncestorGetter)) continue;
                String locInheritedType = mutableValueType(locAncestorGetter, locMarker,
                        aInputNames, aMutableNames, aConcreteNames, aMutableSubpackage);
                String locInheritedRole = dataObjectRole(locAncestorGetter.getDeclaringClass());
                String locInheritedConvention = aMutableNames.selectedRole(locInheritedRole);
                String locInheritedSetter = locAccessorCatalog.format(locInheritedConvention,
                        "setter_method_name", Map.of("identifier", locName), locIdentifierConvention);
                String locSignature = locInheritedSetter + "(" + locInheritedType + ")";
                if (!locEmittedSignatures.add(locSignature)) continue;
                locImplementation.append("    /** Implement the non-generic setter inherited from ")
                        .append(locAncestorGetter.getDeclaringClass().getSimpleName())
                        .append(". */\n")
                        .append("    @Override public void ").append(locInheritedSetter)
                        .append('(').append(locInheritedType).append(' ')
                        .append(locParameter).append(") { set_RawField(")
                        .append(locLiteral).append(", ").append(locParameter)
                        .append("); }\n");
            }
            if (locRawGetter != null)
                locImplementation.append("    @Override public ").append(locType).append(' ').append(locRawGetter)
                        .append("() { return (").append(locBoxed).append(") get_RawField(")
                        .append(locLiteral).append("); }\n");
            if (locPresenceChecker != null)
                locImplementation.append("    @Override public boolean ").append(locPresenceChecker)
                        .append("() { return isPresent_Field(").append(locLiteral).append("); }\n");
            if (locUnsetter != null)
                locImplementation.append("    @Override public void ").append(locUnsetter)
                        .append("() { unset_Field(").append(locLiteral).append("); }\n");
            if (locEmptySetter != null)
                locImplementation.append("    @Override public void ").append(locEmptySetter)
                        .append("() { set_EmptyField(").append(locLiteral).append("); }\n");
            if (locEmptyChecker != null)
                locImplementation.append("    @Override public boolean ").append(locEmptyChecker)
                        .append("() { return isEmpty_Field(").append(locLiteral).append("); }\n");
        }
        locInterface.append("}\n");
        locImplementation.append("}\n");
        String locMutablePath = locMutablePackage.replace('.', '/') + "/";
        String locConcretePath = locConcretePackage.replace('.', '/') + "/";
        String locSourceId = locSchemaId;
        Integer locSourceVersion = locSchemaVersion;
        return new AIcdSdoGenerationResult(
                new AIcdGeneratedSdoSource(locMutable, locMutablePath
                        + fileName(locMutable, true, aMutableNames, aConcreteNames, locContractRole), locInterface.toString(),
                        locMutablePackage, locMutablePackage, locMutablePackage + "." + locMutable,
                        "MUTABLE_INTERFACE_TYPE", locSourceId, locSourceVersion),
                new AIcdGeneratedSdoSource(locConcrete, locConcretePath
                        + fileName(locConcrete, false, aMutableNames, aConcreteNames, locContractRole), locImplementation.toString(),
                        locConcretePackage, locConcretePackage, locConcretePackage + "." + locConcrete,
                        "SMART_DATA_OBJECT_TYPE", locSourceId, locSourceVersion));
    }

    /** Preserve explicit read-contract field labels, including custom resolvers and rendering axes. */
    private static String fieldLabelAnnotation(Method aGetter, String aName) {
        AIaFieldLabel locLabel = aGetter.getAnnotation(AIaFieldLabel.class);
        if (locLabel == null) {
            String locTitle = defaultFieldTitle(aName);
            return "@eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = \""
                    + escape(locTitle) + "\")\n";
        }
        StringBuilder locResult = new StringBuilder("@eu.algites.lib.common.object.props.labels.AIaFieldLabel(");
        locResult.append("label = \"").append(escape(locLabel.label())).append("\"");
        locResult.append(", roleCode = \"").append(escape(locLabel.roleCode())).append("\"");
        locResult.append(", purpose = ").append(locLabel.purpose().getClass().getCanonicalName())
                .append('.').append(locLabel.purpose().name());
        locResult.append(", purposeCode = \"").append(escape(locLabel.purposeCode())).append("\"");
        locResult.append(", format = ").append(locLabel.format().getClass().getCanonicalName())
                .append('.').append(locLabel.format().name());
        locResult.append(", formatCode = \"").append(escape(locLabel.formatCode())).append("\"");
        locResult.append(", localeCode = \"").append(escape(locLabel.localeCode())).append("\"");
        appendResolver(locResult, "labelResolver", locLabel.labelResolver());
        appendResolver(locResult, "purposeResolver", locLabel.purposeResolver());
        appendResolver(locResult, "formatResolver", locLabel.formatResolver());
        appendResolver(locResult, "localeResolver", locLabel.localeResolver());
        if (locLabel.labels().length > 0) {
            locResult.append(", labels = {");
            for (int locIndex = 0; locIndex < locLabel.labels().length; locIndex++) {
                if (locIndex > 0) locResult.append(", ");
                AIaFieldLabel.Entry locEntry = locLabel.labels()[locIndex];
                locResult.append("@eu.algites.lib.common.object.props.labels.AIaFieldLabel.Entry(")
                        .append("label = \"").append(escape(locEntry.label())).append("\"")
                        .append(", roleCode = \"").append(escape(locEntry.roleCode())).append("\"")
                        .append(", purpose = ").append(locEntry.purpose().getClass().getCanonicalName())
                        .append('.').append(locEntry.purpose().name())
                        .append(", purposeCode = \"").append(escape(locEntry.purposeCode())).append("\"")
                        .append(", format = ").append(locEntry.format().getClass().getCanonicalName())
                        .append('.').append(locEntry.format().name())
                        .append(", formatCode = \"").append(escape(locEntry.formatCode())).append("\"")
                        .append(", localeCode = \"").append(escape(locEntry.localeCode())).append("\")");
            }
            locResult.append('}');
        }
        return locResult.append(")\n").toString();
    }

    /** Derive a sentence-case default label while preserving uppercase abbreviations. */
    private static String defaultFieldTitle(String aName) {
        String locSplit = aName.replaceAll("([A-Z]+)([A-Z][a-z])", "$1 $2")
                .replaceAll("([a-z0-9])([A-Z])", "$1 $2")
                .replace('_', ' ').replace('-', ' ').trim();
        StringBuilder locResult = new StringBuilder();
        for (String locWord : locSplit.split("\\s+")) {
            if (locWord.isBlank()) continue;
            if (!locResult.isEmpty()) locResult.append(' ');
            if (locWord.length() > 1 && locWord.equals(locWord.toUpperCase(java.util.Locale.ROOT))) {
                locResult.append(locWord);
            } else {
                String locLower = locWord.toLowerCase(java.util.Locale.ROOT);
                locResult.append(locResult.isEmpty()
                        ? Character.toUpperCase(locLower.charAt(0)) + locLower.substring(1) : locLower);
            }
        }
        return locResult.isEmpty() ? aName : locResult.toString();
    }

    /**
     * Preserve explicit discovery selections without instantiating providers by reflection.
     * The factoryInterface names the specialized factory SPI, not a concrete resolver.
     */
    private static void appendResolver(StringBuilder aTarget, String aName,
            AIaCategoryProviderFactoryDefinition aResolver) {
        aTarget.append(", ").append(aName)
                .append(" = @eu.algites.lib.factory.cpdiscovery.AIaCategoryProviderFactoryDefinition(factoryInterface = ")
                .append(aResolver.factoryInterface().getCanonicalName()).append(".class")
                .append(", factoryCategory = \"").append(escape(aResolver.factoryCategory())).append("\"")
                .append(", factoryProviderId = \"").append(escape(aResolver.factoryProviderId())).append("\")");
    }

    /**
     * Find the virtual parent-map key accessor, which is not a schema field.
     *
     * @param aReadContract source type defining (or inheriting) the accessor
     * @param aMethodName configured accessor name from the method naming catalog
     * @return accessor or null when this is not a keyed map entry
     * @throws IllegalArgumentException if the accessor has an invalid declaration
     */
    private static Method syntheticGetter(Class<?> aReadContract, String aMethodName) {
        if (aMethodName == null || aMethodName.isBlank()) return null;
        Method locMethod;
        try {
            locMethod = aReadContract.getMethod(aMethodName);
        } catch (NoSuchMethodException locMissing) {
            return null;
        }
        if (locMethod.getParameterCount() != 0 || locMethod.getReturnType() != String.class
                || locMethod.getAnnotation(AIaDataObjectField.class) != null)
            throw new AIxCodegenValidationException("Invalid synthetic map key accessor: " + locMethod, "Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.");
        return locMethod;
    }

    /**
     * Locate the typed synthetic getter of a JSON/YAML additional-property entry.
     * This getter has no data-field annotation, because it represents the value
     * associated with a parent map key rather than a nested serialized field.
     *
     * @param aReadContract declared read-only contract
     * @param aMethodName resolved Common naming convention for the value getter
     * @return reflected method or null if the contract does not contain one
     * @throws AIxCodegenValidationException for malformed virtual getters
     */
    private static Method syntheticValueGetter(Class<?> aReadContract, String aMethodName) {
        if (aMethodName == null || aMethodName.isBlank()) return null;
        Method locMethod;
        try {
            locMethod = aReadContract.getMethod(aMethodName);
        } catch (NoSuchMethodException locMissing) {
            return null;
        }
        if (locMethod.getParameterCount() != 0 || locMethod.getReturnType() == void.class
                || locMethod.getReturnType().isPrimitive()
                || locMethod.getAnnotation(AIaDataObjectField.class) != null)
            throw new AIxCodegenValidationException("Invalid synthetic map value accessor: " + locMethod,
                    "Use a nonprimitive typed getter with no data-field annotation.");
        if (hasXmlSchema(aReadContract))
            throw new AIxCodegenValidationException("Virtual map value getters cannot be XML DataObject fields: "
                    + aReadContract.getName(), "Remove virtual map getters from XML contracts.");
        return locMethod;
    }

    /** Return the single format-neutral marker for every mutable SDO contract. */
    private static String mutableBase(Class<?> aRead) {
        return "eu.algites.lib.data.smartdataobject.AIiSmartDataObject";
    }

    /** Return the independent shared SDO runtime, never a format-specific base. */
    private static String implementationBase(Class<?> aRead) {
        return "eu.algites.lib.data.smartdataobject.impl.common.AIcSmartDataObject";
    }

    /**
     * Preserve the source read contract's optional effective-read behavior on its
     * generated writable interface. Runtime metadata resolves the most-derived
     * annotated getter, so the policy must accompany the generated declaration.
     *
     * @param aMetadata explicit source-level SmartDataObject policy or {@code null}
     * @return the annotation source, or an empty string when there is no override
     */
    private static String smartTypeAnnotation(
            eu.algites.lib.data.smartdataobject.AIaSmartDataObject aMetadata) {
        if (aMetadata == null) return "";
        return "@eu.algites.lib.data.smartdataobject.AIaSmartDataObject(allowNonPresentRead = "
                + aMetadata.allowNonPresentRead() + ")\n";
    }

    /**
     * Preserve an explicit getter-level override, including {@code false}, so
     * the generated mutable getter does not inherit a more permissive type default.
     *
     * @param aGetter original annotated read-only getter
     * @return the Java annotation source, or an empty string when unspecified
     */
    private static String smartFieldAnnotation(Method aGetter) {
        var locMetadata = aGetter.getDeclaredAnnotation(
                eu.algites.lib.data.smartdataobject.AIaSmartDataObjectField.class);
        if (locMetadata == null) return "";
        return "@eu.algites.lib.data.smartdataobject.AIaSmartDataObjectField(allowNonPresentRead = "
                + locMetadata.allowNonPresentRead() + ")\n";
    }

    /** Carry the XML QName and type/element distinction onto the mutable contract. */
    /**
     * Copy the exact format-local identity and enabled wire metadata of a read contract.
     *
     * @param json optional JSON Schema annotation
     * @param yaml optional YAML Schema annotation
     * @return complete annotation source or empty string when neither is declared
     */
    private static String formatTypeAnnotation(
            eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema json,
            eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema yaml) {
        var result = new StringBuilder();
        if (json != null) result.append(schemaAnnotation("jsondefs.AIaDataObjectJsonSchema",
                json.schemaId(), json.schemaVersion(), json.schemaUrl(),
                json.dataSourceSchemaUrlField(), json.dataSourceSchemaIdentifierField(),
                json.dataSourceSchemaVersionField()));
        if (yaml != null) result.append(schemaAnnotation("yamldefs.AIaDataObjectYamlSchema",
                yaml.schemaId(), yaml.schemaVersion(), yaml.schemaUrl(),
                yaml.dataSourceSchemaUrlField(), yaml.dataSourceSchemaIdentifierField(),
                yaml.dataSourceSchemaVersionField()));
        return result.toString();
    }

    /** Serialize one format-local schema descriptor without merging JSON and YAML. */
    private static String schemaAnnotation(String qualified, String id, int version, String url,
            String urlField, String idField, String versionField) {
        return "@eu.algites.lib.data.dataobject." + qualified
                + "(schemaId = \"" + escape(id) + "\", schemaVersion = " + version
                + ", schemaUrl = \"" + escape(url)
                + "\", dataSourceSchemaUrlField = \"" + escape(urlField)
                + "\", dataSourceSchemaIdentifierField = \"" + escape(idField)
                + "\", dataSourceSchemaVersionField = \"" + escape(versionField) + "\")\n";
    }

    /** Preserve one XML schema annotation without legacy duplicates. */
    private static String xmlTypeAnnotation(Class<?> readContract) {
        var schema = readContract.getDeclaredAnnotation(
                eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema.class);
        if (schema == null) return "";
        return "@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema("
                + "definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind."
                + schema.definitionKind().name() + ", namespace = \"" + escape(schema.namespace())
                + "\", namespaceLocalName = \"" + escape(schema.namespaceLocalName()) + "\")\n";
    }

    /** Does the contract declare XML Schema metadata? This is not DataObject inheritance. */
    private static boolean hasXmlSchema(Class<?> type) {
        return type.getDeclaredAnnotation(
                eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema.class) != null;
    }

    /** True only when a getter explicitly declares an XML Schema field projection. */
    private static boolean isXmlWireField(Method getter) {
        return getter.isAnnotationPresent(
                eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema.class);
    }

    /** Copy XML wire metadata without a duplicate legacy annotation. */
    private static String xmlFieldAnnotation(Method getter) {
        var field = getter.getDeclaredAnnotation(
                eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema.class);
        if (field == null) return "";
        return "@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema("
                + "namespace = \"" + escape(field.namespace())
                + "\", namespaceLocalName = \"" + escape(field.namespaceLocalName())
                + "\", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind."
                + field.valueKind().name() + ")\n";
    }

    /**
     * Carry every supported schema-independent typed restriction onto the mutable getter.
     * @param getter original read-only annotated getter
     * @return complete Java annotation source, possibly empty
     */
    private static String fieldConstraintsAnnotations(Method getter) {
        var text = new StringBuilder();
        var str = getter.getDeclaredAnnotation(eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints.class);
        if (str != null) text.append("@eu.algites.lib.data.dataobject.AIaDataObjectFieldStringConstraints(minLength = ")
                .append(str.minLength()).append(", maxLength = ").append(str.maxLength())
                .append(", pattern = \"").append(escape(str.pattern())).append("\")\n    ");
        var num = getter.getDeclaredAnnotation(eu.algites.lib.data.dataobject.AIaDataObjectFieldNumericConstraints.class);
        if (num != null) text.append("@eu.algites.lib.data.dataobject.AIaDataObjectFieldNumericConstraints(minimum = \"")
                .append(escape(num.minimum())).append("\", maximum = \"").append(escape(num.maximum()))
                .append("\", exclusiveMinimum = ").append(num.exclusiveMinimum())
                .append(", exclusiveMaximum = ").append(num.exclusiveMaximum())
                .append(", multipleOf = \"").append(escape(num.multipleOf())).append("\")\n    ");
        var list = getter.getDeclaredAnnotation(eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints.class);
        if (list != null) text.append("@eu.algites.lib.data.dataobject.AIaDataObjectFieldListConstraints(minItems = ")
                .append(list.minItems()).append(", maxItems = ").append(list.maxItems())
                .append(", uniqueItems = ").append(list.uniqueItems()).append(")\n    ");
        var obj = getter.getDeclaredAnnotation(eu.algites.lib.data.dataobject.AIaDataObjectFieldObjectConstraints.class);
        if (obj != null) text.append("@eu.algites.lib.data.dataobject.AIaDataObjectFieldObjectConstraints(minProperties = ")
                .append(obj.minProperties()).append(", maxProperties = ").append(obj.maxProperties())
                .append(")\n    ");
        return text.toString();
    }

    /** Retain a field default factory selection on the mutable getter. */
    private static String defaultValueAnnotation(Method aGetter) {
        AIaDataObjectFieldDefault declared = aGetter.getDeclaredAnnotation(AIaDataObjectFieldDefault.class);
        if (declared == null) return "";
        AIaCategoryProviderFactoryDefinition selection = declared.defaultValueFactory();
        String arguments = java.util.Arrays.stream(declared.defaultArguments())
                .map(value -> "\"" + escape(value) + "\"")
                .collect(java.util.stream.Collectors.joining(", "));
        return "@eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault(" 
                + "kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind." + declared.kind().name()
                + ", defaultValueFactory = @eu.algites.lib.factory.cpdiscovery.AIaCategoryProviderFactoryDefinition("
                + "factoryInterface = " + selection.factoryInterface().getCanonicalName() + ".class"
                + ", factoryCategory = \"" + escape(selection.factoryCategory()) + "\""
                + ", factoryProviderId = \"" + escape(selection.factoryProviderId()) + "\")"
                + ", defaultArguments = {" + arguments + "})\n";
    }


    /**
     * Merge explicit XML wire projections into inherited semantic field metadata.
     *
     * <p>A generated XML contract overrides a getter from its common ancestor
     * with an XML-mapped, covariant getter but deliberately does not repeat
     * {@link AIaDataObjectField}. Looking only at annotated common getters
     * loses both the QName and the specialized XML DataObject return type.
     * The most-specific declared XML getter is therefore selected by semantic
     * identity, while neutral field restrictions remain on the parent method.
     * An unannotated inherited getter is never turned into an XML element by
     * guessing its name or return type.
     *
     * @param contract XML read-only DataObject contract to generate
     * @param fields effective inherited semantic fields, updated in place
     * @param names the configured input naming catalog
     */
    private static void applyXmlFieldProjections(Class<?> contract,
            LinkedHashMap<String, AIcdGetter> fields, AIiNameConventionCatalog names) {
        for (Class<?> parent : contract.getInterfaces()) {
            if (AIiDataObject.class.isAssignableFrom(parent))
                applyXmlFieldProjections(parent, fields, names);
        }
        for (Method xmlGetter : Arrays.stream(contract.getDeclaredMethods())
                .filter(getter -> !getter.isBridge() && !getter.isSynthetic())
                .sorted(Comparator.comparing(Method::getName)).toList()) {
            if (!isXmlWireField(xmlGetter)) continue;
            String fieldName = semanticFieldId(xmlGetter, names);
            AIcdGetter inherited = fields.get(fieldName);
            if (inherited == null)
                throw new AIxCodegenValidationException("XML wire getter has no semantic DataObject field: "
                        + xmlGetter + " (" + contract.getName() + ")",
                        "Declare the schema-neutral DataObject field on a compatible ancestor; "
                        + "use the XML projection only for QName and covariant return type metadata.");
            Method original = inherited.dataMethod();
            if (!original.getName().equals(xmlGetter.getName())
                    || xmlGetter.getParameterCount() != 0
                    || !original.getReturnType().isAssignableFrom(xmlGetter.getReturnType()))
                throw new AIxCodegenValidationException("Incompatible XML field projection: "
                        + xmlGetter + " for " + original,
                        "The XML getter must preserve the semantic field identity and "
                        + "narrow, never widen, the original DataObject return type.");
            // Reject contradictory modern and legacy XML annotations even if
            // this field does not refer to a nested DataObject.
            xmlFieldAnnotation(xmlGetter);
            fields.put(fieldName, new AIcdGetter(xmlGetter, inherited.field(), original));
        }
    }

    /**
     * Determines whether an interface is a usable read-only DataObject contract.
     *
     * <p>The predicate is shared with binary-artifact discovery in the SDO CLI.
     * Mutable SmartDataObject interfaces are not read-only generation inputs,
     * even when they also extend {@link AIiDataObject}. This includes both
     * the framework markers and user-defined mutable descendants.
     * A marker such as a generated XML namespace interface may indirectly extend
     * {@link AIiDataObject}, but does not describe a DataObject to instantiate.
     * In particular, an unannotated {@link AIiXmlDataObjectNamespace} descendant
     * is excluded, while an annotated XML definition implementing the same
     * namespace marker remains eligible. Handwritten DataObject interfaces are
     * not required to carry an {@link AIaDataObject} annotation.
     *
     * @param aClass candidate type obtained from compiled artifacts or source loading;
     *               must not be {@code null}
     * @return {@code true} only for an eligible non-framework read-only contract
     */
    public static boolean isReadContract(Class<?> aClass) {
        return aClass.isInterface() && !eu.algites.lib.common.list.AIiBoundedList.class.isAssignableFrom(aClass)
                && !aClass.getPackageName().startsWith("eu.algites.lib.data.dataobject")
                && AIiDataObject.class.isAssignableFrom(aClass)
                && !AIiSmartDataObject.class.isAssignableFrom(aClass)
                && !(AIiXmlDataObjectNamespace.class.isAssignableFrom(aClass)
                    && aClass.getDeclaredAnnotation(AIaDataObject.class) == null);
    }

    /**
     * Determine whether a source type is a schema-neutral SDO generation input.
     *
     * <p>Names and naming profiles must never establish eligibility. A neutral
     * child inherits its parent's annotation even when it has no annotation
     * of its own. Legacy XML/JSON/YAML projection marker interfaces, however,
     * are never independently generated, even if they repeat the neutral
     * annotation: the single shared interface is the only source of SDOs.
     *
     * @param aClass candidate class to inspect
     * @return whether this class can be generated as an independent SDO
     */
    public static boolean isSdoInput(Class<?> aClass) {
        if (!isReadContract(aClass) || commonDataObjectMetadata(aClass) == null)
            return false;
        if (aClass.getDeclaredAnnotation(AIaDataObject.class) != null)
            return true;
        return !hasXmlSchema(aClass)
                && aClass.getDeclaredAnnotation(eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema.class) == null
                && aClass.getDeclaredAnnotation(eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema.class) == null;
    }

    /** Read the schema-neutral annotation from the common read-only ancestor. */
    private static AIaDataObject commonDataObjectMetadata(Class<?> aType) {
        AIaDataObject direct = aType.getDeclaredAnnotation(AIaDataObject.class);
        if (direct != null) return direct;
        for (Class<?> parent : aType.getInterfaces()) {
            if (!AIiDataObject.class.isAssignableFrom(parent)) continue;
            AIaDataObject inherited = commonDataObjectMetadata(parent);
            if (inherited != null) return inherited;
        }
        return null;
    }

    /** Every read-only DataObject uses the same technology-independent naming role. */
    private static String dataObjectRole(Class<?> aContract) {
        return "common";
    }

    /** Appends only valid explicit package suffixes to the original contract package. */
    private static String appendedPackage(String aPackage, String aSubpackage) {
        if (aSubpackage == null || aSubpackage.isBlank()) return aPackage;
        if (!aSubpackage.matches("[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)*"))
            throw new AIxCodegenValidationException("Invalid output subpackage: " + aSubpackage, "Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.");
        return aPackage + "." + aSubpackage;
    }

    /**
     * Preserve technology-specific covariant getters with neutral field metadata.
     *
     * <p>JSON/YAML read-only projections intentionally inherit their schema-neutral
     * {@link AIaDataObjectField} annotations rather than copying them onto every
     * specialization. In particular, a getter returning {@code List<? extends
     * FormatItem>} has the same erased return type as its neutral ancestor but
     * must retain the narrower element type when producing a writable SDO.
     * Selecting only annotated methods silently widens generated setters and
     * causes unrelated inherited getters in the common and specialized APIs.
     *
     * @param aType read-only contract declaring specialized methods
     * @param aFields effective inherited semantic fields to update in place
     * @throws AIxCodegenValidationException for an incompatible override
     */
    private static void applyNonXmlCovariantGetters(Class<?> aType,
            LinkedHashMap<String, AIcdGetter> aFields) {
        for (Method locMethod : Arrays.stream(aType.getDeclaredMethods())
                .filter(aMethod -> !aMethod.isBridge() && !aMethod.isSynthetic()
                        && aMethod.getParameterCount() == 0
                        && aMethod.getDeclaredAnnotation(AIaDataObjectField.class) == null)
                .sorted(Comparator.comparing(Method::getName)).toList()) {
            for (var locEntry : aFields.entrySet()) {
                AIcdGetter locInherited = locEntry.getValue();
                if (!locMethod.getName().equals(locInherited.method().getName())) continue;
                if (!locInherited.method().getReturnType().isAssignableFrom(locMethod.getReturnType()))
                    throw new AIxCodegenValidationException(
                            "Incompatible format-specific DataObject getter: " + locMethod,
                            "Preserve the inherited getter name and use a covariant return type.");
                // The format field is a refinement of the neutral source field;
                // its original annotation continues to govern cardinality etc.
                locEntry.setValue(new AIcdGetter(
                        locMethod, locInherited.field(), locInherited.dataMethod()));
                break;
            }
        }
    }

    /** Collect the complete inherited contract tree, detecting incompatible redeclarations. */
    private static LinkedHashMap<String, AIcdGetter> inheritedFields(Class<?> aType,
            AIiNameConventionCatalog aInputNames) {
        var locResult = new LinkedHashMap<String, AIcdGetter>();
        for (Class<?> locParent : aType.getInterfaces()) {
            if (!AIiDataObject.class.isAssignableFrom(locParent)) continue;
            merge(locResult, inheritedFields(locParent, aInputNames));
        }
        mergeOverrides(locResult, fields(aType.getDeclaredMethods(), aInputNames));
        applyNonXmlCovariantGetters(aType, locResult);
        locResult.entrySet().removeIf(e -> reservedSchemaField(aType, e.getValue().field().dataFieldName()));
        return locResult;
    }

    /** Check only explicitly selected instance-schema metadata names on this format. */
    private static boolean reservedSchemaField(Class<?> aContract, String aFieldName) {
        if (aFieldName == null || aFieldName.isBlank()) return false;
        var json = aContract.getDeclaredAnnotation(
                eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema.class);
        var yaml = aContract.getDeclaredAnnotation(
                eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema.class);
        return isReservedSchemaMetadata(json == null ? "" : json.dataSourceSchemaUrlField(),
                json == null ? "" : json.dataSourceSchemaIdentifierField(),
                json == null ? "" : json.dataSourceSchemaVersionField(), aFieldName)
                || isReservedSchemaMetadata(yaml == null ? "" : yaml.dataSourceSchemaUrlField(),
                yaml == null ? "" : yaml.dataSourceSchemaIdentifierField(),
                yaml == null ? "" : yaml.dataSourceSchemaVersionField(), aFieldName);
    }

    /** Identify enabled metadata fields for one independent source schema. */
    private static boolean isReservedSchemaMetadata(String url, String id, String version, String name) {
        return !url.isBlank() && name.equals(url) || !id.isBlank() && name.equals(id)
                || !version.isBlank() && name.equals(version);
    }

    /**
     * Enumerate every original ancestor field declaration, including declarations
     * hidden by covariant getters in intermediate interfaces. The resulting list
     * is used only to preserve non-generic inherited setter signatures.
     *
     * @param aType the most-derived read-only DataObject contract
     * @param aInputNames the naming catalog used to identify declared fields
     * @return ancestor fields in deterministic depth-first declaration order
     */
    private static List<AIcdGetter> inheritedDeclarations(Class<?> aType,
            AIiNameConventionCatalog aInputNames) {
        List<AIcdGetter> locFields = new ArrayList<>();
        for (Class<?> locParent : aType.getInterfaces()) {
            if (!isReadContract(locParent)) continue;
            locFields.addAll(fields(locParent.getDeclaredMethods(), aInputNames).values());
            locFields.addAll(inheritedDeclarations(locParent, aInputNames));
        }
        return locFields;
    }

    private static void merge(LinkedHashMap<String, AIcdGetter> aResult,
                              LinkedHashMap<String, AIcdGetter> aIncoming) {
        aIncoming.forEach((aName, aField) -> {
            AIcdGetter locPrevious = aResult.putIfAbsent(aName, aField);
            if (locPrevious != null &&
                    (!locPrevious.method().getGenericReturnType().equals(aField.method().getGenericReturnType())
                    || !locPrevious.field().equals(aField.field()))) {
                throw new AIxCodegenValidationException("Conflicting inherited field: " + aName, "Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.");
            }
        });
    }

    /** Child declarations may narrow presence/nullability without erasing parent conflicts. */
    private static void mergeOverrides(LinkedHashMap<String, AIcdGetter> aResult,
                                        LinkedHashMap<String, AIcdGetter> aOverrides) {
        aOverrides.forEach((aName, aField) -> {
            AIcdGetter locParent = aResult.get(aName);
            if (locParent != null) {
                if (!locParent.method().getReturnType().isAssignableFrom(aField.method().getReturnType()))
                    throw new AIxCodegenValidationException("Incompatible restricted field type: " + aName, "Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.");
                var locBefore = locParent.field();
                var locAfter = aField.field();
                if (locBefore.presence() == eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED
                        && locAfter.presence() != eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED
                        || locBefore.presence() == eu.algites.lib.data.dataobject.AInFieldPresenceKind.FORBIDDEN
                        && locAfter.presence() != eu.algites.lib.data.dataobject.AInFieldPresenceKind.FORBIDDEN
                        || !locBefore.allowsNull() && locAfter.allowsNull())
                    throw new AIxCodegenValidationException("Invalid relaxation of field restriction: " + aName, "Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.");
            }
            aResult.put(aName, aField);
        });
    }

    private static LinkedHashMap<String, AIcdGetter> fields(Method[] aMethods,
            AIiNameConventionCatalog aInputNames) {
        var locResult = new LinkedHashMap<String, AIcdGetter>();
        Arrays.stream(aMethods).sorted(Comparator.comparing(Method::getName)).forEach(aMethod -> {
            if (aMethod.isBridge() || aMethod.isSynthetic()) return;
            AIaDataObjectField locAnnotation = aMethod.getDeclaredAnnotation(AIaDataObjectField.class);
            if (locAnnotation == null) return;
            // Format schema metadata belongs to the selected format contract, not to
            // AIaDataObject on the declaring common interface. The caller filters
            // configured instance-metadata fields in the most-derived context.
            if (aMethod.getParameterCount() != 0 || Modifier.isStatic(aMethod.getModifiers())
                    || aMethod.getReturnType() == void.class) {
                throw new AIxCodegenValidationException("Annotated method is not a value getter: " + aMethod, "Inspect the selected DataObject contract and SDO naming profile; correct the incompatible declaration, then regenerate the SDO sources.");
            }
            AIcdGetter locPrevious = locResult.putIfAbsent(semanticFieldId(aMethod, aInputNames), new AIcdGetter(aMethod, locAnnotation));
            if (locPrevious != null) {
                throw new AIxCodegenValidationException("Two annotated getters resolve to the same semantic field: "
                        + semanticFieldId(aMethod, aInputNames) + " (" + locPrevious.method().getName()
                        + ", " + aMethod.getName() + ")", "Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.");
            }
        });
        return locResult;
    }

    /**
     * Resolve a field's canonical internal identifier exclusively from its getter and
     * its explicitly selected input naming convention. Wire field names are opaque.
     *
     * @param aGetter annotated read-only getter
     * @param aInputNames complete input naming catalog
     * @return normalized UpperCamelCase semantic identifier
     */
    private static String semanticFieldId(Method aGetter, AIiNameConventionCatalog aInputNames) {
        Class<?> locOwner = aGetter.getDeclaringClass();
        String locRole = dataObjectRole(locOwner);
        AIaDataObject locMetadata = locOwner.getDeclaredAnnotation(AIaDataObject.class);
        AIiNameConventionCatalog locCatalog = Objects.requireNonNull(aInputNames, "input naming profile");
        String locProfile = locCatalog.selectedRole(locRole);
        if (locProfile == null || locProfile.isBlank())
            throw new AIxCodegenValidationException("Missing input getter naming profile for " + locOwner.getName(), "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        String locIdentifier = locCatalog.parse(locProfile, "getter_method_name", aGetter.getName())
                .get("identifier");
        if (locIdentifier == null || locIdentifier.isBlank())
            throw new AIxCodegenValidationException("Getter naming convention has no semantic identifier: " + aGetter, "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        String locSourceConvention = locCatalog.identifierConvention(locProfile, "getter_method_name");
        String locCanonical = "upper_camel_case_1".equals(locSourceConvention)
                ? locIdentifier : locCatalog.convertIdentifierByDeclaredStyle(
                        locIdentifier, locSourceConvention, "upper_camel_case_1");
        if (!locCanonical.matches("[A-Z][A-Za-z0-9]*"))
            throw new AIxCodegenValidationException("Invalid canonical field identifier for " + aGetter + ": " + locCanonical, "Rename the indicated type, method or field to match the selected naming convention and update every reference to the renamed declaration.");
        return locCanonical;
    }

    /**
     * Resolve external data names and check uniqueness over the effective inherited contract.
     * A missing annotation value inherits the parent's explicit wire name, or defaults
     * to the canonical semantic identifier for a newly introduced field.
     *
     * @param aType selected read-only contract
     * @param aInputNames input naming catalog
     * @return semantic identifier to canonical data name
     */
    private static Map<String, String> effectiveDataNames(Class<?> aType, AIiNameConventionCatalog aInputNames) {
        LinkedHashMap<String, String> locNames = new LinkedHashMap<>();
        for (Class<?> locParent : aType.getInterfaces()) {
            if (!AIiDataObject.class.isAssignableFrom(locParent)) continue;
            effectiveDataNames(locParent, aInputNames).forEach((aSemantic, aData) -> {
                String locExisting = locNames.putIfAbsent(aSemantic, aData);
                if (locExisting != null && !locExisting.equals(aData))
                    throw new AIxCodegenValidationException("Conflicting inherited dataFieldName for " + aSemantic, "Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.");
            });
        }
        for (var locEntry : fields(aType.getDeclaredMethods(), aInputNames).entrySet()) {
            String locSemantic = locEntry.getKey();
            String locExplicit = locEntry.getValue().field().dataFieldName();
            String locPrevious = locNames.get(locSemantic);
            if (locPrevious != null && !locExplicit.isBlank() && !locPrevious.equals(locExplicit))
                throw new AIxCodegenValidationException("Inherited dataFieldName cannot be changed for " + locSemantic
                        + " from " + locPrevious + " to " + locExplicit, "Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.");
            locNames.put(locSemantic, locExplicit.isBlank()
                    ? locPrevious == null ? locSemantic : locPrevious : locExplicit);
        }
        Map<String, String> locOwners = new LinkedHashMap<>();
        locNames.forEach((aSemantic, aData) -> {
            String locPrevious = locOwners.putIfAbsent(aData, aSemantic);
            if (locPrevious != null && !locPrevious.equals(aSemantic))
                throw new AIxCodegenValidationException("Duplicate dataFieldName '" + aData + "' for getters "
                        + locPrevious + " and " + aSemantic, "Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.");
        });
        return locNames;
    }

    private static String typeName(Class<?> aContract, String aMarker, boolean aMutable,
            AIiNameConventionCatalog aInput, AIiNameConventionCatalog aMutableCatalog,
            AIiNameConventionCatalog aConcreteCatalog) {
        if (aInput == null || aMutableCatalog == null || aConcreteCatalog == null)
            throw new AIxCodegenValidationException("Missing required input/mutable/concrete SDO naming profiles", "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        String locSemanticRole = dataObjectRole(aContract);
        AIaDataObject locMetadata = aContract.getDeclaredAnnotation(AIaDataObject.class);
        String locSourceRole = aInput.selectedRole(locSemanticRole);
        var locVars = aInput.parse(locSourceRole, "type_name", aContract.getSimpleName());
        AIiNameConventionCatalog locTarget = aMutable ? aMutableCatalog : aConcreteCatalog;
        String locTargetRole = locTarget.selectedRole(locSemanticRole);
        return locTarget.format(locTargetRole, "type_name", locVars,
                aInput.identifierConvention(locSourceRole, "type_name"));
    }

    private static String fileName(String aType, boolean aMutable,
            AIiNameConventionCatalog aMutableCatalog, AIiNameConventionCatalog aConcreteCatalog,
            String aContractRole) {
        AIiNameConventionCatalog locTarget = aMutable ? aMutableCatalog : aConcreteCatalog;
        if (locTarget == null) throw new AIxCodegenValidationException("Missing SDO output naming profile", "Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.");
        String locRole = locTarget.selectedRole(aContractRole);
        var locVars = locTarget.parse(locRole, "type_name", aType);
        String locConvention = locTarget.identifierConvention(locRole, "type_name");
        return locTarget.format(locRole, "file_name_stem", locVars, locConvention)
                + locTarget.format(locRole, "file_name_suffix", locVars, locConvention);
    }

    /** Determine the effective published setter inheritance policy of a reflected field. */
    private static AInFieldSetterInheritancePolicy setterPolicy(AIcdGetter aField) {
        AInFieldSetterInheritancePolicy locPolicy = aField.field().setterInheritancePolicy();
        if (locPolicy != AInFieldSetterInheritancePolicy.DEFAULT) return locPolicy;
        AIaDataObject locOwner = aField.method().getDeclaringClass().getDeclaredAnnotation(AIaDataObject.class);
        if (locOwner != null && locOwner.setterInheritancePolicy() != AInFieldSetterInheritancePolicy.DEFAULT)
            return locOwner.setterInheritancePolicy();
        return defaultSetterPolicy();
    }

    /**
     * Return the concrete default policy of an unannotated handwritten contract.
     *
     * @return the configured invocation default, or generic inheritance policy
     */
    private static AInFieldSetterInheritancePolicy defaultSetterPolicy() {
        return AInFieldSetterInheritancePolicy.valueOf(System.getProperty(
                "algites.sdocodegen.setterInheritancePolicy",
                AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER.name()));
    }

    /**
     * List setters participate in type-safe generic inheritance even when the
     * source list contains a scalar such as String, an enum, or an unknown Object.
     * Otherwise a broad parent setter such as setLanguages(List<?>) clashes by
     * erasure with a specialized child setter setLanguages(List<? extends String>).
     * Indexed {@code AIiMultiMappedList} projections must participate as well:
     * JSON/YAML/XML may covariantly narrow a common {@code List} getter to an
     * indexed list, and the inherited mutable type parameter must survive.
     * Non-collection nested DataObjects also need a type variable, as before.
     *
     * @param aGetter the read-only getter
     * @return true if its setter supports a generic value parameter
     */
    private static boolean supportsGenericSetterValue(Method aGetter) {
        return isSdoInput(aGetter.getReturnType())
                || referencedContract(aGetter) != null
                || java.util.List.class.isAssignableFrom(aGetter.getReturnType());
    }

    /**
     * Determine the value bound shared by the interface getter and setter.
     * Only eligible, annotated nested DataObjects use their generated mutable interface;
     * auxiliary union/choice interfaces retain their original read-only type. A scalar
     * collection uses the element's own Java type rather than the raw collection.
     * This permits a shared List<?> read contract to be specialized by JSON,
     * YAML, or XML into a List of a stricter element type.
     *
     * @param aGetter read-only getter providing the element type
     * @param aMarker legacy implementation marker
     * @param aInput input naming catalog
     * @param aMutableNames mutable naming catalog
     * @param aConcreteNames implementation naming catalog
     * @param aMutableSubpackage generated mutable package suffix
     * @return full Java type name forming the upper bound and implementation argument
     */
    private static String genericSetterElementBound(Method aGetter, String aMarker,
            AIiNameConventionCatalog aInput, AIiNameConventionCatalog aMutableNames,
            AIiNameConventionCatalog aConcreteNames, String aMutableSubpackage) {
        Class<?> locNested = referencedContract(aGetter);
        if (locNested != null)
            return qualifiedMutableValueName(locNested, aMarker, aInput,
                    aMutableNames, aConcreteNames, aMutableSubpackage);
        if (java.util.List.class.isAssignableFrom(aGetter.getReturnType())) {
            Type locType = aGetter.getGenericReturnType();
            if (locType instanceof ParameterizedType locList) {
                Type locItem = locList.getActualTypeArguments()[0];
                if (locItem instanceof WildcardType locWildcard) {
                    Type[] locUpper = locWildcard.getUpperBounds();
                    if (locUpper.length == 1) locItem = locUpper[0];
                    else return "java.lang.Object";
                }
                return locItem.getTypeName().replace('$', '.');
            }
            return "java.lang.Object";
        }
        throw new AIxCodegenValidationException("Field has no generically typed setter: " + aGetter, "Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.");
    }

    /**
     * Express a mutable getter and setter through the same interface-level variable.
     *
     * <p>Preserve the source collection interface when specializing its value:
     * {@code AIiMultiMappedList<? extends T>} is covariant with an inherited
     * {@code List<? extends T>} getter, whereas replacing it with a plain list
     * would violate the read-only override and lose indexed operations.
     *
     * @param aGetter effective read-only getter
     * @param aVariable mutable interface type parameter for its field
     * @return writable getter type retaining the read-only collection kind
     */
    private static String genericMutableValueType(Method aGetter, String aVariable) {
        if (isSdoInput(aGetter.getReturnType())) return aVariable;
        if (eu.algites.lib.common.list.AIiMultiMappedList.class
                .isAssignableFrom(aGetter.getReturnType()))
            return "eu.algites.lib.common.list.AIiMultiMappedList<? extends " + aVariable + ">";
        if (java.util.List.class.isAssignableFrom(aGetter.getReturnType()))
            return "eu.algites.lib.common.list.AIiBoundedList<? extends " + aVariable + ">";
        return aVariable;
    }

    /**
     * Discovers an eligible SDO contract referenced by one field, including a list element.
     *
     * <p>Only schema-neutral annotated DataObjects (or eligible descendants) may be
     * converted into generated writable references. XML choice markers and other
     * auxiliary interfaces remain typed read-only references even when they have
     * DataObject ancestry for compatibility. They have no generated AIigd type.
     *
     * @param aGetter the annotated getter in the read-only schema contract
     * @return the referenced read contract, or {@code null} for scalar fields
     */
    private static Class<?> referencedContract(Method aGetter) {
        Class<?> locRaw = aGetter.getReturnType();
        if (isSdoInput(locRaw)) return locRaw;
        if (java.util.List.class.isAssignableFrom(locRaw) &&
                aGetter.getGenericReturnType() instanceof ParameterizedType locList) {
            Type locItem = locList.getActualTypeArguments()[0];
            if (locItem instanceof Class<?> locClass && isSdoInput(locClass)) return locClass;
            if (locItem instanceof WildcardType locWildcard && locWildcard.getLowerBounds().length == 0) {
                for (Type locBound : locWildcard.getUpperBounds()) {
                    if (locBound instanceof Class<?> locClass && isSdoInput(locClass)) return locClass;
                }
            }
        }
        return null;
    }

    /** Eligible nested SDO contracts become writable values; helper types stay read-only. */
    private static String mutableValueType(Method aGetter, String aMarker,
            AIiNameConventionCatalog aInput, AIiNameConventionCatalog aMutableNames,
            AIiNameConventionCatalog aConcreteNames, String aMutableSubpackage) {
        Class<?> locReturn = aGetter.getReturnType();
        if (isSdoInput(locReturn)) {
            return qualifiedMutableValueName(locReturn, aMarker,
                    aInput, aMutableNames, aConcreteNames, aMutableSubpackage);
        }
        if (eu.algites.lib.common.list.AIiMultiMappedList.class.isAssignableFrom(locReturn)) {
            Class<?> locNested = referencedContract(aGetter);
            if (locNested != null)
                return "eu.algites.lib.common.list.AIiMultiMappedList<? extends "
                        + qualifiedMutableValueName(locNested, aMarker,
                                aInput, aMutableNames, aConcreteNames, aMutableSubpackage) + ">";
            return aGetter.getGenericReturnType().getTypeName().replace('$', '.');
        }
        if (java.util.List.class.isAssignableFrom(locReturn)) {
            Class<?> locNested = referencedContract(aGetter);
            if (locNested != null) {
                return "eu.algites.lib.common.list.AIiBoundedList<? extends " + qualifiedMutableValueName(locNested, aMarker,
                        aInput, aMutableNames, aConcreteNames, aMutableSubpackage) + ">";
            }
            /* Choice helpers, enums and scalar entries are not writable DataObjects.
             * Preserve their declared element type while retaining the bounded-list
             * contract.  Falling back to java.util.List here breaks covariant SDO
             * overrides even when the read-only getter already returns AIiBoundedList.
             */
            Type locGeneric = aGetter.getGenericReturnType();
            if (locGeneric instanceof ParameterizedType locParameterized) {
                Type locItem = locParameterized.getActualTypeArguments()[0];
                String locElement = locItem.getTypeName().replace('$', '.');
                String locRaw = eu.algites.lib.common.list.AIiMultiMappedList.class
                        .isAssignableFrom(locReturn)
                        ? "eu.algites.lib.common.list.AIiMultiMappedList"
                        : "eu.algites.lib.common.list.AIiBoundedList";
                return locRaw + "<" + locElement + ">";
            }
            return "eu.algites.lib.common.list.AIiBoundedList<?>";
        }
        return aGetter.getGenericReturnType().getTypeName().replace('$', '.');
    }

    /**
     * Qualify a mutable referenced contract with wildcard type arguments when the
     * referenced writable interface is itself generic. This avoids exposing a raw
     * generated interface in the public bound of another generated type variable.
     */
    private static String qualifiedMutableValueName(Class<?> aRead, String aMarker,
            AIiNameConventionCatalog aInput, AIiNameConventionCatalog aMutableNames,
            AIiNameConventionCatalog aConcreteNames, String aSubpackage) {
        // A writable name exists only for an eligible, annotated DataObject.
        // XML choice interfaces and other auxiliary read-only types must retain
        // their original Java type; naming a hypothetical AIigd type would leave
        // the generated source uncompilable.
        if (!isSdoInput(aRead))
            throw new AIxCodegenValidationException(
                    "No writable SDO contract exists for unannotated auxiliary type: " + aRead.getName(),
                    "Keep the source read-only type for helper interfaces, or explicitly declare "
                    + "an annotated DataObject contract if an SDO is intended.");
        String locName = qualifiedName(aRead, typeName(aRead, aMarker, true,
                aInput, aMutableNames, aConcreteNames), aSubpackage);
        long locCount = inheritedFields(aRead, aInput).values().stream()
                .filter(aField -> setterPolicy(aField)
                        == AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER
                        && supportsGenericSetterValue(aField.method())).count();
        if (locCount == 0) return locName;
        return locName + "<" + String.join(", ", java.util.Collections.nCopies((int) locCount, "?")) + ">";
    }

    private static String qualifiedName(Class<?> aParent, String aReplacement, String aSubpackage) {
        return appendedPackage(aParent.getPackageName(), aSubpackage) + "." + aReplacement;
    }
    /**
     * Encode arbitrary annotation metadata as the contents of a Java string literal.
     *
     * <p>Descriptions may contain newlines, tabs, quotation marks and other control
     * characters. Escaping just quotation marks and backslashes would emit malformed
     * source code for valid multiline descriptions. The octal form is used for the
     * remaining ASCII controls so that Unicode-escape preprocessing cannot introduce
     * a physical line terminator before Java parses the generated string literal.
     *
     * @param aValue metadata value to render, never {@code null}
     * @return escaped Java string literal contents, without surrounding quotation marks
     */
    private static String escape(String aValue) {
        StringBuilder locResult = new StringBuilder(aValue.length());
        for (int locIndex = 0; locIndex < aValue.length(); locIndex++) {
            char locCharacter = aValue.charAt(locIndex);
            switch (locCharacter) {
                case '\\' -> locResult.append("\\\\");
                case '"' -> locResult.append("\\\"");
                case '\n' -> locResult.append("\\n");
                case '\r' -> locResult.append("\\r");
                case '\t' -> locResult.append("\\t");
                case '\b' -> locResult.append("\\b");
                case '\f' -> locResult.append("\\f");
                default -> {
                    if (locCharacter < 0x20 || locCharacter == 0x7f) {
                        locResult.append('\\');
                        locResult.append((char) ('0' + ((locCharacter >>> 6) & 7)));
                        locResult.append((char) ('0' + ((locCharacter >>> 3) & 7)));
                        locResult.append((char) ('0' + (locCharacter & 7)));
                    } else {
                        locResult.append(locCharacter);
                    }
                }
            }
        }
        return locResult.toString();
    }
    private static String boxed(Class<?> aClass, String aType) {
        if (!aClass.isPrimitive()) return aType;
        return Map.of(int.class, "Integer", long.class, "Long", boolean.class, "Boolean",
                double.class, "Double", float.class, "Float", short.class, "Short",
                byte.class, "Byte", char.class, "Character").get(aClass);
    }
}
