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
The canonical `generators/code/bootstrap.sh` delegates to the shared
`devops/bootstrap/bootstrap.sh --root generators/code` entry point. By default,
it preserves unrelated files in native `.gen` trees, updates generated Defs
contracts before build and recreates `build/run/tool-bootstrap`. **Whole-folder
cleanup is opt-in**, using `--cleanup-output-folder-before-generation=true`
on the universal bootstrap. The `--root` argument narrows the selected source
scope; on cleanup=true, only the selected `src/<branch>/{java,python}.gen` trees
are emptied *before* either Defs or SDO runs. Do not put handwritten sources
in these output trees. The historical `generators/code/bootstrap-selfhosted.sh` is a compatibility
alias for the universal bootstrap, never a second generator implementation.
The old `regenerate_sources.py generate` action also delegates to the current
Defs/SDO CLI. No bootstrap entry point may call `defs.old`.

Common contract identity normalization accepts XML `urn:eu:algites:` namespace
aliases of an explicit dotted JSON/YAML schema ID only where the package,
logical name and version match exactly. A closed choice of string constants
and an XML string project to a common string getter, while the source-specific
choice constraints remain on the format-specific contract.

## 2. Defs Codegen — explicit semantic naming roles

The Java CLI entry point is
`eu.algites.tool.codegen.defs.impl.cli.AIcDefsCodegenCanonicalCli`; the Python CLI is
`python -m eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli`.
Both accept the same kebab-case option names. See
[Defs Codegen naming CLI](defscodegen/DEFS-CODEGEN-REFERENCE.md) for a complete
invocation and the role/configuration contract.

The key distinction is **one repeatable list of naming catalog files**, such
as `--naming-conventions-file:java=classpath:algites-java-name-conventions.yml`,
and **independent mappings of semantic roles to exact convention IDs**:

| Parameter | Meaning |
|---|---|
| `--schema-input-dir:KIND=PATH` | Discover XMLDEFS, YAMLDEFS or JSONDEFS schemas. |
| `--input-schema-naming-convention:KIND=ID` | Convention to parse input schema filenames. |
| `--technology-dointf-output-dir:TECH=PATH` | Generated getter-interface root. |
| `--output-interface-technology-naming-convention:TECH:ROLE:defsintf=ID` | Convention for a specific generated read-interface role. |
| `--output-enum-technology-naming-convention:TECH=ID` | Independent naming for generated enums. |
| `--naming-conventions-file:ENTRY_ID=PATH` | Add a YAML catalog; repeatable, including `classpath:NAME`. |
| `--common-codegen-naming-convention:TECH=ID` | Common getters/setters, CONST and schema metadata naming shared with SDO. |
| `--defs-codegen-naming-convention:TECH=ID` | Defs-only synthetic type/enum naming; linked to the Common profile. |
| `--settings-file=PATH` | Overlay an invocation settings file on bundled and classpath defaults; explicit CLI arguments override matching keys. |
| `--check`, `--clean-only` | Read-only verification or explicitly removing previously indexed generator-owned outputs. |
| `--cleanup-output-folder-before-generation=true|false` | Default `false`: replace only files generated now; `true`: additionally remove obsolete indexed outputs owned by this generator. |

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
`defscodegen-java-default.settings` and
`defscodegen-python-default.settings` from their shared `src/product/config`
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
See [SDO Codegen naming CLI](sdocodegen/SDO-CODEGEN-REFERENCE.md).

| Parameter | Meaning |
|---|---|
| `--sdo-input-paths:TECH=LIST` | Source directories, individual files or compiled input archives selected for generation. |
| `--sdo-input-artifacts:TECH=LIST` | Maven/Python input distributions selected for generation. |
| `--sdo-dependency-paths:TECH=LIST` | Supporting source/classpath dependencies, never automatic generation inputs. |
| `--sdo-dependency-artifacts:TECH=LIST` | Packaged dependencies used only for resolution. |
| `--dointf-input-classes:TECH=LIST` | Optional filter of explicitly selected contracts. |
| `--technology-sdointf-output-dir:TECH=PATH` | Mutable-interface output directory. |
| `--technology-sdoimpl-output-dir:TECH=PATH` | Concrete-implementation output directory. |
| `--dointf-naming-convention:TECH=ID`, `--sdointf-naming-convention:TECH=ID`, `--sdoimpl-naming-convention:TECH=ID` | Independent, schema-neutral input and output naming roles. |
| `--naming-conventions-file:ENTRY_ID=PATH` | Shared and generator-specific catalog or `classpath:NAME`. |
| `--common-codegen-naming-convention:TECH=ID` | Common naming profile. |
| `--sdo-codegen-naming-convention:TECH=ID` | SDO-specific naming profile, linked to Common. |
| `--sdointf-subpackage=SUFFIX`, `--sdoclass-subpackage=SUFFIX` | Optional package suffixes. |
| `--settings-file=PATH`, `--check`, `--clean-only` | Layered settings, verification, owned-output cleanup. |
| `--cleanup-output-folder-before-generation=true|false` | Optional removal of obsolete files owned by this Codegen (default `false`). |

A direct `.java` or `.py` input selects that file alone; a directory
selects eligible annotated contracts beneath it. File names never establish
SDO eligibility; the input must carry the common DataObject metadata or
inherit them from its neutral parent.

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
`sdocodegen-java-default.settings` for Java and
`sdocodegen-python-default.settings` for Python; it selects separate `impl.intf` and
`impl` output subpackages to avoid split-package conflicts between different
JPMS modules. As with Defs, missing role mappings mean no output for that
role; IDs in custom catalogs need not carry an `_1` suffix.

**Split codegen catalog entries:** Defs uses `codegen_common` plus
`codegen_defs`; SDO uses `codegen_common` plus `codegen_sdo`. These entries
refer to separate files (`*-common-codegen-conventions.yml`,
`*-defs-codegen-conventions.yml`, `*-sdo-codegen-conventions.yml`). Each native
CLI selects both matching profile IDs for its technology, and validates
`CommonNamingConvention`. The Algites, Standard Prefix and Standard Postfix
Java/Python `.settings` files use this layout. The older combined method
profile is not selected by these stock settings.

## 4. YAML naming configuration — reference

All catalogs are **data files** interpreted by `pub.lib.General` naming
components. Source schema formats and target languages each have a catalog:

- `standard-conventions.yml`: identifier and version regex patterns.
- `algites-jsondef-name-conventions.yml`, `algites-yamldef-name-conventions.yml`, `algites-xmldef-name-conventions.yml`: input schema filename/type conventions.
- `algites-java-name-conventions.yml`, `algites-python-name-conventions.yml`: output and contract naming conventions.

The shared catalog is described by `common-naming-conventions_1`, with
`standard-conventions_1` and the specialized source-structure/DO/SDO schemas.
XSD is the reference for collection structure. JSONDEFS and YAMLDEFS use the
same named-list model. An illustrative input profile looks like:

```yaml
StandardConventionsFile: standard-conventions.yml
NameFragments:
  NameFragment:
    - name: prefix
      Segments:
        - NameFragmentsSegmentValue:
            Kind: constant_string
            Value: AI
NameCompositions:
  NameComposition:
    - name: generated-interface-stem
      Segments:
        - NameFragmentsSegmentReference:
            Ref: prefix
        - NameFragmentsSegmentValue:
            Kind: constant_string
            Value: ig
        - NameFragmentsSegmentValue:
            Kind: identifier
            Convention: upper_camel_case_1
SourceStructureNameConventions:
  NameConventions:
    NameConvention:
      - name: custom-java-do-interface
        ContainerStructureType: interface
        StructureNaming:
          Rule:
            - kind: type_name
              Value: generated-interface-stem
            - kind: file_name_stem
              Value: generated-interface-stem
```

This is an illustrative custom profile, not a stock CLI profile. All named
entries carry an explicit `name`; roles use an explicit `kind` and `Value`.
The Java/Python resolvers index these lists internally and reject duplicate
identifiers. `NameFragments` are reusable ordered sequences; `Ref` expands a
sequence with cycle checking. `NameCompositions` preserve ordered
`NameFragmentsSegmentValue` and `NameFragmentsSegmentReference` alternatives.
Metadata fields of DataObject source/instance schemas live in the separate
DataObject naming profiles, not in the source-structure profile.

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
The transient indexes are per artifact, language and producer (Java/Python and
Defs/SDO) under `build/`. Output files are in the configured `*.gen` trees.
The default does **not** scan those trees and delete files that were absent
from the current generation. For example, a former `AIigOld_1.java` remains
until generator-owned cleanup with an available historical index or explicit
bootstrap folder cleanup. `--check` compares current expected files without
modifying either output or index; it cannot be combined with cleanup=true.
Refer to the two generator-specific reference files for publication guarantees
and the difference between clean-only and full bootstrap cleanup.

## 5. Diagnostics and troubleshooting

| Symptom | Meaning / response |
|---|---|
| `Canonical identity collision` | Two definitions would generate the same source path but carry distinct canonical IDs. Align canonical schema IDs or keep output namespaces separate. |
| `Incompatible canonical representations` | Same identity/output but different normalized type contracts. Inspect requiredness, nullability, constraints, reference and enum shape. |
| `Overlapping schema input roots` | The exact same physical file was discovered more than once. Remove the overlapping input-root declaration. |
| `Ambiguous filename` | Multiple naming profiles accept the complete filename. Fix the YAML rules (or select only relevant roles). |
| `Unversioned schema is not allowed` | Schema filename matched a non-versioned profile. Supply a version or opt in with `--allow-unversioned-schemas`. |
| `Cannot resolve generated reference package` | A schema reference does not resolve to one generated contract. Include its schema/input root or repair the reference. |
| `Incompatible resolved pub.lib.General_data.dataobject.intf:1.1-SNAPSHOT` | Codegen requires `AInFieldSetterInheritancePolicy` and `setterInheritancePolicy()` on both `AIaDataObject` and `AIaDataObjectField`. A resolved 1.1-SNAPSHOT may be older despite having the expected Maven version. In remote dependency mode publish the updated `pub.lib.General` to Cloudsmith before retrying; `--refresh-dependencies` cannot supply API absent from the remote artifact. Alternatively select source mode with a current sibling `pub.lib.General` checkout, which publishes the updated library to Maven Local before building generators. |
| `Cannot compile DO sources for SDO reflection` | A source file has a compilation error or an external Java dependency is absent. Supply the dependency through the JVM or `--dointf-classpath`. |
| `Missing or outdated generated ...` | `--check` compared expected output to the filesystem; run a normal generation to update it. |

## 6. Build, tests and migration

The native Java tests use TestNG exclusively. TestNG tests in both `impl` and
`cli` artifacts are discovered and executed by the Gradle `test` tasks; Java
regression classes are not executable test `main` programs. The Defs Java/Python
parity test is a TestNG test that produces its JVM reference outputs in the
same Gradle test JVM and invokes the Python parity assertions as part of that
TestNG test. SDO native Python pytest tests are also wired into the standalone
bootstrap Gradle test lifecycle.

The native Java TestNG and Python pytest tests live under
`generators/code/{defscodegen,sdocodegen}/impl/src/develop/`, with additional
Java CLI tests in the corresponding `cli/src/develop/java` trees. Regression
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
`naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/example-input.yml`
and `example-output.yml`. They illustrate the native YAML engine's `variable`
segments and the nested `(?<version>(?<major>...)\.(?<minor>...))` captures.
For example, `customer_address--eu_west--beta--2.7.demo.schema` can be
converted into `AIigCustomerAddress__beta__7-2__eu_west.java` by reordering
`region` and `channel`, switching `identifier` to UpperCamelCase, and reversing
`major` and `minor`. This demonstrates the naming library's capabilities; it
is not a separate code generator or a built-in source schema format.

## 1.1 Unified read-only DataObject contracts

The active Defs Codegen emits one read-only `AIig…` contract for each
canonical semantic definition, irrespective of the source XMLDEFS, JSONDEFS
or YAMLDEFS technology. The same contract can carry independent schema and
wire-format metadata for each applicable technology. No separate inheritance
projection is created simply to distinguish wire formats.

Nested objects, sequences, references, scalar constraints and closed choices
are represented by the shared canonical model. An explicitly declared closed
choice uses a sealed Java interface with selected records and the corresponding
Python typed selection wrappers. These structural alternatives are not
standalone mutable SDO contracts without shared DataObject metadata.

XML QName, substitution and element-level wire metadata belong to the XML
annotations of the owning shared DataObject. They must not cause additional
technology-specific contract interfaces or a parallel writable hierarchy.

See [Defs Codegen reference](defscodegen/DEFS-CODEGEN-REFERENCE.md) for
validation and the supported recursive forms; see
[SDO Codegen reference](sdocodegen/SDO-CODEGEN-REFERENCE.md) for writable
contracts derived only from eligible annotated read-only DataObjects.

The shared field annotation uses `dataFieldName`, `presence` (REQUIRED,
ALLOWED, FORBIDDEN), and `allowsNull`. XML QName metadata belongs to
`AIaDataObjectXmlSchema` and `AIaDataObjectFieldXmlSchema`, not the shared field annotation.
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
[the technical limits and examples](defscodegen/DEFS-CODEGEN-REFERENCE.md).

## Writable setter parameter inheritance (1.1)

`pub.lib.General/data/dataobject/intf` publishes
`AInFieldSetterInheritancePolicy`, with values `DEFAULT`,
`INHERIT_AS_GENERIC_PARAMETER`, and `INHERIT_AS_FIXED_PARAMETER`.
Both the Java `@AIaDataObject` and `@AIaDataObjectField` annotations and their
Python descriptor counterparts carry `setterInheritancePolicy` /
`setter_inheritance_policy`. An explicit field value takes precedence over the
contract value. `DEFAULT` defers to a generation-time setting; the emitted
read-only contracts record the effective policy for consumption by another
artifact. The built-in effective default is `INHERIT_AS_GENERIC_PARAMETER`.

Native Defs and SDO Codegen now resolve one unified `.settings` hierarchy:

1. Packaged `algites-{defs|sdo}codegen-{java|python}-default.settings`, with
   `--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER`.
2. **All** classpath/package resources named
   `algites-{defs|sdo}codegen-{java|python}.settings`, combined by complete key.
   Java enumerates all `ClassLoader.getResources` results; Python combines
   `importlib.resources` with every matching `sys.path` directory. Earlier
   classpath/sys.path entries have higher priority for duplicate keys; unique
   entries from lower-priority sources are retained.
3. An optional `--settings-file=PATH` for the concrete invocation.
4. Explicit CLI options for the concrete invocation.

The complete key before `=` determines override identity, including colon-
separated qualifiers such as `--schema-input-dir:yamldefs` or
`--naming-conventions-file:standard`. An empty value deletes the inherited
entry. Repeatable options carry a stable entry ID. `classpath:NAME` locates a
packaged naming catalog; a bare value denotes a filesystem path. The previous
unqualified CLI syntax remains accepted for compatibility and is normalized
before merging. A missing configured source directory is logged and skipped;
when none of the configured source roots exist, no generated files are touched.

The source annotation's explicit type/field policies take precedence over all
CLI and `.settings` layers. The SDO CLI applies its policy default only to
otherwise unspecified handwritten DataObject contracts; it never overwrites
explicit policy metadata from Defs Codegen or a parent contract. Programmatic
service calls without CLI settings retain a generic-inheritance fallback.
`DEFAULT` is not a valid effective generator setting. No additional
`.properties` policy configuration is used.

Handwritten read contracts may declare the policy directly; this release does
not define a new schema-language extension for per-property overrides in XSD,
JSON Schema, or YAML Schema.

For Java, **every active Defs Codegen emitter** publishes covariant read-only
collection getters `List<? extends Value>` and
`AIiMultiMappedList<? extends Value>`, also in technology-specific and nested
arrays, not only in common projected contracts. Direct named collection
interfaces themselves may extend `AIiMultiMappedList<Value>` because Java
forbids wildcards in an interface supertype declaration; that is not a getter. The mutable `AIigd`
interface introduces a type variable for each reference-valued field whose
setter policy is `INHERIT_AS_GENERIC_PARAMETER`; its getter and setter share
that variable, including `List<? extends TVariable>` for repeated values.
The variable is bounded by the generated **technology-specific mutable**
contract, selected through the naming catalog rather than inferred by
concatenating marker strings. Descendant mutable contracts extend every
corresponding parent mutable contract and propagate or narrow inherited type
variables, including Java diamonds/multiple inheritance. A `FIXED` field does
not introduce a variable: its inherited setter remains callable with the
published parameter type, so an incompatible refined getter in a descendant
is rejected before generation. No unchecked bridge setter is generated.

A concrete `AIcgd` implementation fixes its writable generic arguments to
its matching technology-specific mutable field contracts. Concrete-class
inheritance is retained when the inherited field types are unchanged. When a
narrowing would conflict with a concrete ancestor's already-specialized type
arguments, the concrete class instead extends the technology-specific SDO
base and implements all inherited fields directly. The *mutable-interface*
inheritance still retains all parent edges. Python emits corresponding
`typing.Generic`/`TypeVar`-based writable interfaces and concrete
specializations; its runtime does not itself enforce static typing.

The setter policy controls the signature and substitutability of a setter,
not whether a Java method literally ceases to be inherited. Setter input
validation remains the responsibility of the SDO runtime. When introducing
new descendants in another artifact, consumers must compile against the
published read contracts and mutable parent interfaces rather than
reinterpreting local generator defaults for an already-published parent.

## Portable classpath catalog locations

`--naming-conventions-file:ENTRY_ID=classpath:NAME.yml` selects a naming
catalog from **every** matching Java classloader resource or Python source.
Python searches package resources through `importlib.resources` and also scans
all direct `sys.path` directories. Catalogs are **combined**, not replaced:
each distinct file contributes its naming definitions. Identical shared
identifiers are deduplicated; conflicting definitions of the same naming ID
are rejected by the naming catalog loader rather than silently overridden.
A relative filesystem path without a prefix remains relative to the repository.

Python reads referenced sibling catalogs such as `StandardConventionsFile`
from the same source as the referring YAML file, including ZIP resources.
Java uses each resource's own JAR/directory for referenced sibling catalogs.
Classpath references accept only a simple YAML filename, not path traversal.
The previous `resource:NAME.yml` spelling remains a compatibility alias.

### Deferred: XML round-trip for repeated `xs:choice`

The Defs frontends and contract generators can represent repeated XML choices
as collections of generated `ParentTypeChoice1`, `ParentTypeChoice2`, etc.
This is **not yet a complete XML runtime feature**: Java and Python
SmartDataObject marshalling/unmarshalling must dispatch each collection item
by its own QName and preserve order, cardinality and variants. Complete the
cross-language XML round-trip and invalid-input tests before declaring this
feature supported end-to-end. This is independent of the Security
`ProfileType` XSD 1.0 `xs:all` contract.


## Qualified artifact inputs (1.1-SNAPSHOT)

See [CODEGEN-ARTIFACT-INPUTS.md](CODEGEN-ARTIFACT-INPUTS.md). Qualified
parameter names are now parsed directly without the obsolete kind:value
conversion. Artifact selector lists use semicolons, and fully specified lists
replace earlier values under the same qualified key.
