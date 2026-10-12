# Defs Codegen core implementation

Default distinct `yamldefs`, `jsondefs`, and `xmldefs` frontends plus Java/Python generation backends. Package namespace: `eu.algites.tool.codegen.defs`; `impl` is only an artifact boundary.

The default Java and Python backends propagate canonical descriptions into
Javadoc/docstrings and preserve property descriptions in generated data-object
documentation. The current **contract-only** first stage emits `AIig..._N`
read-only interfaces and `AIng..._N` enums. The separate SDO Codegen stage
creates `AIigd..._N` and `AIcgd..._N`; legacy paired Defs APIs may still
construct concrete Java/Python types for compatibility.


## Enum-value documentation

The canonical enum model preserves each wire value together with its optional human-readable description. JSON/YAML definitions may provide per-value descriptions through `oneOf` branches containing `const` plus `description`; XSD definitions use `xs:enumeration/xs:annotation/xs:documentation`. Java enum constants and Python enum class documentation are generated from the normalized per-value descriptions.

See [generated source conventions](../GENERATED-SOURCES.md) for per-object contracts, concrete implementations, package ownership, and clean-checkout CI generation.

Both native generator implementations provide the paired interface/implementation
API and repository binding API. The Java TestNG suite compares JVM and Python
outputs for both target languages; it also compiles/imports the generated sources.

See [Code Generators Reference Guide](../../CODEGEN-REFERENCE.md) for overlap,
canonical identity, CLI and cleanup rules.
