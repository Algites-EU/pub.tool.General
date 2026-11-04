package eu.algites.tool.codegen.defs;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.Objects;

/**
 * A finite set of wire values with an explicit scalar base type.
 *
 * @param baseScalarType scalar family of enumerated values, including non-string enums
 * @param values ordered immutable wire values, never implicitly renumbered
 */
public record AIcdDefsCodegenEnum(AInDefsCodegenScalarKind baseScalarType,
        List<AIcdDefsCodegenEnumValue> values) implements AIiDefsCodegenStructure {
    /**
     * Validates and freezes the ordered wire values, rejecting duplicate values
     * even when two numeric/boolean lexical forms differ but mean the same thing.
     *
     * @throws IllegalArgumentException for an empty enumeration, invalid numeric
     *         or boolean wire spelling, or repeated semantic enum values
     */
    public AIcdDefsCodegenEnum {
        Objects.requireNonNull(baseScalarType, "baseScalarType");
        values = List.copyOf(Objects.requireNonNull(values, "values"));
        if (values.isEmpty()) throw new IllegalArgumentException("ENUM requires at least one value");
        Set<Object> seen = new HashSet<>();
        for (var value : values) {
            Object semantic;
            String wire = value.wireValue();
            try {
                semantic = switch (baseScalarType) {
                    case INTEGER -> new BigInteger(wire);
                    case NUMBER -> new BigDecimal(wire).stripTrailingZeros();
                    case BOOLEAN -> switch (wire) {
                        case "true", "1" -> Boolean.TRUE;
                        case "false", "0" -> Boolean.FALSE;
                        default -> throw new IllegalArgumentException("Invalid boolean ENUM value: " + wire);
                    };
                    default -> wire;
                };
            } catch (NumberFormatException failure) {
                throw new IllegalArgumentException("Invalid numeric ENUM wire value: " + wire, failure);
            }
            if (!seen.add(semantic)) {
                throw new IllegalArgumentException("Duplicate ENUM wire value: " + wire);
            }
        }
    }
    /** {@inheritDoc} */
    @Override public AInDefsCodegenStructureKind kind() { return AInDefsCodegenStructureKind.ENUM; }
}

