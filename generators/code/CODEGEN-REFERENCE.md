# Algites Code Generators — Reference Guide (1.1-SNAPSHOT)

This guide describes the **implemented** Defs Codegen and SDO Codegen APIs in
`pub.tool.General`, including their YAML naming-catalog integration. The naming
engine and stock catalogs are supplied by `pub.lib.General` 1.1-SNAPSHOT.
Neither generator requires a JVM to execute its **native Python** implementation.
The Java implementation is independent and requires a JVM; the two can optionally
produce source code for multiple target technologies when explicitly requested.

## 1. Pipeline and ownership

| Phase | Input | Output role | Typical Java type | Typical Python module |
|---|---|---|---|---|
| Defs Codegen | `yamldefs`, `jsondefs`, `xmldefs` | `dointf` | `AIigCustomer_1.java` | `aiig_customer_1.py` |
| Defs Codegen | enum definition in a schema | DO enum | `AIngStatus_1.java` | `aing_status_1.py` |
| SDO Codegen | annotated/importable DO interface | `sdointf` | `AIigdCustomer_1.java` | `aiigd_customer_1.py` |
| SDO Codegen | annotated/importable DO interface | `sdoimpl` | `AIcgdCustomer_1.java` | `aicgd_customer_1.py` |

Defs Codegen generates read-only, annotated interfaces and enum types, **not**
mutable interfaces or concrete SDO implementations. SDO Codegen reads the
annotated contracts and does not read schema definitions. The generators may
share one `*.gen` output tree, but operate on **different naming roles**.
The output root in each CLI is a filesystem path; the relative namespace/package
of generated sources is appended by the generator.

`*.gen` trees are generated outputs, not handwritten sources. Gradle `clean`
removes standard `src/product/java.gen`, `src/product/python.gen`,
`src/develop/java.gen`, and `src/develop/python.gen` under each artifact.

## 2. Defs Codegen — batch CLI

Java entry point:

```text
eu.algites.tool.codegen.defs.impl.cli.AIcDefsCodegenCli
```

Python entry point:

```sh
python -m eu.algites.tool.codegen.defs.impl.cli.aic_defs_codegen_cli
```

The examples below use `defs-codegen` as shorthand for **either** native entry
point. This is a documentation placeholder, not a shell command installed by
this repository. For Java invoke `java -cp <runtime-classpath>
 eu.algites.tool.codegen.defs.impl.cli.AIcDefsCodegenCli ...` on one command line.

### 2.1 Complete batch example

```sh
python -m eu.algites.tool.codegen.defs.impl.cli.aic_defs_codegen_cli \
  --repository-root=. \
  --schema-input-dir=yamldefs:src/product/yamldefs \
  --schema-input-dir=jsondefs:src/product/jsondefs \
  --schema-input-dir=xmldefs:src/product/xmldefs \
  --schema-input-naming-profile=yamldefs:config/algites-yamldef-name-conventions.yml \
  --schema-input-naming-profile=jsondefs:config/algites-jsondef-name-conventions.yml \
  --schema-input-naming-profile=xmldefs:config/algites-xmldef-name-conventions.yml \
  --technology-dointf-output-dir=java:src/product/java.gen \
  --technology-dointf-output-dir=python:src/product/python.gen \
  --technology-dointf-output-naming-profile=java:config/algites-java-name-conventions.yml \
  --technology-dointf-output-naming-profile=python:config/algites-python-name-conventions.yml
```

The `config/` paths must refer to **actual YAML catalogs**. Stock catalogs and
`standard-conventions.yml` are located in the naming-convention implementation
artifact of `pub.lib.General` (`src/product/resources/.../naming/convention/`
for Java and `src/product/python/eu/algites/lib/naming/convention/` for Python).
When using `StandardConventionsFile`, keep the referenced standard catalog
beside the main YAML file. Copying the names shown above is only an example;
they are not automatically created in the consuming repository.

### 2.2 Batch options

| Option | Cardinality | Meaning |
|---|---|---|
| `--repository-root=PATH` | 0–1 | Resolve relative schema, output, and catalog paths against this root (default: working directory). |
| `--schema-input-dir=KIND:PATH` | 1+ normally | Recursively discover definitions under one `yamldefs`, `jsondefs` or `xmldefs` root. May repeat, including for the **same** kind. |
| `--schema-input-naming-profile=KIND:PATH` | 1 per selected kind | YAML catalog used to recognize input filenames and enforce versioning. |
| `--technology-dointf-output-dir=TECH:PATH` | 1 per selected technology | Output root; `TECH` is `java` or `python`. |
| `--technology-dointf-output-naming-profile=TECH:PATH` | 1 per selected technology | Catalog controlling generated interface and enum filenames/types. |
| `--check` | Flag | Verify expected output contents without cleaning or writing. |
| `--clean-only` | Flag | Clean recognized output files; no schema input or input catalog is required. Cannot be combined with `--check`. |
| `--allow-unversioned-schemas` | Flag | Permit source schema filename conventions without a version; default is versioned-only when an input catalog is configured. |

Every selected output technology requires exactly one output root and naming
catalog. An input kind may have multiple directories, but exactly one input
catalog. The batch implementation accepts both technologies in one call, or
one technology only; using the Python native CLI with `python:` only does not
start Java.

Schema discovery extensions are `*.yamldef.schema.json`,
`*.jsondef.schema.json`, and `*.xsd` respectively. Each discovered schema's
namespace/package is derived from the relative path beneath its declared
schema root. The current generator requires a legal Java/Python dotted package
name from that path (a schema placed directly at the root produces an empty
package and is currently rejected). Avoid overlapping roots that discover the
**same physical file**: such overlap is rejected. Two distinct files in two
roots are permitted to represent the same contract.

### 2.3 Multiple definitions targeting one source file

The engine collects all inputs and computes their target relative source paths
before writing. For a group targeting the same path:

1. Every representation must denote the **same canonical identity** and version.
   Exact IDs match. Format-specific Algites public definition URLs with
   `/api/yamldefs/`, `/api/jsondefs/`, or `/api/xmldefs/` and their schema
   extensions normalize to the same canonical alias. **Arbitrary different IDs
   are never treated as equivalent.** When JSON/YAML inputs omit an explicit ID,
   their implicit identity is the namespace/package, logical name, version and
   schema pointer. XSD without `targetNamespace` uses the same fallback.
   An explicit ID does not silently match an implicit one.
2. Every representation must agree structurally: logical name, version, kind,
   normalized property types, requiredness, nullability, references,
   constraints and enum values. Descriptions and provenance may differ and
   are merged. The merger does not use "first wins" for incompatible fields.
3. **Same-format duplicates are allowed** if their identities and structures
   agree; this is not limited to one input per `yamldefs`/`jsondefs`/`xmldefs`
   family. Different identities mapping to one file fail with a `Canonical
   identity collision`; equal identities with incompatible contracts fail
   with `Incompatible canonical representations`.
4. Inherited interface relationships must resolve consistently across the
   representations; incompatible inherited contracts fail.

This is a *source-output collision* policy. Two representations with equal
identities and shapes may each be listed in the returned discovery results,
while the physical output file is generated **once**.

### 2.4 Output cleanup and error safety

Normal batch generation proceeds as follows:

1. Load naming catalogs and discover inputs.
2. Validate filenames, build canonical definitions, resolve references and
   inheritance, check duplicate identities and field equivalence, and
   materialize **all** intended output sources in memory.
3. Only after successful preflight, clean the previously generated `dointf`
   and enum sources matched by their **full** filename convention
   (`file_name_stem` + `file_name_suffix`) throughout each selected output
   tree; leave other roles and unrelated source files alone.
4. Write the new selected outputs.

Therefore malformed input, incompatible definitions or output collisions found
in preflight do **not** delete the preceding sources. This is **not** a fully
transactional filesystem commit: disk errors during cleanup/write can still
leave partial output. `--check` performs no mutations. `--clean-only` performs
step 3 alone and needs only output directories/catalogs, for example:

```sh
python -m eu.algites.tool.codegen.defs.impl.cli.aic_defs_codegen_cli \
  --technology-dointf-output-dir=python:src/product/python.gen \
  --technology-dointf-output-naming-profile=python:config/algites-python-name-conventions.yml \
  --clean-only
```

In the **legacy repository-manifest API** (no explicit `schema_inputs`), the
existing `build/run/schema-contract-bindings/generated-files.json` state file
still controls stale-source removal. The explicit batch CLI instead uses naming
catalog recognition without per-file ownership manifests.

### 2.5 Legacy single-definition invocation

The positional entry point remains temporarily supported:

```text
<yamldefs|jsondefs|xmldefs> <java|python> <input-file> <package> <output-root>
```

It processes **one** schema and writes **one** generated source; it does not
perform batch discovery, structural merging, or the catalog-driven cleanup.
The pre-1.1 paired schema/DTO generator has been removed. The legacy
positional CLI form still invokes the contract-only first stage.

## 3. SDO Codegen — batch CLI

Java entry point:

```text
eu.algites.tool.codegen.sdo.impl.cli.AIcSdoCodegenCli
```

Python entry point:

```sh
python -m eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli
```

### 3.1 Native Python example

```sh
python -m eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli \
  --technology-dointf-input-dir=python:src/product/python.gen \
  --technology-dointf-input-naming-profile=python:config/algites-python-name-conventions.yml \
  --technology-sdointf-output-dir=python:src/product/python.gen \
  --technology-sdointf-output-naming-profile=python:config/algites-python-name-conventions.yml \
  --technology-sdoimpl-output-dir=python:../coreimpl/src/product/python.gen \
  --technology-sdoimpl-output-naming-profile=python:config/algites-python-name-conventions.yml
```

The Python entry point accepts **only `python:`** mappings, and the Java entry
point accepts **only `java:`** mappings. They are separate native executions;
unlike Defs Codegen, an individual SDO batch invocation does not presently
emit both technologies. Python contracts are imported from their source root.
Java contracts and sibling enums are compiled **in memory** with the JDK
compiler, then reflected over using the existing SDO implementation. Neither
technology needs a preceding compilation or packaging task for DO contracts.

### 3.2 Options

| Option | Meaning |
|---|---|
| `--technology-dointf-input-dir=TECH:PATH` | Root of generated read contracts; required except in clean-only mode. |
| `--technology-dointf-input-naming-profile=TECH:PATH` | YAML catalog for recognizing `dointf` filenames and type names. |
| `--technology-sdointf-output-dir=TECH:PATH` | Destination for mutable interface sources. |
| `--technology-sdointf-output-naming-profile=TECH:PATH` | Catalog defining `sdointf` output names. |
| `--technology-sdoimpl-output-dir=TECH:PATH` | Destination for concrete SDO sources. |
| `--technology-sdoimpl-output-naming-profile=TECH:PATH` | Catalog defining `sdoimpl` output names. |
| `--dointf-classpath=PATHS` | **Java only**: OS-path-separated binary dependency classpath (compiled DO contracts are optional). |
| `--check` | Verify generated output without writing/cleaning. |
| `--clean-only` | Remove recognized mutable/concrete output files using output catalogs only; cannot be combined with `--check`. |

The output profiles must include role names
`algites-{java|python}-gen-data-intf-versioned` and
`algites-{java|python}-gen-data-class-versioned`. The input profile must include
`algites-{java|python}-gen-intf-versioned`. Those role identifiers are currently
selected in the SDO CLI. Output roots **may overlap each other and the input
root**, because cleanup is restricted to SDO naming roles. Distinct files must
still match unambiguous whole-file naming conventions.

SDO batch preflights source loading and all generated filename conventions
before cleaning output-role files. Missing or invalid input sources therefore
do not erase previously generated SDO implementations. For Java, preflight
compiles all generated read interfaces and enums together in memory and refuses
to use stale precompiled classes of the same name.

### 3.3 Legacy single-contract invocation

Java:

```sh
java -cp "$CLASSPATH" eu.algites.tool.codegen.sdo.impl.cli.AIcSdoCodegenCli \
  example.contracts.AIigCustomer_1 path/to/mutable.gen path/to/impl.gen d
```

Python:

```sh
python -m eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli \
  example.contracts.aiig_customer_1:AIigCustomer_1 path/to/mutable.gen path/to/impl.gen \
  --marker d
```

`--check` is supported by both; the legacy form does not perform YAML catalog
batch matching. The Python legacy form rejects the same root for both output
roles; the batch form permits shared `.gen` directories with role-based cleanup.

## 4. YAML naming configuration — reference

All catalogs are **data files** interpreted by `pub.lib.General` naming
components. Source schema formats and target languages each have a catalog:

- `standard-conventions.yml`: identifier and version regex patterns.
- `algites-jsondef-name-conventions.yml`, `algites-yamldef-name-conventions.yml`, `algites-xmldef-name-conventions.yml`: input schema filename/type conventions.
- `algites-java-name-conventions.yml`, `algites-python-name-conventions.yml`: output and contract naming conventions.

The catalog schema in `pub.lib.General` is `name-conventions_1` (with the
`standard-conventions_1`, `source-structure-kind_1` and
`container-structure-type_1` companion schemas). The YAML uses:

```yaml
StandardConventionsFile: standard-conventions.yml
NameFragments:
  prefix:
    Segments:
      - Kind: constant_string
        Value: AI
NameCompositions:
  generated-interface-stem:
    Segments:
      - Ref: prefix
      - Kind: constant_string
        Value: ig
      - Kind: identifier
        Convention: upper_camel_case
      - Kind: constant_string
        Value: '_'
      - Kind: version
        Convention: positive_integer
  source-suffix:
    Segments:
      - Kind: constant_string
        Value: .java
NameConventions:
  custom-java-do-interface:
    ContainerStructureType: interface
    StructureNaming:
      main_container_name: generated-interface-stem
      file_name_stem: generated-interface-stem
      file_name_suffix: source-suffix
```

This is an illustrative **custom** profile, not an additional built-in CLI
role. `NameFragments` are reusable sequences; `Ref` expands a sequence with
cycle checking. `NameCompositions` are ordered sequences of `constant_string`,
`identifier`, `version` or named `variable` segments. `NameConventions` map
`source-structure-kind` keys to compositions, plus `ContainerStructureType`.
`file_name_stem` and `file_name_suffix` concatenate **without an implicit dot**;
for example `customer_1` + `.yamldef.schema.json`.

Built-in standard regexes use Java-style named groups such as
`(?<identifier>...)` and `(?<version>...)`; the Python catalog interpreter
translates those to Python-compatible named groups. A segment may specify
`Convention: <standard-id>` or `CustomConventionRegexp: <regex>`.
`variable` segments use `Name` and `Regexp` and support custom captures such
as `major`/`minor`. A catalog provides the operations `matches`, `parse`,
`format`, `convert`, `recognizeFilename`/`recognize_filename`, and `clean`.

**Conversion caveat:** custom regexes provide recognition and extraction; they
do **not** automatically define arbitrary spelling transformations. Automatic
identifier case conversion presently supports the eight standard lexical
conventions (`all_lower`, `all_upper`, snake, camel, kebab variants). Native
Java and Python formatters may differ on edge-case Unicode/acronym handling;
use parity tests when extending a naming catalog. Current code-generation
renderers support the standard Algites versioned role layouts; arbitrary
remapping of custom `major`/`minor` into generated type syntax is not yet a
fully supported codegen feature.

Profile recognition uses the complete filename and requires **exactly one**
matching profile in the considered set. Multiple matches are a configuration
error. The batch generator's cleanup restricts that set to its owned output
roles. Prefix strings alone are never sufficient for cleanup matching.

## 5. Diagnostics and troubleshooting

| Symptom | Meaning / response |
|---|---|
| `Canonical identity collision` | Two definitions would generate the same source path but carry distinct canonical IDs. Align canonical schema IDs or keep output namespaces separate. |
| `Incompatible canonical representations` | Same identity/output but different normalized type contracts. Inspect requiredness, nullability, constraints, reference and enum shape. |
| `Overlapping schema input roots` | The exact same physical file was discovered more than once. Remove the overlapping input-root declaration. |
| `Ambiguous filename` | Multiple naming profiles accept the complete filename. Fix the YAML rules (or select only relevant roles). |
| `Unversioned schema is not allowed` | Schema filename matched a non-versioned profile. Supply a version or opt in with `--allow-unversioned-schemas`. |
| `Cannot resolve generated reference package` | A schema reference does not resolve to one generated contract. Include its schema/input root or repair the reference. |
| `Cannot compile DO sources for SDO reflection` | A source file has a compilation error or an external Java dependency is absent. Supply the dependency through the JVM or `--dointf-classpath`. |
| `Missing or outdated generated ...` | `--check` compared expected output to the filesystem; run a normal generation to update it. |

## 6. Build, tests and migration

The native Java TestNG and Python pytest tests live under
`generators/code/{defscodegen,sdocodegen}/impl/src/develop/`. Regression
coverage includes same-format duplicates across independent input roots,
canonical-ID collisions, incompatible schema shapes, generated-source
preservation on preflight failure, Java/Python type rendering and the
separate SDO stage.

The repository-specific Gradle parity bridges have been retired in the
Phase-0 native Python verification preview. The Builder provides an isolated
virtualenv from native wheels and Python subscriptions and attaches `pytest`
to each artifact `check`; cross-language Java tests receive the same interpreter.
This requires the matching Builder update and an enabled
`MODUSTRO_ENABLE_NATIVE_PYTHON_TESTS` property. Standalone emergency bootstraps
are independent of the normal Modustro verification lifecycle.

The complete snapshot publish/deployment still requires running the actual
JVM/Gradle integration tests in CI with published `pub.lib.General` 1.1-SNAPSHOT.


### User-defined naming variables example

The `pub.lib.General` naming catalog contains a tested pair of files,
`naming/convention/algites/src/product/config/eu/algites/lib/naming/convention/example-input.yml`
and `example-output.yml`. They illustrate the native YAML engine's `variable`
segments and the nested `(?<version>(?<major>...)\.(?<minor>...))` captures.
For example, `customer_address--eu_west--beta--2.7.demo.schema` can be
converted into `AIigCustomerAddress__beta__7-2__eu_west.java` by reordering
`region` and `channel`, switching `identifier` to UpperCamelCase, and reversing
`major` and `minor`. This demonstrates the naming library's capabilities; it
is not a separate code generator or a built-in source schema format.

## 1.1 recursive and XML contract migration

The current staged model, XML element naming `_xe`, closed choices, canonical field presence and explicit limitations are documented in [Defs Codegen recursive types](defscodegen/RECURSIVE-TYPES-AND-XML-ELEMENTS.md). This replaces neither the explicit bootstrap procedure nor the existing source-ownership contracts.


## 5. Recursive canonical contracts and XML-element naming (migration)

The 1.1 canonical model uses only `AIcdDataType` / `AInDataTypeKind` for
recursively nested objects, arrays, reference identities and distinct `ONE_OF`
and `ANY_OF` semantics. The previous `AInDefinitionKind` and `AInValueKind`
are removed, including their redundant canonical property and definition
projections. Source-specific scalar/type hints are normalized inside each
frontend. An unresolved `AIcdDefinitionReference` now carries optional
`targetDataType` instead of a separate `targetKind` projection, with an
unknown target remaining nullable until the reference graph is resolved. **Not every supported recursive shape is yet emitted as a full
Java/Python contract**; unsupported nested structures must fail explicitly.

A top-level finite choice emits a sealed Java contract with one separate
public record per explicitly selected alternative. Python generates frozen
value wrappers. Record names are disambiguated using stable reference
identities; dependencies from other business packages retain their actual
qualified names. Wire-format `oneOf` and `anyOf` validation is not implied by
selecting a programming-language wrapper.

Each global XSD element has its own nominal `AIig_xe...` contract in the
existing business package, with `AIigd_xe...` / `AIcgd_xe...` generated by
SDO Codegen. The Java marker is `_xe`, while Python filenames use an
additional underscore: `aiig__xe_payment_1.py`. The naming catalog contains
separate XML-element interface/class profiles; automatic pattern resolution
must stay unambiguous across **all** active profiles. Users defining different
conventions are responsible for the same uniqueness and reversibility.

The element's XML QName, its content type and optional substitution head are
separate canonical concepts; element interface inheritance preserves supported substitution relationships.
There is no Open Choice annotation or runtime substitution registry.
Named content types are not renamed or moved into artificial Java packages.

The shared field annotation uses `fieldName`, `presence` (REQUIRED,
ALLOWED, FORBIDDEN), and `allowsNull`. XML QName metadata belongs to
`AIaXmlDataObject` and `AIaXmlDataObjectField`, not the shared field annotation.
Java SDO contracts provide `sourceContract` metadata for reflection. For `allOf`,
compatible field presence/nullability restrictions on derived contracts are
kept; incompatible relaxations fail.

The XSD frontend supports named `complexContent` extension with real
Java/Python inheritance for emitted base types, including bases in the same
XSD and local include/import files. It emits all named types, not just the
primary declaration. A conservative flat-sequence restriction subset permits
narrowing particle occurrence bounds and removing optional elements while
preserving order and type. The recursive canonical model records repeated
element cardinalities as array `minItems`/`maxItems`. Same-schema named
`xs:group`/`xs:attributeGroup` references and `xs:element ref` resolve with
cycle guards where applicable. Direct mandatory `xs:choice` generates a closed
typed choice, including global element references within the same schema.
Unsupported nested/repeated compositors, optional multi-field groups,
imported group/element references, wildcards, unrestricted restriction,
`xsi:type` polymorphism and complete `block`/`final` enforcement remain
outside the supported subset and must not be treated as silently equivalent
to valid generated contracts. See
[the technical limits and examples](defscodegen/RECURSIVE-TYPES-AND-XML-ELEMENTS.md).
