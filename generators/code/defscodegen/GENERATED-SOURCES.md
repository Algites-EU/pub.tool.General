# Schema object contracts and implementations

The JVM `AIcSchemaObjectBindingsGenerator` renders both Java and Python using the
existing canonical reader, naming profiles and code generation backends.
`AIcSchemaInterfaceGenerator.generate(request)` returns a contract and its
implementation; enum definitions return only the shared enum contract.
The existing standalone `service.generate(request)` API is unchanged.

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
