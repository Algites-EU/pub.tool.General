# Schema object contracts and implementations

Both the JVM and native Python `AIcSchemaObjectBindingsGenerator` render Java and
Python using their existing canonical readers, naming profiles and backends.
`AIcSchemaInterfaceGenerator.generate(request)` returns a contract and its
implementation; enum definitions return only the shared enum contract.
The existing standalone `service.generate(request)` API is unchanged.

The native Python classes live in `aic_schema_interface_generator.py` and
`aic_schema_object_bindings_generator.py`. Their paired API is `generate(request)`;
their repository API is `generate_repository(repository, manifest, check=False)`.
The JVM equivalent is `generateRepository(repository, manifest, check)`.
Both return the same per-schema metadata and use the same ownership manifest.
For example, with the generator and its declared dependencies installed:

```bash
python3 -m eu.algites.tool.codegen.defs.aic_schema_object_bindings_generator \
  /path/to/repository /path/to/repository/devtools/schema-field-bindings.json
```

`--check` and `--json` have the same meaning in both CLIs. Whichever implementation
last generated a tree owns its exact formatting; a check verifies that formatting.
Cross-implementation integration tests compare semantics independently of formatting.

Repository generation accepts a manifest such as:

```json
{
  "artifact": "aac/coreintf",
  "implementation_artifact": "aac/coreimpl",
  "languages": ["python"],
  "bindings": []
}
```

Objects, nested objects and enums are discovered in `src/product/jsondefs` and
`src/product/yamldefs`. A generated package is derived from the schema's package
path, never from a shared output package. JSON/YAML representations are merged
only if their canonical shapes are compatible. Different object pointers in
one source remain different types, including a named definition and a property
that use the same label. Cross-package references retain their owning package.

Contracts (`AIig...`) and enums (`AIng...`) belong to the interface artifact's
`java.gen`/`python.gen` roots. Concrete records/dataclasses (`AIcgd...`) implement
those contracts in the implementation artifact's roots. Abstract Python
contracts expose annotated attributes, documented `ClassVar` field constants,
canonical provenance and abstract `to_mapping()`; Java interfaces expose field
constants and documented typed accessors. Concrete implementations retain the
normal backend's validation, optional-value and wire serialization behavior.
Native Python temporal/duration helper types used in contract annotations live
with the contract; its concrete dataclass imports the same types. No generator
package is required at application runtime.

Only the generator writes these roots. All `.gen`/`.extgen` directories are
ignored by Git and excluded from source archives. Handwritten source imports
the generated contracts, constants and enums. Generated classes require no
installed generator at program runtime. Standalone inline DTO generation, such
as AAC capability bindings, remains supported.

Compile/publish the updated Defs Codegen generator **before** building consumer
repositories. The existing `bootstrap.sh` breaks the self-hosting dependency;
without arguments it tests and publishes the JVM generator to Maven Local.
Consumers in GitHub need the corresponding published generator snapshot.
AAC and Security wire `generateModustroSchemaBindings` into their compile,
staging, package metadata and test prerequisites. Local AAC build/test scripts
call the same Gradle entry point. No `.gen` contents are fetched from Git.

The generator records owned paths in
`build/run/schema-bindings/generated-files.json`. Later generation removes only
stale owned paths, preserving files produced by other generators. `--check`
validates without writing; `--json` prints per-schema output metadata. All outputs
are calculated and collision/representation checks pass before any file is
changed. Inputs and owned paths must remain inside the repository.

These conventions apply to any technology with interface/abstract-class and
implementation concepts, and are retained here for future changes.

## Independent implementation integration tests

`AItcGeneratorImplementationParityTest` is part of the ordinary Java TestNG suite.
It runs `src/develop/python/generator_implementation_parity.py`, which invokes
the native Python API and the JVM API/CLI on the same inputs. It checks all three
standalone source frontends (JSON/YAML/XSD) and both output targets. Repository
binding discovery itself accepts the canonical JSON/YAML roots.

Python output is compared as AST, preserving constants, annotations, control flow
and documentation; only docstring whitespace is normalized. Java output is compared
as lexical tokens, preserving string/character literals and documentation text.
The tests separately compile Java outputs, import every Python module, resolve
type hints, round-trip nested references and check invalid values. They also cover
cross-package repeated references, enum/null/boolean normalization, exact decimal
facets, escaped documentation, name collisions, ignored non-schema examples,
compatible representations, owned stale pruning and read-only checks.

`gradle/generator-parity.gradle.kts` prepares the Java test's Python dependencies
under `build/run/generator-parity` using Builder-generated `pyproject.toml` metadata
and configured public Python input subscriptions. It does not install into the
global interpreter. Standard `test`/`check` run the TestNG bridge automatically.
The bootstrap build mirrors its naming dependencies and prepares the same isolated
environment without needing repository metadata or the updated published generator.
`prepareModustroGeneratorParityPython` can also be run explicitly. The independent
Python pytest suite includes direct paired API, enum, repository CLI and comparison
regressions. For direct execution outside Gradle, install the declared naming and
PyYAML dependencies or place their source packages on `PYTHONPATH`.

## Production naming dependency

Repository binding generation calls `AIcAlgitesNamingProfiles` from
`pub.lib.General_naming.convention.coreimpl` in production. The CoreImpl
descriptor must declare this dependency with `Usages: [product_implementation]`;
`develop_implementation` only adds it to the Java test classpath and fails
`compileJava`. Python also requires this package at runtime. The bootstrap build
uses `implementation` for the same reason. No naming source is copied into the
generator, and the standard naming implementation remains the single owner.

A source-only compilation that merges generator and naming sources cannot
verify dependency scopes. Build each artifact against its declared production
classpath and the published naming JARs. The CI revision
`fa865facc441e487690ab8018b45f97083b937f9` predates this scope correction.
