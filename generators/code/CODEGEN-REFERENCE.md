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

## 2. Defs Codegen — explicit semantic naming roles

The Java CLI entry point is
`eu.algites.tool.codegen.defs.impl.cli.AIcDefsCodegenCli`; the Python CLI is
`python -m eu.algites.tool.codegen.defs.impl.cli.aic_defs_codegen_cli`.
Both accept the same kebab-case option names. See
[Defs Codegen naming CLI](defscodegen/CLI-NAMING-BATCH.md) for a complete
invocation and the role/configuration contract.

The key distinction is **one repeatable list of naming catalog files**, such
as `--naming-conventions-file=resource:algites-java-name-conventions.yml`,
and **independent mappings of semantic roles to exact convention IDs**:

| Parameter | Meaning |
|---|---|
| `--schema-input-dir=KIND:PATH` | Discover XMLDEFS, YAMLDEFS or JSONDEFS schemas. |
| `--input-schema-naming-convention=KIND:ID` | Convention to parse input schema filenames. |
| `--technology-dointf-output-dir=TECH:PATH` | Generated getter-interface root. |
| `--output-interface-technology-naming-convention=TECH:ROLE:defsintf=ID` | Convention for a specific generated read-interface role. |
| `--output-enum-technology-naming-convention=TECH:ID` | Independent naming for generated enums. |
| `--naming-conventions-file=PATH` | Add a YAML catalog; repeatable, including `resource:NAME`. |
| `--settings-file=PATH` | Load one option per line; explicit options may override matching settings. |
| `--check`, `--clean-only` | Read-only verification or cleanup of generator-owned outputs. |

The getter-interface roles are `common`, `xmldefs_type`, `xmldefs_element`,
`xmldefs_namespace`, `yamldefs` and `jsondefs`, independently for Java and Python.
`xmldefs_namespace` selects a dedicated **unversioned XML namespace interface**
naming profile (type and filename) and is not a separately generated schema
family. It never derives a marker by replacing an XML element prefix. If omitted
by a custom batch manifest, the independent standard XML namespace profile is
used; standard settings supply the mapping explicitly. A missing role
mapping suppresses generation of that role, subject to consistency of
referenced contracts. Standard Algites settings cover all families but do not
restrict custom naming identifiers. Without arguments, Java and Python CLIs respectively select
`algites-defscodegen-java-default.settings` and
`algites-defscodegen-python-default.settings` from their shared `src/product/config`
package folder. The default configuration generates only the corresponding
technology, not both.

A generated contract records the actually selected naming ID in its
DataObject annotation/metadata. When both a common getter interface and a
format-specific getter interface exist, the format-specific interface can
extend the shared contract and a corresponding technology marker.

**Cross-format common-role semantics (1.1):** `common` is a semantic
intersection, not a strict serialization parity assertion. When XML/YAML/JSON
schemas map to the same read-contract name, only fields present in every
representation are emitted on `common`; format-specific fields remain on the
independently named `xmldefs_type`, `yamldefs`, or `jsondefs` interfaces. Shared
fields retain compatible structural kinds and the least restrictive presence
and nullability. Differences in serialization facets are preserved in the
specialized contracts. General `xs:anyType`, scalar-enum projections, and
object/choice representations use an `Any`/`Object` common supertype when the
specialized value types cannot safely share a narrower getter return type.
Incompatible scalar categories (such as `STRING` versus `INTEGER`) fail with
the field path; they are not silently dropped. If an object representation and
a closed-choice representation have no common object structure, the shared
role is an empty semantic marker interface.

For `common` only, the format marker in Algites canonical URNs (`:yamldef:`
or `:jsondef:`) is removed when comparing identity. An XML schema without an
explicit namespace may join such a group only when the normalized Algites
URN ends in the same logical name and version. Unrelated schema identities
remain collisions. Original publication identities are kept in provenance.
The shared role inherits an `allOf` parent only if **every** representation
has the same emitted common parent chain. Other representations keep their
independent technology-specific inheritance. Public definition URLs on the
`defs.dev.algites.eu/api/{kind}/` host resolve to the matching input tree for
cross-file reference qualification, even when the schema has an explicit URN
rather than using the publication URL as its identity.

**XSD documents without `targetNamespace`:** Global XML type and element QNames
are resolved within their defining document when different independent XSDs
reuse the same no-namespace names. Such collisions must not merge unrelated
XML types or direct an element to another document's content type. When a
collision would otherwise produce identical Java/Python output paths, only
the XML-specialized type, element and namespace-marker contracts receive a
stable `xmlschema_<versioned-schema-stem>` subpackage. The shared `common`
contract remains in its existing package. XSDs without conflicting names
retain their original generated paths. Each specialized XML contract keeps
the appropriate document-specific XML namespace-marker inheritance; external
nonempty namespaces continue to use the usual URI-based resolution. Both
implementations have regression tests for the collisions and unchanged paths.

Batch processing retains canonical-source deduplication, format parity and
preflight checks. Cleanup is based on **generator ownership state**, not
regex deletion of all filenames that happen to match a convention. Positional single-definition CLI entry points have been removed; use the
programmatic generator service for individual definitions.

## 3. SDO Codegen — independent input and output mapping

The Java CLI entry point is
`eu.algites.tool.codegen.sdo.impl.cli.AIcSdoCodegenCli`; the Python CLI is
`python -m eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli`.
See [SDO Codegen naming CLI](sdocodegen/CLI-NAMING-BATCH.md).

| Parameter | Meaning |
|---|---|
| `--technology-dointf-input-dir=TECH:PATH` | Source directory of annotated getter interfaces. |
| `--technology-sdointf-output-dir=TECH:PATH` | Mutable-interface output directory. |
| `--technology-sdoimpl-output-dir=TECH:PATH` | Concrete-implementation output directory. |
| `--input-technology-naming-convention=TECH:ROLE:defsintf=ID` | Name parser for read interfaces of a role. |
| `--output-technology-naming-convention=TECH:ROLE:sdointf=ID,sdoclass=ID` | Independent output naming conventions. |
| `--naming-conventions-file=PATH` | Repeatable shared YAML catalog or `resource:NAME`. |
| `--sdointf-subpackage=SUFFIX`, `--sdoclass-subpackage=SUFFIX` | Optional, independent package suffixes; defaults are in settings. |
| `--dointf-classpath=PATHS` | Java input-class dependencies, preserved from the old CLI. |
| `--dointf-input-artifact=PATH`, `--dointf-input-class=TYPE` | Java only: JAR/classdir or class specifically selected for generation. |
| `--settings-file=PATH`, `--check`, `--clean-only` | Settings, verification and cleanup. |

Java SDO uses source compilation/reflection and can also scan full compiled
JARs and class directories. A modular JAR can be loaded for generation as a
classpath artifact; generated sources must still comply with JPMS package
separation during the actual application build. Python SDO imports annotated
classes. Handwritten read interfaces are supported in both languages and
need not use an Algites prefix.

The input naming convention, recorded on an annotated source contract, is
used to reverse-parse its name. No `sourceContract` field is required: Java
inheritance and Python bases already express that relationship.

With zero arguments, each SDO CLI selects its technology-specific settings:
`algites-sdocodegen-java-default.settings` for Java and
`algites-sdocodegen-python-default.settings` for Python; it selects separate `impl.intf` and
`impl` output subpackages to avoid split-package conflicts between different
JPMS modules. As with Defs, missing role mappings mean no output for that
role; IDs in custom catalogs need not carry an `_1` suffix.

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
error. The generator checks paths of generated outputs against its ownership state.
Prefix strings alone are never sufficient for safe cleanup matching.

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
Java SDO contracts provide the direct inherited getter contract for reflection. For `allOf`,
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
