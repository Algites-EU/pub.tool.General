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

Contract repository generation records ownership under
`build/run/schema-contract-bindings/generated-files.json` and supports
`--check`, stale output removal and collision detection. It does not own
SDO-generated files or outputs of unrelated generators.

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
