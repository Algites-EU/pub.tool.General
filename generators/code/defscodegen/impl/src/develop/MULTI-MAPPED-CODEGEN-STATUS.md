# Defs Codegen: typed multi-mapped collections and field addressing roles

**Author:** linhart1  
**Status:** partial integration, 2026-10-30; **not approved for publication**

## Canonical roles

The addressing role of a field is independent of its data type and schema source:

| Role | Source examples | Representation |
| --- | --- | --- |
| `NAMED_VALUE` | JSON Schema `properties`, named XSD elements/attributes | Statically named field with a typed value. |
| `KEYED_VALUES` | JSON Schema `additionalProperties`; direct XSD collection with qualifying `xs:key` | Typed member collection; index definitions identify key fields, ordered composite key parts, and uniqueness. |
| `POSITION_TYPED_VALUE` | JSON Schema `prefixItems`; legacy positional `items` arrays | A list whose prefix positions have individually declared types. XSD has no direct name-independent equivalent. |
| `SEQUENTIAL_VALUES` | JSON Schema homogeneous `items`; repeated XSD element | Ordered sequence whose item type does not depend on index. |

Do not restrict schema expressiveness to the common subset. Merge only genuinely overlapping common definitions and reject incompatible types before source generation. Preserve format-specific contract extensions without widening to `Object`.

## Multi-mapped list API

Java source declarations must expose `eu.algites.lib.common.list.AIiMultiMappedList<V>`, **not** `AIcMultiMappedList<V>`. The library implements `AIiMultiMappedList<V> extends java.util.List<V>`, and its key definitions provide `Map<K,List<V>>` live views over the one underlying ordered list. The map's grouped lists are immutable snapshots. Removing a key removes the entire group across all views. Inserting/replacing through maps is forbidden. The collection tracks sublists weakly and synchronizes removals; direct mutation of key-bearing fields while stored is a caller contract violation.

Python declares a matching abstract `AIiMultiMappedList[V]` interface built on `collections.abc.MutableSequence[V]`; `AIcMultiMappedList` implements it. Python grouping map values are immutable `tuple[V,...]` snapshots. Do not expose concrete `AIcMultiMappedList` from generated interfaces.

For overlapping common and format-specific contract getters, use one **identical generic value type** for the mutable mapped list. Generic Java collections are invariant: `AIiMultiMappedList<SpecializedValue>` does **not** override `AIiMultiMappedList<CommonValue>`. Format-specific item contracts may still extend the common value contract. Python follows the same nominal convention for predictable static type checking.

## JSON/YAML dynamic keys

`additionalProperties` with a schema defines typed values and one *virtual* key definition whose key is the containing property name. JSON/YAML item interfaces have the configurable synthetic getter `multi_mapped_list_key_synthetic_getter: _getKey`, selected from the Java/Python generated-method naming profile. This method is **not serialized inside the value**; it represents the parent object's property name and must be initialized by the runtime factory. XML value interfaces do not acquire this getter because their keys come from declared XML fields.

Unlike `additionalProperties`, `patternProperties` may have distinct overlapping patterns. The current frontend fails explicitly instead of discarding their constraints. This requires a later rule/merge design.

## XML keys

Example:

```xml
<xs:element name="Employees">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Employee" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType>
          <xs:sequence><xs:element name="Label" type="xs:string"/></xs:sequence>
          <xs:attribute name="region" type="xs:string" use="required"/>
          <xs:attribute name="code" type="xs:string" use="required"/>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
  <xs:key name="ByRegionAndCode">
    <xs:selector xpath="Employee"/>
    <xs:field xpath="@region"/>
    <xs:field xpath="@code"/>
  </xs:key>
</xs:element>
```

The ordered compound key `(region,code)` is one unique key definition. Multiple `xs:key` declarations produce multiple unique indexes; **none may be silently ignored**. The key attributes remain regular declared fields of the XML value object. `xs:selector` and `xs:field` are XPath expressions whose prefixes have namespace semantics: a `tns:` prefix must refer to the actual target namespace, and unprefixed steps do **not** select qualified XML elements.

The Python and native Java XML frontends now recognize **one direct repeated child** with one or more `xs:key` declarations. Both validate QName prefixes and allow typed nested `xs:field` paths through nonrepeating child elements, e.g. `tns:Identity/tns:Code`; the path is retained for a future null-safe extractor. **Parsing the path does not create or execute that extractor.** Descendant selectors spanning several nested lists, `xs:unique`, and exotic XPath are not yet indexed. `xs:keyref` is deliberately ignored during structural projection; it creates no index or relation and does not block generation. Referenced values must be checked by a full XSD validator. `xs:unique` remains explicitly unsupported in the keyed-collection projection. Full XSD validation remains necessary.

## `xs:choice` and ordered wrappers

A nested XSD `xs:choice` models mutually exclusive alternatives, corresponding to JSON `oneOf` when branches are semantically distinct. Named XML choice types are now emitted independently and share common nominal branch interfaces with matching JSON/YAML `$defs`; exact format-specific XPath and XML element QNames must be preserved. The `NameFragments.Segments` wrapper with one repeated typed `Segment` is recognized as an array, not as an unrelated object. A targeted 208-source generated-output check passed for the naming schema family.

## Explicit remaining limitations — important

1. **Java/Python XML frontend parity is partial**: Java now projects direct and composite `xs:key`, including type-checked nested field paths and namespace checks (targeted Java tests passed). It still lacks full Python parity for nested choice and some wrapper shapes.
2. **No runtime JSON/YAML/XML serializer or SmartDataObject factory integration has been completed.** The virtual `_getKey()` is an interface contract, not yet proof that deserialization populates it, or that XML/JSON/YAML round trips work.
3. **Java `POSITION_TYPED_VALUE` emission remains unimplemented**: canonical `prefixItems` types are now preserved and Python tuple typing is emitted in supported cases, but Java generation rejects unsupported positional combinations rather than widening them to `Object`.
4. **`patternProperties` validation and descendant-scope XSD `xs:key` selectors** are not supported; unsupported cases are explicitly rejected rather than silently degraded.
5. **Complete Gradle bootstrap, Java TestNG suite and schema-to-runtime round trips are not verified.** Do not publish rebuilt artifacts based solely on the targeted tests below.

## Targeted verification

- Naming family direct Python-batch Defs Codegen: 208 generated Java/Python entries; previously failing `IdentifierConventions` now passes at generation.
- Fifteen targeted tests in `test_multi_mapped_field_contracts.py` covering JSON typed maps, positional slots, XML compound keys, XML QName checks, `patternProperties` diagnostics, and generated interface types.
- Forty-one targeted Python regressions passed in the working environment (collection library and XML frontend regression files).
- Java canonical model source types compiled with JDK 21 `javac --release 17`.
- Java TestNG regressions were authored but not executed in the full Gradle classpath.

Do not manually edit or publish files beneath `java.gen` or `python.gen`. These are generated verification outputs, not patch inputs.

## Extended mapping and validation specification (2026-10-30)

The detailed schema illustrations, XML `xs:key` extraction and nullable paths,
synthetic `_getKey()` / `_getValue()`, and the standards-preserving rewrite for
pattern-constrained maps are described in
[`MULTI-MAPPED-SCHEMA-SEMANTICS.md`](MULTI-MAPPED-SCHEMA-SEMANTICS.md).
Distinguish tested source-contract changes from unimplemented DO/SDO runtime
validation and nested-collection index synchronization.

## Verification update: native Java XML key projection

The Java `AIcXmlDefsFrontend` now projects each direct `xs:key` into
`AIcdDataType.keyDefinitions()` and preserves its full ordered field path.
The implementation was compiled with `javac --release 17` (using only a
temporary Jackson API stub because the Gradle wrapper distribution is not
installed in the isolated environment). Two Java regression methods were
executed with a temporary TestNG-compatible assertion stub; **this is not a
full TestNG run**. The real naming XSD was also loaded and all four keyed
collections were recognized.

The source fixture uses a qualified nested path:

```xml
<xs:key name="ByCode">
  <xs:selector xpath="tns:Employee"/>
  <xs:field xpath="tns:Identity/tns:Code"/>
</xs:key>
```

Its canonical key path is `Identity.Code`; the current reader does not yet
produce executable Java/Python key extractors. A missing `Identity` node
therefore still requires a generated null guard, and a missing key is a schema
validation error for `xs:key`. `xs:keyref` is intentionally ignored by structural code generation; a
full validating XSD parser remains responsible for referential integrity.
`xs:unique` is still explicitly unsupported by the keyed-collection reader.
