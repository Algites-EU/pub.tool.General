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
