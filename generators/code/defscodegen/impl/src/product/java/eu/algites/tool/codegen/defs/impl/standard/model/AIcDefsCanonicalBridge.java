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
public final class AIcDefsCanonicalBridge {
    private AIcDefsCanonicalBridge() { }
    /** Wrap the SDO itself into its schema-generated sealed choice. @param node input @return selected variant */
    public static AIigStructure_1 select(AIiDefsCanonicalStructure node) {
        Objects.requireNonNull(node, "node");
        if (node instanceof AIcDefsCanonicalType x) {
            return new AIigStructureVariantType1_1(x);
        } else if (node instanceof AIcDefsCanonicalElementList x) {
            return new AIigStructureVariantElementList2_1(x);
        } else if (node instanceof AIcDefsCanonicalElement x) {
            return new AIigStructureVariantElement3_1(x);
        } else if (node instanceof AIcDefsCanonicalList x) {
            return new AIigStructureVariantList4_1(x);
        } else if (node instanceof AIcDefsCanonicalMap x) {
            return new AIigStructureVariantMap5_1(x);
        } else if (node instanceof AIcDefsCanonicalScalar x) {
            return new AIigStructureVariantScalar6_1(x);
        } else if (node instanceof AIcDefsCanonicalEnum x) {
            return new AIigStructureVariantEnum7_1(x);
        }
        throw new IllegalArgumentException("Unrecognized schema-generated canonical structure: " + node);
    }
    /** Unwrap a generated sealed choice with its typed SDO inside. @param selected variant @return SDO node */
    public static AIiDefsCanonicalStructure unselect(AIigStructure_1 selected) {
        if (selected == null) return null;
        Object node;
        if (selected instanceof AIigStructureVariantType1_1 x) node=x.getType();
        else if (selected instanceof AIigStructureVariantElementList2_1 x) node=x.getElementList();
        else if (selected instanceof AIigStructureVariantElement3_1 x) node=x.getElement();
        else if (selected instanceof AIigStructureVariantList4_1 x) node=x.getList();
        else if (selected instanceof AIigStructureVariantMap5_1 x) node=x.getMap();
        else if (selected instanceof AIigStructureVariantScalar6_1 x) node=x.getScalar();
        else if (selected instanceof AIigStructureVariantEnum7_1 x) node=x.getEnum();
        else throw new IllegalArgumentException("Unsupported sealed Structure variant: " + selected.getClass());
        if (!(node instanceof AIiDefsCanonicalStructure view))
            throw new IllegalStateException("Expected the typed generated SDO view, received " + node);
        return view;
    }
    /** Choose a generated ELEMENTLIST child alternative. @param node child @return selected alternative */
    public static AIigElementListChild_1 selectChild(AIiDefsCanonicalStructure node) {
        Objects.requireNonNull(node, "node");
        if (node instanceof AIcDefsCanonicalElementList x) {
            return new AIigElementListChildVariantElementList2_1(x);
        } else if (node instanceof AIcDefsCanonicalElement x) {
            return new AIigElementListChildVariantElement1_1(x);
        } else if (node instanceof AIcDefsCanonicalList x) {
            return new AIigElementListChildVariantList3_1(x);
        } else if (node instanceof AIcDefsCanonicalMap x) {
            return new AIigElementListChildVariantMap4_1(x);
        }
        throw new IllegalArgumentException("Invalid ELEMENTLIST child structure: " + node.kind());
    }
    /** Unwrap a generated ELEMENTLIST child. @param selected child @return typed node */
    public static AIiDefsCanonicalStructure unselectChild(AIigElementListChild_1 selected) {
        Object node;
        if (selected instanceof AIigElementListChildVariantElementList2_1 x) node=x.getElementList();
        else if (selected instanceof AIigElementListChildVariantElement1_1 x) node=x.getElement();
        else if (selected instanceof AIigElementListChildVariantList3_1 x) node=x.getList();
        else if (selected instanceof AIigElementListChildVariantMap4_1 x) node=x.getMap();
        else throw new IllegalArgumentException("Unexpected ELEMENTLIST child: " + selected);
        if (!(node instanceof AIiDefsCanonicalStructure view))
            throw new IllegalStateException("Unexpected generated SDO child: " + node);
        return view;
    }
    /**
     * Build provenance with the generated SDO getters and the actual bounded
     * collection implementation. Virtual-graph ArrayList placeholders are not
     * assignable to AIiBoundedList and failed at runtime before Java could
     * process any canonical schema source binding.
     *
     * @param value provenance grouped by schema input technology
     * @return schema-backed provenance container
     */
    @SuppressWarnings("unchecked")
    public static AIcgdSourceBindings_1 bindings(
            Map<AIngSourceInputKind_1, List<AIcDefsCanonicalSourceBinding>> value) {
        var result = new AIcgdSourceBindings_1();
        if (value == null || value.isEmpty()) return result;
        var groups = (eu.algites.lib.common.list.AIiBoundedList<
                eu.algites.tool.codegen.defs.model.impl.intf.AIigdSourceBindingGroup_1<?>>)
                (eu.algites.lib.common.list.AIiBoundedList<?>) result.getSourceBindingGroupList();
        for (var entry : value.entrySet()) {
            var kind = Objects.requireNonNull(entry.getKey(), "source kind");
            var sourceEntries = List.copyOf(Objects.requireNonNull(entry.getValue(), "source entries"));
            if (sourceEntries.isEmpty()) {
                throw new IllegalArgumentException("Source binding group " + kind + " must not be empty");
            }
            var group = new AIcgdSourceBindingGroup_1();
            group.setInputKind(kind);
            var bindingList = (eu.algites.lib.common.list.AIiBoundedList<
                    eu.algites.tool.codegen.defs.model.impl.intf.AIigdSourceBinding_1>)
                    (eu.algites.lib.common.list.AIiBoundedList<?>) group.getBindingList();
            bindingList.addAll(sourceEntries);
            groups.add(group);
        }
        return result;
    }

    /**
     * Read schema-defined provenance groups and preserve their source order.
     * The virtual graph constructor recreates generated SDOs, so reconstruct
     * the convenience view from their typed getters rather than assuming a
     * particular Java subclass survives an identity-preserving mapping load.
     *
     * @param value canonical source-binding SDO
     * @return immutable provenance map
     */
    public static Map<AIngSourceInputKind_1, List<AIcDefsCanonicalSourceBinding>> bindings(
            AIigSourceBindings_1 value) {
        if (value == null || value instanceof AIcgdSourceBindings_1 concrete
                && !concrete._isPresent_SourceBindingGroupList()) return Map.of();
        var out = new LinkedHashMap<AIngSourceInputKind_1, List<AIcDefsCanonicalSourceBinding>>();
        var groups = value.getSourceBindingGroupList();
        if (groups == null) return Map.of();
        for (var entry : groups) {
            var kind = entry.getInputKind();
            var items = new ArrayList<AIcDefsCanonicalSourceBinding>();
            var bindings = entry.getBindingList();
            if (bindings != null) for (var binding : bindings) {
                items.add(new AIcDefsCanonicalSourceBinding(binding.getSourceResource(),
                        binding.getSourcePointer(), binding.getRepresentationKind()));
            }
            if (out.putIfAbsent(kind, List.copyOf(items)) != null)
                throw new IllegalStateException("Repeated provenance kind " + kind);
        }
        return Collections.unmodifiableMap(out);
    }
    /** Resolve the source kind using its serialized schema code, not the Java identifier.
     * @param code schema-defined source-language name
     * @return matching canonical source language
     * @throws IllegalArgumentException if no source language owns this code
     */
    private static AIngSourceInputKind_1 sourceKind(String code) {
        for (var kind : AIngSourceInputKind_1.values()) {
            if (kind.code().equals(code)) return kind;
        }
        throw new IllegalArgumentException("Unknown canonical source binding kind: " + code);
    }
    /** Validate occurrence limits before storing them in generated Long fields. @param min lower @param max upper */
    public static void checkItemCountBounds(int min,int max) {
        if (min<0 || max<-1 || (max != -1 && max<min)) throw new IllegalArgumentException("Invalid occurrence bounds: "+min+".."+max);
    }
    /** Convert source occurrence bound into generated Long representation. @param number integer @return bound as Long */
    public static Long number(int number) { return (long) number; }
    /** Convert the emitted bound losslessly. @param number value @return exact integer */
    public static int number(Long number) { return Math.toIntExact(Objects.requireNonNull(number, "occurrence value")); }
    /** Retrieve and preserve the exact list of SDO objects as a typed view. @param list SDO values @return values */
    @SuppressWarnings("unchecked")
    public static <T> List<T> values(List<? extends Object> list) { return list == null ? List.of() : (List<T>) list; }
}

