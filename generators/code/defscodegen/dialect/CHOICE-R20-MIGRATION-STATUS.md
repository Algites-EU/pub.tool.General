# Named Choice r20: source and reader migration (2026-11-02)

## Scope

This release follows the r19 vocabulary migration. It migrates **all 29 shipped
General naming profile YAML files** (2,737 `Segments` values) from unwrapped
`{Kind: ..., ...}` / `{Ref: ...}` entries to one of the explicitly named
`NameFragmentsSegmentValue` or `NameFragmentsSegmentReference` alternatives.
Both JSONDEFS and YAMLDEFS shared schema definitions are used when validating
these resources. The JSON/YAML `x-algites-defscodegen-choice: true` marker stays
structural and the instance constraints enforce exactly one property.

The Java and Python naming catalog readers normalize the new tagged entries
back to their pre-existing internal representation without modifying that
representation. They also accept old unwrapped entries for transitional data.
The Security credential ValueSource reader similarly reads tagged and legacy
values, and the writer emits canonical tagged values. Do not include real
secrets in tests or diagnostic archives.

XML naming's NameFragmentsSegmentChoice now has two explicit element names
matching the JSON/YAML alternatives. Security's XML ConfigurationEntryType
represents its `xs:choice` directly, with its Name attribute, avoiding an
unsupported XML complexContent extension of a Choice type. Both production
XSDs validate under XSD 1.0.

## Codegen correctness fixes

* Closed-choice inline branch identities are stable, named and independent
  of alternative order. Selected-variant wrappers are named distinctly from
  the actual payload contracts to avoid duplicate classes.
* Inline payload contracts are emitted for JSON and YAML as well as XML; they
  inherit the correct common/specialized contract role and naming profile.
* The contract binder no longer assumes that every choice source after index
  zero is a selected-value wrapper. It accounts for emitted payload contracts.
* XML `xs:key` extraction traverses inherited attribute/element declarations
  rather than relying on hardwired field names.

Do not edit any `src/product/java.gen` or `src/product/python.gen` output by hand.

## Verification

* 89 focused pytest checks pass (naming catalogs, all migrated naming-resource
  validations, credentials reader/service, Choice dialect/reader).
* Source-mode pre-generation of **pub.lib.General** passed in an isolated
  build trial: 196 Defs contracts across two artifacts, followed by 110 Python
  SDO sources. This is a generator smoke test, not a Gradle compile.
* `pub.lib.Security` Defs pre-generation advances past the XML inheritance
  problem but **still fails at Python SDO import** for
  `AIigConfigurationTypeAdditionalProperties_1`. This is the previously known
  `Configuration` XML keyed-collection / JSON additionalProperties / common
  `Map<K,V>` incompatibility, not a naming profile migration failure.
* Gradle 9.2.1 is not installed/cached in the execution environment, and
  downloading it from services.gradle.org was unavailable. Thus no full Java
  compilation, Gradle bootstrap or Cloudsmith deployment has been verified.

## Blocker to making Security bootstrap-ready

Complete the agreed canonical `MAP<K,V>` projection for JSON/YAML
`additionalProperties` and XML keyed-list entries, including emitting a
consistent Java and Python common contract, preserving `xs:choice` as a
single exclusive alternative, and retaining physical schema bindings.
Avoid a workaround that replaces the typed value with `Object`, rewrites
`java.gen` output or disables incompatible-return-type validation.

The current Security output also demonstrates incompatible Java signatures:
`AIiMultiMappedList<AIigConfigurationValueType_1>` versus
`AIiMultiMappedList<AIigCredentialProfileConfigurationAdditionalProperties_1>`
for `getConfiguration()`. A full canonical MAP implementation and runtime
integration remain necessary before claiming a successful Security build.

## Local integration order

1. Develop/build/publish updated `pub.tool.General` and `pub.lib.General`
   using the **source** dependency mode (or install the exact new versions
   in the configured local Maven/Python indexes).
2. Only then attempt `pub.lib.Security` in `remote` mode, because `remote`
   otherwise resolves the previously published Codegen that does not
   understand the new Choice declaration.
3. Finish the MAP/Choice cross-format projection and re-run both Java and
   Python generation and Gradle compilation before deployment.

This archive is a verified migration of naming profiles and both readers,
**not a fully bootstrap-ready release of pub.lib.Security**.
