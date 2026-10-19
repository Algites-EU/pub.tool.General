package eu.algites.tool.codegen.sdo.impl.standard;


import eu.algites.tool.codegen.sdo.AIcdGeneratedSdoSource;
import eu.algites.tool.codegen.sdo.AIcdSdoGenerationResult;
import eu.algites.tool.codegen.sdo.AIiSdoCodegenService;
import eu.algites.lib.data.dataobject.AIaDataObjectField;
import eu.algites.lib.data.dataobject.AIaFieldDefault;
import eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject;
import eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField;
import eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject;
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
        Objects.requireNonNull(aContractSources, "contract sources");
        if (aContractSources.isEmpty()) return Map.of();
        try (var locCompiled = AIcSdoContractSourceLoader.compile(aSourceRoot, aDependencyClassPath)) {
            Map<Path, AIcdSdoGenerationResult> locResults = new LinkedHashMap<>();
            for (Path locSource : aContractSources) {
                Path locCanonical = locCompiled.validate(locSource);
                Class<?> locClass = locCompiled.load(locCanonical);
                if (locResults.putIfAbsent(locCanonical, generate(locClass, aImplementationMarker,
                        aInputNames, aMutableNames, aConcreteNames)) != null)
                    throw new IllegalArgumentException("Duplicate read contract source: " + locCanonical);
            }
            return Map.copyOf(locResults);
        }
    }

    /** Generates SDO classes using the selected YAML naming catalogs for each of the three roles. */
    public AIcdSdoGenerationResult generate(Class<?> aReadContract, String aImplementationMarker,
            AIcNameConventionCatalog_1 aInputNames, AIcNameConventionCatalog_1 aMutableNames,
            AIcNameConventionCatalog_1 aConcreteNames) {
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
        LinkedHashMap<String, AIcdGetter> locOwn = fields(aReadContract.getDeclaredMethods());
        LinkedHashMap<String, AIcdGetter> locAll = inheritedFields(aReadContract);
        /* A multiply inherited contract cannot extend both concrete parent classes.
         * Flatten its fields into a single concrete SDO while implementing every
         * inherited mutable interface and keeping the original read-only diamond.
         */
        if (locParents.size() > 1) locOwn = locAll;
        String locPackage = aReadContract.getPackageName();
        AIaDataObject locSourceAnnotation = aReadContract.getDeclaredAnnotation(AIaDataObject.class);
        String locSchemaId = locSourceAnnotation == null ? "" : locSourceAnnotation.schemaId();
        int locSchemaVersion = locSourceAnnotation == null ? -1 : locSourceAnnotation.schemaVersion();
        var locParsedIdentity = Pattern.compile("^AIi(?:g)?(.+?)(?:_([1-9][0-9]*))?$")
                .matcher(aReadContract.getSimpleName());
        if (!locParsedIdentity.matches()) throw new IllegalArgumentException("Invalid AIig name");
        if (locSchemaId.isBlank()) {
            String locLogicalName = aInputNames == null
                    ? locParsedIdentity.group(1)
                        .replaceAll("([a-z0-9])([A-Z])", "$1-$2").toLowerCase(java.util.Locale.ROOT)
                    : AIcNameConventionCatalog_1.convertIdentifier(
                        aInputNames.parse("algites-java-gen-intf-versioned", "main_container_name",
                                normalizedReadName(aReadContract)).get("identifier"),
                        "upper_camel_case", "lower_kebab_case");
            locSchemaId = locPackage + "." + locLogicalName;
        }
        if (locSchemaVersion < 0) {
            if (locParsedIdentity.group(2) == null)
                throw new IllegalArgumentException("Missing SchemaVersion on handwritten AIig: " + aReadContract
                        + "; supply schemaVersion or use a versioned AIig name");
            locSchemaVersion = Integer.parseInt(locParsedIdentity.group(2));
        }
        String locAnnotationLiteral = "@eu.algites.lib.data.dataobject.AIaDataObject(schemaId = \""
                + escape(locSchemaId) + "\", schemaVersion = " + locSchemaVersion
                + ", schemaUrl = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.schemaUrl()) + "\""
                + ", title = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.title())
                + "\", description = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.description())
                + "\", fingerprint = \"" + escape(locSourceAnnotation == null ? "" : locSourceAnnotation.fingerprint())
                + "\", sourceContract = " + aReadContract.getCanonicalName() + ".class)\n";
        String locXmlAnnotationLiteral = xmlTypeAnnotation(aReadContract.getDeclaredAnnotation(AIaXmlDataObject.class));
        String locMutable = typeName(aReadContract, locMarker, true, aInputNames, aMutableNames, aConcreteNames);
        String locConcrete = typeName(aReadContract, locMarker, false, aInputNames, aMutableNames, aConcreteNames);
        String locMutableParents = locParents.stream()
                .map(aParent -> qualifiedName(aParent, typeName(aParent, locMarker, true,
                        aInputNames, aMutableNames, aConcreteNames)))
                .reduce("", (aLeft, aRight) -> aLeft + ", " + aRight);
        String locConcreteParent = locParent == null || locParents.size() > 1
                ? implementationBase(aReadContract)
                : qualifiedName(locParent, typeName(locParent, locMarker, false, aInputNames, aMutableNames, aConcreteNames));
        StringBuilder locInterface = new StringBuilder("package " + locPackage + ";\n\n"
                + "/** Generated mutable contract derived from " + aReadContract.getSimpleName() + ". */\n"
                + locAnnotationLiteral
                + locXmlAnnotationLiteral
                + "public interface " + locMutable + " extends " + aReadContract.getCanonicalName()
                + locMutableParents
                + ", " + mutableBase(aReadContract) + " {\n");
        StringBuilder locImplementation = new StringBuilder("package " + locPackage + ";\n\n"
                + "/** Generated mutable implementation of " + aReadContract.getSimpleName() + ". */\n"
                + "public class " + locConcrete + " extends " + locConcreteParent
                + " implements " + locMutable + " {\n"
                + "    /** Create an object whose raw fields are initially absent. */\n"
                + "    public " + locConcrete + "() { super(); }\n"
                + "    /** Reconstruct an identity-preserving typed SmartDataObject graph. */\n"
                + "    public " + locConcrete
                + "(java.util.Map<String, eu.algites.lib.data.smartdataobject.AIidVirtualFieldValue> aMapping) { super(aMapping); }\n");
        for (var locField : locOwn.values()) {
            Method locGetter = locField.method();
            String locName = fieldName(locField.method(), locField.field());
            String locType = mutableValueType(locGetter, locMarker, aInputNames, aMutableNames, aConcreteNames);
            String locSuffix = suffix(locGetter.getName());
            String locParameter = aMutableNames == null ? "a" + locSuffix
                    : aMutableNames.format("algites-java-gen-data-intf-versioned", "method_parameter_name",
                            Map.of("identifier", locSuffix), "upper_camel_case");
            if (aConcreteNames != null && !aConcreteNames.matches(
                    "algites-java-gen-data-class-versioned", "method_parameter_name", locParameter))
                throw new IllegalArgumentException("SDO parameter name does not match concrete naming profile: " + locParameter);
            String locLiteral = "\"" + escape(locName) + "\"";
            String locBoxed = boxed(locGetter.getReturnType(), locType);
            locInterface.append("    ").append(fieldLabelAnnotation(locGetter, locName));
            locInterface.append("    ").append(xmlFieldAnnotation(locGetter));
            locInterface.append("    ").append(defaultValueAnnotation(locGetter));
            locInterface.append("    @Override ").append(locType).append(' ')
                    .append(locGetter.getName()).append("();\n");
            locInterface.append("    void set").append(locSuffix).append('(').append(locType).append(' ')
                    .append(locParameter).append(");\n")
                    .append("    ").append(locType).append(" get_").append(locSuffix).append("();\n")
                    .append("    boolean isPresent_").append(locSuffix).append("();\n")
                    .append("    void unset_").append(locSuffix).append("();\n");
            locImplementation.append("    @Override public ").append(locType).append(' ').append(locGetter.getName())
                    .append("() { return (").append(locBoxed).append(") get_EffectiveField(")
                    .append(locLiteral).append("); }\n")
                    .append("    @Override public void set").append(locSuffix).append('(').append(locType).append(' ')
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
                String locName = fieldName(locGetter, locField.field());
                locNested.put(locName, qualifiedName(locTarget,
                        typeName(locTarget, locMarker, false, aInputNames, aMutableNames, aConcreteNames)));
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
        String locPath = locPackage.replace('.', '/') + "/";
        String locSourceId = locSchemaId;
        Integer locSourceVersion = locSchemaVersion;
        return new AIcdSdoGenerationResult(
                new AIcdGeneratedSdoSource(locMutable, locPath
                        + fileName(locMutable, true, aMutableNames, aConcreteNames), locInterface.toString(),
                        locPackage, locPackage, locPackage + "." + locMutable,
                        "MUTABLE_INTERFACE_TYPE", locSourceId, locSourceVersion),
                new AIcdGeneratedSdoSource(locConcrete, locPath
                        + fileName(locConcrete, false, aMutableNames, aConcreteNames), locImplementation.toString(),
                        locPackage, locPackage, locPackage + "." + locConcrete,
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
                + ", maxOccurs = " + locXml.maxOccurs() + ")\n";
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

    /** Handwritten AIi and generated AIig contracts share the same naming suffix. */
    private static boolean isReadContract(Class<?> aClass) {
        return aClass.isInterface() && !aClass.getPackageName().startsWith("eu.algites.lib.data.dataobject")
                && AIiDataObject.class.isAssignableFrom(aClass)
                && (aClass.getSimpleName().startsWith("AIig") || aClass.getSimpleName().startsWith("AIi"));
    }

    /** A selected General naming profile expects the generated-interface role prefix. */
    private static String normalizedReadName(Class<?> aClass) {
        String locName = aClass.getSimpleName();
        return locName.startsWith("AIig") ? locName : "AIig" + locName.substring(3);
    }

    /** Collect the complete inherited contract tree, detecting incompatible redeclarations. */
    private static LinkedHashMap<String, AIcdGetter> inheritedFields(Class<?> aType) {
        var locResult = new LinkedHashMap<String, AIcdGetter>();
        for (Class<?> locParent : aType.getInterfaces()) {
            if (!AIiDataObject.class.isAssignableFrom(locParent)) continue;
            merge(locResult, inheritedFields(locParent));
        }
        mergeOverrides(locResult, fields(aType.getDeclaredMethods()));
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

    private static LinkedHashMap<String, AIcdGetter> fields(Method[] aMethods) {
        var locResult = new LinkedHashMap<String, AIcdGetter>();
        Arrays.stream(aMethods).sorted(Comparator.comparing(Method::getName)).forEach(aMethod -> {
            AIaDataObjectField locAnnotation = aMethod.getDeclaredAnnotation(AIaDataObjectField.class);
            if (locAnnotation == null) return;
            if (aMethod.getParameterCount() != 0 || Modifier.isStatic(aMethod.getModifiers())
                    || aMethod.getReturnType() == void.class) {
                throw new IllegalArgumentException("Annotated method is not a value getter: " + aMethod);
            }
            AIcdGetter locPrevious = locResult.putIfAbsent(fieldName(aMethod, locAnnotation), new AIcdGetter(aMethod, locAnnotation));
            if (locPrevious != null && (!locPrevious.method().getGenericReturnType()
                    .equals(aMethod.getGenericReturnType()) || !locPrevious.field().equals(locAnnotation))) {
                throw new IllegalArgumentException("Conflicting inherited field: " + fieldName(aMethod, locAnnotation));
            }
        });
        return locResult;
    }

    private static String fieldName(Method aGetter, AIaDataObjectField aField) {
        return aField.fieldName().isBlank() ? suffix(aGetter.getName()) : aField.fieldName();
    }

    private static String typeName(Class<?> aContract, String aMarker, boolean aMutable,
            AIcNameConventionCatalog_1 aInput, AIcNameConventionCatalog_1 aMutableCatalog,
            AIcNameConventionCatalog_1 aConcreteCatalog) {
        if (aInput == null || aMutableCatalog == null || aConcreteCatalog == null)
            return (aMutable ? "AIig" : "AIcg") + aMarker + aContract.getSimpleName().substring(aContract.getSimpleName().startsWith("AIig") ? 4 : 3);
        boolean locXmlElement = aContract.getSimpleName().startsWith("AIig_xe");
        String locSourceRole = locXmlElement ? "algites-java-gen-xml-element-intf-versioned"
                : "algites-java-gen-intf-versioned";
        var locVars = aInput.parse(locSourceRole, "main_container_name",
                normalizedReadName(aContract));
        AIcNameConventionCatalog_1 locTarget = aMutable ? aMutableCatalog : aConcreteCatalog;
        return locTarget.format(aMutable
                ? (locXmlElement ? "algites-java-gen-data-xml-element-intf-versioned" : "algites-java-gen-data-intf-versioned")
                : (locXmlElement ? "algites-java-gen-data-xml-element-class-versioned" : "algites-java-gen-data-class-versioned"),
                "main_container_name", locVars, "upper_camel_case");
    }

    private static String fileName(String aType, boolean aMutable,
            AIcNameConventionCatalog_1 aMutableCatalog, AIcNameConventionCatalog_1 aConcreteCatalog) {
        AIcNameConventionCatalog_1 locTarget = aMutable ? aMutableCatalog : aConcreteCatalog;
        if (locTarget == null) return aType + ".java";
        boolean locXmlElement = aType.contains("_xe");
        String locRole = aMutable
                ? (locXmlElement ? "algites-java-gen-data-xml-element-intf-versioned" : "algites-java-gen-data-intf-versioned")
                : (locXmlElement ? "algites-java-gen-data-xml-element-class-versioned" : "algites-java-gen-data-class-versioned");
        var locVars = locTarget.parse(locRole, "main_container_name", aType);
        return locTarget.format(locRole, "file_name_stem", locVars, "upper_camel_case")
                + locTarget.format(locRole, "file_name_suffix", locVars, "upper_camel_case");
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
            AIcNameConventionCatalog_1 aConcreteNames) {
        Class<?> locReturn = aGetter.getReturnType();
        if (isReadContract(locReturn)) {
            return qualifiedName(locReturn, typeName(locReturn, aMarker, true,
                    aInput, aMutableNames, aConcreteNames));
        }
        /* Invariant generic collections cannot be narrowed in a Java override. */
        return aGetter.getGenericReturnType().getTypeName().replace('$', '.');
    }

    private static String qualifiedName(Class<?> aParent, String aReplacement) {
        return aParent.getPackageName() + "." + aReplacement;
    }
    private static String suffix(String aGetter) {
        String locSuffix = aGetter.startsWith("get") && aGetter.length() > 3
                ? aGetter.substring(3) : aGetter;
        if (!locSuffix.matches("[A-Za-z_$][A-Za-z0-9_$]*")) {
            throw new IllegalArgumentException("Unsupported getter: " + aGetter);
        }
        return Character.toUpperCase(locSuffix.charAt(0)) + locSuffix.substring(1);
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
