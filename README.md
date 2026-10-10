# Algites General Development Tools

Reusable public development tools shared across the Algites ecosystem.

> Public Algites project.

## Overview

`pub.tool.General` contains executable and programmatically callable development tools. General-purpose naming semantics do **not** live here: naming convention, conversion, and validation APIs are provided by `pub.lib.General` under GroupId `eu.algites.lib.naming`. This repository consumes those libraries.

The repository name `General` is a repository classification only. It is intentionally omitted from program package namespaces and from functional artifact GroupIds.

## Modules

```text
.
├── naming/
│   └── validator/
│       └── cli/
└── generators/
    └── code/
        ├── defscodegen/
        │   ├── intf/
        │   ├── impl/
        │   └── cli/
        └── sdocodegen/
            ├── intf/
            ├── impl/
            └── cli/
```

### Naming validator CLI

The naming validator CLI is a thin command-line adapter over `pub.lib.General_naming.validation.*`.

- GroupId: `eu.algites.tool.naming`
- package namespace: `eu.algites.tool.naming.validator`

The reusable validator model and implementation remain library functionality rather than being duplicated in this tool repository.

### Defs Codegen

`generators/code/defscodegen` is the first stage: it generates annotated, read-only
`AIig*` contracts and `AIng*` enums from canonical definitions. The new,
schema-independent `generators/code/sdocodegen` second stage generates mutable
`AIigd*` interfaces and `AIcgd*` implementations from those contracts. Both
stages support Java and Python. The 1.0 paired generator API remains available
for existing consumers but is not used by the new 1.1 pipeline.

Defs Codegen deliberately treats the three source families as distinct frontends: It deliberately treats the three Algites definition source families as distinct frontends:

- `yamldefs` — YAML-oriented definition language/profile; it may carry semantics beyond JSON definitions;
- `jsondefs` — JSON definition/schema frontend;
- `xmldefs` — XML/XSD definition frontend.

Shared lower-level parsing/model logic may be reused, but the formats are not assumed to be semantically interchangeable.

- GroupId: `eu.algites.tool.codegen`
- package namespace: `eu.algites.tool.codegen.defs`

The normalized model preserves canonical definition identity, logical name, source format, source resource, and **definition version as a separate semantic value**. Version handling is not delegated to ordinary case conversion. With the Algites profile, for example, `some-kebab-schema-name_1` is interpreted as logical name `some-kebab-schema-name` plus version `1`, and may generate `AIcgdSomeKebabSchemaName_1`.

The first-stage output policy generates versioned read contracts (`AIig..._N`)
and enum types (`AIng..._N`) with canonical provenance. The second stage
produces mutable interfaces (`AIigd..._N`) and concrete types (`AIcgd..._N`). Naming prefixes, type markers, conventions, and version rendering are policy-driven rather than hard-coded into the generic codegen contracts. Handwritten data objects use the corresponding non-generated `AIcd...` marker, independently of whether the implementation is a Java `record` or Python `@dataclass`.

Canonical definition documentation is part of code generation. `jsondefs` and `yamldefs` descriptions and XSD `xs:documentation` are normalized into the canonical model and propagated to generated Java Javadoc and Python docstrings. Read-contract property descriptions are emitted as normalized Java annotations
and Python field descriptors. Legacy paired DTO generation also retains record
components and Python `Attributes` documentation. Generated source always retains canonical provenance and a do-not-edit notice in addition to source documentation. Algites-authored definitions are expected to provide meaningful descriptions rather than relying on generated fallback text.

## API and CLI boundaries

`intf` and `impl` are artifact/dependency boundaries only. They never appear in Java/Python package names. Defs Codegen contributes to `eu.algites.tool.codegen.defs`; SDO Codegen uses
`eu.algites.tool.codegen.sdo`. In both cases, module boundaries are absent from
source package names.

Python uses PEP 420 namespace packages: the new packages contain no `__init__.py`. Each main public `AI*` Python type is stored in its own deterministic snake_case module, analogous to the Java one-public-type-per-file layout.

The CLI is only an adapter. Builder/AAC integrations should use the programmatic `intf` API directly when they run in-process.

## Build

```bash
./gradlew clean modustroBuild
```

The repository uses the shared Modustro build lifecycle and supports Java and Python artifacts.

## Architectural role

`pub.lib.General` owns reusable algorithms and models that are useful outside a development tool. `pub.tool.General` owns development operations such as code generation and command-line traversal/adapters. AAC-specific code generation should build on Defs Codegen and retain only AAC capability/Data-Entity-specific generation in AAC.

## License

See `LICENSE` and `license-usage.yml`.


## Modustro repository initialization

Repository and artifact metadata use `modustro-source-repository.yml`,
`modustro-artifact-set.yml` and `modustro-artifact.yml`. Root Settings load the
compiled `modustro.builder.gradleinit` artifact once; project inclusion,
resource endpoints and metadata are resolved by that plugin. Artifact source
sets, dependencies and output production are configured by the shared Modustro
conventions. Source generation is inferred from `src/product/yamldefs`,
`src/product/jsondefs` and `src/product/xmldefs`, without per-file generation
sections in descriptors. Test-only canonical fixtures belong below `src/develop`.


## Canonical representation regression and bootstrap

Compatible YAML/JSON representations are compared by their logical type,
version and property contract, rather than raw generated text. The merger keeps
all descriptions and origins in generated Javadoc/docstrings while retaining
the first representation's primary identity. Different required fields, types,
nullability, references or enum values fail with an incompatibility error.
Pointers and anchors refer to nodes inside a schema; their fragments are never
parsed as versioned filenames. `allOf` compositions contribute object fields
and requiredness. Canonical URL references are resolved from checked-out
schema roots, without downloading schema documents during generation.

The original common-metadata YAML/JSON fixtures are under Impl
`src/develop/yamldefs` and `src/develop/jsondefs`. Java TestNG and Python pytest
regressions cover both output targets, descriptions, provenance, Java source
compilation, Python mapping roundtrips, incompatible contracts, local pointers,
anchors, composed objects and XML filename identity/repeated elements.

The updated Builder build conventions need the new generator API. Bootstrap and
publish the generator before activating those conventions. With JDK 17:

```bash
bash generators/code/defscodegen/bootstrap.sh test publishToMavenLocal
./gradlew modustroBuild -Pmodustro.useMavenLocalForResolution=true
```

The Defs bootstrap builds its Intf, Impl and CLI against published
naming libraries and does not evaluate consumer Settings. Publish their JARs,
POMs and Gradle module metadata to the shared snapshot repository before CI
uses the updated public governance conventions. `MODUSTRO_GRADLE_EXECUTABLE`
optionally selects the Gradle executable.

## 1.1 migration and deployment order

1. `pub.lib.General` stays unchanged at `1.1-SNAPSHOT` and must already be published.
2. Build and publish both tool generators (`defscodegen` and `sdocodegen`) at `1.1-SNAPSHOT`.
3. Only after successful publication, migrate `pub.gov.Algites` Builder bootstrap
   and consumer repositories to the new coordinates. Never change the
   currently published `gradleinit:1.0-SNAPSHOT` bootstrap coordinate as part
   of this tool-only migration.
4. Migrate existing AAC/Builder schema-binding integrations from the legacy
   paired generator to the separate contract and SDO stages.

The descriptor/directory rename helper is
`pub.tool.General-git-mv-1.1-codegen.sh`. No changes in `pub.lib.General` are
necessary for the independent Java/Python generators implemented here.
