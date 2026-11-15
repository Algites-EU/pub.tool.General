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
public final class AIcDefsCanonicalXmlWireName extends AIcgdXmlWireName_1 {
    /** Construct one typed wire name. @param namespaceUri expanded namespace @param localName local part @param valueKind schema wire kind */
    public AIcDefsCanonicalXmlWireName(String namespaceUri,String localName,AIngXmlWireNameValueKind_1 valueKind){
        Objects.requireNonNull(namespaceUri,"namespaceUri"); Objects.requireNonNull(localName,"localName"); Objects.requireNonNull(valueKind,"valueKind");
        if(localName.isEmpty()||localName.contains(":")||localName.startsWith("{")) throw new IllegalArgumentException("Invalid XML QName local name");
        setNamespaceUri(namespaceUri);setLocalName(localName);setValueKind(valueKind);
    }
    /** @return XML namespace URI */ public String namespaceUri(){return getNamespaceUri();}
    /** @return XML local name */ public String localName(){return getLocalName();}
    /** @return XML value kind */ public AIngXmlWireNameValueKind_1 valueKind(){return getValueKind();}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalXmlWireName other && Objects.equals(namespaceUri(), other.namespaceUri()) && Objects.equals(localName(), other.localName()) && Objects.equals(valueKind(), other.valueKind());
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(namespaceUri(), localName(), valueKind()); }
}
