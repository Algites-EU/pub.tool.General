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
public final class AIcDefsCanonicalList extends AIcgdList_1 implements AIiDefsCanonicalStructure {
    /** Unkeyed collection. @param name field @param item element @param minItemCount min @param maxItemCount max */
    public AIcDefsCanonicalList(String name,AIiDefsCanonicalStructure item,int minItemCount,int maxItemCount){this(name,item,minItemCount,maxItemCount,List.of(),null,false);}
    /** Unkeyed, unbounded collection. @param name field @param item element */
    public AIcDefsCanonicalList(String name,AIiDefsCanonicalStructure item){this(name,item,0,-1,List.of(),null,false);}
    /** Keyed collection. @param name field @param item element @param minItemCount min @param maxItemCount max @param keyDefinitions keys */
    public AIcDefsCanonicalList(String name,AIiDefsCanonicalStructure item,int minItemCount,int maxItemCount,List<AIcDefsCanonicalKeyDefinition> keyDefinitions){this(name,item,minItemCount,maxItemCount,keyDefinitions,null,false);}
    /** Full generated collection. @param name field @param item item @param minItemCount min @param maxItemCount max @param keyDefinitions keys @param xmlWire wire */
    public AIcDefsCanonicalList(String name,AIiDefsCanonicalStructure item,int minItemCount,int maxItemCount,List<AIcDefsCanonicalKeyDefinition> keyDefinitions,AIcDefsCanonicalXmlWireName xmlWire){
        this(name,item,minItemCount,maxItemCount,keyDefinitions,xmlWire,false);
    }
    /** Full collection, including uniqueness restriction.
     * @param name logical name
     * @param item canonical item type
     * @param minItemCount minimum item count
     * @param maxItemCount maximum item count
     * @param keyDefinitions source key definitions
     * @param xmlWire optional XML identity
     * @param uniqueItems enforce distinct items
     */
    public AIcDefsCanonicalList(String name,AIiDefsCanonicalStructure item,int minItemCount,int maxItemCount,List<AIcDefsCanonicalKeyDefinition> keyDefinitions,AIcDefsCanonicalXmlWireName xmlWire,boolean uniqueItems){
        name=name==null?"":name;Objects.requireNonNull(item,"item");AIcDefsCanonicalBridge.checkItemCountBounds(minItemCount,maxItemCount);
        var keys=List.copyOf(Objects.requireNonNull(keyDefinitions,"keyDefinitions"));
        if(xmlWire!=null && xmlWire.valueKind()!=AIngXmlWireNameValueKind_1.ELEMENT) throw new IllegalArgumentException("Repeated LIST cannot represent an XML attribute");
        if(!keys.isEmpty()&&name.isBlank()) throw new IllegalArgumentException("Keyed LIST requires a source field name");
        if(keys.stream().map(AIcDefsCanonicalKeyDefinition::identifier).distinct().count()!=keys.size())throw new IllegalArgumentException("Duplicate keyed LIST constraint name");
        setName(name);setItem(AIcDefsCanonicalBridge.select(item));
        setMinItemCount(AIcDefsCanonicalBridge.number(minItemCount));setMaxItemCount(AIcDefsCanonicalBridge.number(maxItemCount));
        AIcDefsCanonicalBridge.values(getKeyDefinitionsList()).addAll(keys);if(xmlWire!=null)setXmlWire(xmlWire);setUniqueItems(uniqueItems);
    }
    /** @return collection name */ public String name(){return getName();}
    /** @return item type */ public AIiDefsCanonicalStructure item(){return AIcDefsCanonicalBridge.unselect(getItem());}
    /** @return min */ public int minItemCount(){return AIcDefsCanonicalBridge.number(getMinItemCount());}
    /** @return max */ public int maxItemCount(){return AIcDefsCanonicalBridge.number(getMaxItemCount());}
    /** @return keys */ public List<AIcDefsCanonicalKeyDefinition> keyDefinitions(){return AIcDefsCanonicalBridge.values(getKeyDefinitionsList());}
    /** @return true if values must be unique */ public boolean uniqueItems(){return Boolean.TRUE.equals(getUniqueItems());}
    /** @return wire name */ public AIcDefsCanonicalXmlWireName xmlWire(){return (AIcDefsCanonicalXmlWireName)getXmlWire();}
    /** @return kind */ @Override public AIngStructureKind_1 kind(){return AIngStructureKind_1.LIST;}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalList other && Objects.equals(name(), other.name()) && Objects.equals(item(), other.item()) && Objects.equals(minItemCount(), other.minItemCount()) && Objects.equals(maxItemCount(), other.maxItemCount()) && Objects.equals(keyDefinitions(), other.keyDefinitions()) && Objects.equals(xmlWire(), other.xmlWire()) && uniqueItems()==other.uniqueItems();
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(name(), item(), minItemCount(), maxItemCount(), keyDefinitions(), xmlWire(), uniqueItems()); }
}
