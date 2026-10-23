package eu.algites.tool.codegen.sdo.impl.standard;


import eu.algites.tool.codegen.sdo.AIcdGeneratedSdoSource;
import eu.algites.tool.codegen.sdo.AIcdSdoGenerationResult;
import eu.algites.tool.codegen.sdo.AIiSdoCodegenService;
import eu.algites.lib.data.dataobject.AIaDataObjectField;
import eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy;
import eu.algites.lib.data.dataobject.AIaFieldDefault;
import eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField;
import eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObjectNamespace;
import eu.algites.lib.data.dataobject.jsondefs.AIiJsonDataObject;
import eu.algites.lib.data.dataobject.yamldefs.AIiYamlDataObject;
import eu.algites.lib.factory.cpdiscovery.AIaCategoryProviderFactoryDefinition;
import eu.algites.lib.common.object.props.labels.AIaFieldLabel;
import eu.algites.lib.data.dataobject.AIiDataObject;
import eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1;
import java.lang.reflect.Method;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.lang.reflect.WildcardType;
import java.lang.reflect.Modifier;
import java.util.Arrays;
import java.util.regex.Pattern;
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

/** Generate mutable contracts and concrete SmartDataObjects solely from compiled AIig contracts. */
public final class AIcSdoCodegenService implements AIiSdoCodegenService {
    private record AIcdGetter(Method method, AIaDataObjectField field) { }

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
            AIcNameConventionCatalog_1 aInputNames, AIcNameConventionCatalog_1 aMutableNames,
            AIcNameConventionCatalog_1 aConcreteNames) {
        return generateFromSources(aSourceRoot, aContractSources, aImplementationMarker,
                aDependencyClassPath, aInputNames, aMutableNames, aConcreteNames, "", "");
    }

    /**
     * Generates SDOs from source contracts with independently selectable JPMS-safe output packages.
     *
     * @param aSourceRoot root containing importable read-only Java contracts
     * @param aContractSources exact sources to generate; dependencies are not independently generated
     * @param aImplementationMarker legacy fallback prefix marker
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
            AIcNameConventionCatalog_1 aInputNames, AIcNameConventionCatalog_1 aMutableNames,
            AIcNameConventionCatalog_1 aConcreteNames,
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
     * @param aImplementationMarker fallback marker for legacy name generation
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
            AIcNameConventionCatalog_1 aInputNames, AIcNameConventionCatalog_1 aMutableNames,
            AIcNameConventionCatalog_1 aConcreteNames,
            String aMutableSubpackage, String aConcreteSubpackage, Set<String> aEnabledRoles) {
        Objects.requireNonNull(aContractSources, "contract sources");
        if (aContractSources.isEmpty()) return Map.of();
        try (var locCompiled = AIcSdoContractSourceLoader.compile(aSourceRoot, aDependencyClassPath)) {
            Map<Path, AIcdSdoGenerationResult> locResults = new LinkedHashMap<>();
            for (Path locSource : aContractSources) {
                Path locCanonical = locCompiled.validate(locSource);
                Class<?> locClass = locCompiled.load(locCanonical);
                if (aEnabledRoles != null && (!isReadContract(locClass)
                        || !aEnabledRoles.contains(dataObjectRole(locClass)))) continue;
                if (locResults.putIfAbsent(locCanonical, generate(locClass, aImplementationMarker,
                        aInputNames, aMutableNames, aConcreteNames,
                        aMutableSubpackage, aConcreteSubpackage)) != null)
                    throw new IllegalArgumentException("Duplicate read contract source: " + locCanonical);
            }
            return Map.copyOf(locResults);
        }
    }

    /** Generates SDO classes using the selected YAML naming catalogs for each of the three roles. */
    public AIcdSdoGenerationResult generate(Class<?> aReadContract, String aImplementationMarker,
            AIcNameConventionCatalog_1 aInputNames, AIcNameConventionCatalog_1 aMutableNames,
            AIcNameConventionCatalog_1 aConcreteNames) {
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
            AIcNameConventionCatalog_1 aInputNames, AIcNameConventionCatalog_1 aMutableNames,
            AIcNameConventionCatalog_1 aConcreteNames,
            String aMutableSubpackage, String aConcreteSubpackage) {
        Objects.requireNonNull(aReadContract, "read contract");
        String locMarker = Objects.requireNonNull(aImplementationMarker, "marker");
        if (!locMarker.matches("[a-z][a-z0-9]*")) {
            throw new IllegalArgumentException("Invalid implementation marker: " + locMarker);
        }
        if (!aReadContract.isInterface() || !AIiDataObject.class.isAssignableFrom(aReadContract)
                || !isReadContract(aReadContract)) {
            throw new IllegalArgumentException("Expected AIi/AIig extending AIiDataObject: " + aReadContract);
        }
        var locParents = Arrays.stream(aReadContract.getInterfaces())
                .filter(AIcSdoCodegenService::isReadContract).toList();
        Class<?> locParent = locParents.isEmpty() ? null : locParents.get(0);
        LinkedHashMap<String, AIcdGetter> locOwn = fields(aReadContract.getDeclaredMethods(), aInputNames);
        LinkedHashMap<String, AIcdGetter> locAll = inheritedFields(aReadContract, aInputNames);
        /* Generic mutable ancestors cannot be extended through an implementation
         * that has already fixed their type arguments. A concrete subtype therefore
         * implements its complete writable contract and its inherited fields directly.
         * The mutable interface retains every parent edge, including diamonds.
         */
        boolean locNeedsFlattenedImplementation = locParents.size() > 1;
        if (locParent != null) {
            LinkedHashMap<String, AIcdGetter> locParentFields = inheritedFields(locParent, aInputNames);
            for (var locEntry : locParentFields.entrySet()) {
                AIcdGetter locOverride = locAll.get(locEntry.getKey());
                if (locOverride == null || referencedContract(locEntry.getValue().method())
                        != referencedContract(locOverride.method())) {
                    locNeedsFlattenedImplementation = true;
                    break;
                }
            }
        }
        if (locNeedsFlattenedImplementation) locOwn = locAll;
        String locPackage = aReadContract.getPackageName();
        String locMutablePackage = appendedPackage(locPackage, aMutableSubpackage);
        String locConcretePackage = appendedPackage(locPackage, aConcreteSubpackage);
        String locContractRole = dataObjectRole(aReadContract);
        String locMutableConvention = aMutableNames == null ? "" : aMutableNames.selectedRole(locContractRole);
        String locConcreteConvention = aConcreteNames == null ? "" : aConcreteNames.selectedRole(locContractRole);
        AIaDataObject locSourceAnnotation = aReadContract.getDeclaredAnnotation(AIaDataObject.class);
        String locSchemaId = locSourceAnnotation == null ? "" : locSourceAnnotation.schemaId();
        int locSchemaVersion = locSourceAnnotation == null ? -1 : locSourceAnnotation.schemaVersion();
        var locParsedIdentity = Pattern.compile("^AIi(?:g)?(.+?)(?:_([1-9][0-9]*))?$")
                .matcher(aReadContract.getSimpleName());
        boolean locLegacyIdentity = locParsedIdentity.matches();
        String locSourceConvention = locSourceAnnotation != null
                && !locSourceAnnotation.namingConvention().isBlank()
                ? locSourceAnnotation.namingConvention()
                : aInputNames == null ? "" : aInputNames.selectedRole(locContractRole);
        Map<String, String> locParsedNames = null;
        if (aInputNames != null && !locSourceConvention.isBlank())
            locParsedNames = aInputNames.parse(locSourceConvention, "main_container_name",
                    aReadContract.getSimpleName());
        if (locSchemaId.isBlank()) {
            if (locParsedNames == null && !locLegacyIdentity)
                throw new IllegalArgumentException("Handwritten DataObject needs schemaId or namingConvention: " + aReadContract);
            String locLogicalName = locParsedNames == null
                    ? locParsedIdentity.group(1).replaceAll("([a-z0-9])([A-Z])", "$1-$2")
                            .toLowerCase(java.util.Locale.ROOT)
                    : AIcNameConventionCatalog_1.convertIdentifier(locParsedNames.get("identifier"),
                            aInputNames.identifierConvention(locSourceConvention, "main_container_name"),
                            "lower_kebab_case_1");
            locSchemaId = locPackage + "." + locLogicalName;
        }
        if (locSchemaVersion < 0) {
            String locVersion = locParsedNames == null ? (locLegacyIdentity ? locParsedIdentity.group(2) : null)
                    : locParsedNames.get("version");
            if (locVersion == null || !locVersion.matches("[1-9][0-9]*"))
                throw new IllegalArgumentException("Handwritten DataObject requires schemaVersion: " + aReadContract);
            locSchemaVersion = Integer.parseInt(locVersion);
        }
        String locAnnotationLiteral = "@eu.algites.lib.data.dataobject.AIaDataObject(schemaId = \""
                + escape(locSchemaId) + "\", schemaVersion = " + locSchemaVersion
                + ", schemaUrl = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.schemaUrl()) + "\""
                + ", title = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.title())
                + "\", description = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.description())
                + "\", fingerprint = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.fingerprint())
                + "\", namingConvention = \"" + escape(locMutableConvention) + "\""
                + ", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy."
                + (locSourceAnnotation == null || locSourceAnnotation.setterInheritancePolicy()
                    == AInFieldSetterInheritancePolicy.DEFAULT
                        ? defaultSetterPolicy().name()
                        : locSourceAnnotation.setterInheritancePolicy().name()) + ")\n";
        String locConcreteAnnotationLiteral = locAnnotationLiteral.replace(
                "namingConvention = \"" + escape(locMutableConvention) + "\"",
                "namingConvention = \"" + escape(locConcreteConvention) + "\"");
        String locXmlAnnotationLiteral = xmlTypeAnnotation(aReadContract.getDeclaredAnnotation(AIaXmlDataObject.class));
        String locSmartAnnotationLiteral = smartTypeAnnotation(
                aReadContract.getDeclaredAnnotation(eu.algites.lib.data.smartdataobject.AIaSmartDataObject.class));
        String locMutable = typeName(aReadContract, locMarker, true, aInputNames, aMutableNames, aConcreteNames);
        String locConcrete = typeName(aReadContract, locMarker, false, aInputNames, aMutableNames, aConcreteNames);
        LinkedHashMap<String, AIcdGetter> locInherited = new LinkedHashMap<>();
        for (Class<?> locAncestor : locParents)
            merge(locInherited, inheritedFields(locAncestor, aInputNames));
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
                        throw new IllegalArgumentException("Setter inheritance policy of " + locFieldName
                                + " conflicts with published parent contract " + locInheritedField.method().getDeclaringClass());
                    locPolicy = locParentPolicy;
                }
                if (locParentPolicy == AInFieldSetterInheritancePolicy.INHERIT_AS_FIXED_PARAMETER
                        && !locInheritedField.method().getGenericReturnType().getTypeName().equals(
                                locDefinition.method().getGenericReturnType().getTypeName()))
                    throw new IllegalArgumentException("Cannot narrow a fixed inherited setter parameter: " + locFieldName);
            }
            locFieldPolicies.put(locFieldName, locPolicy.name());
            if (locPolicy == AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER
                    && referencedContract(locDefinition.method()) != null)
                locTypeVariables.put(locFieldName, "T" + Character.toUpperCase(locFieldName.charAt(0)) + locFieldName.substring(1));
        }
        List<String> locTypeBounds = new ArrayList<>();
        for (var locEntry : locTypeVariables.entrySet()) {
            AIcdGetter locDefinition = locAll.get(locEntry.getKey());
            Class<?> locTarget = referencedContract(locDefinition.method());
            locTypeBounds.add(locEntry.getValue() + " extends " + qualifiedMutableValueName(locTarget,
                    locMarker, aInputNames, aMutableNames, aConcreteNames, aMutableSubpackage));
        }
        String locGenericDeclaration = locTypeBounds.isEmpty() ? "" : "<" + String.join(", ", locTypeBounds) + ">";
        List<String> locParentDeclarations = new ArrayList<>();
        for (Class<?> locAncestor : locParents) {
            List<String> locParentArguments = new ArrayList<>();
            for (var locAncestorField : inheritedFields(locAncestor, aInputNames).entrySet()) {
                if (setterPolicy(locAncestorField.getValue()) != AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER
                        || referencedContract(locAncestorField.getValue().method()) == null) continue;
                String locVariable = locTypeVariables.get(locAncestorField.getKey());
                if (locVariable == null) throw new IllegalArgumentException("Missing inherited setter type argument for "
                        + locAncestorField.getKey() + " in " + aReadContract);
                locParentArguments.add(locVariable);
            }
            String locParentType = qualifiedName(locAncestor, typeName(locAncestor, locMarker, true,
                    aInputNames, aMutableNames, aConcreteNames), aMutableSubpackage);
            locParentDeclarations.add(locParentType + (locParentArguments.isEmpty() ? ""
                    : "<" + String.join(", ", locParentArguments) + ">"));
        }
        String locMutableParents = locParentDeclarations.stream()
                .reduce("", (aLeft, aRight) -> aLeft + ", " + aRight);
        String locConcreteParent = locNeedsFlattenedImplementation || locParent == null
                ? implementationBase(aReadContract)
                : qualifiedName(locParent, typeName(locParent, locMarker, false,
                        aInputNames, aMutableNames, aConcreteNames), aConcreteSubpackage);
        String locConcreteArguments = locTypeVariables.isEmpty() ? "" : "<" + String.join(", ",
                locTypeVariables.keySet().stream().map(aName -> {
                    Class<?> locTarget = referencedContract(locAll.get(aName).method());
                    return qualifiedMutableValueName(locTarget, locMarker,
                            aInputNames, aMutableNames, aConcreteNames, aMutableSubpackage);
                }).toList()) + ">";
        StringBuilder locInterface = new StringBuilder("package " + locMutablePackage + ";\n\n"
                + "/** Generated mutable contract derived from " + aReadContract.getSimpleName() + ". */\n"
                + locAnnotationLiteral
                + locXmlAnnotationLiteral
                + locSmartAnnotationLiteral
                + "public interface " + locMutable + locGenericDeclaration + " extends " + aReadContract.getCanonicalName()
                + locMutableParents
                + ", " + mutableBase(aReadContract) + " {\n");
        StringBuilder locImplementation = new StringBuilder("package " + locConcretePackage + ";\n\n"
                + "/** Generated mutable implementation of " + aReadContract.getSimpleName() + ". */\n"
                + locConcreteAnnotationLiteral
                + "public class " + locConcrete + " extends " + locConcreteParent
                + " implements " + locMutablePackage + "." + locMutable + locConcreteArguments + " {\n"
                + "    /** Create an object whose raw fields are initially absent. */\n"
                + "    public " + locConcrete + "() { super(); }\n"
                + "    /** Reconstruct an identity-preserving typed SmartDataObject graph. */\n"
                + "    public " + locConcrete
                + "(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }\n");
        for (var locField : locOwn.values()) {
            Method locGetter = locField.method();
            String locName = fieldName(locField.method(), locField.field(), aInputNames);
            String locType = mutableValueType(locGetter, locMarker, aInputNames, aMutableNames,
                    aConcreteNames, aMutableSubpackage);
            String locVariable = locTypeVariables.get(locName);
            String locInterfaceType = locVariable == null ? locType
                    : genericMutableValueType(locGetter, locVariable);

            String locSuffix = Character.toUpperCase(locName.charAt(0)) + locName.substring(1);
            AIcNameConventionCatalog_1 locAccessorCatalog = aMutableNames == null
                    ? standardNaming() : aMutableNames;
            String locSetterProfile = aMutableNames == null
                    ? standardProfile(locContractRole, true) : locMutableConvention;
            String locIdentifierConvention = semanticIdentifierConvention(locName);
            String locSetterName = locAccessorCatalog.format(locSetterProfile, "setter_method_name",
                    Map.of("identifier", locName), locIdentifierConvention);
            if (aConcreteNames != null && !aConcreteNames.matches(
                    locConcreteConvention, "setter_method_name", locSetterName))
                throw new IllegalArgumentException("SDO setter name does not match concrete naming profile: " + locSetterName);
            String locParameter = locAccessorCatalog.format(locSetterProfile, "method_parameter_name",
                    Map.of("identifier", locName), locIdentifierConvention);
            if (aConcreteNames != null && !aConcreteNames.matches(
                    locConcreteConvention, "method_parameter_name", locParameter))
                throw new IllegalArgumentException("SDO parameter name does not match concrete naming profile: " + locParameter);
            String locLiteral = "\"" + escape(locName) + "\"";
            String locBoxed = boxed(locGetter.getReturnType(), locType);
            locInterface.append("    /** Typed writable access to field ")
                    .append(locName).append(" under the published setter policy. */\n");
            locInterface.append("    @eu.algites.lib.data.dataobject.AIaDataObjectField(fieldName = \"")
                    .append(escape(locName)).append("\", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.")
                    .append(locField.field().presence().name()).append(", allowsNull = ")
                    .append(locField.field().allowsNull())
                    .append(", setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.")
                    .append(locFieldPolicies.get(locName)).append(")\n");
            locInterface.append("    ").append(fieldLabelAnnotation(locGetter, locName));
            locInterface.append("    ").append(xmlFieldAnnotation(locGetter));
            locInterface.append("    ").append(defaultValueAnnotation(locGetter));
            locInterface.append("    ").append(smartFieldAnnotation(locGetter));
            locInterface.append("    @Override ").append(locInterfaceType).append(' ')
                    .append(locGetter.getName()).append("();\n");
            locInterface.append("    void ").append(locSetterName).append('(').append(locInterfaceType).append(' ')
                    .append(locParameter).append(");\n")
                    .append("    ").append(locInterfaceType).append(" get_").append(locSuffix).append("();\n")
                    .append("    boolean isPresent_").append(locSuffix).append("();\n")
                    .append("    void unset_").append(locSuffix).append("();\n");
            locImplementation.append("    @Override public ").append(locType).append(' ').append(locGetter.getName())
                    .append("() { return (").append(locBoxed).append(") get_EffectiveField(")
                    .append(locLiteral).append("); }\n")
                    .append("    @Override public void ").append(locSetterName).append('(').append(locType).append(' ')
                    .append(locParameter).append(") { set_RawField(").append(locLiteral).append(", ")
                    .append(locParameter).append("); }\n")
                    .append("    @Override public ").append(locType).append(" get_").append(locSuffix)
                    .append("() { return (").append(locBoxed).append(") get_RawField(")
                    .append(locLiteral).append("); }\n")
                    .append("    @Override public boolean isPresent_").append(locSuffix)
                    .append("() { return isPresent_Field(").append(locLiteral).append("); }\n")
                    .append("    @Override public void unset_").append(locSuffix)
                    .append("() { unset_Field(").append(locLiteral).append("); }\n");
        }
        if (AIiXmlDataObject.class.isAssignableFrom(aReadContract)) {
            locImplementation.append("    /**\n")
                    .append("     * Parse one XML document by expanded QName, independently of child element order.\n")
                    .append("     * Nested schema contracts are materialized as their generated concrete\n")
                    .append("     * SmartDataObject implementations, including repeated sibling elements.\n")
                    .append("     * This method enforces the runtime mapping and field checks; strict full\n")
                    .append("     * XSD validation remains the responsibility of a schema validator.\n")
                    .append("     *\n")
                    .append("     * @param aXml the XML document to deserialize; DTDs and entities are forbidden\n")
                    .append("     * @return a populated instance of this generated concrete XML type\n")
                    .append("     * @throws IllegalArgumentException if the XML contains unknown or ambiguous QNames\n")
                    .append("     * @throws eu.algites.lib.data.smartdataobject.AIxSmartDataValidationException\n")
                    .append("     *         if populated fields violate SmartDataObject constraints\n")
                    .append("     */\n")
                    .append("    public static ").append(locConcrete).append(" fromXml(String aXml) {\n")
                    .append("        return eu.algites.lib.data.smartdataobject.impl.xmldefs.AIcXmlSmartDataObject.fromXml(\n")
                    .append("                aXml, ").append(locConcrete).append(".class, ");
            var locNested = new java.util.LinkedHashMap<String, String>();
            for (var locField : locAll.values()) {
                Method locGetter = locField.method();
                Class<?> locTarget = referencedContract(locGetter);
                if (locTarget == null) continue;
                if (!AIiXmlDataObject.class.isAssignableFrom(locTarget))
                    throw new IllegalArgumentException("XML field references a non-XML DataObject: " + locGetter);
                String locName = fieldName(locGetter, locField.field(), aInputNames);
                locNested.put(locName, qualifiedName(locTarget,
                        typeName(locTarget, locMarker, false, aInputNames, aMutableNames, aConcreteNames),
                        aConcreteSubpackage));
            }
            if (locNested.isEmpty()) {
                locImplementation.append("java.util.Map.of());\n");
            } else {
                locImplementation.append("java.util.Map.ofEntries(\n");
                int locIndex = 0;
                for (var locEntry : locNested.entrySet()) {
                    if (locIndex++ > 0) locImplementation.append(",\n");
                    locImplementation.append("                    java.util.Map.entry(\"")
                            .append(escape(locEntry.getKey())).append("\", ")
                            .append(locEntry.getValue()).append(".class)");
                }
                locImplementation.append("));\n");
            }
            locImplementation.append("    }\n");
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
     * The factoryClass names the specialized factory SPI, not a concrete resolver.
     */
    private static void appendResolver(StringBuilder aTarget, String aName,
            AIaCategoryProviderFactoryDefinition aResolver) {
        aTarget.append(", ").append(aName)
                .append(" = @eu.algites.lib.factory.cpdiscovery.AIaCategoryProviderFactoryDefinition(factoryClass = ")
                .append(aResolver.factoryClass().getCanonicalName()).append(".class")
                .append(", factoryCategory = \"").append(escape(aResolver.factoryCategory())).append("\"")
                .append(", factoryProviderId = \"").append(escape(aResolver.factoryProviderId())).append("\")");
    }

    /** Choose the source-family mutable contract marker from the actual read interface. */
    private static String mutableBase(Class<?> aRead) {
        if (AIiXmlDataObject.class.isAssignableFrom(aRead))
            return "eu.algites.lib.data.smartdataobject.xmldefs.AIiXmlSmartDataObject";
        if (AIiJsonDataObject.class.isAssignableFrom(aRead))
            return "eu.algites.lib.data.smartdataobject.jsondefs.AIiJsonSmartDataObject";
        if (AIiYamlDataObject.class.isAssignableFrom(aRead))
            return "eu.algites.lib.data.smartdataobject.yamldefs.AIiYamlSmartDataObject";
        return "eu.algites.lib.data.smartdataobject.AIiSmartDataObject";
    }

    /** Choose the future-proof technology implementation base for root/diamond SDO classes. */
    private static String implementationBase(Class<?> aRead) {
        if (AIiXmlDataObject.class.isAssignableFrom(aRead))
            return "eu.algites.lib.data.smartdataobject.impl.xmldefs.AIcXmlSmartDataObject";
        if (AIiJsonDataObject.class.isAssignableFrom(aRead))
            return "eu.algites.lib.data.smartdataobject.impl.jsondefs.AIcJsonSmartDataObject";
        if (AIiYamlDataObject.class.isAssignableFrom(aRead))
            return "eu.algites.lib.data.smartdataobject.impl.yamldefs.AIcYamlSmartDataObject";
        return "eu.algites.lib.data.smartdataobject.impl.standard.AIcSmartDataObject";
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
    private static String xmlTypeAnnotation(AIaXmlDataObject aMetadata) {
        if (aMetadata == null) return "";
        return "@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject(definitionKind = "
                + "eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind."
                + aMetadata.definitionKind().name() + ", namespace = \"" + escape(aMetadata.namespace())
                + "\", namespaceLocalName = \"" + escape(aMetadata.namespaceLocalName()) + "\")\n";
    }

    /** Retain XML field QName independently of its common fieldName annotation. */
    private static String xmlFieldAnnotation(Method aGetter) {
        AIaXmlDataObjectField locXml = aGetter.getDeclaredAnnotation(AIaXmlDataObjectField.class);
        if (locXml == null) return "";
        return "@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField(namespace = \""
                + escape(locXml.namespace()) + "\", namespaceLocalName = \""
                + escape(locXml.namespaceLocalName()) + "\", valueKind = "
                + "eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind."
                + locXml.valueKind().name() + ", order = " + locXml.order()
                + ", minOccurs = " + locXml.minOccurs()
                + ", maxOccurs = " + locXml.maxOccurs()
                + ", wildcardNamespace = \"" + escape(locXml.wildcardNamespace()) + "\""
                + ", wildcardProcessContents = \"" + escape(locXml.wildcardProcessContents()) + "\")\n";
    }

    /** Retain a field default factory selection on the mutable getter. */
    private static String defaultValueAnnotation(Method aGetter) {
        AIaFieldDefault locField = aGetter.getDeclaredAnnotation(AIaFieldDefault.class);
        if (locField == null) return "";
        StringBuilder locResult = new StringBuilder(
                "@eu.algites.lib.data.dataobject.AIaFieldDefault(");
        AIaCategoryProviderFactoryDefinition locResolver = locField.defaultValueResolver();
        locResult.append("defaultValueResolver = @eu.algites.lib.factory.cpdiscovery.AIaCategoryProviderFactoryDefinition(factoryClass = ")
                .append(locResolver.factoryClass().getCanonicalName()).append(".class")
                .append(", factoryCategory = \"").append(escape(locResolver.factoryCategory())).append("\"")
                .append(", factoryProviderId = \"").append(escape(locResolver.factoryProviderId())).append("\"))\n");
        return locResult.toString();
    }

    /** Tests the semantic contract hierarchy, independent of the declared Java type name. */
    private static boolean isReadContract(Class<?> aClass) {
        return aClass.isInterface() && !aClass.getPackageName().startsWith("eu.algites.lib.data.dataobject")
                && AIiDataObject.class.isAssignableFrom(aClass)
                && !(AIiXmlDataObjectNamespace.class.isAssignableFrom(aClass)
                    && aClass.getDeclaredAnnotation(AIaDataObject.class) == null);
    }

    /** Determines the independent schema role from actual marker types and XML metadata. */
    private static String dataObjectRole(Class<?> aContract) {
        if (AIiXmlDataObject.class.isAssignableFrom(aContract)) {
            AIaXmlDataObject locXml = aContract.getDeclaredAnnotation(AIaXmlDataObject.class);
            return locXml != null && locXml.definitionKind()
                    == eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT
                    ? "xmldefs_element" : "xmldefs_type";
        }
        if (AIiYamlDataObject.class.isAssignableFrom(aContract)) return "yamldefs";
        if (AIiJsonDataObject.class.isAssignableFrom(aContract)) return "jsondefs";
        return "common";
    }

    /** Appends only valid explicit package suffixes to the original contract package. */
    private static String appendedPackage(String aPackage, String aSubpackage) {
        if (aSubpackage == null || aSubpackage.isBlank()) return aPackage;
        if (!aSubpackage.matches("[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)*"))
            throw new IllegalArgumentException("Invalid output subpackage: " + aSubpackage);
        return aPackage + "." + aSubpackage;
    }

    /** Collect the complete inherited contract tree, detecting incompatible redeclarations. */
    private static LinkedHashMap<String, AIcdGetter> inheritedFields(Class<?> aType,
            AIcNameConventionCatalog_1 aInputNames) {
        var locResult = new LinkedHashMap<String, AIcdGetter>();
        for (Class<?> locParent : aType.getInterfaces()) {
            if (!AIiDataObject.class.isAssignableFrom(locParent)) continue;
            merge(locResult, inheritedFields(locParent, aInputNames));
        }
        mergeOverrides(locResult, fields(aType.getDeclaredMethods(), aInputNames));
        return locResult;
    }

    private static void merge(LinkedHashMap<String, AIcdGetter> aResult,
                              LinkedHashMap<String, AIcdGetter> aIncoming) {
        aIncoming.forEach((aName, aField) -> {
            AIcdGetter locPrevious = aResult.putIfAbsent(aName, aField);
            if (locPrevious != null &&
                    (!locPrevious.method().getGenericReturnType().equals(aField.method().getGenericReturnType())
                    || !locPrevious.field().equals(aField.field()))) {
                throw new IllegalArgumentException("Conflicting inherited field: " + aName);
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
                    throw new IllegalArgumentException("Incompatible restricted field type: " + aName);
                var locBefore = locParent.field();
                var locAfter = aField.field();
                if (locBefore.presence() == eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED
                        && locAfter.presence() != eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED
                        || locBefore.presence() == eu.algites.lib.data.dataobject.AInFieldPresenceKind.FORBIDDEN
                        && locAfter.presence() != eu.algites.lib.data.dataobject.AInFieldPresenceKind.FORBIDDEN
                        || !locBefore.allowsNull() && locAfter.allowsNull())
                    throw new IllegalArgumentException("Invalid relaxation of field restriction: " + aName);
            }
            aResult.put(aName, aField);
        });
    }

    private static LinkedHashMap<String, AIcdGetter> fields(Method[] aMethods,
            AIcNameConventionCatalog_1 aInputNames) {
        var locResult = new LinkedHashMap<String, AIcdGetter>();
        Arrays.stream(aMethods).sorted(Comparator.comparing(Method::getName)).forEach(aMethod -> {
            AIaDataObjectField locAnnotation = aMethod.getDeclaredAnnotation(AIaDataObjectField.class);
            if (locAnnotation == null) return;
            if (aMethod.getParameterCount() != 0 || Modifier.isStatic(aMethod.getModifiers())
                    || aMethod.getReturnType() == void.class) {
                throw new IllegalArgumentException("Annotated method is not a value getter: " + aMethod);
            }
            AIcdGetter locPrevious = locResult.putIfAbsent(fieldName(aMethod, locAnnotation, aInputNames), new AIcdGetter(aMethod, locAnnotation));
            if (locPrevious != null && (!locPrevious.method().getGenericReturnType()
                    .equals(aMethod.getGenericReturnType()) || !locPrevious.field().equals(locAnnotation))) {
                throw new IllegalArgumentException("Conflicting inherited field: " + fieldName(aMethod, locAnnotation, aInputNames));
            }
        });
        return locResult;
    }

    /**
     * Resolve an omitted semantic field identifier by parsing the original accessor
     * through its input convention. No getter prefix is assumed by the generator.
     */
    private static String fieldName(Method aGetter, AIaDataObjectField aField,
            AIcNameConventionCatalog_1 aInputNames) {
        if (!aField.fieldName().isBlank()) return aField.fieldName();
        Class<?> locOwner = aGetter.getDeclaringClass();
        String locRole = dataObjectRole(locOwner);
        AIaDataObject locMetadata = locOwner.getDeclaredAnnotation(AIaDataObject.class);
        AIcNameConventionCatalog_1 locCatalog = aInputNames == null ? standardNaming() : aInputNames;
        String locProfile = locMetadata != null && !locMetadata.namingConvention().isBlank()
                ? locMetadata.namingConvention()
                : aInputNames == null ? standardProfile(locRole, false)
                : aInputNames.selectedRole(locRole);
        String locIdentifier = locCatalog.parse(locProfile, "getter_method_name", aGetter.getName())
                .get("identifier");
        if (locIdentifier == null || locIdentifier.isBlank())
            throw new IllegalArgumentException("Getter naming convention has no semantic identifier: "
                    + locOwner.getName() + "." + aGetter.getName());
        return locIdentifier;
    }

    /**
     * Identifies the lexical form of a semantic field identifier, not the output method syntax.
     *
     * <p>The naming catalog converts this source form into whatever identifier convention
     * the selected getter, setter, or parameter structure declares. Raw SDO field
     * helpers deliberately retain their existing independent naming rules.
     *
     * @param aIdentifier semantic field identifier from source contract metadata
     * @return standard identifier convention used to interpret the original field name
     * @throws IllegalArgumentException if the field identifier has no supported lexical form
     */
    private static String semanticIdentifierConvention(String aIdentifier) {
        if (aIdentifier.matches("[A-Z][A-Za-z0-9]*")) return "upper_camel_case_1";
        if (aIdentifier.matches("[a-z][A-Za-z0-9]*")) return "lower_camel_case_1";
        if (aIdentifier.matches("[a-z][a-z0-9]*(?:_[a-z0-9]+)+")) return "lower_snake_case_1";
        if (aIdentifier.matches("[a-z][a-z0-9]*(?:-[a-z0-9]+)+")) return "lower_kebab_case_1";
        throw new IllegalArgumentException("Unsupported source field identifier: " + aIdentifier);
    }

    /** Standard profiles are used only when no caller-selected naming catalog exists. */
    private static AIcNameConventionCatalog_1 standardNaming() {
        try {
            return AIcNameConventionCatalog_1.standard("java");
        } catch (java.io.IOException aError) {
            throw new IllegalStateException("Default Java naming catalog is not available", aError);
        }
    }

    /** Select the stock profile by semantic role, without encoding accessor syntax. */
    private static String standardProfile(String aRole, boolean aMutable) {
        String locGroup = switch (aRole) {
            case "xmldefs_type" -> "xml-type-";
            case "xmldefs_element" -> "xml-element-";
            case "yamldefs" -> "yaml-";
            case "jsondefs" -> "json-";
            case "common" -> "";
            default -> throw new IllegalArgumentException("Unsupported DataObject naming role: " + aRole);
        };
        return "algites-java-gen-" + (aMutable ? "data-" : "") + locGroup + "intf-versioned_1";
    }

    private static String typeName(Class<?> aContract, String aMarker, boolean aMutable,
            AIcNameConventionCatalog_1 aInput, AIcNameConventionCatalog_1 aMutableCatalog,
            AIcNameConventionCatalog_1 aConcreteCatalog) {
        if (aInput == null || aMutableCatalog == null || aConcreteCatalog == null) {
            String locReadName = aContract.getSimpleName();
            if (!locReadName.matches("AI(?:ig|i)[A-Z_][A-Za-z0-9_]*"))
                throw new IllegalArgumentException("Handwritten contract " + aContract.getName()
                        + " requires configured input/output naming conventions; "
                        + "the legacy AIig/AIi prefix rule is not applicable");
            return (aMutable ? "AIig" : "AIcg") + aMarker
                    + locReadName.substring(locReadName.startsWith("AIig") ? 4 : 3);
        }
        String locSemanticRole = dataObjectRole(aContract);
        AIaDataObject locMetadata = aContract.getDeclaredAnnotation(AIaDataObject.class);
        String locSourceRole = locMetadata != null && !locMetadata.namingConvention().isBlank()
                ? locMetadata.namingConvention() : aInput.selectedRole(locSemanticRole);
        var locVars = aInput.parse(locSourceRole, "main_container_name", aContract.getSimpleName());
        AIcNameConventionCatalog_1 locTarget = aMutable ? aMutableCatalog : aConcreteCatalog;
        String locTargetRole = locTarget.selectedRole(locSemanticRole);
        return locTarget.format(locTargetRole, "main_container_name", locVars,
                aInput.identifierConvention(locSourceRole, "main_container_name"));
    }

    private static String fileName(String aType, boolean aMutable,
            AIcNameConventionCatalog_1 aMutableCatalog, AIcNameConventionCatalog_1 aConcreteCatalog,
            String aContractRole) {
        AIcNameConventionCatalog_1 locTarget = aMutable ? aMutableCatalog : aConcreteCatalog;
        if (locTarget == null) return aType + ".java";
        String locRole = locTarget.selectedRole(aContractRole);
        var locVars = locTarget.parse(locRole, "main_container_name", aType);
        String locConvention = locTarget.identifierConvention(locRole, "main_container_name");
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

    /** Express a mutable getter and setter through the same interface-level variable. */
    private static String genericMutableValueType(Method aGetter, String aVariable) {
        return java.util.List.class.isAssignableFrom(aGetter.getReturnType())
                ? "java.util.List<? extends " + aVariable + ">" : aVariable;
    }

    /**
     * Discovers the read-only contract referenced by one field, including a list element.
     *
     * <p>A parameterized collection with an unknown element type is not silently treated
     * as a typed nested object. Only declared interface types are eligible for a generated
     * concrete XML implementation mapping.
     *
     * @param aGetter the annotated getter in the read-only schema contract
     * @return the referenced read contract, or {@code null} for scalar fields
     */
    private static Class<?> referencedContract(Method aGetter) {
        Class<?> locRaw = aGetter.getReturnType();
        if (isReadContract(locRaw)) return locRaw;
        if (java.util.List.class.isAssignableFrom(locRaw) &&
                aGetter.getGenericReturnType() instanceof ParameterizedType locList) {
            Type locItem = locList.getActualTypeArguments()[0];
            if (locItem instanceof Class<?> locClass && isReadContract(locClass)) return locClass;
            if (locItem instanceof WildcardType locWildcard && locWildcard.getLowerBounds().length == 0) {
                for (Type locBound : locWildcard.getUpperBounds()) {
                    if (locBound instanceof Class<?> locClass && isReadContract(locClass)) return locClass;
                }
            }
        }
        return null;
    }

    /** A nested read contract becomes a covariant mutable value in the generated SDO API. */
    private static String mutableValueType(Method aGetter, String aMarker,
            AIcNameConventionCatalog_1 aInput, AIcNameConventionCatalog_1 aMutableNames,
            AIcNameConventionCatalog_1 aConcreteNames, String aMutableSubpackage) {
        Class<?> locReturn = aGetter.getReturnType();
        if (isReadContract(locReturn)) {
            return qualifiedMutableValueName(locReturn, aMarker,
                    aInput, aMutableNames, aConcreteNames, aMutableSubpackage);
        }
        if (java.util.List.class.isAssignableFrom(locReturn)) {
            Class<?> locNested = referencedContract(aGetter);
            if (locNested != null) {
                return "java.util.List<? extends " + qualifiedMutableValueName(locNested, aMarker,
                        aInput, aMutableNames, aConcreteNames, aMutableSubpackage) + ">";
            }
        }
        return aGetter.getGenericReturnType().getTypeName().replace('$', '.');
    }

    /**
     * Qualify a mutable referenced contract with wildcard type arguments when the
     * referenced writable interface is itself generic. This avoids exposing a raw
     * generated interface in the public bound of another generated type variable.
     */
    private static String qualifiedMutableValueName(Class<?> aRead, String aMarker,
            AIcNameConventionCatalog_1 aInput, AIcNameConventionCatalog_1 aMutableNames,
            AIcNameConventionCatalog_1 aConcreteNames, String aSubpackage) {
        String locName = qualifiedName(aRead, typeName(aRead, aMarker, true,
                aInput, aMutableNames, aConcreteNames), aSubpackage);
        long locCount = inheritedFields(aRead, aInput).values().stream()
                .filter(aField -> setterPolicy(aField)
                        == AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER
                        && referencedContract(aField.method()) != null).count();
        if (locCount == 0) return locName;
        return locName + "<" + String.join(", ", java.util.Collections.nCopies((int) locCount, "?")) + ">";
    }

    private static String qualifiedName(Class<?> aParent, String aReplacement, String aSubpackage) {
        return appendedPackage(aParent.getPackageName(), aSubpackage) + "." + aReplacement;
    }
    private static String escape(String aValue) {
        return aValue.replace("\\", "\\\\").replace("\"", "\\\"");
    }
    private static String boxed(Class<?> aClass, String aType) {
        if (!aClass.isPrimitive()) return aType;
        return Map.of(int.class, "Integer", long.class, "Long", boolean.class, "Boolean",
                double.class, "Double", float.class, "Float", short.class, "Short",
                byte.class, "Byte", char.class, "Character").get(aClass);
    }
}
