# Algites Defs Codegen Vocabulary v1

Vocabulary identifier: `https://defs.dev.algites.eu/api/jsonmetadefs/eu/algites/tool/codegen/defs/jsonmetadef/vocabulary_1.md`

This version defines a static source-contract **generation vocabulary**, not a JSON instance-validation vocabulary. Implementations that do not support it may still validate input instances against the standard JSON Schema constraints. The vocabulary is optional in the advertised dialects (`false` in `$vocabulary`); an Algites Defs Codegen implementation requires support for it when generating the corresponding constructs.

## `x-algites-defscodegen-extends`

The keyword applies only to a named object schema (not a scalar, array, anonymous validation branch or map entry). Its value is a non-empty ordered array of distinct URI references to **named object contracts**. The order is significant for deterministic API emission, not for JSON Schema instance evaluation. Each reference is resolved using the current schema's base URI and normal JSON Schema resource identification, including local fragment identifiers. The generated read-only contract directly inherits all referenced contracts; mutable contracts retain the corresponding compatible hierarchy. Concrete SDO implementations MUST inherit directly from the format-specific SmartDataObject base, not other generated concrete implementations.

A missing or non-object parent, inheritance cycle, or incompatible inherited methods is an error. The presence or absence of `allOf` or other validation rules does not determine generated inheritance. When no direct validation reference to an explicitly declared parent is found, a tool MAY emit a warning recommending validation of that parent's schema; this is not a semantic equivalence check.

## `x-algites-defscodegen-choice`

The keyword applies only to a named schema designated as a closed alternative type. It is an object with `alternatives`, an ordered list of at least two distinct URI references. Each reference identifies a named alternative contract. Generation may produce a Java sealed interface plus variants and corresponding Python union/variant types, respecting language-specific limitations. Choice does **not** itself assert that an instance validates under exactly one alternative; `oneOf` can express that independently. A tool MAY warn when it cannot identify corresponding standard validation.

The metadata do not introduce fields; named fields are structurally declared in `properties`, keyed entries by `additionalProperties`/`patternProperties`, positional entries by tuple items (`prefixItems` for 2020-12), and sequential entries by `items` as applicable to the source draft. General validation applicators (`allOf`, `anyOf`, `oneOf`, `not`, `if`/`then`/`else`) MUST NOT by themselves create fields, inheritance links or generated choice types. Recursive references and unions must resolve to explicit nominal definitions without inventing field names from validation paths.

## Compatibility and publication

One semantic vocabulary URI is shared across dialect-specific vocabulary keyword meta-schemas for JSON Schema 2019-09 and 2020-12. The keyword meta-schemas describe JSON syntax only; the semantic requirements above must be implemented and tested by consuming tools. Older drafts without `$vocabulary` may use these `x-` keywords as proprietary annotations with separately documented support, but they MUST NOT be described as implementing the 2019-09/2020-12 `$vocabulary` mechanism.

The versioned public identifiers are immutable. Schema-sidecar `GlobalPublicationPathId` values are deployment metadata only, not a substitute for `$id`. This artifact is data-only and must never be treated as a JSONDEFS/YAMLDEFS business-object definition by the Defs/SDO generator.
