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
public final class AIcDefsCanonicalSourceBinding extends AIcgdSourceBinding_1 {
    /** Build one generated, typed source provenance entry. @param sourceResource original resource @param sourcePointer source path @param representationKind construct */
    public AIcDefsCanonicalSourceBinding(String sourceResource,String sourcePointer,String representationKind) {
        Objects.requireNonNull(sourceResource,"sourceResource");
        if (sourceResource.isBlank()) throw new IllegalArgumentException("sourceResource must not be blank");
        setSourceResource(sourceResource); setSourcePointer(Objects.requireNonNull(sourcePointer,"sourcePointer"));
        setRepresentationKind(Objects.requireNonNull(representationKind,"representationKind"));
    }
    /** @return original source resource */ public String sourceResource(){return getSourceResource();}
    /** @return original source path */ public String sourcePointer(){return getSourcePointer();}
    /** @return source construct */ public String representationKind(){return getRepresentationKind();}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalSourceBinding other && Objects.equals(sourceResource(), other.sourceResource()) && Objects.equals(sourcePointer(), other.sourcePointer()) && Objects.equals(representationKind(), other.representationKind());
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(sourceResource(), sourcePointer(), representationKind()); }
}
