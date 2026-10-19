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

For JSON/YAML object schemas, one explicit `allOf` `$ref` to an emitted
object contract creates a real inheritance edge. The canonical recursive
`AIcdDataType` records nested object, array, scalar and choice structures;
array nodes also preserve schema `minItems`/`maxItems` constraints. JSON/YAML
inherited-field compatibility is checked recursively, including nested choices
and array shapes. Unsupported multiple-base `allOf` fails explicitly.

XSD batch generation emits all top-level named types independently, including
multiple types in the same XSD. Named `complexContent` extension bases, whether
same-file or resolved from local `xs:include`/`xs:import`, become actual
Java/Python parent interfaces when their contracts are emitted. Direct XML
fields preserve their expanded QNames and `ELEMENT`/`ATTRIBUTE` distinction.
For repeated elements, the canonical array node retains the interval implied
by `minOccurs`/`maxOccurs`, independently of scalar item facets. A conservative
flat-sequence `complexContent restriction` subset permits tightening occurrence
bounds and removing optional particles without changing the element type or
order; incompatible restrictions fail explicitly. Same-schema `xs:group`,
`xs:attributeGroup`, and global `xs:element ref` are supported for the
non-lossy structures covered by the frontends, with cycle checks for named
groups. A direct, mandatory `xs:choice` of element declarations generates
closed, typed alternatives, including same-schema element references.

**XSD limitations remain:** arbitrary nested/repeated compositors, optional
multi-field groups, cross-schema group/element references, wildcards, mixed
content, general content-model restrictions and exhaustive `block`/`final`
substitution semantics are not yet supported. Such unsupported structures are
rejected rather than silently flattened. XML-vs-JSON/YAML canonical comparison
checks recursively representable scalar/array structures; equivalence of
arbitrary nested named XML objects is not established by this comparison.


Legacy manifest-based repository generation records ownership under
`build/run/schema-contract-bindings/generated-files.json`. The **explicit
YAML-driven batch CLI** instead uses whole-filename naming conventions to
clean its generated interface/enum roles after successful preflight. Both
paths support `--check` and collision detection; neither may delete
SDO-generated files or unrelated generator outputs.

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
actual generated type (for example `List<List<AIigInvoiceLinesItemsItems_1>>`
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

This is a deliberately conservative subset. XSD nested/repeated particles,
full XSD type inheritance, and removal of legacy flat model projections are
not yet implemented. Full repository-level Gradle/JPMS verification remains
a separate integration requirement.
