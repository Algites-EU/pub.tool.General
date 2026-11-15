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
public final class AIcDefsCanonicalEnumValue extends AIcgdEnumValue_1 {
    /** Build a schema-generated enumerator. @param wireValue wire value @param displayName optional label */
    public AIcDefsCanonicalEnumValue(String wireValue,String displayName) {
        setWireValue(Objects.requireNonNull(wireValue,"wireValue")); setDisplayName(displayName == null? "":displayName);
    }
    /** @return exact wire representation */ public String wireValue(){return getWireValue();}
    /** @return human label */ public String displayName(){return getDisplayName();}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalEnumValue other && Objects.equals(wireValue(), other.wireValue()) && Objects.equals(displayName(), other.displayName());
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(wireValue(), displayName()); }
}
