package eu.algites.tool.codegen.defs.impl.standard.model;

import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.defs.model.impl.*;
import java.math.*;
import java.util.*;

/**
 * SDO-backed convenience view for the schema-generated canonical model.
 * Stores no independent canonical fields; every value is held in the generated SDO.
 * @author linhart1
 */
public final class AIcDefsCanonicalEnum extends AIcgdEnum_1 implements AIiDefsCanonicalStructure {
    /** Create an enum as a generated SDO with canonical wire values. @param baseScalarType scalar @param values members */
    public AIcDefsCanonicalEnum(AIngScalarKind_1 baseScalarType,List<AIcDefsCanonicalEnumValue> values) {
        setBaseScalarType(Objects.requireNonNull(baseScalarType,"baseScalarType"));
        var list=List.copyOf(Objects.requireNonNull(values,"values"));
        if(list.isEmpty()) throw new IllegalArgumentException("ENUM requires at least one value");
        var seen=new HashSet<Object>();
        for(var v:list){ Object semantic;String wire=v.wireValue();
            try { semantic=switch(baseScalarType){
                case INTEGER -> new BigInteger(wire);
                case NUMBER -> new BigDecimal(wire).stripTrailingZeros();
                case BOOLEAN -> switch(wire){case "true","1" -> Boolean.TRUE;case "false","0" -> Boolean.FALSE;default -> throw new IllegalArgumentException("Invalid boolean ENUM value: "+wire);};
                default -> wire;
            };}catch(NumberFormatException ex){throw new IllegalArgumentException("Invalid numeric ENUM wire value: "+wire,ex);}
            if(!seen.add(semantic)) throw new IllegalArgumentException("Duplicate ENUM wire value: "+wire);
        }
        AIcDefsCanonicalBridge.values(getValuesList()).addAll(list);
    }
    /** @return scalar base */ public AIngScalarKind_1 baseScalarType(){return getBaseScalarType();}
    /** @return canonical enum entries */ public List<AIcDefsCanonicalEnumValue> values(){return AIcDefsCanonicalBridge.values(getValuesList());}
    /** @return canonical variant */ @Override public AIngStructureKind_1 kind(){return AIngStructureKind_1.ENUM;}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalEnum other && Objects.equals(baseScalarType(), other.baseScalarType()) && Objects.equals(values(), other.values());
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(baseScalarType(), values()); }
}
