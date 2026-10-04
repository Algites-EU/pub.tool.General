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
        └── defscodegen/
            ├── coreintf/
            ├── coreimpl/
            └── cli/
```

### Naming validator CLI

The naming validator CLI is a thin command-line adapter over `pub.lib.General_naming.validation.*`.

- GroupId: `eu.algites.tool.naming`
- package namespace: `eu.algites.tool.naming.validator`

The reusable validator model and implementation remain library functionality rather than being duplicated in this tool repository.

### Defs Codegen

`generators/code/defscodegen` generates Java and Python program types from canonical definitions. It deliberately treats the three Algites definition source families as distinct frontends:

- `yamldefs` — YAML-oriented definition language/profile; it may carry semantics beyond JSON definitions;
- `jsondefs` — JSON definition/schema frontend;
- `xmldefs` — XML/XSD definition frontend.

Shared lower-level parsing/model logic may be reused, but the formats are not assumed to be semantically interchangeable.

- GroupId: `eu.algites.tool.codegen`
- package namespace: `eu.algites.tool.codegen.defs`

The normalized model preserves canonical definition identity, logical name, source format, source resource, and **definition version as a separate semantic value**. Version handling is not delegated to ordinary case conversion. With the Algites profile, for example, `some-kebab-schema-name_1` is interpreted as logical name `some-kebab-schema-name` plus version `1`, and may generate `AIcgdSomeKebabSchemaName_1`.

The default Algites output policy generates versioned data types (`AIcgd..._N`) and enum types (`AIng..._N`) with canonical provenance. Naming prefixes, type markers, conventions, and version rendering are policy-driven rather than hard-coded into the generic codegen contracts. Handwritten data objects use the corresponding non-generated `AIcd...` marker, independently of whether the implementation is a Java `record` or Python `@dataclass`.

Canonical definition documentation is part of code generation. `jsondefs` and `yamldefs` descriptions and XSD `xs:documentation` are normalized into the canonical model and propagated to generated Java Javadoc and Python docstrings. Property descriptions are emitted as Java record-component `@param` documentation and Python `Attributes` documentation. Generated source always retains canonical provenance and a do-not-edit notice in addition to source documentation. Algites-authored definitions are expected to provide meaningful descriptions rather than relying on generated fallback text.

## API and CLI boundaries

`coreintf` and `coreimpl` are artifact/dependency boundaries only. They never appear in Java/Python package names. Both Defs Codegen artifacts contribute to `eu.algites.tool.codegen.defs`.

Python uses PEP 420 namespace packages: the new packages contain no `__init__.py`. Each main public `AI*` Python type is stored in its own deterministic snake_case module, analogous to the Java one-public-type-per-file layout.

The CLI is only an adapter. Builder/AAC integrations should use the programmatic `coreintf` API directly when they run in-process.

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

The original common-metadata YAML/JSON fixtures are under CoreImpl
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

The independent bootstrap builds CoreIntf, CoreImpl and CLI against published
naming libraries and does not evaluate consumer Settings. Publish their JARs,
POMs and Gradle module metadata to the shared snapshot repository before CI
uses the updated public governance conventions. `MODUSTRO_GRADLE_EXECUTABLE`
optionally selects the Gradle executable.
