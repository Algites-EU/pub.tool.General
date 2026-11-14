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
public final class AIcDefsCanonicalElement extends AIcgdElement_1 implements AIiDefsCanonicalStructure {
    /** Single property. @param name name @param structure nested structure @param keyDefinitions keys @param sourceBindings provenance */
    public AIcDefsCanonicalElement(String name,AIiDefsCanonicalStructure structure,List<AIcDefsCanonicalKeyDefinition> keyDefinitions,Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings){this(name,structure,keyDefinitions,sourceBindings,0,1,"",null);}
    /** Explicit multiplicities. @param name name @param structure structure @param keyDefinitions keys @param sourceBindings provenance @param minItemCount min @param maxItemCount max */
    public AIcDefsCanonicalElement(String name,AIiDefsCanonicalStructure structure,List<AIcDefsCanonicalKeyDefinition> keyDefinitions,Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings,int minItemCount,int maxItemCount){this(name,structure,keyDefinitions,sourceBindings,minItemCount,maxItemCount,"",null);}
    /** Described property. @param name name @param structure structure @param keyDefinitions keys @param sourceBindings provenance @param minItemCount min @param maxItemCount max @param description description */
    public AIcDefsCanonicalElement(String name,AIiDefsCanonicalStructure structure,List<AIcDefsCanonicalKeyDefinition> keyDefinitions,Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings,int minItemCount,int maxItemCount,String description){this(name,structure,keyDefinitions,sourceBindings,minItemCount,maxItemCount,description,null);}
    /** Full schema-generated property. @param name name @param structure structure @param keyDefinitions keys @param sourceBindings provenance @param minItemCount min @param maxItemCount max @param description description @param xmlWire wire name */
    public AIcDefsCanonicalElement(String name,AIiDefsCanonicalStructure structure,List<AIcDefsCanonicalKeyDefinition> keyDefinitions,Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings,int minItemCount,int maxItemCount,String description,AIcDefsCanonicalXmlWireName xmlWire){
        this(name,structure,keyDefinitions,sourceBindings,minItemCount,maxItemCount,description,xmlWire,"","",false);
    }
    /** Construct a schema field including default/fixed metadata and empty-state permission.
     * @param name logical member name
     * @param structure resolved or referenced canonical child
     * @param keyDefinitions static index declarations
     * @param sourceBindings source declarations by technology
     * @param minItemCount minimum cardinality
     * @param maxItemCount maximum cardinality, or -1 for unbounded
     * @param description schema documentation
     * @param xmlWire representation-specific XML QName, if applicable
     * @param defaultKind one of the four standard default modes, or empty when absent
     * @param defaultValue lexical default/fixed value; empty remains a valid literal
     * @param emptyAllowed whether a special EMPTY_VALUE assignment is permitted
     * @throws IllegalArgumentException for invalid cardinality, name or default kind
     * @throws NullPointerException for required null parameters
     */
    public AIcDefsCanonicalElement(String name,AIiDefsCanonicalStructure structure,List<AIcDefsCanonicalKeyDefinition> keyDefinitions,Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings,int minItemCount,int maxItemCount,String description,AIcDefsCanonicalXmlWireName xmlWire,String defaultKind,String defaultValue,boolean emptyAllowed){
        this(name, structure, keyDefinitions, sourceBindings, minItemCount, maxItemCount,
                description, xmlWire, defaultKind, defaultValue, emptyAllowed,
                AIngElementKind_1.REFERENCED);
    }
    /** Canonical member placement; the origin of the referenced type is independent.
     * @param name logical getter name
     * @param structure object or scalar definition
     * @param keyDefinitions scoped indexes
     * @param sourceBindings input provenance
     * @param minItemCount minimum occurrences
     * @param maxItemCount maximum occurrences, -1 means unbounded
     * @param description member documentation
     * @param xmlWire XML wire identity for referenced members only
     * @param defaultKind default application rule
     * @param defaultValue lexical default value
     * @param emptyAllowed whether empty XML values may be represented
     * @param elementKind whether the member introduces a wire name
     */
    public AIcDefsCanonicalElement(String name, AIiDefsCanonicalStructure structure,
            List<AIcDefsCanonicalKeyDefinition> keyDefinitions,
            Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings,
            int minItemCount, int maxItemCount, String description, AIcDefsCanonicalXmlWireName xmlWire,
            String defaultKind, String defaultValue, boolean emptyAllowed, AIngElementKind_1 elementKind) {
        if (Objects.requireNonNull(elementKind, "elementKind") == AIngElementKind_1.EMBEDDED
                && (xmlWire != null || !defaultKind.isEmpty() || !defaultValue.isEmpty()
                    || emptyAllowed || !(structure instanceof AIcDefsCanonicalType
                    || structure instanceof AIcDefsCanonicalList))) {
            throw new IllegalArgumentException("EMBEDDED requires an object type without a wire QName/default");
        }
        Objects.requireNonNull(defaultKind, "defaultKind");
        Objects.requireNonNull(defaultValue, "defaultValue");
        if (!List.of("", "DECLARATION_ONLY", "IF_FIELD_VALUE_NOT_PRESENT",
                "IF_FIELD_VALUE_EMPTY", "CONSTRAINT_DEFAULT").contains(defaultKind)) {
            throw new IllegalArgumentException("Unknown field default kind: " + defaultKind);
        }
        if (defaultKind.isEmpty() && !defaultValue.isEmpty()) {
            throw new IllegalArgumentException("A default literal requires a default kind");
        }
        if(Objects.requireNonNull(name,"name").isBlank())throw new IllegalArgumentException("ELEMENT name must not be blank");
        AIcDefsCanonicalBridge.checkItemCountBounds(minItemCount,maxItemCount);
        if(xmlWire!=null&&xmlWire.valueKind()==AIngXmlWireNameValueKind_1.ATTRIBUTE&&(minItemCount>1||maxItemCount!=1)) throw new IllegalArgumentException("Invalid XML attribute occurrence");
        setName(name);setStructure(AIcDefsCanonicalBridge.select(Objects.requireNonNull(structure,"structure")));
        AIcDefsCanonicalBridge.values(getKeyDefinitionsList()).addAll(List.copyOf(Objects.requireNonNull(keyDefinitions,"keyDefinitions")));
        setSourceBindings(AIcDefsCanonicalBridge.bindings(sourceBindings));
        setMinItemCount(AIcDefsCanonicalBridge.number(minItemCount));setMaxItemCount(AIcDefsCanonicalBridge.number(maxItemCount));
        setDescription(Objects.requireNonNull(description,"description"));
        if(xmlWire!=null)setXmlWire(xmlWire);
        setDefaultKind(defaultKind);setDefaultValue(defaultValue);setIsEmptyAllowed(emptyAllowed);
        setElementKind(elementKind);
    }
    /** @return whether this occurrence has its own wire name */
    public AIngElementKind_1 elementKind(){return getElementKind();}
    /** @return element name */ public String name(){return getName();}
    /** @return nested structure */ public AIiDefsCanonicalStructure structure(){return AIcDefsCanonicalBridge.unselect(getStructure());}
    /** @return key definitions */ public List<AIcDefsCanonicalKeyDefinition> keyDefinitions(){return AIcDefsCanonicalBridge.values(getKeyDefinitionsList());}
    /** @return grouped provenance */ public Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings(){return AIcDefsCanonicalBridge.bindings(getSourceBindings());}
    /** @return min */ public int minItemCount(){return AIcDefsCanonicalBridge.number(getMinItemCount());}
    /** @return max */ public int maxItemCount(){return AIcDefsCanonicalBridge.number(getMaxItemCount());}
    /** @return description */ public String description(){return getDescription();}
    /** @return exact wire name */ public AIcDefsCanonicalXmlWireName xmlWire(){return (AIcDefsCanonicalXmlWireName)getXmlWire();}
    /** @return empty or one of DECLARATION_ONLY, IF_FIELD_VALUE_NOT_PRESENT,
     * IF_FIELD_VALUE_EMPTY, CONSTRAINT_DEFAULT */
    public String defaultKind(){return getDefaultKind()==null?"":getDefaultKind();}
    /** @return lexical default or fixed value, including the valid empty literal */
    public String defaultValue(){return getDefaultValue()==null?"":getDefaultValue();}
    /** @return true if this field admits the explicit EMPTY_VALUE state */
    public boolean isEmptyAllowed(){return Boolean.TRUE.equals(getIsEmptyAllowed());}
    /** @return canonical kind */ @Override public AIngStructureKind_1 kind(){return AIngStructureKind_1.ELEMENT;}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalElement other && Objects.equals(elementKind(), other.elementKind()) && Objects.equals(name(), other.name()) && Objects.equals(structure(), other.structure()) && Objects.equals(keyDefinitions(), other.keyDefinitions()) && Objects.equals(sourceBindings(), other.sourceBindings()) && Objects.equals(minItemCount(), other.minItemCount()) && Objects.equals(maxItemCount(), other.maxItemCount()) && Objects.equals(description(), other.description()) && Objects.equals(xmlWire(), other.xmlWire()) && Objects.equals(defaultKind(), other.defaultKind()) && Objects.equals(defaultValue(), other.defaultValue()) && isEmptyAllowed()==other.isEmptyAllowed();
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(elementKind(), name(), structure(), keyDefinitions(), sourceBindings(), minItemCount(), maxItemCount(), description(), xmlWire(), defaultKind(), defaultValue(), isEmptyAllowed()); }
}
