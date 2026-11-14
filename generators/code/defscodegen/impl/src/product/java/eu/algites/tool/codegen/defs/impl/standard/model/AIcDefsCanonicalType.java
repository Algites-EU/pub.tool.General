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
public final class AIcDefsCanonicalType extends AIcgdType_1 implements AIiDefsCanonicalStructure {
    /** Create a declared/synthetic type with no target. @param identity ID @param name name @param origin origin @param pathSegments path @param inheritedFromTypes parents @param structure node @param resolutionState resolution @param sourceBindings sources */
    public AIcDefsCanonicalType(String identity,String name,AIngTypeOrigin_1 origin,List<String> pathSegments,List<String> inheritedFromTypes,AIiDefsCanonicalStructure structure,AIngResolutionState_1 resolutionState,Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings){
        this(identity,name,origin,pathSegments,inheritedFromTypes,structure,resolutionState,sourceBindings,"", "", "");
    }
    /** Create a type with target. @param identity ID @param name name @param origin origin @param pathSegments path @param inheritedFromTypes parents @param structure node @param resolutionState resolution @param sourceBindings sources @param targetIdentity linked identity */
    public AIcDefsCanonicalType(String identity,String name,AIngTypeOrigin_1 origin,List<String> pathSegments,List<String> inheritedFromTypes,AIiDefsCanonicalStructure structure,AIngResolutionState_1 resolutionState,Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings,String targetIdentity){
        this(identity,name,origin,pathSegments,inheritedFromTypes,structure,resolutionState,sourceBindings,targetIdentity,"", "");
    }
    /** Create the complete SDO type. @param identity ID @param name name @param origin origin @param pathSegments path @param inheritedFromTypes parents @param structure node @param resolutionState resolution @param sourceBindings sources @param targetIdentity target @param schemaVersion version @param description documentation */
    public AIcDefsCanonicalType(String identity,String name,AIngTypeOrigin_1 origin,List<String> pathSegments,List<String> inheritedFromTypes,AIiDefsCanonicalStructure structure,AIngResolutionState_1 resolutionState,Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings,String targetIdentity,String schemaVersion,String description){
        if(Objects.requireNonNull(identity,"identity").isBlank())throw new IllegalArgumentException("Type identity must not be blank");
        Objects.requireNonNull(name,"name");Objects.requireNonNull(origin,"origin");Objects.requireNonNull(resolutionState,"resolutionState");
        targetIdentity=Objects.requireNonNull(targetIdentity,"targetIdentity");
        schemaVersion=Objects.requireNonNull(schemaVersion,"schemaVersion");description=Objects.requireNonNull(description,"description");
        var segments=List.copyOf(pathSegments==null?List.of():pathSegments);
        var parents=List.copyOf(inheritedFromTypes==null?List.of():inheritedFromTypes);
        if(resolutionState==AIngResolutionState_1.RESOLVED){
            if((structure==null)==targetIdentity.isEmpty()) throw new IllegalArgumentException("Resolved TYPE requires exactly one structure or linked target identity");
        }else if(!targetIdentity.isEmpty())throw new IllegalArgumentException("Pending TYPE cannot already have a linked target");
        if(origin==AIngTypeOrigin_1.SYNTHETIC&&segments.isEmpty())throw new IllegalArgumentException("Synthetic TYPE requires semantic naming path segments");
        setIdentity(identity);setName(name);setOrigin(origin);AIcDefsCanonicalBridge.values(getPathSegmentsList()).addAll(segments);AIcDefsCanonicalBridge.values(getInheritedFromTypesList()).addAll(parents);
        if(structure!=null) setContent(new AIigTypeContentVariantStructure1_1(AIcDefsCanonicalBridge.select(structure)));
        else if(!targetIdentity.isEmpty()) setContent(new AIigTypeContentVariantTargetIdentity2_1(targetIdentity));
        setResolutionState(resolutionState);setSourceBindings(AIcDefsCanonicalBridge.bindings(sourceBindings));
        setSchemaVersion(schemaVersion);setDescription(description);
    }
    /** @return canonical identity */ public String identity(){return getIdentity();}
    /** @return type name */ public String name(){return getName();}
    /** @return origin */ public AIngTypeOrigin_1 origin(){return getOrigin();}
    /** @return path */ public List<String> pathSegments(){return AIcDefsCanonicalBridge.values(getPathSegmentsList());}
    /** @return parents */ public List<String> inheritedFromTypes(){return AIcDefsCanonicalBridge.values(getInheritedFromTypesList());}
    /** @return nested schema structure */ public AIiDefsCanonicalStructure structure(){return _isPresent_Content() && getContent() instanceof AIigTypeContentVariantStructure1_1 c
            ? AIcDefsCanonicalBridge.unselect(c.getStructure()) : null;}
    /** @return resolution state */ public AIngResolutionState_1 resolutionState(){return getResolutionState();}
    /** @return source binding map */ public Map<AIngSourceInputKind_1,List<AIcDefsCanonicalSourceBinding>> sourceBindings(){return AIcDefsCanonicalBridge.bindings(getSourceBindings());}
    /** @return target identity */ public String targetIdentity(){return _isPresent_Content() && getContent() instanceof AIigTypeContentVariantTargetIdentity2_1 c
            ? c.getTargetIdentity() : "";}
    /** @return schema version */ public String schemaVersion(){return getSchemaVersion()==null?"":getSchemaVersion();}
    /** @return description */ public String description(){return getDescription()==null?"":getDescription();}
    /** @return kind */ @Override public AIngStructureKind_1 kind(){return AIngStructureKind_1.TYPE;}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalType other && Objects.equals(identity(), other.identity()) && Objects.equals(name(), other.name()) && Objects.equals(origin(), other.origin()) && Objects.equals(pathSegments(), other.pathSegments()) && Objects.equals(inheritedFromTypes(), other.inheritedFromTypes()) && Objects.equals(structure(), other.structure()) && Objects.equals(resolutionState(), other.resolutionState()) && Objects.equals(sourceBindings(), other.sourceBindings()) && Objects.equals(targetIdentity(), other.targetIdentity()) && Objects.equals(schemaVersion(), other.schemaVersion()) && Objects.equals(description(), other.description());
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(identity(), name(), origin(), pathSegments(), inheritedFromTypes(), structure(), resolutionState(), sourceBindings(), targetIdentity(), schemaVersion(), description()); }
}
