package eu.algites.tool.codegen.defs;

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
 */
public record AIcdDataType(AInDataTypeKind kind, AIcdDataType elementType,
        List<AIcdPropertyDefinition> properties, List<AIcdDataType> alternatives,
        AIcdDefinitionReference reference, AIcdValueConstraints constraints) {
    /** Validate recursive invariants and freeze child collections. */
    public AIcdDataType {
        Objects.requireNonNull(kind, "kind");
        properties = List.copyOf(properties == null ? List.of() : properties);
        alternatives = List.copyOf(alternatives == null ? List.of() : alternatives);
        constraints = constraints == null ? AIcdValueConstraints.empty() : constraints;
        if (kind == AInDataTypeKind.ARRAY && elementType == null)
            throw new IllegalArgumentException("ARRAY requires elementType");
        if ((kind == AInDataTypeKind.ONE_OF || kind == AInDataTypeKind.ANY_OF) && alternatives.isEmpty())
            throw new IllegalArgumentException("Choice requires at least one alternative");
        if (kind == AInDataTypeKind.REFERENCE && reference == null)
            throw new IllegalArgumentException("REFERENCE requires a target");
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
            throw new IllegalArgumentException("Not a closed choice kind: " + aKind);
        return new AIcdDataType(aKind, null, List.of(), aAlternatives, null, AIcdValueConstraints.empty());
    }
    /** Rebuild an object node with a new collection of properties, keeping all other type metadata. */
    public AIcdDataType withProperties(List<AIcdPropertyDefinition> aProperties) {
        if (kind != AInDataTypeKind.OBJECT)
            throw new IllegalStateException("Only an OBJECT data type has named properties");
        return new AIcdDataType(kind, elementType, aProperties, alternatives, reference, constraints);
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
