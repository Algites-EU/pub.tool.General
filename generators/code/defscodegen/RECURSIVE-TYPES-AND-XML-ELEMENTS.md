# Definition-to-contract generation — 1.1

`defscodegen` is the **first stage** of the SmartDataObject generation pipeline.
It supports standalone canonical `yamldefs`, `jsondefs`, and `xmldefs` inputs and emits
annotated, read-only `AIig*` contracts plus shared `AIng*` enums in Java and Python.
It must not write implementations into a second artifact root.

- JVM: `AIcSchemaContractInterfaceGenerator` and `AIcSchemaContractBindingsGenerator`.
- Python: `AIcSchemaContractInterfaceGenerator` and `AIcSchemaContractBindingsGenerator` in
  `aic_schema_contract_interface_generator.py` and
  `aic_schema_contract_bindings_generator.py`.
- CLI: `AIcDefsCodegenCli` / `aic_defs_codegen_cli.py`.

The repository manifest has `artifact`, `languages`, and optional `bindings`:

```json
{
  "artifact": "aac/intf",
  "languages": ["java", "python"],
  "bindings": []
}
```

Each generated field carries a stable `fieldName` / `field_name`, `presence`
(REQUIRED / ALLOWED / FORBIDDEN), and `allowsNull` / `allows_null`.
Human-readable titles and descriptions belong to `AIaFieldLabel`, not the
structural field annotation. Java emits `AIaDataObject` and
`AIaDataObjectField`; Python emits `AIcdDataObject` and `AIcdDataObjectField`.
A read contract extends the source-family marker `AIiXmlDataObject`,
`AIiJsonDataObject`, or `AIiYamlDataObject` (all of which extend
`AIiDataObject`). Explicit inherited schema contracts preserve their parent
edge instead of redundantly naming the technology marker. This makes the
source technology visible to second-stage SDO generation. Named XSD content
types additionally carry the declaration's expanded QName as
`AIaXmlDataObject(definitionKind=TYPE)` (Python: `__xml_data_object__`),
which is independent from separately generated global XML element contracts.

**The second stage** is `../sdocodegen/`. It consumes the annotated contracts,
not the schemas. It writes mutable interfaces and concrete SmartDataObjects into
separate `java.gen`/`python.gen` roots. See its README.

Repository-scoped schema discovery covers `yamldefs`, `jsondefs` and `xmldefs`
(`*.xsd`) for both Java and Python. XML documents pass through the existing XSD
canonical frontend. A parity fixture verifies that equivalent JSON, YAML and XSD
object contracts merge into the same generated type, and imported XSD definitions
and enums are discovered together.

For JSON/YAML object schemas, a single explicit `allOf` `$ref` to an emitted
object contract creates a *real interface inheritance edge*; only the new fields
are declared on the child. Inherited fields are validated against their parent;
contradictory metadata or an unresolved parent fails generation. Parent references
may be file-relative or local JSON Pointers. Equivalent JSON/YAML representations
may merge while preserving the same parent relationship. Arbitrary multiple-base
`allOf` is not supported. XSD direct attributes are projected into canonical
fields, including `use="prohibited"`. A limited **same-XSD** `complexContent`
`xs:extension` retains both inherited and appended fields by flattening their
metadata; attribute-only `xs:restriction` can prohibit optional attributes or
make them required. Repository-batch XSD generation emits all top-level named types independently,
including additional complex/simple types in the same XSD as the primary unit,
so named extension bases in the same file can be referenced by genuine Java/Python
interface inheritance edges. Only local child fields appear on the generated
derived interface. Cross-file `xs:import`/`xs:include` bases resolve locally
and retain their original XML QNames. A base not present in the emitted batch
causes an explicit error instead of silently flattening into the derived API. Standalone XSD `load()` still exposes
flattened property metadata, and unrestricted XML derivation is not yet
supported. Repeated sequence/all and named group particles containing **exactly one mandatory,
nonrepeating leaf element** are reduced to a single repeated XML field with the
same QName and exact minOccurs/maxOccurs bounds; both compositor names follow
identical canonical ordering rules. Multi-field correlated groups, groups with
already repeating members, wildcard particles, and unresolved references fail
explicitly rather than silently producing invalid sources. Recursive canonical comparison is complete for the
represented JSON/YAML structural nodes but **not yet for XSD nested named
complex types**. These are current frontend limitations, not `pub.lib.General`
constraints.

Legacy manifest-based repository generation records ownership under
`build/run/schema-contract-bindings/generated-files.json`. The **explicit
YAML-driven batch CLI** instead uses whole-filename naming conventions to
clean its generated interface/enum roles after successful preflight. Both
paths support `--check` and collision detection; neither may delete
SDO-generated files or unrelated generator outputs.

Named local JSON/YAML `$defs` objects and choices retain nominal references, including
recursive members such as `FinalizationAction.FinalizationActions[]` that refer back
to their own containing contract. Defs Codegen must not eagerly inline those
members: a named object target is represented by its kind and stable identity,
while a named choice retains its alternatives until a recursive back-edge is
reached. The back-edge remains a reference without a recursively embedded
`targetDataType`. Invalid cyclic aliases without a named target fail with an
explicit error rather than overflowing the Java/Python call stack. This rule
applies equally to the Java and Python canonical schema readers.

The first-stage renderers emit contracts directly from canonical definitions,
without rendering or parsing a concrete DTO source. There is no paired
Defs Codegen API: the former `AIcSchemaInterfaceGenerator` and
`AIcSchemaObjectBindingsGenerator` have been removed as part of the 1.1
migration. The same applies to their Python modules. Consumers must use the
canonical contract API and then explicitly invoke SDO Codegen for mutable and
concrete SmartDataObject types.

`bootstrap.sh` builds the first generator without loading the bootstrap Builder
plugin, and parity tests cover Java and Python native implementations.

In explicit CLI batch mode, outputs are recognized by their complete YAML naming
conventions; source collision validation (including canonical identity) runs
before any output cleanup. Same-format schema duplicates from distinct roots
may merge when both their canonical identities and their structures match.
See [Code Generators Reference Guide](../CODEGEN-REFERENCE.md).

## Structured generated type identities

`AIcdGeneratedSource` exposes `generated_types` and `primary_type` for the
importable declarations it owns. Every generated type identity reports:
`type_name`, `namespace`, `module_name`, `fully_qualified_type_name`,
`type_role`, `technology_kind`, `source_definition_id` and
`source_definition_version`. For Python, a qualified name includes the
**module file** before the class; in Java it is `package.Class`.

Canonical schema contract generation populates this metadata directly in both
Java and Python. Consumers (AAC included) must not reconstruct qualified names
by splitting the rendered source or guessing from file names. The three-argument source constructor remains for other/non-type outputs; requesting
`primary_type` from a source with no type metadata is an explicit error.

The canonical data pipeline is `Defs Codegen (AIig)` followed by `SDO Codegen
(AIigd / AIcgd)`. Consumers must not select the legacy paired DTO generator
as a substitute for the standard two-stage pipeline.

## Canonical representation conflict diagnostics

The repository/batch generators use strict multi-representation validation before
writing output. `AIcCanonicalDefinitionMerger.AIcMergeStrict(definitions,
sourceRoot)` (Python: `merge_strict`) checks both the canonical field model and
root/field/enum titles and descriptions. The ordinary `AIcMerge`/`merge` API
continues to support documentation aggregation when explicitly requested by
other consumers.

If any representations disagree, the exception includes **all** source files
(as absolute paths), the consistency status of **every pair**, all differences
by field/constraint or documentation member, both conflicting values, and a
best-effort `file:line` for each. In Gradle, the exception text is printed
without needing `--stacktrace`. Only the self-publication URL of the JSON/YAML
`$schema` property is treated as format-specific; this property is not
required in XML because `$` is not an XML element name. Other missing fields,
const values, type constraints and descriptions remain strict.

The current canonical projection covers the root model, its properties and
canonical enum values; format-specific XSD declarations that have no canonical
counterpart are outside this check. Line positions are best effort for nested
or reused schema fragments.

## Recursive types, closed choices and XML nominal contracts

See [RECURSIVE-TYPES-AND-XML-ELEMENTS.md](RECURSIVE-TYPES-AND-XML-ELEMENTS.md) for the staged recursive canonical model, the generated closed choice compilation units, the XML `_xe` element interfaces, migration constraints, and current XSD limitations.

### Recursive property contracts (repository batch)

Java and Python preserve nested arrays containing scalars, named references,
inline objects, and named closed choices. Inline JSON/YAML objects and nested
`oneOf`/`anyOf` are discovered as separate, versioned read-contract sources
in the same business package. The enclosing getter/property refers to that
actual generated type (for example `List<? extends List<? extends AIigInvoiceLinesItemsItems_1>>`
or `tuple[tuple[AIigInvoiceLinesItemsItems_1, ...], ...]`). Closed-choice
wrappers are generated as independent compilation units alongside the choice
interface. Direct `$defs` references and nested array references resolve to
the same nominal target type.

This support applies to the **repository batch** which writes all discovered
compilation units. The single-unit `generate()` preview may contain references
to sibling contracts not created by that individual call. See
[RECURSIVE-TYPES-AND-XML-ELEMENTS.md](RECURSIVE-TYPES-AND-XML-ELEMENTS.md)
for XML limitations, `oneOf`/`anyOf` runtime semantics, and remaining deep
runtime validation work.

### XML member representation

XMLDefs properties preserve `AIcdXmlFieldRepresentation` through the canonical
property model. Generated Java member getters carry `@AIaXmlDataObjectField`
and generated Python read interfaces carry `__xml_data_object_fields__`, preserving
the XML namespace, local name and `ELEMENT`/`ATTRIBUTE` distinction independently
of `AIaDataObjectField.fieldName` and the generated language identifier. XSD
qualification uses the local declaration's `form` or the schema's corresponding
form default, never a blanket `targetNamespace` assumption.


### Recursive choice and XML content-type compatibility (checkpoint 10)

The XML frontend supports a direct mandatory `xs:choice` of local element
declarations as a closed recursive `ONE_OF` and emits distinct Java/Python
branch read-only contracts plus wrappers. Global elements whose named type is
a sealed choice expose a typed value getter and do not extend an unpermitted
sealed interface. XML QName and ELEMENT/ATTRIBUTE metadata remain separate
from canonical field names. JSON/YAML `allOf` duplicate field definitions
with incompatible shapes are rejected before merging. Inherited field matching
compares recursive types, not just legacy flat value kinds.

The current XSD subset also models repeated element cardinality as array
`minItems`/`maxItems` and permits safe narrowing of flat `xs:sequence` **or**
`xs:all` in `complexContent restriction`. Both compositors project to the same
ordered canonical property model: generated getters include `AIaXmlDataObjectField.order` to make Java XML
serialization independent of reflection method ordering (Python retains the
same ordinal in `__xml_data_object_fields__`). Canonical XML writing
emits repeated elements as adjacent siblings sharing their declared QName,
never as an artificial `Item` wrapper; an empty array emits no element.
The XML reader in `pub.lib.General` checkpoint 19 binds by expanded QName
regardless of input order, constructs nested typed SDO objects with generated
class bindings, and enforces known `minOccurs`/`maxOccurs` occurrence bounds.
This intended behavior differs from **strict XSD validation**, which must still enforce the
original order of `xs:sequence`. No hidden canonical flag
for `all` versus `sequence` is introduced. Optional/repeated multi-field
compositors are still rejected when flattening would change group cardinality.
The frontend also resolves local named `xs:group` and `xs:attributeGroup` with
cycle detection, and supports references to global elements and groups through
local, namespace-checked `xs:import`/`xs:include` paths, including direct
choice alternatives. Remote imports, ambiguities, wildcards and general
content-model restrictions outside the provably safe subset are rejected rather
than silently flattened. The frontends also reject unmodelled content-model
members (`xs:assert`, `xs:openContent`), conditional element types
(`xs:alternative`), schema-level `xs:redefine`/`xs:override` and default open
content. A document whose root is not `xs:schema` is not accepted as a schema.
Named type inheritance works across emitted types
from the same XSD and local include/import files. The
canonical `AIcdDataType` hierarchy now replaces the old flat `DefinitionKind`/
`ValueKind` and their duplicate canonical fields in both Java and Python.
Normalization of source-language primitive hints is private to the frontends.
Full repository-level Gradle/JPMS verification remains a separate integration
requirement.

### XML wire cardinalities and cross-format publication (checkpoint 20)

`AIcdXmlFieldRepresentation` carries the source element/attribute QName together
with an independent XML occurrence interval. This interval is propagated to
`@AIaXmlDataObjectField(minOccurs, maxOccurs)` and Python
`AIaXmlDataObjectField(min_occurs, max_occurs)`. A finite XSD maximum and
minimum are checked by the XML reader against the actual count of QName
occurrences, even when the caller provides elements in a different order.
An unspecified or unbounded maximum remains `-1`. The recursive array's
`minItems` and `maxItems` are independent of XML sibling cardinalities:
`xs:list` constraints apply to list items, not the count of surrounding XML
elements. Complex multi-field repeated particles and wildcard content models
are still rejected rather than projected into unrelated flat fields.

When several schemas describe one canonical contract, `$schema` publication
self-links are format-specific, not shared scalar enum restrictions. The merger
checks that a self-link matches the declaring source format and path, excludes
only that publication constant from cross-format comparison, and excludes it
from the merged canonical `DataType`. Original per-format definitions keep
their own `$schema` constraint. Incompatible fields and unrelated enum or
lexical constraints continue to fail the strict merge.

This source-level fix requires the matching `defscodegen.impl:1.1-SNAPSHOT` to
be bootstrapped into `pub.gov.Algites`: a CI invocation resolving legacy
`defscodegen.coreimpl:1.0-SNAPSHOT` runs older merger bytecode and cannot be
repaired by changes to this repository's unbuilt sources alone.
