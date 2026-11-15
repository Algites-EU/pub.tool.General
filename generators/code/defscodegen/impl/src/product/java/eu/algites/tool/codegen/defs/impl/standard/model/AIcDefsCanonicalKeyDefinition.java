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
public final class AIcDefsCanonicalKeyDefinition extends AIcgdKeyDefinition_1 {
    /** Create a deferred key definition. @param identifier ID @param selector selector @param sourcePointer source path */
    public AIcDefsCanonicalKeyDefinition(String identifier,String selector,String sourcePointer) {
        this(identifier,selector,sourcePointer,List.of(),true);
    }
    /** Build the generated key-definition SDO. @param identifier ID @param selector selector @param sourcePointer path @param fields field paths @param required key or unique */
    public AIcDefsCanonicalKeyDefinition(String identifier,String selector,String sourcePointer,List<String> fields,boolean required) {
        if(Objects.requireNonNull(identifier,"identifier").isBlank() || Objects.requireNonNull(selector,"selector").isBlank() || Objects.requireNonNull(sourcePointer,"sourcePointer").isBlank())
            throw new IllegalArgumentException("Key definition identifier, selector, sourcePointer must be nonempty");
        var copy=List.copyOf(Objects.requireNonNull(fields,"fields"));
        if(copy.stream().anyMatch(String::isBlank)||copy.stream().distinct().count()!=copy.size()) throw new IllegalArgumentException("Duplicate or blank key fields");
        setIdentifier(identifier);setSelector(selector);setSourcePointer(sourcePointer);AIcDefsCanonicalBridge.values(getFieldsList()).addAll(copy);setRequired(required);
    }
    /** @return schema key ID */ public String identifier(){return getIdentifier();}
    /** @return selector */ public String selector(){return getSelector();}
    /** @return source pointer */ public String sourcePointer(){return getSourcePointer();}
    /** @return fields */ public List<String> fields(){return AIcDefsCanonicalBridge.values(getFieldsList());}
    /** @return key required */ public boolean required(){return Boolean.TRUE.equals(getRequired());}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalKeyDefinition other && Objects.equals(identifier(), other.identifier()) && Objects.equals(selector(), other.selector()) && Objects.equals(sourcePointer(), other.sourcePointer()) && Objects.equals(fields(), other.fields()) && Objects.equals(required(), other.required());
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(identifier(), selector(), sourcePointer(), fields(), required()); }
}
