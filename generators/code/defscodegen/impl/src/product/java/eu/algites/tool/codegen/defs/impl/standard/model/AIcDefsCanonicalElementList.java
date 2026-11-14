package eu.algites.tool.codegen.defs.impl.standard.model;

import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.impl.*;
import java.math.*;
import java.util.*;

/**
 * SDO-backed convenience view for the schema-generated canonical model.
 * Stores no independent canonical fields; every value is held in the generated SDO.
 * @author linhart1
 */
public final class AIcDefsCanonicalElementList extends AIcgdElementList_1 implements AIiDefsCanonicalStructure {
    /** Convenience for single-occurrence group. @param composition group compositor @param children group children */
    public AIcDefsCanonicalElementList(AIngComposition_1 composition,List<AIiDefsCanonicalStructure> children){this(composition,children,1,1,-1,-1);}
    /** Create a generated SDO compositional group. @param composition composition @param children direct children @param minItemCount minimum @param maxItemCount maximum */
    public AIcDefsCanonicalElementList(AIngComposition_1 composition,List<AIiDefsCanonicalStructure> children,int minItemCount,int maxItemCount){
        this(composition,children,minItemCount,maxItemCount,-1,-1);
    }
    /** Object member-count restrictions, independent of group occurrence bounds.
     * @param composition group composition
     * @param children canonical group children
     * @param minItemCount minimum group occurrences
     * @param maxItemCount maximum group occurrences
     * @param minProperties minimum present object properties or -1
     * @param maxProperties maximum present object properties or -1
     */
    public AIcDefsCanonicalElementList(AIngComposition_1 composition,List<AIiDefsCanonicalStructure> children,int minItemCount,int maxItemCount,int minProperties,int maxProperties){
        if(minProperties < -1 || maxProperties < -1 || maxProperties>=0 && minProperties>maxProperties)
            throw new IllegalArgumentException("Invalid object property bounds");
        setComposition(Objects.requireNonNull(composition,"composition"));AIcDefsCanonicalBridge.checkItemCountBounds(minItemCount,maxItemCount);
        var copies=List.copyOf(Objects.requireNonNull(children,"children"));
        AIcDefsCanonicalBridge.values(getChildrenList()).addAll(copies.stream().map(AIcDefsCanonicalBridge::selectChild).toList());
        setMinItemCount(AIcDefsCanonicalBridge.number(minItemCount));setMaxItemCount(AIcDefsCanonicalBridge.number(maxItemCount));
        setMinProperties((long) minProperties);setMaxProperties((long) maxProperties);
    }
    /** @return composition */ public AIngComposition_1 composition(){return getComposition();}
    /** @return direct child nodes */ public List<AIiDefsCanonicalStructure> children(){return getChildrenList().stream().map(AIcDefsCanonicalBridge::unselectChild).toList();}
    /** @return minimum */ public int minItemCount(){return AIcDefsCanonicalBridge.number(getMinItemCount());}
    /** @return maximum */ public int maxItemCount(){return AIcDefsCanonicalBridge.number(getMaxItemCount());}
    /** @return minimum present properties, -1 if absent */ public int minProperties(){return getMinProperties()==null?-1:getMinProperties().intValue();}
    /** @return maximum present properties, -1 if absent */ public int maxProperties(){return getMaxProperties()==null?-1:getMaxProperties().intValue();}
    /** @return canonical variant */ @Override public AIngStructureKind_1 kind(){return AIngStructureKind_1.ELEMENTLIST;}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalElementList other && Objects.equals(composition(), other.composition()) && Objects.equals(children(), other.children()) && Objects.equals(minItemCount(), other.minItemCount()) && Objects.equals(maxItemCount(), other.maxItemCount()) && minProperties()==other.minProperties() && maxProperties()==other.maxProperties();
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(composition(), children(), minItemCount(), maxItemCount(), minProperties(), maxProperties()); }
}
