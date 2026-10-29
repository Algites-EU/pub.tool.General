# Algites Defs Codegen JSON Schema dialects (jsonmetadefs)

This independent, data-only artifact publishes one semantic Algites Defs Codegen
vocabulary specification (`vocabulary_1.md`) and **draft-specific** metadata for
all supported historical JSON Schema syntax families:

| Schema dialect directory | Base specification | `$vocabulary` available? | Algites keyword syntax |
| --- | --- | --- | --- |
| `draft-03` | JSON Schema Draft-03 | No | Draft-03 compatible extension |
| `draft-04` | JSON Schema Draft-04 (also Draft-05, which has no new meta-schema) | No | Draft-04 compatible extension |
| `draft-06` | JSON Schema Draft-06 | No | Draft-06 compatible extension |
| `draft-07` | JSON Schema Draft-07 | No | Draft-07 compatible extension |
| `2019-09` | JSON Schema Draft 2019-09 | Yes | 2019-09 vocabulary meta-schema |
| `2020-12` | JSON Schema Draft 2020-12 | Yes | 2020-12 vocabulary meta-schema |

All directories contain `vocabulary_1.jsonmetadef.schema.json` and
`dialect_1.jsonmetadef.schema.json`, each with a publication `.meta.yml` sidecar.
Every dialect is versioned independently, while the **meaning** of the two
custom keywords is specified once in `vocabulary_1.md`.

## Legacy dialect design

Draft-03 through Draft-07 have **no `$vocabulary` mechanism**. Their combined
Algites dialects are therefore draft-correct extended meta-schemas, not
implementations of modern JSON Schema vocabularies. They preserve the official
meta-schema's recursive structure, with an updated `id`/`$id` and references
to the sibling vocabulary keyword-shape meta-schema. This is necessary to
validate annotations inside nested `properties`, `items`, etc.; a plain `allOf`
combining an external official meta-schema and a keyword schema would validate
only root-level annotations. The base meta-schema is therefore embedded as a
snapshot under our new immutable `$id`/`id` (with no changed standard keyword
rules), while the Algites keyword syntax remains in its separately maintained
file. Draft-03 uses its historical boolean property-level `required` syntax.

Draft-05 was a clarification of Draft-04 and did not introduce a separate
meta-schema. Draft-00 through Draft-02 are historical pre-Draft-03 proposals
not implemented by this artifact. Adding a dialect resource for a draft **does
not** mean the current Defs Codegen source readers support that entire draft.
In particular, recursive URI identifiers, tuple array representations and
Draft-03's `type`/`extends` features need separate, tested reader adapters.

## Modern dialects

The 2019-09 and 2020-12 dialects declare standard vocabularies and the optional
Algites Defs Codegen vocabulary (`false` in `$vocabulary`). Their dialect
meta-schemas combine standard keyword metaschemas with the corresponding
Algites vocabulary syntax metaschema via `allOf`. The standard JSON Schema
`$schema` keyword is reused, not redefined.

## Publication and integration

The artifact is independent of the Java/Python generators and contains only
schema resources and documentation. It is not intended as a business-object
input to Defs/SDO generation. The current bootstrap and Builder configuration
still need explicit support for the `jsonmetadefs` source kind before the
resources can be published to the schema site; no public deployment is implied.
