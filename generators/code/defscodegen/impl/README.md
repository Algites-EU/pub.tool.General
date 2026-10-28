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

## Repeated XML Schema choices (contract-generation stage)

A repeated `xs:choice` inside a named `xs:complexType` is represented as a
collection of closed alternatives, not as several unrelated optional fields.
Each such particle receives a deterministic ordinal named type:
`ProfileTypeChoice1`, `ProfileTypeChoice2`, and so on, counting the choices
within the enclosing complex type in declaration order. The enclosing
contract exposes `Choice1`, `Choice2`, etc. with their XSD `minOccurs` and
`maxOccurs` recorded on the array type. The branch contracts retain their
original XML element QNames. Java and Python Defs contract generation both
implement this mapping.

**Integration limitation:** This stage does not yet implement grouped-choice
XML marshalling and unmarshalling in SmartDataObject. Those runtimes currently
assume one XML QName per field, which cannot describe a choice's distinct
branches. The synthetic `ChoiceN` field therefore deliberately has no false
XML QName mapping. Generating its contract does **not** imply that an XML
round-trip is supported. Completing that requires explicit grouped-particle
metadata and matching Java/Python XML materializers before publishing a module
whose wire format uses repeated choices.

The independent `xs:all` compositor remains a set of optional or required
properties, not a sealed alternative. In XSD 1.0 it cannot assert that at
least one of several individually optional elements appears; that check
belongs to the appropriate application validation layer.
