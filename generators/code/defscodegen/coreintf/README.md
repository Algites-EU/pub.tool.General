# Defs Codegen core interfaces

Normalized canonical-definition model and frontend/backend/service contracts. Package namespace: `eu.algites.tool.codegen.defs`; `coreintf` is not part of the package name.

Canonical-definition descriptions and property documentation are first-class normalized data and are preserved for generation backends. Definition version is carried independently from logical-name tokens.


## Enum-value documentation

The canonical enum model preserves each wire value together with its optional human-readable description. JSON/YAML definitions may provide per-value descriptions through `oneOf` branches containing `const` plus `description`; XSD definitions use `xs:enumeration/xs:annotation/xs:documentation`. Java enum constants and Python enum class documentation are generated from the normalized per-value descriptions.

See [generated source conventions](../GENERATED-SOURCES.md) for per-object contracts, concrete implementations, package ownership, and clean-checkout CI generation.
