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

## `x-algites-defscodegen-key`

The keyword is an object with exactly two nonempty string members, `id` and
`field-name`; additional members are forbidden. It applies to a JSONDEFS or
YAMLDEFS schema of one of two forms:

- A homogeneous JSON/YAML **object map** with an object-valued `additionalProperties`
  schema, where map property names supply virtual key values.
- A homogeneous JSON/YAML **array** with an `items` schema describing typed
  objects and a required scalar/enum item field selected by `field-name`.
  For arrays, `field-name` selects a *real item field*, not a synthetic map key.
  The key is attached to the canonical LIST and the owning generated getter.

For object maps, the map's **property names** provide virtual key values;
`field-name` names the **logical data field** returned by the generated synthetic
map-key getter, and overrides the `multi_mapped_list_key_synthetic_getter`
naming-role default. It is **not** the spelling of a method in a specific
programming language. `id` names the identity constraint local to the map's
owning collection, equivalent to `xs:key/@name`. `field-name` corresponds to
the one selected field of a simple XML `xs:key` such as `@kind` or `@name`.

Example:

```json
{
  "type": "object",
  "x-algites-defscodegen-key": {
    "id": "UniqueStructureRoles",
    "field-name": "kind"
  },
  "propertyNames": {"$ref": "https://example.org/structure-kind.schema.json"},
  "additionalProperties": {"type": "string"}
}
```

For arrays, for example:

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {"name": {"type": "string"}, "Value": {"type": "string"}},
    "required": ["name", "Value"]
  },
  "x-algites-defscodegen-key": {"id": "UniqueNames", "field-name": "name"}
}
```

`items` may also reference a named object type; the resolved key field must
still be a typed scalar or enum. Invalid or missing fields are diagnosed rather
than interpreted as untyped map values. Both representations preserve their
original wire format.

The property-name schema remains the source of validation and the **typed key**
(enum when its referenced contract is an enum); the extension does not widen an
enum to `String`. The index must expose a typed keyed collection equivalent to
the corresponding XML indexed list, **not** a raw `Map<String, String>`.
Absent the extension, the previously configured synthetic key getter remains
applicable. Repeated JSON/YAML member names cannot form distinct entries.

Explicit `additionalProperties: true` and `additionalProperties: {}` carry no
value type and MUST NOT produce `Object`, `Any`, or `Map<String,Object>` getters.
The generator ignores those wildcards, emits a location-specific warning, and
shows a typed declaration such as `"additionalProperties":{"type":"string"}`
or `"additionalProperties":{"$ref":"#/$defs/Item"}`. Omitted
`additionalProperties` follows JSON Schema's default open semantics but does
not trigger a warning or create an untyped getter. Ignoring unknown values can
prevent lossless data roundtrips. A typed `additionalProperties` schema still
creates a typed collection.

Both `id` and `field-name` MUST be valid, collision-free logical identifiers;
loss of typed enum identity, ambiguous external references and incompatible
field/value projections MUST be rejected rather than silently emitted as an
untyped map. The keyword does not itself describe a composite XML key.

## `x-algites-defscodegen-root-type-name`

The value MUST be a string matching `^[A-Za-z_][A-Za-z0-9_]*$`.
This is an optional **explicit name override for the document-root generated
contract** of a JSONDEFS or YAMLDEFS source schema. Normally the root name is
obtained from the source filename using the selected naming profile. This
keyword overrides that name only when a different shared canonical root name
is needed; it MUST NOT derive the name from `title` or `description`.

The keyword is permitted only at the top level of a source schema that
actually defines a document root. It MUST NOT rename any definitions in
`$defs` / `definitions`, change the logical `x-algites-schema-id`, change the
on-wire JSON/YAML properties, or rename XSD global elements. Named definitions
use their own declaration keys. A schema containing a single named
`$defs` declaration referenced by a root `$ref` has no need for this override:
its named declaration supplies the type name. Implementations MUST avoid
emitting a duplicate synthetic root type for a root that merely aliases its
own named `$defs` declaration.

Example of a deliberate override (when a different source filename is
required by the publishing convention):

```json
{
  "$schema": "https://defs.dev.algites.eu/api/jsonmetadefs/eu/algites/tool/codegen/defs/jsonmetadef/2020-12/dialect_1.jsonmetadef.schema.json",
  "$id": "https://example.org/credentials-envelope_1.jsondef.schema.json",
  "x-algites-defscodegen-root-type-name": "CredentialDocument",
  "type": "object",
  "properties": {"Profile": {"type": "array", "items": {"type": "object"}}}
}
```

The keyword affects **code-generation naming only**, not JSON Schema
instance validation. JSON Schema validators that do not implement the Defs
Codegen vocabulary can ignore it without changing the accepted document set.

## Compatibility and publication

One semantic vocabulary URI is shared across dialect-specific vocabulary keyword meta-schemas for JSON Schema 2019-09 and 2020-12. For Draft-03, Draft-04, Draft-06, and Draft-07, the same semantics are expressed as proprietary annotations in extended, version-specific meta-schemas. These historical dialects lack `$vocabulary`; the corresponding `vocabulary_1.jsonmetadef.schema.json` resources validate keyword syntax, while `dialect_1.jsonmetadef.schema.json` preserves the published standard metaschema’s recursive validation rules and references the keyword definitions. Draft-05 shares the Draft-04 metaschema (no distinct dialect resource). The keyword meta-schemas describe JSON syntax only; the semantic requirements above must be implemented and tested by consuming tools. Older drafts without `$vocabulary` may use these `x-` keywords as proprietary annotations with separately documented support, but they MUST NOT be described as implementing the 2019-09/2020-12 `$vocabulary` mechanism.

The versioned public identifiers are immutable after stable publication. This 1.1-SNAPSHOT working migration modifies the existing version-1 resource; before a stable release, publish a version-2 identifier rather than silently modifying a previously published immutable version. Schema-sidecar `GlobalPublicationPathId` values are deployment metadata only, not a substitute for `$id`. This artifact is data-only and must never be treated as a JSONDEFS/YAMLDEFS business-object definition by the Defs/SDO generator.
