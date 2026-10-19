# Defs Codegen core implementation

Default distinct `yamldefs`, `jsondefs`, and `xmldefs` frontends plus Java/Python generation backends. Package namespace: `eu.algites.tool.codegen.defs`; `impl` is only an artifact boundary.

The default Java and Python backends propagate canonical descriptions into
Javadoc/docstrings and preserve property descriptions in generated data-object
documentation. The current **contract-only** first stage emits `AIig..._N`
read-only interfaces and `AIng..._N` enums. The separate SDO Codegen stage
creates `AIigd..._N` and `AIcgd..._N`. Defs Codegen does not expose a paired
contract/DTO generator, and renders `AIig` contracts directly from canonical
properties rather than parsing a generated DTO source.


## Enum-value documentation

The canonical enum model preserves each wire value together with its optional human-readable description. JSON/YAML definitions may provide per-value descriptions through `oneOf` branches containing `const` plus `description`; XSD definitions use `xs:enumeration/xs:annotation/xs:documentation`. Java enum constants and Python enum class documentation are generated from the normalized per-value descriptions.

See [generated source conventions](../GENERATED-SOURCES.md) for per-object contracts, concrete implementations, package ownership, and clean-checkout CI generation.

Both native implementations expose the contract-only API and repository
binding API. Java TestNG compares Java and Python first-stage source output;
SDO Codegen has its own native integration tests for mutable interfaces and
implementations.

See [Code Generators Reference Guide](../../CODEGEN-REFERENCE.md) for overlap,
canonical identity, CLI and cleanup rules.

### XSD restriction safety (checkpoint 5)

For the supported `xs:simpleType` restriction subset, both language frontends
reject relaxed inherited numeric bounds, lengths, enumerations, and patterns.
Unsupported XML Schema scalar facets are rejected rather than silently lost;
pattern conjunction across levels is not yet supported. Attribute-only
`xs:complexContent` restrictions retain inherited type information when
`use="prohibited"` omits a type and validate retained scalar facets.
For coverage see `test_xsd_facet_narrowing.py` and
`AItcXmlFacetNarrowingTest.java`. Full XSD restriction validation and
complex content particle derivation remain out of scope.
