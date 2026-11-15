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
public final class AIcDefsCanonicalMap extends AIcgdMap_1 implements AIiDefsCanonicalStructure {
    /** Create generated keyed map. @param name field @param mapKind map kind @param keyType key @param valueType value @param sourceBindings provenance */
    public AIcDefsCanonicalMap(String name,AIngMapKind_1 mapKind,AIiDefsCanonicalStructure keyType,AIiDefsCanonicalStructure valueType,Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings){
        setName(name==null?"":name);setMapKind(Objects.requireNonNull(mapKind,"mapKind"));
        setKeyType(AIcDefsCanonicalBridge.select(Objects.requireNonNull(keyType,"keyType")));
        setValueType(AIcDefsCanonicalBridge.select(Objects.requireNonNull(valueType,"valueType")));
        setSourceBindings(AIcDefsCanonicalBridge.bindings(sourceBindings));
    }
    /** @return map name */ public String name(){return getName();}
    /** @return map kind */ public AIngMapKind_1 mapKind(){return getMapKind();}
    /** @return key type */ public AIiDefsCanonicalStructure keyType(){return AIcDefsCanonicalBridge.unselect(getKeyType());}
    /** @return value type */ public AIiDefsCanonicalStructure valueType(){return AIcDefsCanonicalBridge.unselect(getValueType());}
    /** @return source provenance */ public Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings(){return AIcDefsCanonicalBridge.bindings(getSourceBindings());}
    /** @return kind */ @Override public AIngStructureKind_1 kind(){return AIngStructureKind_1.MAP;}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalMap other && Objects.equals(name(), other.name()) && Objects.equals(mapKind(), other.mapKind()) && Objects.equals(keyType(), other.keyType()) && Objects.equals(valueType(), other.valueType()) && Objects.equals(sourceBindings(), other.sourceBindings());
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(name(), mapKind(), keyType(), valueType(), sourceBindings()); }
}
