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
public interface AIiDefsCanonicalStructure {
    /** Schema-defined structure variant of this generated SDO node. @return canonical kind */
    AIngStructureKind_1 kind();
    /** Check a non-null canonical child. @param node child @param location location @return child */
    static AIiDefsCanonicalStructure requireChild(AIiDefsCanonicalStructure node, String location) {
        return Objects.requireNonNull(node, Objects.requireNonNull(location, "location"));
    }
}

