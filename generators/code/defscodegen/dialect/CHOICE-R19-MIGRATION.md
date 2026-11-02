# Explicit-property Choice migration — working r19

This is a **source migration checkpoint**, not a confirmed end-to-end bootstrap
release. It builds on r17 of all four repositories and includes the r18
Security Configuration `xs:choice` schema prototype.

## Implemented

* All six dialect vocabulary variants now accept `x-algites-defscodegen-choice:
  true`, with the alternatives declared exactly once under adjacent `properties`.
* For Draft-04 and later, a Choice must have `type: object`, two or more
  `properties`, `minProperties: 1`, `maxProperties: 1`, and
  `additionalProperties: false`; `required` and `patternProperties` on the
  Choice itself are disallowed. Standard third-party validators validate the
  accepted *instances* even if they ignore the Algites marker.
* Draft-03 can recognize the marker syntactically but cannot guarantee portable
  exclusive-choice semantics with standard Draft-03 validators.
* JSONDEFS and YAMLDEFS source readers in both Java and Python now interpret
  the boolean marker and preserve the **property name** as the alternative's
  canonical one-field `OBJECT` identity. Constraint-only `oneOf` remains
  nonstructural; marker declarations in validation-only branches are rejected.
* Migrated `NameFragmentsSegmentChoice`, `ValueSource`, and the r18 Security
  `ConfigurationValueType` in both JSONDEFS and YAMLDEFS.
* No generated `.gen` sources have been manually edited.

## Explicit remaining blockers

1. **Naming resource data:** `NameFragmentsSegmentChoice` now uses named
   wrappers (`NameFragmentsSegmentValue` and `NameFragmentsSegmentReference`).
   Existing YAML resource files still use unwrapped `Segments` entries such as
   `{Kind: constant_string, Value: AI}`. They do not validate against the new
   schema. A follow-up migration must coordinate actual resource instances
   and the Java/Python catalog readers; it must not blindly reformat YAML or
   change the loaders before compatibility testing.
2. **Credential instance data:** `ValueSource` previously allowed
   `{Source: direct_value, Value: abc}`. The new schema requires
   `{DirectValue: {Source: direct_value, Value: abc}}`; existing external
   credentials documents need deliberate migration. Credential secrets must
   not be included in a diagnostic archive.
3. **XML and map projection:** The r18 Security XML `xs:choice`/inherited-key
   and the canonical `Map<K,V>` unification discussed earlier are **not yet
   implemented**. Java/Python codegen may still fail on their signatures.
4. **Other separately approved refactors:** renaming the internal datatype-kind
   enum and introducing `MAP` are not included in this scoped vocabulary
   migration. Keep those in the follow-up canonical-model change.
5. **Publication semantics:** The working snapshot modifies resources named
   `vocabulary_1`. Before publishing a stable incompatible resource, use a new
   vocabulary identifier/version rather than replacing an immutable release.

## Verification performed in this checkpoint

* 45 focused Python tests passed (dialects, validator compatibility, parser
  structural semantics, XML/JSON/YAML r18 prototype).
* Six migrated JSONDEFS/YAMLDEFS schemas passed Draft 2020-12 schema checks;
  positive and negative `ValueSource` instance checks were exercised.
* The unified patch applies cleanly to the r17 archive snapshot.
* **No Gradle 9.2.1 bootstrap/build completed in this environment**. The
  change is not declared bootstrap-ready.

## Suggested integration order

First complete the naming-resource instance migration and loader parity;
then finalize the XML choice/`xs:key` inheritance and canonical map projection;
then build/publish the updated Defs Codegen before expecting repositories
resolved in `remote` mode to understand the new `Choice` syntax. Validate
Java and Python generated contracts rather than patching `java.gen` or
`python.gen` outputs directly.
