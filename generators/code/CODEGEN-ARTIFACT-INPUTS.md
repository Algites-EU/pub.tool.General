# Artifact inputs and qualified Codegen CLI configuration

This document describes the qualified configuration contract used by both native
Java and Python Defs/SDO Codegen implementations. It applies to the proposed
`defsintf` → `sdo` two-artifact workflow. The artifact coordinates are examples;
replace them with artifacts that actually exist in the configured local store.

## Layering (no legacy conversion)

A setting's entire key, including qualifiers after `:`, is its identity.
Packaged defaults, all discovered classpath overlays, one explicitly selected
`--settings-file`, and explicit CLI values are merged in priority order.
The later value for an identical key replaces **the complete earlier value**;
an empty assignment removes a key. No pass converts a `:java` / `:python`
qualified key into a legacy `java:...` value. Such values are no longer valid
on the native CLI. The bootstrap passes qualified options as well.

## Defs inputs

```properties
--defs-input-artifacts:java=eu.algites.lib:pub.lib.General_example.defsintf:1.1-SNAPSHOT;eu.algites.lib:pub.lib.General_another.defsintf:1.1-SNAPSHOT
--defs-input-artifacts:python=example-definitions>=1.1.dev0,<1.1a0;another-definitions==1.2
--schema-input-dir:xmldefs=src/product/xmldefs
--schema-input-dir:yamldefs=src/product/yamldefs
--schema-input-dir:jsondefs=src/product/jsondefs
--technology-dointf-output-dir:java=src/product/java.gen
--technology-dointf-output-dir:python=src/product/python.gen
```

The selected Java JARs and Python wheels must actually contain source schema
resources (`*.xsd`, `*.yamldef.schema.json`, `*.jsondef.schema.json`). Defs
Codegen does **not** attempt to reconstruct schema sources from `.class` files.
An artifact is an explicitly selected schema source; unrelated transitive
artifacts are not scanned. Existing directory inputs remain supported.

## SDO inputs

```properties
--dointf-input-artifacts:java=eu.algites.lib:pub.lib.General_example.defsintf:1.1-SNAPSHOT
--dointf-input-artifacts:python=example-defsintf>=1.1.dev0,<1.1a0
--dointf-input-classes:java=eu.example.AIiPerson_1;eu.example.AIiAddress_1
--dointf-input-classes:python=eu.example.person:AIiPerson_1;eu.example.address:AIiAddress_1
--technology-dointf-input-dir:java=src/product/java.gen
--technology-dointf-input-dir:python=src/product/python.gen
--technology-sdointf-output-dir:java=src/product/java.gen
--technology-sdoimpl-output-dir:java=src/product/java.gen
--technology-sdointf-output-dir:python=src/product/python.gen
--technology-sdoimpl-output-dir:python=src/product/python.gen
```

The class selectors narrow the selected sources. Java uses Java class FQNs;
Python uses `importable.module:Class`. `--dointf-input-paths:java` accepts a
semicolon-separated set of local JAR or class-directory paths, and the Python
variant accepts wheels or source directories. Supporting Java binary paths and
Python module paths are supplied with `--dointf-classpath:java` and
`--dointf-classpath:python` respectively. They are **not automatically
included** in the generation selection.

## Shared artifact selector grammar

Artifact items are separated by `;` (quote the entire argument in a shell).

| Form | Example | Legal technologies |
|---|---|---|
| Maven | `group.id:artifact.id:1.1-SNAPSHOT` | Java |
| Python requirement (PEP 508 subset) | `distribution>=1.1.dev0,<1.1a0` | Python |
| Modustro | `pub.lib.General_example.defsintf@1.1-SNAPSHOT` | Both |

Optional `maven:`, `pypi:`, `modustro:` prefixes are accepted. In an inline
Python list, PEP 508 environment markers (`; python_version ...`) and direct
URLs/extras are deliberately disallowed: `;` is reserved for the artifact
separator. Complex requirements should be materialized to a wheel or installed
through a standard `requirements.txt` separately.

Modustro `@1.1-SNAPSHOT` resolves to that exact Maven snapshot in Java, and
to the newest available `1.1.devN` wheel in the **local** Modustro wheel store
for Python. Resolution is explicit and fails when an artifact is unavailable
or ambiguous. No Codegen CLI performs remote downloading, invokes pip, or
silently runs an older published generator. The source bootstrap must prepare
required build-time dependencies from source before invoking the CLI.

## Example staged publication

Create two separate Modustro artifact directories with their own
`modustro-artifact.yml`. Run Defs Codegen so its `--technology-dointf-output-dir`
points into the `defsintf` artifact, compile and publish that artifact locally,
then run SDO Codegen selecting this compiled `defsintf` via
`--dointf-input-artifacts`. Direct SDO outputs into the `sdo` artifact, compile
and publish. Artifact naming and distribution publication remain the Builder's
responsibility; a generator only produces sources.

**Note:** A complete production build must declare any selected input artifact
in the relevant build-time dependency graph. Supplying its name to Codegen
alone cannot force a missing source repository to materialize. Source mode
must not substitute a cached binary for a required unbuilt source artifact.
