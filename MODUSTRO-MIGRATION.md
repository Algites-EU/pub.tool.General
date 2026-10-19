# Modustro migration and generator fixes

Repository descriptors use the current modustro-* names. Settings bootstrap the
compiled Gradleinit plugin; source generation and dependencies are declared in
the descriptors instead of duplicated module Gradle scripts.

YAML and JSON canonical definitions are compared structurally, then their
documentation and origins are merged. Local references, composition and Python
wire-name mapping are covered by regressions. XML definitions use a separate
xmldefs namespace where their contracts differ.

Bootstrap/publish the updated Defs Codegen before the updated Gradleinit plugin,
then activate the governance scripts. Both standalone bootstrap scripts and
artifact coordinates are documented in their repository READMEs. Remote
publication has not been performed.

Validation: 147 Java tests and 4 Python tests passed locally across the three
repositories. Packaging phases passed; external Cloudsmith access returned HTTP
403 during a repeated preflight, so final Python dependency checks use locally
built wheels. This does not establish remote GitHub Actions success.

## Removed repository-relative paths

Descriptor files in this list were renamed to modustro-*; module build scripts
were replaced by descriptor declarations; obsolete resolver scripts were removed.

```text
algites-source-repository.yml
generators/algites-artifact-set.yml
generators/code/algites-artifact-set.yml
generators/code/defscodegen/algites-artifact-set.yml
generators/code/defscodegen/cli/algites-artifact.yml
generators/code/defscodegen/impl/algites-artifact.yml
generators/code/defscodegen/intf/algites-artifact.yml
naming/algites-artifact-set.yml
naming/validator/algites-artifact-set.yml
naming/validator/cli/algites-artifact.yml
```

## Schema parity and precise scalar types (2026-10-04)

The generator now retains exact integers/decimals, calendars, durations, binary
content and basic scalar facets. The cross-format fixtures and coverage limits
are documented in `generators/code/defscodegen/impl/src/develop/SCHEMA-PARITY.md`.
Generated Java numeric components now use BigInteger/BigDecimal where earlier
outputs used Long/Double. Generated Python Decimal values require a compatible
JSON serializer. No further pub.lib.General source changes are required.
Publish the matching Intf, Impl and CLI generator modules together.

The compiled generator bundle also contains rebuilt Python naming dependencies
from pub.lib.General. Their source code is unchanged, but earlier multi-root
wheel discovery omitted handwritten modules. Publish those dependency wheels
before the matching generator Python wheels. The nine-wheel set passed all
seventeen Python generator tests without source-tree imports.

## 1.1 generator split (2026-10-10)

`pub.tool.General` now has two code generators with separate `intf`, `impl`
and `cli` artifacts. The published `pub.lib.General:1.1-SNAPSHOT` is consumed
unchanged; naming dependencies have been migrated from the old `coreintf` /
`coreimpl` coordinates to `intf` / `impl`.

New Builder integrations must use `AIcSchemaContractBindingsGenerator`
(first stage, no concrete outputs) and `AIcSdoCodegenService` (second stage,
no schema input). The old schema-object binding API remains a compatibility
adapter for consumer repositories that have not yet migrated. Publish both
new generator families before updating the governance Builder bootstrap.

## 1.1 canonical batch inputs and YAML naming (2026-10-12)

The new explicit Defs Codegen batch CLI accepts multiple schema input roots,
including several roots of the same source kind. Schemas mapping to one generated
source are merged only if their canonical identities (with recognized public
format-URL aliases) and normalized contracts agree. Distinct IDs cannot occupy
the same output path; same-format duplicate declarations are not rejected merely
for sharing a source kind. All schema parsing, reference resolution, merging
and output collision detection completes before any naming-based cleanup.
Failures found during preflight therefore leave the previous generated files
untouched. This is not a filesystem transaction if writing fails later.

Detailed options, naming YAML rules, single-definition compatibility mode, SDO
reflection/import requirements and error semantics are described in
[Code Generators Reference Guide](generators/code/CODEGEN-REFERENCE.md).

The 2026-10-04 validation figures above are historical for that migration;
they are **not** a statement that the new 1.1 snapshot has passed a full JVM or
remote deployment test.

## 1.1 canonical merge versus stale self-hosted Gradle generator (2026-10-19)

A build reporting `Incompatible canonical representations` for
`schema-field-bindings_1.yamldef.schema.json` and
`schema-field-bindings_1.jsondef.schema.json`, while the invocation identifies
`pub.tool.General_generators.code.defscodegen.coreimpl:1.0-SNAPSHOT` as its
`source-generator`, has selected the **obsolete bootstrap generator**. The
current module is `pub.tool.General_generators.code.defscodegen.impl:1.1-SNAPSHOT`
and its merger reports the individual conflicting fields if a contract is
incompatible. Merely changing the sources in this repository does not replace
an already resolved generator JAR inside the Gradle initialization/bootstrap
classpath of `pub.gov.Algites`.

The two input schemas intentionally publish different `$id` and `$schema`
self-publication URLs. These are representation-specific transport identifiers,
not a mismatch of the shared contract. The current merger validates that each
self-link is the genuine publication URL of its own source before normalizing
it; unrelated string constants, document properties, facets and other schema
constraints continue to be compared strictly. The normalized merged contract
must not retain either format's private `$schema` constant; the original
published JSON/YAML schemas retain their own constants.

To fix the affected CI invocation, bootstrap/publish matching 1.1 `intf`,
`impl` and `cli` source-generator modules, then change the actual source-generator
bootstrap coordinate in **`pub.gov.Algites`** to `...defscodegen.impl:1.1-SNAPSHOT`
(and update its dependent Builder/Gradleinit artifacts as required). Confirm
that the `Modustro invocation` reports the new coordinate and SHA-256 before
retrying `:generators:code:defscodegen:intf:generateModustroDefinitionSources`.
The local repository's `generators/code/bootstrap.sh` already builds and
publishes the 1.1 split. Do **not** remove either `$schema` constant to make
an outdated generator pass; that would weaken validation of each individual
published format. This is a **cross-repository bootstrap prerequisite**, not a
claim that the `pub.gov.Algites` build was executed here.
