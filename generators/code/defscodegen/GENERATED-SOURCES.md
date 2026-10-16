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

Each generated field carries normalized name, description, `presenceRequired`
/ `presence_required`, and `allowsNull` / `allows_null`. Java uses
`AIaDataObject` and `AIaDataObjectField`, Python uses `AIcdDataObject` and
`AIcdDataObjectField`. The resulting contracts extend the matching general
`AIiDataObject` marker, regardless of the original schema format.

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
`allOf` and XSD `complexContent`/`extension` are not silently flattened into
incorrect inheritance. XSD XML attributes are also not yet mapped into the
canonical field projection: both native XML frontends reject those constructs
explicitly instead of losing fields. These are limitations of the currently
supported XSD projection, not `pub.lib.General` constraints.

Legacy manifest-based repository generation records ownership under
`build/run/schema-contract-bindings/generated-files.json`. The **explicit
YAML-driven batch CLI** instead uses whole-filename naming conventions to
clean its generated interface/enum roles after successful preflight. Both
paths support `--check` and collision detection; neither may delete
SDO-generated files or unrelated generator outputs.

The first-stage wrapper continues to reuse parts of the legacy DTO renderer
in memory, but never publishes its DTO result. Fully removing that internal
compatibility path is a follow-up; output ownership is already separate.

The old `AIcSchemaInterfaceGenerator` (paired API) and
`AIcSchemaObjectBindingsGenerator` (paired repository API) remain temporarily
for existing 1.0 consumers. They are **legacy compatibility APIs** and must
not be selected by new 1.1 Builder integrations. A follow-up migration of AAC
and other consumers is required before these APIs can be removed.

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
by splitting the rendered source or guessing from file names. The legacy
three-argument source constructor remains for other/non-type outputs; requesting
`primary_type` from a source with no type metadata is an explicit error.

The canonical data pipeline is `Defs Codegen (AIig)` followed by `SDO Codegen
(AIigd / AIcgd)`. Consumers must not select the legacy paired DTO generator
as a substitute for the standard two-stage pipeline.
