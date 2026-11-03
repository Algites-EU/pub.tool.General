# R21 → R22: legacy Codegen namespace isolation

This is a **mechanical namespace migration**, not the implementation of the proposed
new canonical TYPE/ELEMENTLIST/LIST/MAP model. Both original generators remain the
comparison baseline, now in `eu.algites.tool.codegen.defs.old` and
`eu.algites.tool.codegen.sdo.old`. The names of product artifacts, source schema
identities, generated contracts, and naming profiles remain unchanged.

## From a Git checkout of R21

```bash
cd pub.tool.General
bash devops/migrations/migrate_codegen_to_old.sh --dry-run
bash devops/migrations/migrate_codegen_to_old.sh --apply
git diff --check
git status --short
git diff --find-renames --stat
# Commit only after checking the diff and bootstrapping the relevant artifacts.
```

The script uses `git mv` on the maintained Java/Python source trees in `intf`,
`impl`, and `cli`, their package-relative resources, and the packaged default
configuration settings. It rewrites imports, package declarations, tests and
CLI launcher references. Re-running `--apply` is safe (already-moved paths are
skipped). It does **not** touch `java.gen` or `python.gen` and does not migrate
XMLDEFS/YAMLDEFS/JSONDEFS schema identifiers. Source Java/Python generated
contract packages are therefore intentionally unchanged.

## Consumers and bootstrap

The active `devops/bootstrap/generate_sources.py` and `sdo-java.gradle` are shared
across `pub.tool.General`, `pub.lib.General`, and `pub.lib.Security`; they must
be updated to use the `.old` generator implementations **as a coordinated
change**. Use the companion changes shipped with the full R22 bundle.

Source-mode builds should use the matching R22 Codegen sources. A remote-mode
build using previously published R21 generator artifacts may not contain the
`.old` entry points; republish the matching R22 Codegen artifacts before
switching remote consumers. Publication is **not** performed by this migration.

Some archival scripts such as `pub.lib.Security/devops.old/` and
`pub.lib.General/devops.orig/` are intentionally untouched. The obsolete
`pub.lib.Security/gradle/schema-bindings.gradle.kts` refers to pre-R21
classes and is not migrated as a working CLI entry point.

## Validation

- Python source syntax and Java declared-package/directory consistency.
- Python Defs and SDO service imports from the relocated namespaces.
- Focused Python parity, choice, setter-policy, and SDO regression tests.
- Shared bootstrap file checksum comparisons across active repositories.
- Full Gradle/bootstrap and TestNG require the full dependency/toolchain setup
  and must be run before publication.

Do not edit generated `src/product/java.gen` or `src/product/python.gen` files by hand.
When the new generators are ready, put them in the original public packages,
remove the `.old` namespace only after parity tests and cutover verification.
