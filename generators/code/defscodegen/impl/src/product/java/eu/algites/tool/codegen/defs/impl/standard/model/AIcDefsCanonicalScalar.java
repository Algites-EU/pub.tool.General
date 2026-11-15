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
public final class AIcDefsCanonicalScalar extends AIcgdScalar_1 implements AIiDefsCanonicalStructure {
    /** Construct an unconstrained canonical scalar.
     * @param scalarKind canonical scalar kind
     * @param format optional source format
     */
    public AIcDefsCanonicalScalar(AIngScalarKind_1 scalarKind, String format) {
        this(scalarKind, format, -1, -1, "", "", "", false, false, "");
    }
    /** Construct a scalar with schema-defined string and numeric facets.
     * @param scalarKind scalar kind
     * @param format source format
     * @param minLength minimum string length, -1 for absent
     * @param maxLength maximum string length, -1 for absent
     * @param pattern source regular expression
     * @param minimum inclusive or exclusive decimal lower bound
     * @param maximum inclusive or exclusive decimal upper bound
     * @param exclusiveMinimum whether minimum is exclusive
     * @param exclusiveMaximum whether maximum is exclusive
     * @param multipleOf exact positive decimal divisor, or empty
     * @throws IllegalArgumentException for inconsistent bounds
     */
    public AIcDefsCanonicalScalar(AIngScalarKind_1 scalarKind, String format,
            int minLength, int maxLength, String pattern, String minimum, String maximum,
            boolean exclusiveMinimum, boolean exclusiveMaximum, String multipleOf) {
        Objects.requireNonNull(scalarKind, "scalarKind");
        if (minLength < -1 || maxLength < -1 || maxLength >= 0 && minLength > maxLength)
            throw new IllegalArgumentException("Invalid scalar length bounds");
        if (minimum != null && !minimum.isEmpty() && maximum != null && !maximum.isEmpty()
                && new BigDecimal(minimum).compareTo(new BigDecimal(maximum)) > 0)
            throw new IllegalArgumentException("Invalid numeric bounds");
        if (multipleOf != null && !multipleOf.isEmpty()
                && new BigDecimal(multipleOf).signum() <= 0)
            throw new IllegalArgumentException("multipleOf must be positive");
        setScalarKind(scalarKind);setFormat(format == null ? "" : format);
        setMinLength((long) minLength);setMaxLength((long) maxLength);setPattern(pattern == null ? "" : pattern);
        setMinimum(minimum == null ? "" : minimum);setMaximum(maximum == null ? "" : maximum);
        setExclusiveMinimum(exclusiveMinimum);setExclusiveMaximum(exclusiveMaximum);
        setMultipleOf(multipleOf == null ? "" : multipleOf);
    }
    /** @return schema kind */ public AIngScalarKind_1 scalarKind(){return getScalarKind();}
    /** @return original format */ public String format(){return getFormat();}
    /** @return minimum code-point length, -1 when absent */ public int minLength(){return getMinLength()==null?-1:getMinLength().intValue();}
    /** @return maximum code-point length, -1 when absent */ public int maxLength(){return getMaxLength()==null?-1:getMaxLength().intValue();}
    /** @return string pattern */ public String pattern(){return getPattern()==null?"":getPattern();}
    /** @return lexical lower numeric bound */ public String minimum(){return getMinimum()==null?"":getMinimum();}
    /** @return lexical upper numeric bound */ public String maximum(){return getMaximum()==null?"":getMaximum();}
    /** @return whether lower bound is exclusive */ public boolean exclusiveMinimum(){return Boolean.TRUE.equals(getExclusiveMinimum());}
    /** @return whether upper bound is exclusive */ public boolean exclusiveMaximum(){return Boolean.TRUE.equals(getExclusiveMaximum());}
    /** @return positive divisor, or empty */ public String multipleOf(){return getMultipleOf()==null?"":getMultipleOf();}
    /** @return canonical variant */ @Override public AIngStructureKind_1 kind(){return AIngStructureKind_1.SCALAR;}

    /** SDO fields define equality, not allocation identity. @param candidate peer @return equal field values */
    @Override public boolean equals(Object candidate) {
        if(this == candidate) return true;
        return candidate instanceof AIcDefsCanonicalScalar other && Objects.equals(scalarKind(), other.scalarKind()) && Objects.equals(format(), other.format()) && minLength()==other.minLength() && maxLength()==other.maxLength() && Objects.equals(pattern(), other.pattern()) && Objects.equals(minimum(), other.minimum()) && Objects.equals(maximum(), other.maximum()) && exclusiveMinimum()==other.exclusiveMinimum() && exclusiveMaximum()==other.exclusiveMaximum() && Objects.equals(multipleOf(), other.multipleOf());
    }
    /** Hash only schema-defined field values. @return schema-value hash */
    @Override public int hashCode() { return Objects.hash(scalarKind(), format(), minLength(), maxLength(), pattern(), minimum(), maximum(), exclusiveMinimum(), exclusiveMaximum(), multipleOf()); }
}
