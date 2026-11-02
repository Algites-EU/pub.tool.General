package eu.algites.tool.codegen.defs;

import eu.algites.tool.codegen.common.AIxCodegenValidationException;

import java.util.List;
import java.util.Objects;

/**
 * Recursively composable schema data type. A collection may contain any other type,
 * including collections, choices, references or inline object definitions.
 * The structural kind is separate from property presence and nullability.
 *
 * @param kind structural kind
 * @param elementType array member type, only when kind is ARRAY
 * @param properties inline object properties, only when kind is OBJECT
 * @param alternatives choice alternatives, only when kind is ONE_OF or ANY_OF
 * @param reference target identity, only when kind is REFERENCE
 * @param constraints lexical and numeric restrictions of this node
 * @param keyedValueType type of keyed collection members, or null for non-keyed objects
 * @param keyDefinitions ordered typed key definitions of the keyed collection
 * @param positionTypes types assigned by position to the leading array slots
 * @author linhart1
 */
public record AIcdDataType(AInDataTypeKind kind, AIcdDataType elementType,
        List<AIcdPropertyDefinition> properties, List<AIcdDataType> alternatives,
        AIcdDefinitionReference reference, AIcdValueConstraints constraints,
        AIcdDataType keyedValueType, List<AIcdKeyDefinition> keyDefinitions,
        List<AIcdDataType> positionTypes) {
    /**
     * Validate recursive invariants and freeze child collections.
     *
     * @throws NullPointerException if a required kind is null
     * @throws IllegalArgumentException if array, key or choice structure is invalid
     */
    public AIcdDataType {
        Objects.requireNonNull(kind, "kind");
        properties = List.copyOf(properties == null ? List.of() : properties);
        alternatives = List.copyOf(alternatives == null ? List.of() : alternatives);
        keyDefinitions = List.copyOf(keyDefinitions == null ? List.of() : keyDefinitions);
        positionTypes = List.copyOf(positionTypes == null ? List.of() : positionTypes);
        if (keyedValueType != null && kind != AInDataTypeKind.OBJECT)
            throw new AIxCodegenValidationException("KEYED_VALUES requires OBJECT parent", "Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.");
        if (keyedValueType == null && !keyDefinitions.isEmpty() && kind != AInDataTypeKind.ARRAY
                || keyedValueType != null && keyDefinitions.isEmpty())
            throw new AIxCodegenValidationException("Key definitions require an ARRAY or a keyed OBJECT value type", "Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.");
        if (!positionTypes.isEmpty() && kind != AInDataTypeKind.ARRAY)
            throw new AIxCodegenValidationException("POSITION_TYPED_VALUE requires ARRAY parent", "Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.");
        constraints = constraints == null ? AIcdValueConstraints.empty() : constraints;
        if (kind == AInDataTypeKind.ARRAY && elementType == null)
            throw new AIxCodegenValidationException("ARRAY requires elementType", "Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.");
        if ((kind == AInDataTypeKind.ONE_OF || kind == AInDataTypeKind.ANY_OF) && alternatives.isEmpty())
            throw new AIxCodegenValidationException("Choice requires at least one alternative", "Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.");
        if (kind == AInDataTypeKind.REFERENCE && reference == null)
            throw new AIxCodegenValidationException("REFERENCE requires a target", "Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.");
    }
    /**
     * Backwards-compatible constructor for structural type nodes without keyed
     * or positional children.
     *
     * @param kind node kind
     * @param elementType homogeneous item type or null for non-arrays
     * @param properties object field declarations
     * @param alternatives choices associated with this node
     * @param reference named reference target, when this is a reference node
     * @param constraints scalar, lexical and collection constraints
     */
    public AIcdDataType(AInDataTypeKind kind, AIcdDataType elementType,
            List<AIcdPropertyDefinition> properties, List<AIcdDataType> alternatives,
            AIcdDefinitionReference reference, AIcdValueConstraints constraints) {
        this(kind, elementType, properties, alternatives, reference, constraints, null, List.of(), List.of());
    }

    /**
     * Create a map-shaped object with typed values and one or more keys.
     *
     * @param valueType non-null value contract
     * @param definitions nonempty ordered set of key definitions
     * @return canonical object preserving typed KEYED_VALUES
     * @throws IllegalArgumentException if no keys were specified
     */
    public static AIcdDataType keyedValues(AIcdDataType valueType, List<AIcdKeyDefinition> definitions) {
        return new AIcdDataType(AInDataTypeKind.OBJECT, null, List.of(), List.of(), null,
                AIcdValueConstraints.empty(), Objects.requireNonNull(valueType), definitions, List.of());
    }

    /**
     * Create a repeated XML element collection whose entries are uniquely indexed by
     * one or more direct {@code xs:key} constraints on its owning element.
     *
     * @param aElement typed element contract, normally a named XML content reference
     * @param aMinItems permitted minimum cardinality
     * @param aMaxItems permitted maximum cardinality, or null for unbounded
     * @param aKeys nonempty ordered set of key constraints
     * @return one ordered multi-mapped array whose values are XML element objects
     * @throws IllegalArgumentException if no key constraints were supplied
     */
    public static AIcdDataType keyedArray(AIcdDataType aElement, Integer aMinItems,
            Integer aMaxItems, List<AIcdKeyDefinition> aKeys) {
        if (aKeys == null || aKeys.isEmpty())
            throw new AIxCodegenValidationException("A keyed XML array needs key definitions", "Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.");
        return new AIcdDataType(AInDataTypeKind.ARRAY, Objects.requireNonNull(aElement),
                List.of(), List.of(), null,
                AIcdValueConstraints.empty().withArrayBounds(aMinItems, aMaxItems),
                null, aKeys, List.of());
    }

    /** Construct an atomic type with optional scalar constraints. */
    public static AIcdDataType atom(AInDataTypeKind aKind, AIcdValueConstraints aConstraints) {
        return new AIcdDataType(aKind, null, List.of(), List.of(), null, aConstraints);
    }
    /** Construct an array with a recursively composable element type. */
    public static AIcdDataType array(AIcdDataType aElement) {
        return new AIcdDataType(AInDataTypeKind.ARRAY, Objects.requireNonNull(aElement),
                List.of(), List.of(), null, AIcdValueConstraints.empty());
    }
    /**
     * Construct an array with explicit source cardinality and nested element type.
     *
     * @param aElement element's complete recursive type
     * @param aMinItems minimum count, or null when not constrained
     * @param aMaxItems maximum count, or null when unlimited
     * @return immutable array type with its own bounds, separate from element facets
     */
    public static AIcdDataType array(AIcdDataType aElement, Integer aMinItems, Integer aMaxItems) {
        return new AIcdDataType(AInDataTypeKind.ARRAY, Objects.requireNonNull(aElement),
                List.of(), List.of(), null, AIcdValueConstraints.empty().withArrayBounds(aMinItems, aMaxItems));
    }

    /** Construct a reference preserving its canonical identity. */
    public static AIcdDataType reference(AIcdDefinitionReference aReference) {
        return new AIcdDataType(AInDataTypeKind.REFERENCE, null, List.of(), List.of(),
                Objects.requireNonNull(aReference), AIcdValueConstraints.empty());
    }
    /** Construct a closed choice without conflating oneOf and anyOf. */
    public static AIcdDataType choice(AInDataTypeKind aKind, List<AIcdDataType> aAlternatives) {
        if (aKind != AInDataTypeKind.ONE_OF && aKind != AInDataTypeKind.ANY_OF)
            throw new AIxCodegenValidationException("Not a closed choice kind: " + aKind, "Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.");
        return new AIcdDataType(aKind, null, List.of(), aAlternatives, null, AIcdValueConstraints.empty());
    }
    /** Rebuild an object node with a new collection of properties, keeping all other type metadata. */
    public AIcdDataType withProperties(List<AIcdPropertyDefinition> aProperties) {
        if (kind != AInDataTypeKind.OBJECT)
            throw new IllegalStateException("Only an OBJECT data type has named properties");
        return new AIcdDataType(kind, elementType, aProperties, alternatives, reference,
                constraints, keyedValueType, keyDefinitions, positionTypes);
    }

    /** Return the reference of this node, or its array element when the node is a collection. */
    public AIcdDefinitionReference referencedDefinition() {
        return kind == AInDataTypeKind.REFERENCE ? reference
                : kind == AInDataTypeKind.ARRAY ? elementType.referencedDefinition() : null;
    }

    /** Construct an inline object shape. */
    public static AIcdDataType object(List<AIcdPropertyDefinition> aProperties) {
        return new AIcdDataType(AInDataTypeKind.OBJECT, null, aProperties, List.of(), null,
                AIcdValueConstraints.empty());
    }
}
