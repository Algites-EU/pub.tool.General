package eu.algites.tool.codegen.sdo;

import eu.algites.lib.data.dataobject.AIaDataObjectField;
import eu.algites.lib.data.dataobject.AIiDataObject;
import eu.algites.lib.naming.convention.AIcNameConventionCatalog;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

/** Generate mutable contracts and concrete SmartDataObjects solely from compiled AIig contracts. */
public final class AIcSdoCodegenService implements AIiSdoCodegenService {
    private record AIcdGetter(Method method, AIaDataObjectField field) { }

    @Override
    public AIcdSdoGenerationResult generate(Class<?> aReadContract, String aImplementationMarker) {
        return generate(aReadContract, aImplementationMarker, null, null, null);
    }

    /** Generates SDO classes using the selected YAML naming catalogs for each of the three roles. */
    public AIcdSdoGenerationResult generate(Class<?> aReadContract, String aImplementationMarker,
            AIcNameConventionCatalog aInputNames, AIcNameConventionCatalog aMutableNames,
            AIcNameConventionCatalog aConcreteNames) {
        Objects.requireNonNull(aReadContract, "read contract");
        String locMarker = Objects.requireNonNull(aImplementationMarker, "marker");
        if (!locMarker.matches("[a-z][a-z0-9]*")) {
            throw new IllegalArgumentException("Invalid implementation marker: " + locMarker);
        }
        if (!aReadContract.isInterface() || !AIiDataObject.class.isAssignableFrom(aReadContract)
                || !aReadContract.getSimpleName().startsWith("AIig")) {
            throw new IllegalArgumentException("Expected AIig extending AIiDataObject: " + aReadContract);
        }
        var locParents = Arrays.stream(aReadContract.getInterfaces())
                .filter(aClass -> aClass.getSimpleName().startsWith("AIig")
                        && AIiDataObject.class.isAssignableFrom(aClass)).toList();
        if (locParents.size() > 1) {
            throw new IllegalArgumentException("Multiple inherited AIig contracts require an explicit conflict policy");
        }
        Class<?> locParent = locParents.isEmpty() ? null : locParents.get(0);
        LinkedHashMap<String, AIcdGetter> locOwn = fields(aReadContract.getDeclaredMethods());
        LinkedHashMap<String, AIcdGetter> locAll = inheritedFields(aReadContract);
        String locPackage = aReadContract.getPackageName();
        String locTail = aReadContract.getSimpleName().substring(4);
        String locMutable = typeName(aReadContract, locMarker, true, aInputNames, aMutableNames, aConcreteNames);
        String locConcrete = typeName(aReadContract, locMarker, false, aInputNames, aMutableNames, aConcreteNames);
        String locMutableParent = locParent == null ? null
                : qualifiedName(locParent, typeName(locParent, locMarker, true, aInputNames, aMutableNames, aConcreteNames));
        String locConcreteParent = locParent == null
                ? "eu.algites.lib.data.smartdataobject.AIcSmartDataObject"
                : qualifiedName(locParent, typeName(locParent, locMarker, false, aInputNames, aMutableNames, aConcreteNames));
        StringBuilder locInterface = new StringBuilder("package " + locPackage + ";\n\n"
                + "/** Generated mutable contract derived from " + aReadContract.getSimpleName() + ". */\n"
                + "public interface " + locMutable + " extends " + aReadContract.getCanonicalName()
                + (locMutableParent == null ? "" : ", " + locMutableParent)
                + ", eu.algites.lib.data.smartdataobject.AIiSmartDataObject {\n");
        StringBuilder locImplementation = new StringBuilder("package " + locPackage + ";\n\n"
                + "/** Generated mutable implementation of " + aReadContract.getSimpleName() + ". */\n"
                + "public class " + locConcrete + " extends " + locConcreteParent
                + " implements " + locMutable + " {\n"
                + "    /** Create an object whose raw fields are initially absent. */\n"
                + "    public " + locConcrete + "() { super(); }\n");
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
            if (AIiDataObject.class.isAssignableFrom(locGetter.getReturnType())
                    && locGetter.getReturnType().getSimpleName().startsWith("AIig")) {
                locInterface.append("    @Override ").append(locType).append(' ')
                        .append(locGetter.getName()).append("();\n");
            }
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
        locInterface.append("}\n");
        locImplementation.append("}\n");
        String locPath = locPackage.replace('.', '/') + "/";
        var locMetadata = aReadContract.getAnnotation(eu.algites.lib.data.dataobject.AIaDataObject.class);
        String locSourceId = locMetadata == null ? "" : locMetadata.id();
        Integer locSourceVersion = locMetadata == null || locMetadata.version() < 0 ? null : locMetadata.version();
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

    /** Collect the complete inherited contract tree, detecting incompatible redeclarations. */
    private static LinkedHashMap<String, AIcdGetter> inheritedFields(Class<?> aType) {
        var locResult = new LinkedHashMap<String, AIcdGetter>();
        for (Class<?> locParent : aType.getInterfaces()) {
            if (!AIiDataObject.class.isAssignableFrom(locParent)) continue;
            merge(locResult, inheritedFields(locParent));
        }
        merge(locResult, fields(aType.getDeclaredMethods()));
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
        return aField.name().isBlank() ? suffix(aGetter.getName()) : aField.name();
    }

    private static String typeName(Class<?> aContract, String aMarker, boolean aMutable,
            AIcNameConventionCatalog aInput, AIcNameConventionCatalog aMutableCatalog,
            AIcNameConventionCatalog aConcreteCatalog) {
        if (aInput == null || aMutableCatalog == null || aConcreteCatalog == null)
            return (aMutable ? "AIig" : "AIcg") + aMarker + aContract.getSimpleName().substring(4);
        var locVars = aInput.parse("algites-java-gen-intf-versioned", "main_container_name",
                aContract.getSimpleName());
        AIcNameConventionCatalog locTarget = aMutable ? aMutableCatalog : aConcreteCatalog;
        return locTarget.format(aMutable ? "algites-java-gen-data-intf-versioned"
                : "algites-java-gen-data-class-versioned", "main_container_name", locVars, "upper_camel_case");
    }

    private static String fileName(String aType, boolean aMutable,
            AIcNameConventionCatalog aMutableCatalog, AIcNameConventionCatalog aConcreteCatalog) {
        AIcNameConventionCatalog locTarget = aMutable ? aMutableCatalog : aConcreteCatalog;
        if (locTarget == null) return aType + ".java";
        String locRole = aMutable ? "algites-java-gen-data-intf-versioned" : "algites-java-gen-data-class-versioned";
        var locVars = locTarget.parse(locRole, "main_container_name", aType);
        return locTarget.format(locRole, "file_name_stem", locVars, "upper_camel_case")
                + locTarget.format(locRole, "file_name_suffix", locVars, "upper_camel_case");
    }

    /** A nested read contract becomes a covariant mutable value in the generated SDO API. */
    private static String mutableValueType(Method aGetter, String aMarker,
            AIcNameConventionCatalog aInput, AIcNameConventionCatalog aMutableNames,
            AIcNameConventionCatalog aConcreteNames) {
        Class<?> locReturn = aGetter.getReturnType();
        if (locReturn.isInterface() && locReturn.getSimpleName().startsWith("AIig")
                && AIiDataObject.class.isAssignableFrom(locReturn)) {
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
