# Algites Defs Codegen Vocabulary v1

Vocabulary identifier: `https://defs.dev.algites.eu/api/jsonmetadefs/eu/algites/tool/codegen/defs/jsonmetadef/vocabulary_1.md`

This version defines a static source-contract **generation vocabulary**, not a JSON instance-validation vocabulary. Implementations that do not support it may still validate input instances against the standard JSON Schema constraints. The vocabulary is optional in the advertised dialects (`false` in `$vocabulary`); an Algites Defs Codegen implementation requires support for it when generating the corresponding constructs.

## `x-algites-defscodegen-extends`

The keyword applies only to a named object schema (not a scalar, array, anonymous validation branch or map entry). Its value is a non-empty ordered array of distinct URI references to **named object contracts**. The order is significant for deterministic API emission, not for JSON Schema instance evaluation. Each reference is resolved using the current schema's base URI and normal JSON Schema resource identification, including local fragment identifiers. The generated read-only contract directly inherits all referenced contracts; mutable contracts retain the corresponding compatible hierarchy. Concrete SDO implementations MUST inherit directly from the format-specific SmartDataObject base, not other generated concrete implementations.

A missing or non-object parent, inheritance cycle, or incompatible inherited methods is an error. The presence or absence of `allOf` or other validation rules does not determine generated inheritance. When no direct validation reference to an explicitly declared parent is found, a tool MAY emit a warning recommending validation of that parent's schema; this is not a semantic equivalence check.

## `x-algites-defscodegen-choice`

The keyword has the **sole permitted value `true`** and marks a JSON object schema
as an **exclusive named-choice data type**. The alternatives are the direct
entries of the same schema's **`properties`**. Each property name is the stable
alternative identity; its value schema defines the alternative's payload type.

For JSON Schema Draft-04 and newer, the source MUST explicitly declare
`type: object`, `minProperties: 1`, `maxProperties: 1`, and
`additionalProperties: false`, and MUST provide at least two `properties`.
It MUST NOT use `required` or `patternProperties` on the choice itself.
These standard keywords provide independent, portable validation of exactly
one named alternative even when a third-party JSON Schema validator does not
recognize Algites metadata. **The structural type is derived solely from the
marker and `properties`; these constraints do not synthesize data structures.**

For example (JSON Schema 2020-12):

```json
{
  "$defs": {
    "ConfigurationValueType": {
      "type": "object",
      "x-algites-defscodegen-choice": true,
      "properties": {
        "StringValue": {"type": "string"},
        "IntegerValue": {"type": "integer"},
        "BooleanValue": {"type": "boolean"}
      },
      "minProperties": 1,
      "maxProperties": 1,
      "additionalProperties": false
    }
  }
}
```

The accepted instance is `{"StringValue": "hello"}` or
`{"IntegerValue": 42}`, but not two alternatives simultaneously, and not
an unrecognized property. A repeated JSON object member is not a second map
entry and SHOULD be rejected before JSON Schema validation.

The marker may declare a structural choice at the source schema root and in
`$defs` / `definitions`, `properties`, `patternProperties`, `additionalProperties`,
`items`, `prefixItems` (2020-12), and positional legacy `items` or
`additionalItems` where permitted by the corresponding draft. It MUST NOT
**declare a new choice** in validation-only positions: `allOf`, `anyOf`,
`oneOf`, `not`, `if`, `then`, `else`, `contains`, `dependentSchemas`, or their
validation-only counterparts. Referencing an already-declared named type from a
validation constraint is allowed; defining the type there is not.

The historical Draft-03 metaschema lacks standard `minProperties` and
`maxProperties`: its annotation syntax can be recognized, but **standard
third-party Draft-03 validators cannot enforce the same exclusive-choice
contract**. Draft-03 uses draft-specific object-keyword syntax, so support for
this structural extension does not imply cross-validator conformance.

Unlike the old `alternatives` URI-string array, the new marker does not duplicate
any structural information. The old syntax is no longer accepted for the 1.1
snapshot. `oneOf` remains an independent validation applicator and does not
define generated choice interfaces. A repeated or composite choice is modeled
explicitly as an array of choice elements, not as `maxProperties: 2`.

**Backward-compatibility warning:** Existing choices whose alternatives were
whole objects now require a named wrapper property in serialized JSON/YAML.
For example, a previous value `{"Source":"direct_value", "Value":"abc"}`
becomes `{"DirectValue":{"Source":"direct_value","Value":"abc"}}`.
Existing JSON/YAML instance documents must be migrated, and XML/JSON common
contract compatibility requires an independent projection review. Neither the
vocabulary update nor the marker itself implements that projection.

## Compatibility and publication

One semantic vocabulary URI is shared across dialect-specific vocabulary keyword meta-schemas for JSON Schema 2019-09 and 2020-12. For Draft-03, Draft-04, Draft-06, and Draft-07, the same semantics are expressed as proprietary annotations in extended, version-specific meta-schemas. These historical dialects lack `$vocabulary`; the corresponding `vocabulary_1.jsonmetadef.schema.json` resources validate keyword syntax, while `dialect_1.jsonmetadef.schema.json` preserves the published standard metaschema’s recursive validation rules and references the keyword definitions. Draft-05 shares the Draft-04 metaschema (no distinct dialect resource). The keyword meta-schemas describe JSON syntax only; the semantic requirements above must be implemented and tested by consuming tools. Older drafts without `$vocabulary` may use these `x-` keywords as proprietary annotations with separately documented support, but they MUST NOT be described as implementing the 2019-09/2020-12 `$vocabulary` mechanism.

The versioned public identifiers are immutable after stable publication. This 1.1-SNAPSHOT working migration modifies the existing version-1 resource; before a stable release, publish a version-2 identifier rather than silently modifying a previously published immutable version. Schema-sidecar `GlobalPublicationPathId` values are deployment metadata only, not a substitute for `$id`. This artifact is data-only and must never be treated as a JSONDEFS/YAMLDEFS business-object definition by the Defs/SDO generator.
