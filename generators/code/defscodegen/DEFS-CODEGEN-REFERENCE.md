# Defs Codegen — referenční příručka (1.1-SNAPSHOT)

> **Platnost a zdroje pravdy.** Tento dokument konsoliduje funkční specifikace a
> ověřená omezení implementací Java/Python; původní přechodové poznámky a lokální
> Přechodné stavové dokumenty nejsou autoritativními příručkami. Produkční build
> dosud používá `defs.old`, zatímco nový sedmidruhový kanonický backend běží
> samostatně a je zčásti experimentální. Zde popsaná zamýšlená sémantika není
> automaticky důkazem podpory každého vstupu v novém backendu.
>
> **Aktualizace při změně funkcionality:** upravit tento soubor a úvodní
> `README.md`; nevytvářet další migrační/statusové `.md` dokumenty.

## Obsah

1. [Účel, hranice a aktuální stav](#účel-hranice-a-aktuální-stav)
2. [Kanonický model a realizace](#kanonický-model-a-realizace)
3. [CLI a názvosloví](#cli-a-názvosloví)
4. [Vstupní formáty a emise rozhraní](#vstupní-formáty-a-emise-rozhraní)
5. [Kolekce, klíče, volby a XML](#kolekce-klíče-volby-a-xml)
6. [Dialekty a vlastní slovník](#dialekty-a-vlastní-slovník)
7. [Java/Python parita a testování](#javapython-parita-a-testování)
8. [Omezení a publikační pravidla](#omezení-a-publikační-pravidla)

## Účel, hranice a aktuální stav

Defs Codegen zpracovává definice **XMLDEFS / JSONDEFS / YAMLDEFS** a vytváří
**pouze read-only** anotovaná DataObject rozhraní (`AIig*`, případně výčtové
`AIng*`) pro Javu a Python. Není to generátor implementací. Zapisovatelná
`AIigd*` a implementace `AIcgd*` vytváří nezávislý **SDO Codegen** ze vzniklých
rozhraní, případně ze stejně anotovaných ručně napsaných kontraktů. SDO nesmí
přijímat schémata ani znát interní kanonický model Defs.

**Tři různé rozsahy, které nelze zaměňovat:**

| Vrstva | Aktuální skutečnost | Ověření / mezera |
| --- | --- | --- |
| `defs.old` | Dosavadní produkční Java/Python implementace, rozsáhlejší historická podpora XSD | Zachována; nepřepínat bootstrap bez regrese |
| Nový Python kanonický backend | Sedm kindů, merger/linker/normalizátor/emitter nad *generovanými* SDO objekty | Ověřeny cílené JSON/YAML/XML → Defs → samostatný SDO průchody; konstrukční adaptér zatím existuje |
| Nový Java kanonický backend | Frontend, merger, linker, emitter a read-only DataObject výstup | Interně stále používá ruční `AIcdDefsCodegen*` recordy; celý build a SDO průchod neověřeny |
| Produkční builder | Univerzální bootstrap `devops/bootstrap` | Zatím neprovádět migraci na budoucí `model.schema`/`.do`/`.sdo` |

**Budoucí (dosud neimplementované) uspořádání artefaktů:**
`model.schema → model.do → model.sdo` jako produktové API závislosti,
`intf → model.do`, `impl → model.sdo`; vyžaduje obecnou fázi generování v
builderu 1.1. V tomto snapshotu se soubory nepřesouvají a bootstrap se nemění.

## Kanonický model a realizace

Schémata modelu jsou autoritativní. Sedm strukturálních kindů je `TYPE`,
`ELEMENTLIST`, `ELEMENT`, `LIST`, `MAP`, `SCALAR`, `ENUM`; `REFERENCE` a
`UNDEFINED` jsou pouze dočasné stavy. Vstupní vazby `sourceBindings` musí
uchovat všechny vazby ke konkrétním zdrojovým formátům, identitám a pointerům.
Generator nepřevádí neznámou sémantiku na `ANY` bez explicitního odmítnutí.

Generované kanonické read-only typy jsou v
`intf/src/product/{java,python}.gen`; Python generované interní SDO objekty
jsou v `impl/src/product/python.gen`. Do žádného `.gen` zdroje se ručně
nezasahuje. Python již nepoužívá vlastní `canonical_model.py`, Java nadále
používá staré ruční recordy jako přechodný interní model. Nejde o finální stav.

Příklady regenerace / kontroly (se zavedenými zdrojovými závislostmi):

```sh
python devops/bootstrap/generate-canonical-contracts.py --source-dependencies --check
python generators/code/defscodegen/impl/src/develop/python/regenerate_sdo_canonical_fixtures.py --production --check
```

Vstupní schémata a nová rozhraní musejí být oddělena od interních objektových
instancí; první fáze nevytváří writable třídy ani nespouští SDO uvnitř Defs.

## CLI a názvosloví

Parametry jsou kvalifikované podle technologie a sémantické role, vrstvené
settings soubory se **slučují** podle úplného kvalifikovaného klíče. Nové
oddělené profily Common/Defs (pro Javu nebo Python) jsou výchozí konfigurací;
smíšený `--generated-dataobject-method-naming-convention` je pouze přechodná
kompatibilita starších volajících. Pro běžný Defs Java profil:

```text
--naming-conventions-file:codegen_common=classpath:algites-java-common-codegen-conventions.yml
--naming-conventions-file:codegen_defs=classpath:algites-java-defs-codegen-conventions.yml
--common-codegen-naming-convention:java=algites-java-codegen-common_1
--defs-codegen-naming-convention:java=algites-java-defscodegen-standard_1
```

Pro Python platí analogické `:python` a `algites-python-*`. Defs nesmí číst
`codegen_sdo` profil. `CommonNamingConvention` uvnitř Defs profilu se musí
shodovat s výběrem společného profilu. Další vstupy/výstupy a experimentální
native manifest popisují následující kapitoly.


## Kvalifikované dávkové CLI, vrstvení settings a katalogů

**Rozsah:** historický produkční CLI a shodné kvalifikované volby; příklady s `.old` odkazují na dosud používanou produkční implementaci.

The Java and Python native CLIs accept the same **kebab-case** batch options.
Both native CLIs always resolve layered settings: a packaged language-specific
`defscodegen-LANGUAGE-default.settings`, then one selected classpath profile overlay
`defscodegen-LANGUAGE.settings` (never a mixture of installed profile families),
then `--settings-file=PATH`, then explicit CLI arguments. Complete qualified setting keys are overlaid as a
stable ordered map. An empty assignment removes the inherited entry.

### Input and output mapping

```sh
python -m eu.algites.tool.codegen.defs.old.impl.cli.aic_defs_codegen_cli \
  --repository-root=. \
  --schema-input-dir:jsondefs=src/product/jsondefs \
  --input-schema-naming-convention:jsondefs=my-schema-naming \
  --technology-dointf-output-dir:python=src/product/python.gen \
  --output-interface-technology-naming-convention:python:jsondefs:defsintf=my-contract-naming \
  --output-enum-technology-naming-convention:python=my-enum-naming \
  --naming-conventions-file:standard=config/standard.yml \
  --naming-conventions-file:project=config/project.yml
```

`--schema-input-dir:KIND=PATH` accepts `xmldefs`, `yamldefs` and `jsondefs`
input roots. A configured input directory which does not exist is reported
informationally and skipped; the other existing roots are still processed.
If all roots are absent, generation is a non-destructive no-op.
`--input-schema-naming-convention:KIND=ID` chooses the profile for an input
schema kind. `--output-interface-technology-naming-convention:TECH:ROLE:defsintf=ID`
chooses a generated getter-interface profile for each target technology
(`java`, `python`) and semantic role (`common`, `xmldefs_type`,
`xmldefs_element`, `xmldefs_namespace`, `yamldefs`, `jsondefs`). `--output-enum-technology-naming-convention:TECH=ID`
configures enums independently.

`--naming-conventions-file:ENTRY_ID=LOCATION` adds one identifiable entry to the
combined catalog. `ENTRY_ID` is a stable configuration-entry key; settings
layers can override or remove a catalog by this key. `LOCATION` is either a
filesystem path or `classpath:NAME` for a packaged naming catalog. The
`classpath:` prefix is used to distinguish classpath/package resources
from paths relative to the target repository. Each ID is
looked up in that catalog. File locations and naming IDs are independent.
Conflicting definitions of one ID are rejected; identical repeated definitions
can be merged. No generator requires a particular syntax for user-defined IDs;
Algites chooses `_1` in its supplied catalog as a library-versioning policy.

### Separate Common and Defs codegen conventions

Defs Codegen selects **two independent naming profiles** in addition to its
source-schema and output-interface naming profiles. For example, the Algites
Java codegen profile uses:

```text
--naming-conventions-file:codegen_common=classpath:algites-java-common-codegen-conventions.yml
--naming-conventions-file:codegen_defs=classpath:algites-java-defs-codegen-conventions.yml
--common-codegen-naming-convention:java=algites-java-codegen-common_1
--defs-codegen-naming-convention:java=algites-java-defscodegen-standard_1
```

Use `:python` and the corresponding `algites-python-*` resources and IDs for
Python. The `CommonCodegenNameConventions` section provides shared getter,
setter, synthetic multi-mapped/positional accessors, CONST naming and schema
metadata mappings. `DefsCodegenNameConventions` provides **only** Defs-specific
synthetic type and enum-item naming roles. Its `CommonNamingConvention` property
must refer to the selected Common profile. The generator rejects a missing
partner, an incorrect profile family, or a missing `codegen_common` or
`codegen_defs` catalog entry. The Defs generator never loads SDO-specific roles.

For older callers, `--generated-dataobject-method-naming-convention:TECH=ID`
remains an explicit transitional alternative, but **must not** be combined with
the new profile pair. All stock `*.settings` profiles use the new pair.

**A missing output-role naming ID means that a contract family is not generated.**
The `xmldefs_namespace` role is different: it configures the names of auxiliary
XML namespace interfaces, which are emitted when XML contracts need them,
not as a separate contract family. When XML namespace support is requested, the active profile must explicitly
provide the corresponding naming role; no Algites naming convention is selected
implicitly. Namespace type names and file stems are rendered through that
selected profile;
no `_xe`/`_x` text replacement is performed. If two
configured roles would create the same relative output path, generation must
fail instead of overwriting a different contract. The input-schema ID and
required dependency roles still have to resolve. If a common getter and a
technology-specific getter are both enabled, the latter can extend the common
contract and its technology marker interface.

Outputs embed the exact selected naming ID in `@AIaDataObject.namingConvention()`
(Java) or `AIcdDataObject.naming_convention` (Python). The generated sources
remain owned by the generator; their directory trees must not be manually
patched. Generated-file ownership state protects unrelated files during
regeneration and `--clean-only`. `--check` compares without writing.

### Layered settings

The four precedence levels are: packaged `defscodegen-java-default.settings`
(or Python), one explicitly selected `defscodegen-java.settings` (or Python)
profile family from available classpath resources, `--settings-file`, and direct
CLI parameters. Multiple installed naming profile families are alternatives,
not cumulative layers. Without an unambiguous selection the CLI rejects the
configuration instead of mixing Algites with Standard Prefix/Postfix. Settings are merged
using the **entire key before `=`**, including qualifiers separated by `:`.
The higher layer wins; `--key=` removes an inherited entry. Repeatable options
such as `--naming-conventions-file:standard=...` have individually named keys.
Boolean options accept `--check=true` / `--check=false` (bare `--check` is
accepted as `true`). The old `--schema-input-dir=KIND:PATH` translation is removed. All
technology and role qualifiers remain part of the option name until consumed
by the native CLI parser.

The neutral generator defaults do not select naming catalogs. The external
codegen profile supplies the `classpath:...` resources and semantic roles. The
setting `--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER` may be
changed by any higher layer to `INHERIT_AS_FIXED_PARAMETER`; there are no
separate `.properties` defaults. It is emitted into the generated read-only
contract's field and type metadata. Explicit model metadata still wins.
Native Java/Python SDO generation also requires an explicitly selected naming
profile, including for handwritten contracts without annotations.

Positional legacy CLI invocations are not accepted. Programmatic calls use
the service API and require explicit naming information; only the configured setter-inheritance
policy has its documented generic-parameter default.

### Portable classpath catalog locations

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


### External schema resources

Use `--defs-input-artifacts:java=group:artifact:version;...` or
`--defs-input-artifacts:python=distribution>=version;...` to select packaged
XMLDEFS, YAMLDEFS, and JSONDEFS source schemas. See
[CODEGEN-ARTIFACT-INPUTS.md](../CODEGEN-ARTIFACT-INPUTS.md) for Modustro
selectors, PEP 508 constraints and source bootstrap requirements.


## Nový kanonický kompilátor a manifestové CLI

**Rozsah:** explicitně zvolený (dosud neprodukční) kanonický backend. Nejprve porovnat podporovaný rozsah; není náhradou všeho, co umí `.old`.

The canonical compiler is an **experimental, explicitly selected** replacement path for a subset of Defs contracts. It uses the independent Java and Python canonical schema frontends, model merger, reference linker and generated-schema validation, followed by a native source emitter. It does **not** call the `defs.old` backend. The historical bootstrap/production CLI is **not switched** by this feature; do not substitute it until the complete public API and SDO interoperability have been tested.

### What it currently emits

- Java interfaces and Python typed abstract interfaces for supported object declarations, preserving source member names through explicitly selected getter/setter naming rules.
- Named reference properties (including recursive references), schema inheritance, unconstrained arrays and supported maps.
- String, boolean and arbitrary-precision integer enums, preserving their typed values and lexical source codes in the canonical model. Java integer enums expose `BigInteger code()`; Python uses integer-valued `Enum` members. Decimal-number enums are rejected until source parsing can preserve exact numeric precision.
- Exclusive scalar and supported structured `oneOf` choices represented as Java `sealed interface` with same-package `record` variants and Python frozen dataclass variants marked `@final` (a static typing restriction, not a runtime-sealed hierarchy). Structured variants preserve member ordering and catalog-derived typed getters. Their private component names (`field1`, `field2`, etc.) are stable storage positions; required values are checked in variant constructors, while optional members can be `null` / `None`.
- Java and Python outputs separately named through their own selected Common + Defs naming profiles and the external Algites source-code naming catalogs.
- A deliberately restricted form of **local XMLDEFS `xs:key` / `xs:unique` on an inline complex-type container**: a direct repeated child is emitted as `AIiMultiMappedList<T>`, with repeatable `AIaXmlKeyDefinition` annotations on the Java getter and matching `__xml_key_definitions__` metadata on the Python interface. Composite keys and nested element paths (for example `identity/code` → `identity.code`) are supported when every segment resolves to a generated typed field. Keyed lists must have named structured items and cardinality `0..unbounded`. Python XMLDEFS interfaces also emit inherited `__xml_repeated_fields__` metadata for their direct LIST members; unlike `list`, `AIiMultiMappedList` cannot be inferred as a repeated XML field solely from its generic return type. The independent SDO Codegen must expose an `AIiMultiMappedList`-compatible field descriptor rather than the ordinary `list` type. JSONDEFS and YAMLDEFS interfaces do not emit XML-specific repetition metadata.

**Unsupported inputs are rejected rather than approximated.** In particular, nested/repeated choice groups, bounded arrays whose constraints cannot be preserved by these contracts, decimal-number enums, **XSD `xs:keyref`, global-element keys, XML attribute paths (`@...`), namespace-qualified/descendant/predicate XPath selectors, keys on non-inline or non-direct collections**, unsupported JSON Schema validations, and unrestricted SDO accessor/lifecycle generation are not yet supported. Generated output should not be treated as a drop-in replacement for the previous code generator.

### Independent SDO Codegen

This Defs CLI generates only DataObject interfaces. It does not generate mutable
SDO sources and it never consumes SDO naming conventions. Writable interfaces
and concrete implementations are generated by the separate SDO Codegen from
DataObject interfaces, whether they were generated by Defs or written by hand.
The SDO CLI accepts interface sources/artifacts, not Defs input schemas or the
Defs canonical model. The current canonical Defs CLI remains opt-in during
refactoring; the production CLI contract is unchanged.

### Manifest and invocation

Use a JSON manifest, committed alongside the inputs, with paths to explicitly selected source schemas and catalogs. All `inputs[].path` and `output_dirs` entries are relative to `repository_root`; other catalog/schema paths may be absolute or relative to the manifest's directory. The input extension must match its declared technology.

```json
{
  "repository_root": "/absolute/path/to/consumer-repository",
  "canonical_schema": "/absolute/path/to/pub.tool.General/generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json",
  "inputs": [
    {"kind": "jsondefs", "path": "intf/src/product/jsondefs/example/api/records_1.jsondef.schema.json"}
  ],
  "profiles": {
    "java": {
      "common_file": "/absolute/path/to/pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-java-common-codegen-conventions.yml",
      "common_id": "algites-java-codegen-common_1",
      "defs_file": "/absolute/path/to/pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-java-defs-codegen-conventions.yml",
      "defs_id": "algites-java-defscodegen-standard_1",
      "sourcecode_catalog": "/absolute/path/to/pub.lib.General/naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-java-name-conventions.yml"
    },
    "python": {
      "common_file": "/absolute/path/to/pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-common-codegen-conventions.yml",
      "common_id": "algites-python-codegen-common_1",
      "defs_file": "/absolute/path/to/pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-defs-codegen-conventions.yml",
      "defs_id": "algites-python-defscodegen-standard_1",
      "sourcecode_catalog": "/absolute/path/to/pub.lib.General/naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-name-conventions.yml"
    }
  },
  "output_compositions": {
    "java": {
      "interface": "algites-java-gen-intf-versioned_1",
      "interface_file": "algites-java-gen-intf-versioned-file_1",
      "enum": "algites-java-gen-enum-versioned_1",
      "enum_file": "algites-java-gen-enum-versioned-file_1"
    },
    "python": {
      "interface": "algites-python-gen-intf-versioned_1",
      "interface_file": "algites-python-gen-intf-versioned-file_1",
      "enum": "algites-python-gen-enum-versioned_1",
      "enum_file": "algites-python-gen-enum-versioned-file_1"
    }
  },
  "output_dirs": {
    "java": "intf/src/product/java.gen",
    "python": "intf/src/product/python.gen"
  },
  "package_name": "example.api",
  "versions": {"*": "1"}
}
```

Set `PYTHONPATH` to include `src/product/python` for `generators/code/common`, `generators/code/defscodegen/intf`, `generators/code/defscodegen/impl`, `generators/code/defscodegen/cli`, and the necessary `pub.lib.General` naming package directories. With the CLI module on this path, run:

```sh
python -m eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli --manifest canonical-defscodegen.json
python -m eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli --manifest canonical-defscodegen.json --check
```

The CLI validates the complete batch before publication and records owned files and SHA-256 checksums in `build/run/canonical-defscodegen/generated-files.json`. It refuses to overwrite unowned or independently modified outputs; `--check` verifies generated files and ownership without changing them. The publisher stages all outputs and keeps on-disk backups until the ownership manifest has been replaced. An ordinary filesystem exception during publication triggers best-effort restoration of the prior owned files; this behavior has fault-injection regression tests for partial replacement and manifest write failure. **It is still not an atomic multi-file transaction**: power loss, process termination, or a failed rollback can leave a partial update. Run against disposable/staged target repositories first.

A native Java programmatic compiler service is also available as `AIcDefsCodegenCanonicalCompiler`, accepting Java/Python resolved naming profiles, an explicit JSON Schema validation callback, source documents and output compositions; it returns source units without writing files.

### Verification and migration criteria

Before replacing production CLI or bootstrap tasks, the canonical backend must implement and test the complete Defs/SDO contract surface (including full multi-mapped identity constraints, mixed choice structures, inheritance and source metadata), run the Gradle/TestNG module test suites and complete Java/Python bootstrap with generated public API compatibility checks. The supported indexed LIST subset has been checked against the actual Java `AIiMultiMappedList` and annotation source contracts and the Python SDO key-metadata tuple format. **The supported XML subset now includes concrete Java/Python mutable SDO emission and verified XML round-trips**, but full schema support, every inherited and restricted SDO lifecycle case, and exact public API parity are still open. The current opt-in compiler **does not satisfy all migration criteria**.



## Vstupní formáty a emise rozhraní


## Generování kontraktů, rekurze, dědičnost, XML elementy a metadatové vazby

**Rozsah:** většinou produkční generátor (`defs.old`), nikoli garance úplné podpory nového kanonického emitoru.

`defscodegen` is the **first stage** of the SmartDataObject generation pipeline.
It supports standalone canonical `yamldefs`, `jsondefs`, and `xmldefs` inputs and emits
annotated, read-only `AIig*` contracts plus shared `AIng*` enums in Java and Python.
It must not write implementations into a second artifact root.

- JVM: `AIcSchemaContractInterfaceGenerator` and `AIcSchemaContractBindingsGenerator`.
- Python: `AIcSchemaContractInterfaceGenerator` and `AIcSchemaContractBindingsGenerator` in
  `aic_schema_contract_interface_generator.py` and
  `aic_schema_contract_bindings_generator.py`.
- CLI: `AIcDefsCodegenCli` / `aic_defs_codegen_cli.py`.

The repository manifest has `artifact`, `languages`, and optional `bindings`:

```json
{
  "artifact": "aac/intf",
  "languages": ["java", "python"],
  "bindings": []
}
```

Each generated field carries a stable `fieldName` / `field_name`, `presence`
(REQUIRED / ALLOWED / FORBIDDEN), and `allowsNull` / `allows_null`.
Human-readable titles and descriptions belong to `AIaFieldLabel`, not the
structural field annotation. Java emits `AIaDataObject` and
`AIaDataObjectField`; Python emits `AIcdDataObject` and `AIcdDataObjectField`.
A read contract extends the source-family marker `AIiXmlDataObject`,
`AIiJsonDataObject`, or `AIiYamlDataObject` (all of which extend
`AIiDataObject`). Explicit inherited schema contracts preserve their parent
edge instead of redundantly naming the technology marker. This makes the
source technology visible to second-stage SDO generation. Named XSD content
types additionally carry the declaration's expanded QName as
`AIaXmlDataObject(definitionKind=TYPE)` (Python: `__xml_data_object__`),
which is independent from separately generated global XML element contracts.

**The second stage** is `../sdocodegen/`. It consumes the annotated contracts,
not the schemas. It writes mutable interfaces and concrete SmartDataObjects into
separate `java.gen`/`python.gen` roots. See its README.

Repository-scoped schema discovery covers `yamldefs`, `jsondefs` and `xmldefs`
(`*.xsd`) for both Java and Python. XML documents pass through the existing XSD
canonical frontend. A parity fixture verifies that equivalent JSON, YAML and XSD
object contracts merge into the same generated type, and imported XSD definitions
and enums are discovered together.

For JSON/YAML object schemas, a single explicit `allOf` `$ref` to an emitted
object contract creates a *real interface inheritance edge*; only the new fields
are declared on the child. Inherited fields are validated against their parent;
contradictory metadata or an unresolved parent fails generation. Parent references
may be file-relative or local JSON Pointers. Equivalent JSON/YAML representations
may merge while preserving the same parent relationship. Arbitrary multiple-base
`allOf` is not supported. XSD direct attributes are projected into canonical
fields, including `use="prohibited"`. A limited **same-XSD** `complexContent`
`xs:extension` retains both inherited and appended fields by flattening their
metadata; attribute-only `xs:restriction` can prohibit optional attributes or
make them required. Repository-batch XSD generation emits all top-level named types independently,
including additional complex/simple types in the same XSD as the primary unit,
so named extension bases in the same file can be referenced by genuine Java/Python
interface inheritance edges. Only local child fields appear on the generated
derived interface. Cross-file `xs:import`/`xs:include` bases resolve locally
and retain their original XML QNames. A base not present in the emitted batch
causes an explicit error instead of silently flattening into the derived API. Standalone XSD `load()` still exposes
flattened property metadata, and unrestricted XML derivation is not yet
supported. Repeated sequence/all and named group particles containing **exactly one mandatory,
nonrepeating leaf element** are reduced to a single repeated XML field with the
same QName and exact minOccurs/maxOccurs bounds; both compositor names follow
identical canonical ordering rules. Multi-field correlated groups, groups with
already repeating members, wildcard particles, and unresolved references fail
explicitly rather than silently producing invalid sources. Recursive canonical comparison is complete for the
represented JSON/YAML structural nodes but **not yet for XSD nested named
complex types**. These are current frontend limitations, not `pub.lib.General`
constraints.

Legacy manifest-based repository generation records ownership under
`build/run/schema-contract-bindings/generated-files.json`. The **explicit
YAML-driven batch CLI** instead uses whole-filename naming conventions to
clean its generated interface/enum roles after successful preflight. Both
paths support `--check` and collision detection; neither may delete
SDO-generated files or unrelated generator outputs.

Named local JSON/YAML `$defs` objects and choices retain nominal references, including
recursive members such as `FinalizationAction.FinalizationActions[]` that refer back
to their own containing contract. Defs Codegen must not eagerly inline those
members: a named object target is represented by its kind and stable identity,
while a named choice retains its alternatives until a recursive back-edge is
reached. The back-edge remains a reference without a recursively embedded
`targetDataType`. Invalid cyclic aliases without a named target fail with an
explicit error rather than overflowing the Java/Python call stack. This rule
applies equally to the Java and Python canonical schema readers.

The first-stage renderers emit contracts directly from canonical definitions,
without rendering or parsing a concrete DTO source. There is no paired
Defs Codegen API: the former `AIcSchemaInterfaceGenerator` and
`AIcSchemaObjectBindingsGenerator` have been removed as part of the 1.1
migration. The same applies to their Python modules. Consumers must use the
canonical contract API and then explicitly invoke SDO Codegen for mutable and
concrete SmartDataObject types.

`bootstrap.sh` builds the first generator without loading the bootstrap Builder
plugin, and parity tests cover Java and Python native implementations.

In explicit CLI batch mode, outputs are recognized by their complete YAML naming
conventions; source collision validation (including canonical identity) runs
before any output cleanup. Same-format schema duplicates from distinct roots
may merge when both their canonical identities and their structures match.
See [Code Generators Reference Guide](../CODEGEN-REFERENCE.md).

### Structured generated type identities

`AIcdGeneratedSource` exposes `generated_types` and `primary_type` for the
importable declarations it owns. Every generated type identity reports:
`type_name`, `namespace`, `module_name`, `fully_qualified_type_name`,
`type_role`, `technology_kind`, `source_definition_id` and
`source_definition_version`. For Python, a qualified name includes the
**module file** before the class; in Java it is `package.Class`.

Canonical schema contract generation populates this metadata directly in both
Java and Python. Consumers (AAC included) must not reconstruct qualified names
by splitting the rendered source or guessing from file names. The three-argument source constructor remains for other/non-type outputs; requesting
`primary_type` from a source with no type metadata is an explicit error.

The canonical data pipeline is `Defs Codegen (AIig)` followed by `SDO Codegen
(AIigd / AIcgd)`. Consumers must not select the legacy paired DTO generator
as a substitute for the standard two-stage pipeline.

### Canonical representation conflict diagnostics

The repository/batch generators use strict multi-representation validation before
writing output. `AIcCanonicalDefinitionMerger.AIcMergeStrict(definitions,
sourceRoot)` (Python: `merge_strict`) checks both the canonical field model and
root/field/enum titles and descriptions. The ordinary `AIcMerge`/`merge` API
continues to support documentation aggregation when explicitly requested by
other consumers.

If any representations disagree, the exception includes **all** source files
(as absolute paths), the consistency status of **every pair**, all differences
by field/constraint or documentation member, both conflicting values, and a
best-effort `file:line` for each. In Gradle, the exception text is printed
without needing `--stacktrace`. Only the self-publication URL of the JSON/YAML
`$schema` property is treated as format-specific; this property is not
required in XML because `$` is not an XML element name. Other missing fields,
const values, type constraints and descriptions remain strict.

The current canonical projection covers the root model, its properties and
canonical enum values; format-specific XSD declarations that have no canonical
counterpart are outside this check. Line positions are best effort for nested
or reused schema fragments.

### Recursive types, closed choices and XML nominal contracts

See [rekurzivní kontrakty a XML](#generování-kontraktů-rekurze-dědičnost-xml-elementy-a-metadatové-vazby) for the staged recursive canonical model, the generated closed choice compilation units, the XML `_xe` element interfaces, migration constraints, and current XSD limitations.

#### Recursive property contracts

Java and Python preserve nested arrays containing scalars, named references,
inline objects, and named closed choices. Inline JSON/YAML objects and nested
`oneOf`/`anyOf` are discovered as separate, versioned read-contract sources
in the same business package. The enclosing getter/property refers to that
actual generated type (for example `List<? extends List<? extends AIigInvoiceLinesItemsItems_1>>`
or `tuple[tuple[AIigInvoiceLinesItemsItems_1, ...], ...]`). Closed-choice
wrappers are generated as independent compilation units alongside the choice
interface. Direct `$defs` references and nested array references resolve to
the same nominal target type.

When XMLDEFS participates in a cross-format `oneOf`/`anyOf`, the shared
Java and Python choice contract has **no XML-specific superclass**. Only
the XML-specific derivative implements/inherits `AIiXmlDataObject` and
imports the Python marker explicitly. This distinction must hold even when
XMLDEFS is the canonical source selected for the shared contract: otherwise
Python imports fail during independent SDO Codegen discovery.

This support applies to the **repository batch** which writes all discovered
compilation units. The single-unit `generate()` preview may contain references
to sibling contracts not created by that individual call. See
[rekurzivní kontrakty a XML](#generování-kontraktů-rekurze-dědičnost-xml-elementy-a-metadatové-vazby)
for XML limitations, `oneOf`/`anyOf` runtime semantics, and remaining deep
runtime validation work.

#### XML member representation

XMLDefs properties preserve `AIcdXmlFieldRepresentation` through the canonical
property model. Generated Java member getters carry `@AIaXmlDataObjectField`
and generated Python read interfaces carry `__xml_data_object_fields__`, preserving
the XML namespace, local name and `ELEMENT`/`ATTRIBUTE` distinction independently
of `AIaDataObjectField.fieldName` and the generated language identifier. XSD
qualification uses the local declaration's `form` or the schema's corresponding
form default, never a blanket `targetNamespace` assumption.


#### Recursive choice and XML content-type compatibility

The XML frontend supports a direct mandatory `xs:choice` of local element
declarations as a closed recursive `ONE_OF` and emits distinct Java/Python
branch read-only contracts plus wrappers. Global elements whose named type is
a sealed choice expose a typed value getter and do not extend an unpermitted
sealed interface. XML QName and ELEMENT/ATTRIBUTE metadata remain separate
from canonical field names. JSON/YAML `allOf` duplicate field definitions
with incompatible shapes are rejected before merging. Inherited field matching
compares recursive types, not just legacy flat value kinds.

The current XSD subset also models repeated element cardinality as array
`minItems`/`maxItems` and permits safe narrowing of flat `xs:sequence` **or**
`xs:all` in `complexContent restriction`. Both compositors project to the same
ordered canonical property model: generated getters include `AIaXmlDataObjectField.order` to make Java XML
serialization independent of reflection method ordering (Python retains the
same ordinal in `__xml_data_object_fields__`). Canonical XML writing
emits repeated elements as adjacent siblings sharing their declared QName,
never as an artificial `Item` wrapper; an empty array emits no element.
The XML reader in `pub.lib.General` binds by expanded QName
regardless of input order, constructs nested typed SDO objects with generated
class bindings, and enforces known `minOccurs`/`maxOccurs` occurrence bounds.
This intended behavior differs from **strict XSD validation**, which must still enforce the
original order of `xs:sequence`. No hidden canonical flag
for `all` versus `sequence` is introduced. Optional/repeated multi-field
compositors are still rejected when flattening would change group cardinality.
The frontend also resolves local named `xs:group` and `xs:attributeGroup` with
cycle detection, and supports references to global elements and groups through
local, namespace-checked `xs:import`/`xs:include` paths, including direct
choice alternatives. Remote imports, ambiguities, wildcards and general
content-model restrictions outside the provably safe subset are rejected rather
than silently flattened. The frontends also reject unmodelled content-model
members (`xs:assert`, `xs:openContent`), conditional element types
(`xs:alternative`), schema-level `xs:redefine`/`xs:override` and default open
content. A document whose root is not `xs:schema` is not accepted as a schema.
Named type inheritance works across emitted types
from the same XSD and local include/import files. The
canonical `AIcdDataType` hierarchy now replaces the old flat `DefinitionKind`/
`ValueKind` and their duplicate canonical fields in both Java and Python.
Normalization of source-language primitive hints is private to the frontends.
Full repository-level Gradle/JPMS verification remains a separate integration
requirement.

#### XML wire cardinalities and cross-format publication

`AIcdXmlFieldRepresentation` carries the source element/attribute QName together
with an independent XML occurrence interval. This interval is propagated to
`@AIaXmlDataObjectField(minOccurs, maxOccurs)` and Python
`AIaXmlDataObjectField(min_occurs, max_occurs)`. A finite XSD maximum and
minimum are checked by the XML reader against the actual count of QName
occurrences, even when the caller provides elements in a different order.
An unspecified or unbounded maximum remains `-1`. The recursive array's
`minItems` and `maxItems` are independent of XML sibling cardinalities:
`xs:list` constraints apply to list items, not the count of surrounding XML
elements. Complex multi-field repeated particles and wildcard content models
are still rejected rather than projected into unrelated flat fields.

When several schemas describe one canonical contract, `$schema` publication
self-links are format-specific, not shared scalar enum restrictions. The merger
checks that a self-link matches the declaring source format and path, excludes
only that publication constant from cross-format comparison, and excludes it
from the merged canonical `DataType`. Original per-format definitions keep
their own `$schema` constraint. Incompatible fields and unrelated enum or
lexical constraints continue to fail the strict merge.

This source-level fix requires the matching `defscodegen.impl:1.1-SNAPSHOT` to
be bootstrapped into `pub.gov.Algites`: a CI invocation resolving legacy
`defscodegen.coreimpl:1.0-SNAPSHOT` runs older merger bytecode and cannot be
repaired by changes to this repository's unbuilt sources alone.


## Schématová metadata a identita výstupních zdrojů

Zachována specifická pravidla metadat z dřívější příručky; ostatní překryté kapitoly jsou v předchozí kapitole.

### Schema metadata naming conventions

The selected `SourceStructureNameConventions` profile determines six properties:
`schema_source_schema_{url,identifier,version}` specify where to read metadata
inside the **source schema**, whereas `data_source_schema_{url,identifier,version}`
select their names in **instance documents**. An enabled destination property
requires a nonempty corresponding source property in the catalog. Empty target
property names explicitly suppress serialization, not collection of the logical
ID/version in the canonical contract model.

The built-in Algites JSONDEFS/YAMLDEFS profiles read `$id`,
`x-algites-schema-id`, and `x-algites-schema-version` and emit `$schema`
only. `$schema` remains reserved for the JSON Schema dialect in the definitions.
The same mapping is propagated to the Python `__data_object__` descriptor and
Java `@AIaDataObject` annotation, and from read contracts into generated SDOs.
Independent source families retain their own publication URLs even when the
same logical canonical type is shared.

Edit the source definitions, conventions and generators, **not** `java.gen` or
`python.gen` directly. Regenerate them through the usual Modustro bootstrap
following a clean stage. In particular, applying this change to existing
published artifacts requires regenerating the annotations before expecting the
new `$schema` metadata on runtime objects.


## Řízení XSD restrikcí, enumů a opakovaných choice

Rozlišovat podporu historického generátoru od úzké podpory nového backendu. Opakované XML choice dosud nemají úplný SDO wire round-trip.

Default distinct `yamldefs`, `jsondefs`, and `xmldefs` frontends plus Java/Python generation backends. Package namespace: `eu.algites.tool.codegen.defs.old`; `impl` is only an artifact boundary.

The default Java and Python backends propagate canonical descriptions into
Javadoc/docstrings and preserve property descriptions in generated data-object
documentation. The current **contract-only** first stage emits `AIig..._N`
read-only interfaces and `AIng..._N` enums. The separate SDO Codegen stage
creates `AIigd..._N` and `AIcgd..._N`. Defs Codegen does not expose a paired
contract/DTO generator, and renders `AIig` contracts directly from canonical
properties rather than parsing a generated DTO source.


### Enum-value documentation

The canonical enum model preserves each wire value together with its optional human-readable description. JSON/YAML definitions may provide per-value descriptions through `oneOf` branches containing `const` plus `description`; XSD definitions use `xs:enumeration/xs:annotation/xs:documentation`. Java enum constants and Python enum class documentation are generated from the normalized per-value descriptions.

See [generated source conventions](DEFS-CODEGEN-REFERENCE.md) for per-object contracts, concrete implementations, package ownership, and clean-checkout CI generation.

Both native implementations expose the contract-only API and repository
binding API. Java TestNG compares Java and Python first-stage source output;
SDO Codegen has its own native integration tests for mutable interfaces and
implementations.

See [Code Generators Reference Guide](../CODEGEN-REFERENCE.md) for overlap,
canonical identity, CLI and cleanup rules.

#### XSD restriction safety

For the supported `xs:simpleType` restriction subset, both language frontends
reject relaxed inherited numeric bounds, lengths, enumerations, and patterns.
Unsupported XML Schema scalar facets are rejected rather than silently lost;
pattern conjunction across levels is not yet supported. Attribute-only
`xs:complexContent` restrictions retain inherited type information when
`use="prohibited"` omits a type and validate retained scalar facets.
For coverage see `test_xsd_facet_narrowing.py` and
`AItcXmlFacetNarrowingTest.java`. Full XSD restriction validation and
complex content particle derivation remain out of scope.

### Repeated XML Schema choices (contract-generation stage)

A repeated `xs:choice` inside a named `xs:complexType` is represented as a
collection of closed alternatives, not as several unrelated optional fields.
Each such particle receives a deterministic ordinal named type:
`ProfileTypeChoice1`, `ProfileTypeChoice2`, and so on, counting the choices
within the enclosing complex type in declaration order. The enclosing
contract exposes `Choice1`, `Choice2`, etc. with their XSD `minOccurs` and
`maxOccurs` recorded on the array type. The branch contracts retain their
original XML element QNames. Java and Python Defs contract generation both
implement this mapping.

**Integration limitation:** This stage does not yet implement grouped-choice
XML marshalling and unmarshalling in SmartDataObject. Those runtimes currently
assume one XML QName per field, which cannot describe a choice's distinct
branches. The synthetic `ChoiceN` field therefore deliberately has no false
XML QName mapping. Generating its contract does **not** imply that an XML
round-trip is supported. Completing that requires explicit grouped-particle
metadata and matching Java/Python XML materializers before publishing a module
whose wire format uses repeated choices.

The independent `xs:all` compositor remains a set of optional or required
properties, not a sealed alternative. In XSD 1.0 it cannot assert that at
least one of several individually optional elements appears; that check
belongs to the appropriate application validation layer.

### Canonical seven-kind pipeline (1.1-SNAPSHOT migration)

The new `eu.algites.tool.codegen.defs.impl.standard` package is deliberately
separate from the historical generator under `.old`. Both Java and Python have
independent source frontends, a canonical merger, a symbolic reference linker,
a schema-contract projection, and a final normalizer. Their sequence is:

1. Collect all XMLDEFS, YAMLDEFS, and JSONDEFS declarations, retaining each
   exact input resource and pointer in `Map<SourceInputKind, List<SourceBinding>>`.
2. Merge structurally equivalent declarations and report incompatible members.
3. Resolve references as symbolic `targetIdentity` edges; detect missing and
   ambiguous targets and cyclic inheritance without expanding recursive types.
4. Validate the **unnormalized** canonical document against the generated
   `canonical-model_1.jsondef.schema.json` contract (Python uses JSON Schema;
   Java accepts a mandatory schema-validator callback).
5. Normalize only after successful validation and linking.

The seven structural kinds are `TYPE`, `ELEMENTLIST`, `ELEMENT`, `LIST`,
`MAP`, `SCALAR`, and `ENUM`. `REFERENCE` and `UNDEFINED` are temporary
resolution states, not structural kinds. Integrated property maps are direct
`ELEMENTLIST` children, not synthetic `ELEMENT` envelopes. Synthetic types
keep their origin and configured semantic naming paths. XSD QNames are resolved
by their namespace bindings; same-named XSD built-ins and declared types must
not be confused.

This frontend intentionally fails closed when it cannot represent an input
without losing meaning (for example JSON Schema nullable/unions, mixed-scalar
enums, boolean `items`, `patternProperties`, external XSD imports, XML key
constraints, or XML-to-MAP conversion). Some ordinary schema constraints are
not yet enforced by the canonical structure model; do not use it as a general
JSON Schema or XSD validator. Inputs with unsupported semantics must not be
silently coerced to `ANY`.

**Migration status (2026-11-04):** The Python seven-kind pipeline
(frontends, merger, linker, canonical validation, normalizer and emitter) now
uses the schema-generated SDO object graph; the handwritten Python
`canonical_model.py` has been removed. The new Java pipeline still depends on
handwritten `AIcdDefsCodegen*` records and must be migrated before removing
them. Both new read-only emitters now attach DataObject and per-field metadata,
so the independently implemented SDO can consume their output. Native JSON,
YAML and XML Defs → SDO smoke/integration tests pass for Python, but advanced
cases remain deliberately fail-closed and a full Java build has not been
verified. Production bootstrap still uses the `.old` generators.
See [stav implementace](#účel-hranice-a-aktuální-stav)
for the verified status and the remaining Java work.


## Veřejná DataObject API rozhraní

Normalized canonical-definition model and frontend/backend/service contracts. Package namespace: `eu.algites.tool.codegen.defs.old`; `intf` is not part of the package name.

Canonical-definition descriptions and property documentation are first-class normalized data and are preserved for generation backends. Definition version is carried independently from logical-name tokens.


### Enum-value documentation

The canonical enum model preserves each wire value together with its optional human-readable description. JSON/YAML definitions may provide per-value descriptions through `oneOf` branches containing `const` plus `description`; XSD definitions use `xs:enumeration/xs:annotation/xs:documentation`. Java enum constants and Python enum class documentation are generated from the normalized per-value descriptions.

See [generated source conventions](DEFS-CODEGEN-REFERENCE.md) for per-object contracts, concrete implementations, package ownership, and clean-checkout CI generation.

For source-to-contract and contract-to-SDO behavior see
[Code Generators Reference Guide](../CODEGEN-REFERENCE.md).

### New canonical interfaces and schema-generated contracts

The active `eu.algites.tool.codegen.defs` package contains the seven-kind
immutable canonical structure interfaces/records in Java and equivalent Python
value types. Schema-generated `AIig*` contract interfaces and sealed-choice
variants are written solely under `src/product/java.gen` and
`src/product/python.gen` by the Defs generator, **never by manual edits**.
The authoritative source is
`src/product/jsondefs/eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json`;
corresponding XMLDEFS and YAMLDEFS representations are kept alongside it.

For source-checkout regeneration or reproducibility verification, run from a
checkout containing sibling `pub.tool.General` and `pub.lib.General`:

```sh
python pub.tool.General/devops/bootstrap/generate-canonical-contracts.py --source-dependencies
python pub.tool.General/devops/bootstrap/generate-canonical-contracts.py --source-dependencies --check
```

The generation ownership manifest is `generated-canonical-contracts.json`.
The previous `.old` interfaces remain a temporary bootstrap compatibility
layer, not the API for the new canonical compiler.



## Kolekce, klíče, volby a XML


## Datové role a aktuálně realizovaná projekce klíčů

**Pozor:** část starých omezení je dnes zpřesněna v následující specifikaci; považujte konkrétní testy a aktuální zdrojový kód za rozhodující. Tato kapitola popisuje zejména strukturu a omezení historického backendu.

**Author:** linhart1  
**Status:** partial integration, 2026-10-30; **not approved for publication**

### Canonical roles

The addressing role of a field is independent of its data type and schema source:

| Role | Source examples | Representation |
| --- | --- | --- |
| `NAMED_VALUE` | JSON Schema `properties`, named XSD elements/attributes | Statically named field with a typed value. |
| `KEYED_VALUES` | JSON Schema `additionalProperties`; direct XSD collection with qualifying `xs:key` | Typed member collection; index definitions identify key fields, ordered composite key parts, and uniqueness. |
| `POSITION_TYPED_VALUE` | JSON Schema `prefixItems`; legacy positional `items` arrays | A list whose prefix positions have individually declared types. XSD has no direct name-independent equivalent. |
| `SEQUENTIAL_VALUES` | JSON Schema homogeneous `items`; repeated XSD element | Ordered sequence whose item type does not depend on index. |

Do not restrict schema expressiveness to the common subset. Merge only genuinely overlapping common definitions and reject incompatible types before source generation. Preserve format-specific contract extensions without widening to `Object`.

### Multi-mapped list API

Java source declarations must expose `eu.algites.lib.common.list.AIiMultiMappedList<V>`, **not** `AIcMultiMappedList<V>`. The library implements `AIiMultiMappedList<V> extends java.util.List<V>`, and its key definitions provide `Map<K,List<V>>` live views over the one underlying ordered list. The map's grouped lists are immutable snapshots. Removing a key removes the entire group across all views. Inserting/replacing through maps is forbidden. The collection tracks sublists weakly and synchronizes removals; direct mutation of key-bearing fields while stored is a caller contract violation.

Python declares a matching abstract `AIiMultiMappedList[V]` interface built on `collections.abc.MutableSequence[V]`; `AIcMultiMappedList` implements it. Python grouping map values are immutable `tuple[V,...]` snapshots. Do not expose concrete `AIcMultiMappedList` from generated interfaces.

For overlapping common and format-specific contract getters, use one **identical generic value type** for the mutable mapped list. Generic Java collections are invariant: `AIiMultiMappedList<SpecializedValue>` does **not** override `AIiMultiMappedList<CommonValue>`. Format-specific item contracts may still extend the common value contract. Python follows the same nominal convention for predictable static type checking.

### JSON/YAML dynamic keys

`additionalProperties` with a schema defines typed values and one *virtual* key definition whose key is the containing property name. JSON/YAML item interfaces have the configurable synthetic getter `multi_mapped_list_key_synthetic_getter: _getKey`, selected from the Java/Python generated-method naming profile. This method is **not serialized inside the value**; it represents the parent object's property name and must be initialized by the runtime factory. XML value interfaces do not acquire this getter because their keys come from declared XML fields.

Unlike `additionalProperties`, `patternProperties` may have distinct overlapping patterns. The current frontend fails explicitly instead of discarding their constraints. This requires a later rule/merge design.

### XML keys

Example:

```xml
<xs:element name="Employees">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Employee" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType>
          <xs:sequence><xs:element name="Label" type="xs:string"/></xs:sequence>
          <xs:attribute name="region" type="xs:string" use="required"/>
          <xs:attribute name="code" type="xs:string" use="required"/>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
  <xs:key name="ByRegionAndCode">
    <xs:selector xpath="Employee"/>
    <xs:field xpath="@region"/>
    <xs:field xpath="@code"/>
  </xs:key>
</xs:element>
```

The ordered compound key `(region,code)` is one unique key definition. Multiple `xs:key` declarations produce multiple unique indexes; **none may be silently ignored**. The key attributes remain regular declared fields of the XML value object. `xs:selector` and `xs:field` are XPath expressions whose prefixes have namespace semantics: a `tns:` prefix must refer to the actual target namespace, and unprefixed steps do **not** select qualified XML elements.

The Python and native Java XML frontends now recognize **one direct repeated child** with one or more `xs:key` declarations. Both validate QName prefixes and allow typed nested `xs:field` paths through nonrepeating child elements, e.g. `tns:Identity/tns:Code`; the path is retained for a future null-safe extractor. **Parsing the path does not create or execute that extractor.** Descendant selectors spanning several nested lists, `xs:unique`, and exotic XPath are not yet indexed. `xs:keyref` is deliberately ignored during structural projection; it creates no index or relation and does not block generation. Referenced values must be checked by a full XSD validator. `xs:unique` remains explicitly unsupported in the keyed-collection projection. Full XSD validation remains necessary.

### `xs:choice` and ordered wrappers

A nested XSD `xs:choice` models mutually exclusive alternatives, corresponding to JSON `oneOf` when branches are semantically distinct. Named XML choice types are now emitted independently and share common nominal branch interfaces with matching JSON/YAML `$defs`; exact format-specific XPath and XML element QNames must be preserved. The `NameFragments.Segments` wrapper with one repeated typed `Segment` is recognized as an array, not as an unrelated object. A targeted 208-source generated-output check passed for the naming schema family.

### Explicit remaining limitations — important

1. **Java/Python XML frontend parity is partial**: Java now projects direct and composite `xs:key`, including type-checked nested field paths and namespace checks (targeted Java tests passed). It still lacks full Python parity for nested choice and some wrapper shapes.
2. **No runtime JSON/YAML/XML serializer or SmartDataObject factory integration has been completed.** The virtual `_getKey()` is an interface contract, not yet proof that deserialization populates it, or that XML/JSON/YAML round trips work.
3. **Java `POSITION_TYPED_VALUE` emission remains unimplemented**: canonical `prefixItems` types are now preserved and Python tuple typing is emitted in supported cases, but Java generation rejects unsupported positional combinations rather than widening them to `Object`.
4. **`patternProperties` validation and descendant-scope XSD `xs:key` selectors** are not supported; unsupported cases are explicitly rejected rather than silently degraded.
5. **Complete Gradle bootstrap, Java TestNG suite and schema-to-runtime round trips are not verified.** Do not publish rebuilt artifacts based solely on the targeted tests below.

### Targeted verification

- Naming family direct Python-batch Defs Codegen: 208 generated Java/Python entries; previously failing `IdentifierConventions` now passes at generation.
- Fifteen targeted tests in `test_multi_mapped_field_contracts.py` covering JSON typed maps, positional slots, XML compound keys, XML QName checks, `patternProperties` diagnostics, and generated interface types.
- Forty-one targeted Python regressions passed in the working environment (collection library and XML frontend regression files).
- Java canonical model source types compiled with JDK 21 `javac --release 17`.
- Java TestNG regressions were authored but not executed in the full Gradle classpath.

Do not manually edit or publish files beneath `java.gen` or `python.gen`. These are generated verification outputs, not patch inputs.

### Extended mapping and validation specification (2026-10-30)

The detailed schema illustrations, XML `xs:key` extraction and nullable paths,
synthetic `_getKey()` / `_getValue()`, and the standards-preserving rewrite for
pattern-constrained maps are described in
[sémantika map a XML klíčů](#podrobná-sémantika-keyvalue-položek-patternproperties-a-xml-xpath).
Distinguish tested source-contract changes from unimplemented DO/SDO runtime
validation and nested-collection index synchronization.

### Verification update: native Java XML key projection

The Java `AIcXmlDefsFrontend` now projects each direct `xs:key` into
`AIcdDataType.keyDefinitions()` and preserves its full ordered field path.
The implementation was compiled with `javac --release 17` (using only a
temporary Jackson API stub because the Gradle wrapper distribution is not
installed in the isolated environment). Two Java regression methods were
executed with a temporary TestNG-compatible assertion stub; **this is not a
full TestNG run**. The real naming XSD was also loaded and all four keyed
collections were recognized.

The source fixture uses a qualified nested path:

```xml
<xs:key name="ByCode">
  <xs:selector xpath="tns:Employee"/>
  <xs:field xpath="tns:Identity/tns:Code"/>
</xs:key>
```

Its canonical key path is `Identity.Code`; the current reader does not yet
produce executable Java/Python key extractors. A missing `Identity` node
therefore still requires a generated null guard, and a missing key is a schema
validation error for `xs:key`. `xs:keyref` is intentionally ignored by structural code generation; a
full validating XSD parser remains responsible for referential integrity.
`xs:unique` is still explicitly unsupported by the keyed-collection reader.


## Podrobná sémantika key/value položek, `patternProperties` a XML XPath

**Specifikace, nikoli tvrzení o plné implementaci:** následující příklady výslovně rozlišují cílové chování a nepodporované případy. Zejména agregované klíče přes několik kolekcí a XML→MAP se nyní nezavádějí.

**Status:** design specification with explicit implementation status below.  
**Author:** linhart1  
**Baseline:** `pub.lib.General(20261030-061855).tgz` and `pub.tool.General(20261030-061856).tgz`.

This document defines the **intended contract**, including behaviors not yet
fully implemented. A partial parser must never imply that serialization,
validation, Java/Python generator parity, or SDO support has been verified.
The four independent field roles remain `NAMED_VALUE`, `KEYED_VALUES`,
`POSITION_TYPED_VALUE`, and `SEQUENTIAL_VALUES`.

### 1. JSON/YAML dynamically named members

A JSON object's member name is a **key**, not part of its member value:

```json
{
  "all_lower_1": {"Regexp": "[a-z]+"},
  "upper_camel_1": {"Regexp": "[A-Z][a-zA-Z]*"}
}
```

Schema:

```json
{
  "type": "object",
  "propertyNames": {"minLength": 1},
  "additionalProperties": {
    "type": "object",
    "properties": {"Regexp": {"type": "string", "minLength": 1}},
    "required": ["Regexp"],
    "additionalProperties": false
  }
}
```

Each keyed value implements a generated **interface**, with the configured
`multi_mapped_list_key_synthetic_getter` (default `_getKey()`). The getter
returns `all_lower_1` or `upper_camel_1` without adding a `Key` field to the
serialized value. The map is an `AIiMultiMappedList<V>` and can be addressed
using its typed `AIiKeyDefinition<V,K>`; a JSON object member name is unique.

For scalar or array-valued members, there is also a generated virtual
`multi_mapped_list_value_synthetic_getter` (default `_getValue()`):

```json
{"S_name": "Anna", "I_age": 35}
```

An explicitly declared variant contract can produce a string-value interface
with `_getValue(): String` and an integer-value interface with
`_getValue(): BigInteger`, plus `_getKey(): String` on both. The synthetic
value getter is *not* serialized as an inner object property. The same applies
to Python interfaces (`str` / `int`), subject to actual generated support for
closed variants.

**Neither getter is used for an XML key**: its fields are already explicitly
declared as real attributes/elements.

#### 1.1 `properties` and `additionalProperties` together

These are orthogonal, and the dynamic values can themselves be arrays:

```json
{
  "type": "object",
  "properties": {"Description": {"type": "string"}},
  "additionalProperties": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {"something": {"type": "string"}},
      "required": ["something"],
      "additionalProperties": false
    }
  }
}
```

Valid YAML data:

```yaml
Description: Example mappings
aaa:
  - something: else
bbb:
  - something: first
  - something: second
```

There are two map entries (`aaa` and `bbb`), **not** three; the value of `bbb`
is *one array* of two objects. A virtual `_getValue()` exposes that array.
`Description` remains a normal named field. Do not flatten an array-valued
entry into multiple separately keyed entries.

### 2. `patternProperties` is a constraint, not a structural field declaration

JSON Schema requires **all** matched patterns to hold; the first match does
not win. A `properties` rule and a `patternProperties` rule can both apply.
In the *same schema object*, `additionalProperties` applies only to names not
matched by either of the other two keywords. Ignoring that qualification would
silently change JSON Schema semantics.

A schema that is **valid JSON Schema but is not by itself a valid source of a
single typed `KEYED_VALUES` contract**:

```json
{
  "type": "object",
  "patternProperties": {
    "^S_": {"type": "string"},
    "^I_": {"type": "integer"}
  },
  "additionalProperties": false
}
```

It can validate values such as `{"S_name":"Anna","I_age":35}`, but the
patterns alone define heterogeneous value types. Do **not** invent generated
fields or allow a silent `Object`/`Any` fallback.

#### 2.1 Equivalent structural rewrite

Declare the value variants in `additionalProperties` and put the *additional*
name-specific restrictions in a separate `allOf` subschema. This is semantically
slightly **broader** than the preceding schema if unprefixed keys are allowed;
to preserve the original rejection of those keys, include the final
`propertyNames` restriction as shown:

```json
{
  "type": "object",
  "propertyNames": {"pattern": "^(S_|I_)"},
  "additionalProperties": {
    "oneOf": [{"type": "string"}, {"type": "integer"}]
  },
  "allOf": [{
    "patternProperties": {
      "^S_": {"type": "string"},
      "^I_": {"type": "integer"}
    }
  }]
}
```

The outer `additionalProperties` supplies a closed typed variant;
`patternProperties` is only a constraint. The expression `^(S_|I_)` enforces
that no other names occur. **Important:** this is a target-supported modeling
pattern, not a claim that the current Defs frontend has implemented general
`allOf` constraint projection, overlapping-pattern validation or typed scalar
variant wrappers. These steps must be tested before enabling this schema in a
published codegen build.

An overlapping pattern example:

```json
{
  "type": "object",
  "properties": {"S_name": {"type": "string", "minLength": 5}},
  "patternProperties": {
    "^S_": {"type": "string", "maxLength": 20},
    "_name$": {"pattern": "^[A-Z]"}
  },
  "additionalProperties": {"type": "boolean"}
}
```

`S_name` must satisfy **all three** applicable constraints. There must be no
implicit precedence or disjointness assumption.

### 3. XML keyed collections

```xml
<IdentifierConventions>
  <IdentifierConvention name="all_lower_1"><Regexp>[a-z]+</Regexp></IdentifierConvention>
  <IdentifierConvention name="upper_camel_1"><Regexp>[A-Z][a-zA-Z]*</Regexp></IdentifierConvention>
</IdentifierConventions>
```

XSD (simplified, with unqualified local elements):

```xml
<xs:element name="IdentifierConventions">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="IdentifierConvention" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType>
          <xs:sequence><xs:element name="Regexp" type="xs:string"/></xs:sequence>
          <xs:attribute name="name" type="xs:string" use="required"/>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
  <xs:key name="IdentifierByName">
    <xs:selector xpath="IdentifierConvention"/>
    <xs:field xpath="@name"/>
  </xs:key>
</xs:element>
```

A single `xs:key` supplies one unique map view; multiple `xs:key` declarations
supply *multiple independent map views*, all enforced, not merely a warning
for secondary keys. Unlike JSON dynamic property names, the XML `@name`
attribute remains a normal field of the value interface.

#### 3.1 Composite keys

```xml
<xs:key name="ByLanguageAndRegion">
  <xs:selector xpath="Translation"/>
  <xs:field xpath="@language"/>
  <xs:field xpath="@region"/>
</xs:key>
```

This is **one** key consisting of an ordered pair. A generated Java record or
frozen Python dataclass can supply stable equality and hash semantics. The
keyed list has one map *per xs:key*, not per `xs:field`.

#### 3.2 Nullable nested paths: null-safe lookup is mandatory

```xml
<xs:key name="EmployeeByCode">
  <xs:selector xpath="Employee"/>
  <xs:field xpath="Properties/Identity/CommonPart/Code"/>
</xs:key>
```

The extraction contract must guard **every** intermediate level:

```java
EmployeeProperties properties = employee == null ? null : employee.getProperties();
Identity identity = properties == null ? null : properties.getIdentity();
CommonPart commonPart = identity == null ? null : identity.getCommonPart();
String key = commonPart == null ? null : commonPart.getCode();
```

This is illustrative Java with hypothetical application type names. Returning
`null` from extraction avoids a null-pointer failure but **does not make an
`xs:key` valid**: XSD requires key fields to be present and not nil. The map
must reject a missing key (via a diagnostic), preferably before any list
mutation. `xs:unique` differs: absent values may be permitted. An XPath that
selects multiple values for a single key field is invalid.

#### 3.3 Selectors across several descendant lists

```xml
<Company>
  <Department><Employee id="101"/></Department>
  <Department><Employee id="102"/></Department>
</Company>
```

```xml
<xs:key name="CompanyEmployeeId">
  <xs:selector xpath=".//Employee"/>
  <xs:field xpath="@id"/>
</xs:key>
```

The key belongs to the **scope of Company**, not to just one department. The
target design creates one aggregated map view for that `xs:key`; deletion
through the view must remove values from their actual source collection.
Insertion through the aggregate requires an unambiguous destination and may
otherwise be unsupported. Changes in child collections must be visible in the
aggregate. The current frontend does **not** implement this entire mechanism;
reject rather than project such an XPath as a direct list silently.

#### 3.4 `xs:keyref`: validation-only and intentionally ignored

An `xs:keyref` checks **referential integrity**, not a data storage shape.
Defs Codegen deliberately **ignores** it while projecting structural contracts.
It does not create a field, an index definition, a map, a relationship, or
runtime referential validation; its presence never blocks structural generation.
Supported `xs:key` declarations in the same element are still projected.
This does **not** imply that an XML document is valid. A separate full XSD
validator must enforce the original `xs:keyref` constraints when requested.

For example, these XSD constraints define a key and a reference:

```xml
<xs:key name="EmployeeById">
  <xs:selector xpath="Employees/Employee"/>
  <xs:field xpath="@id"/>
</xs:key>
<xs:keyref name="AssignmentEmployee" refer="EmployeeById">
  <xs:selector xpath="Assignments/Assignment"/>
  <xs:field xpath="@employeeId"/>
</xs:keyref>
```

The generated data objects can represent the following XML, even though
`employeeId="999"` is an invalid reference in the original XSD:

```xml
<Company>
  <Employees><Employee id="101"/></Employees>
  <Assignments><Assignment employeeId="999"/></Assignments>
</Company>
```

An external validating XML parser must detect the missing referenced employee.
There is no implicit foreign-key association, cascade deletion, or insertion
restriction. If relationship modeling is ever desired, it requires an explicit
separate design, not silent inference from `xs:keyref`. `xs:unique` is a
**separate** case and presently remains an error in the keyed collection
projection; it is not being changed by this decision.

#### 3.5 Multiple selector element kinds are not automatically projected

```xml
<xs:key name="PersonById">
  <xs:selector xpath="Employee|Contractor"/>
  <xs:field xpath="@id"/>
</xs:key>
```

This is legal XSD, but it selects different element kinds and is **outside the
automatic multi-mapped-list projection**. It must not degenerate to
`AIiMultiMappedList<Object>`.

If the intended data model has a shared person contract, a supported modeling
alternative is to represent both kinds with the *same XML element name* and
`xsi:type` selecting derived XML types:

```xml
<People xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:tns="urn:people">
  <Person id="101" xsi:type="tns:EmployeeType"><Salary>500</Salary></Person>
  <Person id="102" xsi:type="tns:ContractorType"><ContractNumber>C-9</ContractNumber></Person>
</People>
```

The corresponding `Person` element has an abstract base `PersonType`, and
`EmployeeType` / `ContractorType` extend it. An XSD key can then use
`<xs:selector xpath="tns:Person"/>`. This rewrite is **not wire-identical** to
distinct `Employee` and `Contractor` element names, and XSD polymorphic
serialization/runtime support must be verified separately.

### 4. Collection API and mutation contract

```java
AIiMultiMappedList<Employee> employees = ...;
Map<String, List<Employee>> byCity = employees.mapByKeyType(BY_CITY);
List<Employee> pragueSnapshot = byCity.get("Prague");
byCity.remove("Prague");
```

- `AIiMultiMappedList<V>` extends `List<V>`; its primary list preserves
  insertion/index order. It is **not** an ordered map.
- `mapByKeyType()` returns the **cached live map** for the exact registered
  `AIiKeyDefinition<V,K>` instance.
- Each `Map` value is a **non-backed immutable snapshot** (`List<V>` for Java,
  `tuple[V,...]` for Python). It is not a modifiable insertion route.
- Map `remove(key)` deletes the **whole matching group** from the primary list,
  every other map and all living tracked sublists.
- Map `put`, `putAll`, `compute`, replacement and insertion are unsupported.
- Tracked `subList` does not acquire newly added parent elements, but loses
  elements deleted by any route. Released sublists are weakly referenced.
- Modification of a key-bearing field while its value is stored is a **caller
  contract violation**, analogously to mutable hash-map keys. It is not
  tracked automatically.
- Null keys or duplicate values for a **unique** key definition are rejected
  before the affected list mutation becomes visible.

### 5. Feature verification gates

| Area | Intended behavior | Current verified level |
|---|---|---|
| Four canonical field roles | Typed, independent of source format | Partial implementation |
| Direct XML `xs:key`, multiple keys | Keyed collection with all index definitions | Python reader regressions |
| Nested XML `xs:field` path | Typed components, nullable intermediate access | Python field-path recognition tests; Java extractor/runtime pending |
| Descendant `xs:selector` (`.//Employee`) | Live aggregated index scoped by ancestor | Design only; must reject unsupported case |
| Union selector (`Employee\|Contractor`) | No automatic projection | Explicitly unsupported by design |
| JSON `additionalProperties` | Typed dynamic values and synthetic key | Canonical reader and interface generation |
| Configurable `_getValue()` | Typed synthetic scalar/array getter | Python-driven Java/Python interface generation tests |
| `patternProperties` | All matching validation constraints, never structural field definitions | Not yet end-to-end; unsupported instances fail explicitly |
| Java/Python source frontend parity | Identical canonical semantics | Incomplete |
| DO/SDO runtime round-trip | Preserve keys, values, choice and XML order | Not yet verified end-to-end |

All generated Java interfaces, records, constants, methods, parameters,
return types and exceptions must have substantive Javadoc; annotate public
Java types with `@author linhart1`. Java and Python parameter/local names
must start with lowercase letters (or underscores where conventions explicitly
require them) and follow each language's selected naming conventions.
Do not manually modify `java.gen` or `python.gen`.

### Native Java parser parity and unresolved aggregate-key design

The native Java reader now recognizes the same direct keyed shape as Python:

```xml
<xs:element name="Employees">
  <xs:complexType><xs:sequence>
    <xs:element name="Employee" maxOccurs="unbounded">
      <xs:complexType><xs:sequence>
        <xs:element name="Identity" minOccurs="0">
          <xs:complexType><xs:sequence>
            <xs:element name="Code" type="xs:string"/>
          </xs:sequence></xs:complexType>
        </xs:element>
      </xs:sequence></xs:complexType>
    </xs:element>
  </xs:sequence></xs:complexType>
  <xs:key name="ByCode">
    <xs:selector xpath="Employee"/>
    <xs:field xpath="Identity/Code"/>
  </xs:key>
</xs:element>
```

The unprefixed XPath steps above assume **unqualified local elements**. In
a schema declaring `elementFormDefault="qualified"`, use `tns:Employee`
and `tns:Identity/tns:Code` instead. Java and Python frontends reject
namespace mismatches rather than silently mapping by local name.

The distinct descendant-selector case is still outstanding:

```xml
<xs:element name="Company">
  <!-- Company/Department/Employee has its own repeated occurrence. -->
  <xs:key name="AllEmployeeIds">
    <xs:selector xpath=".//Employee"/>
    <xs:field xpath="@id"/>
  </xs:key>
</xs:element>
```

This constraint is scoped to `Company`, not to an individual department.
Preserving it as a live indexed **aggregate** requires tracking modifications
in every nested employee collection and mapping removals to the correct
original parent. A parser that merely records the name cannot claim to have
implemented the corresponding live `AIiMultiMappedList`. Such selectors are currently rejected and not silently flattened.



## Explicitní choice: význam kontraktů a stav integrace

Marker `x-algites-defscodegen-choice: true` definuje **typově významnou,
explicitně deklarovanou** exclusive choice; běžné JSON Schema `oneOf` je
validační kombinátor, nikoli automatické generování typu. Každá alternativa
je samostatná vlastnost pod `properties` a vzniká pojmenovaný payload kontrakt;
inline payload a wrapper vybrané alternativy nesmějí mít kolidující identitu.
Reader i emitter se musí shodovat na identitě alternativ nezávislé na jejich
pořadí, na hranici enum/choice a na společných XML/JSON/YAML typech.

Aktuální profilové YAML prostředky používají tagované varianty
`NameFragmentsSegmentValue` a `NameFragmentsSegmentReference`. Čtečky naming
katalogů Java i Python zachovávají také dočasné čtení starých netagovaných
zápisů; neměnit mapování bez ověření zpětné kompatibility. XML analog používá
pojmenované elementy variant. Dřívější netagované instance credentials
(`{Source: direct_value, Value: abc}`) nejsou totožné s novou reprezentací
(`{DirectValue: {Source: direct_value, Value: abc}}`); migrace skutečných dat
vyžaduje samostatné posouzení, nikdy nevkládat secrets do testovacích logů.

Historicky prokázané generování pojmenovaných větví **nepotvrzuje** úplnou
interoperabilitu s konfigurací `pub.lib.Security`: kombinace zděděných XML
klíčů, `xs:choice` a JSON/YAML `additionalProperties` vytvářela konflikty
`AIiMultiMappedList` getterů odlišného typového parametru. Univerzální
XML→MAP sjednocení bylo následně **výslovně odloženo**; neobcházet problém
vydáním `Object` namísto typované hodnoty nebo editací generovaných zdrojů.

## Dialekty a vlastní slovník


## Dialekty JSON Schema a jejich rozsah

This independent, data-only artifact publishes one semantic Algites Defs Codegen
vocabulary specification (`vocabulary_1.md`) and **draft-specific** metadata for
all supported historical JSON Schema syntax families:

| Schema dialect directory | Base specification | `$vocabulary` available? | Algites keyword syntax |
| --- | --- | --- | --- |
| `draft-03` | JSON Schema Draft-03 | No | Draft-03 compatible extension |
| `draft-04` | JSON Schema Draft-04 (also Draft-05, which has no new meta-schema) | No | Draft-04 compatible extension |
| `draft-06` | JSON Schema Draft-06 | No | Draft-06 compatible extension |
| `draft-07` | JSON Schema Draft-07 | No | Draft-07 compatible extension |
| `2019-09` | JSON Schema Draft 2019-09 | Yes | 2019-09 vocabulary meta-schema |
| `2020-12` | JSON Schema Draft 2020-12 | Yes | 2020-12 vocabulary meta-schema |

All directories contain `vocabulary_1.jsonmetadef.schema.json` and
`dialect_1.jsonmetadef.schema.json`, each with a publication `.meta.yml` sidecar.
Every dialect is versioned independently, while the **meaning** of the two
custom keywords is specified once in `vocabulary_1.md`.

### Legacy dialect design

Draft-03 through Draft-07 have **no `$vocabulary` mechanism**. Their combined
Algites dialects are therefore draft-correct extended meta-schemas, not
implementations of modern JSON Schema vocabularies. They preserve the official
meta-schema's recursive structure, with an updated `id`/`$id` and references
to the sibling vocabulary keyword-shape meta-schema. This is necessary to
validate annotations inside nested `properties`, `items`, etc.; a plain `allOf`
combining an external official meta-schema and a keyword schema would validate
only root-level annotations. The base meta-schema is therefore embedded under an immutable `$id`/`id` (with no changed standard keyword
rules), while the Algites keyword syntax remains in its separately maintained
file. Draft-03 uses its historical boolean property-level `required` syntax.

Draft-05 was a clarification of Draft-04 and did not introduce a separate
meta-schema. Draft-00 through Draft-02 are historical pre-Draft-03 proposals
not implemented by this artifact. Adding a dialect resource for a draft **does
not** mean the current Defs Codegen source readers support that entire draft.
In particular, recursive URI identifiers, tuple array representations and
Draft-03's `type`/`extends` features need separate, tested reader adapters.

### Modern dialects

The 2019-09 and 2020-12 dialects declare standard vocabularies and the optional
Algites Defs Codegen vocabulary (`false` in `$vocabulary`). Their dialect
meta-schemas combine standard keyword metaschemas with the corresponding
Algites vocabulary syntax metaschema via `allOf`. The standard JSON Schema
`$schema` keyword is reused, not redefined.

### Publication and integration

The artifact is independent of the Java/Python generators and contains only
schema resources and documentation. It is not intended as a business-object
input to Defs/SDO generation. The current bootstrap and Builder configuration
still need explicit support for the `jsonmetadefs` source kind before the
resources can be published to the schema site; no public deployment is implied.


## Publikovaný Algites Defs vocabulary (sémantický text)

**Důležité:** originální `vocabulary_1.md` je **verzovaný publikovaný schema resource** s vlastním veřejným URI; na rozdíl od pomocné dokumentace musí zůstat fyzicky na své původní cestě. Tato kapitola zpřístupňuje jeho sémantiku, ale nenahrazuje URI.

Vocabulary identifier: `https://defs.dev.algites.eu/api/jsonmetadefs/eu/algites/tool/codegen/defs/jsonmetadef/vocabulary_1.md`

This version defines a static source-contract **generation vocabulary**, not a JSON instance-validation vocabulary. Implementations that do not support it may still validate input instances against the standard JSON Schema constraints. The vocabulary is optional in the advertised dialects (`false` in `$vocabulary`); an Algites Defs Codegen implementation requires support for it when generating the corresponding constructs.

### `x-algites-defscodegen-extends`

The keyword applies only to a named object schema (not a scalar, array, anonymous validation branch or map entry). Its value is a non-empty ordered array of distinct URI references to **named object contracts**. The order is significant for deterministic API emission, not for JSON Schema instance evaluation. Each reference is resolved using the current schema's base URI and normal JSON Schema resource identification, including local fragment identifiers. The generated read-only contract directly inherits all referenced contracts; mutable contracts retain the corresponding compatible hierarchy. Concrete SDO implementations MUST inherit directly from the format-specific SmartDataObject base, not other generated concrete implementations.

A missing or non-object parent, inheritance cycle, or incompatible inherited methods is an error. The presence or absence of `allOf` or other validation rules does not determine generated inheritance. When no direct validation reference to an explicitly declared parent is found, a tool MAY emit a warning recommending validation of that parent's schema; this is not a semantic equivalence check.

### `x-algites-defscodegen-choice`

The keyword has the **sole permitted value `true`** and marks a JSON object schema
as an **exclusive named-choice data type**. The alternatives are the direct
entries of the same schema's **`properties`**. Each property name is the stable
alternative identity; its value schema defines the alternative's payload type.

For JSON Schema Draft-04 and newer, the source MUST explicitly declare
`type: object`, `minProperties: 1`, `maxProperties: 1`, and
`additionalProperties: false`, and MUST provide at least two `properties`.
It MUST NOT use `required` or `patternProperties` on the choice itself.
These standard keywords provide independent, portable validation of exactly
one named alternative even when a third-party JSON Schema validator does not
recognize Algites metadata. **The structural type is derived solely from the
marker and `properties`; these constraints do not synthesize data structures.**

For example (JSON Schema 2020-12):

```json
{
  "$defs": {
    "ConfigurationValueType": {
      "type": "object",
      "x-algites-defscodegen-choice": true,
      "properties": {
        "StringValue": {"type": "string"},
        "IntegerValue": {"type": "integer"},
        "BooleanValue": {"type": "boolean"}
      },
      "minProperties": 1,
      "maxProperties": 1,
      "additionalProperties": false
    }
  }
}
```

The accepted instance is `{"StringValue": "hello"}` or
`{"IntegerValue": 42}`, but not two alternatives simultaneously, and not
an unrecognized property. A repeated JSON object member is not a second map
entry and SHOULD be rejected before JSON Schema validation.

The marker may declare a structural choice at the source schema root and in
`$defs` / `definitions`, `properties`, `patternProperties`, `additionalProperties`,
`items`, `prefixItems` (2020-12), and positional legacy `items` or
`additionalItems` where permitted by the corresponding draft. It MUST NOT
**declare a new choice** in validation-only positions: `allOf`, `anyOf`,
`oneOf`, `not`, `if`, `then`, `else`, `contains`, `dependentSchemas`, or their
validation-only counterparts. Referencing an already-declared named type from a
validation constraint is allowed; defining the type there is not.

The historical Draft-03 metaschema lacks standard `minProperties` and
`maxProperties`: its annotation syntax can be recognized, but **standard
third-party Draft-03 validators cannot enforce the same exclusive-choice
contract**. Draft-03 uses draft-specific object-keyword syntax, so support for
this structural extension does not imply cross-validator conformance.

Unlike the old `alternatives` URI-string array, the new marker does not duplicate
any structural information. The old syntax is no longer accepted for the 1.1
snapshot. `oneOf` remains an independent validation applicator and does not
define generated choice interfaces. A repeated or composite choice is modeled
explicitly as an array of choice elements, not as `maxProperties: 2`.

**Backward-compatibility warning:** Existing choices whose alternatives were
whole objects now require a named wrapper property in serialized JSON/YAML.
For example, a previous value `{"Source":"direct_value", "Value":"abc"}`
becomes `{"DirectValue":{"Source":"direct_value","Value":"abc"}}`.
Existing JSON/YAML instance documents must be migrated, and XML/JSON common
contract compatibility requires an independent projection review. Neither the
vocabulary update nor the marker itself implements that projection.

### Compatibility and publication

One semantic vocabulary URI is shared across dialect-specific vocabulary keyword meta-schemas for JSON Schema 2019-09 and 2020-12. For Draft-03, Draft-04, Draft-06, and Draft-07, the same semantics are expressed as proprietary annotations in extended, version-specific meta-schemas. These historical dialects lack `$vocabulary`; the corresponding `vocabulary_1.jsonmetadef.schema.json` resources validate keyword syntax, while `dialect_1.jsonmetadef.schema.json` preserves the published standard metaschema’s recursive validation rules and references the keyword definitions. Draft-05 shares the Draft-04 metaschema (no distinct dialect resource). The keyword meta-schemas describe JSON syntax only; the semantic requirements above must be implemented and tested by consuming tools. Older drafts without `$vocabulary` may use these `x-` keywords as proprietary annotations with separately documented support, but they MUST NOT be described as implementing the 2019-09/2020-12 `$vocabulary` mechanism.

The versioned public identifiers are immutable after stable publication. In the 1.1-SNAPSHOT development sources the version-1 resource may change; before a stable release, publish a version-2 identifier rather than silently modifying a previously published immutable version. Schema-sidecar `GlobalPublicationPathId` values are deployment metadata only, not a substitute for `$id`. This artifact is data-only and must never be treated as a JSONDEFS/YAMLDEFS business-object definition by the Defs/SDO generator.


## Integrace dialektů a publikace

Both Defs frontends use explicit-only structural handling for the two Algites metadata keywords. Dialect resources include historical JSON Schema versions and offline validation tests, but the presence of these resources **does not prove** a complete Gradle bootstrap, a deployed public vocabulary, or full legacy-draft reader support.

### Prerequisites for activating these resources

1. Add generic `jsonmetadefs` SourceKind support to Modustro Builder **1.1 in `pub.pltf.Modustro`** (including its Gradle plugin and local bootstrap regression tests), rather than editing the existing Builder 1.0 scripts as a permanent substitute.
2. Complete integration and regression testing of explicit `x-algites-defscodegen-extends` and `x-algites-defscodegen-choice` semantics in both Java and Python Defs frontends and canonical merger. Never infer fields, generated inheritance or choice types from the standard validation combinators. Preserve validation independently. Adding legacy metaschemas is not equivalent to implementing legacy input dialect readers.
3. Build and migrate `pub.tool.General` and `pub.lib.General` before proceeding to other repos; fix the corresponding XSD types without falling back to `xs:anyType` for required structured data.
4. Verify resource-only artifact packaging and staged public URLs for all six meta-schema dialect families and Markdown vocabulary. Publish only after Builder 1.1's local generation, staging and integration tests pass.
5. Switch individual `settings.gradle.kts` to the tested Builder 1.1; switch GitHub Actions workflows **last**, once Builder 1.1 is used everywhere required.

The current universal bootstrap does not deploy to Scaleway and does not yet recognize `jsonmetadefs` as a canonical definition kind. The stable `$id` values in the current sources are **proposed** public identifiers, not claims of deployment.



## Java/Python parita a testování


## Ekvivalence nativních implementací a testovací brány

Tyto testy a ověřovací podmínky zahrnují historický generátor; přesná ekvivalence nového Java/Python kanonického backendu musí být potvrzena plným Java buildem.

The Java and Python Defs Codegen implementations must implement **the same
canonical pipeline**. Their differences should be implementation-language
syntax and unavoidable runtime concerns, never alternative rules for schema
identity, source-name parsing, or emitted Java/Python declarations.

### Runtime architecture

1. Read the explicitly selected input naming catalog and profile.
2. Parse the schema filename using `file_name_stem` and `file_name_suffix`.
   Do not guess the version from underscores or other delimiters.
3. Validate globally named XSD types and named `$defs` entries with the same
   `type_name` rule. Convert a declared type's *local* name with the naming
   catalog. Keep source identity (XML QName or JSON URI + JSON Pointer) separate
   from that local name.
4. Build the canonical, format-neutral definition and resolve references.
5. Generate the requested Java **and** Python sources via each native generator;
   check the complete file set and exact lexical content apart from whitespace.

`AIcDeclaredTypeIdentity.java` and `aic_declared_type_identity.py` implement
stage 3 with the same validation and round-trip checks. The JVM schema reader
and repository binding generator both use the Java helper for named `$defs`;
the XML frontend uses it for global XSD types.

### Mandatory parity tests

`AItcGeneratorImplementationParityTest.java` is a TestNG test under the usual
`src/develop/java` source set. It launches the artifact-local Python
`generator_implementation_parity.py` suite and feeds it the JVM test classpath
and JVM-generated fixtures. Consequently **the normal Gradle Java test task**
executes both native implementations and fails if they disagree. No separate
parity script or bootstrap action is needed.

- Each native generator independently runs the *same* declarative repository
  manifest with both `java` and `python` outputs enabled.
- Generated manifest results and every generated path must match. It is not
  sufficient for a single target language, one file, or an empty result to pass.
- Java and Python contents are token-compared, preserving syntax, declarations,
  string literals, comments, indentation structure, and statement boundaries.
  Whitespace-only differences are tolerated.
- `--check` mode is exercised for both generators; an intentionally deleted
  generated file must make both checkers fail.
- A second layer independently generates 30 first-stage fixtures: three schema
  formats, two target languages, five source schemata. These include real
  examples of nested types, scalars, enum values, collections, restrictions and
  cross-schema references.
- The parity-specific XSD fixtures `parity-supported` and
  `parity-supported-builtins` use typed replacements for `xs:anyType` and
  `xs:anySimpleType`, which the current frontend intentionally rejects.
  The unconstrained `parity-builtins` and `parity-root` three-format
  fixtures are retained in `impl/src/develop/examples/` for negative and
  semantic tests. They are deliberately outside the immediate build-source
  input directories `impl/src/develop/{jsondefs,yamldefs,xmldefs}`; those
  directories are scanned recursively by the bootstrap. Moving the fixtures
  below `examples` leaves their original semantics intact while excluding
  them from bootstrap generation. The supported positive root scenario is
  `parity-supported`, not the original unconstrained `parity-root`.
  Earlier develop-only parity fixtures contained the artificial
  `x-test-xsd-type` marker. It has been removed from the fixtures because
  it does not belong to the Algites schema vocabulary. The historical
  `x-modustro-datatype` hint remains on certain test-only scalar fields
  because the `.old` frontend currently consumes it; it is not an
  agreed public vocabulary keyword. Neither hint is required for the
  unconstrained `anyType` or `anySimpleType` negative fixtures.
- `AItcDeclaredTypeIdentityTest.java` and the existing Python named-type tests
  also verify canonical source-name mapping and rejection of malformed names.

On a properly configured Modustro/Gradle build, `check` is expected to run the
normal Java and Python verification tasks. JVM parity tests require the resolved
`MODUSTRO_ARTIFACT_DIRECTORY`, `MODUSTRO_PYTHON_TEST_EXECUTABLE`, and
`MODUSTRO_PYTHON_TEST_PATH` values supplied by the Gradle test configuration.
Missing inputs fail the test rather than silently disabling parity.

### Aktuální automatické kontroly parity

- `impl/src/develop/python/test_java_python_contract_equivalence.py` kontroluje
  skutečně emitované Java/Python gettery, DataObject metadata a zachování
  hodnot řetězcových, logických a celočíselných enumů. Testy probíhají nad
  stejným kanonickým vstupem, nikoli jen porovnáním textů generátorů.
- `dialect/src/develop/python/test_method_naming_role_consistency.py` kontroluje
  role `Common`, `Defs` a `SDO` u profilů Algites, Standard Prefix a
  Standard Postfix v obou jazycích, včetně vazby na společný profil.
- Java `AIcCommonContractProjection.canonicalIdentity` a Python
  `_common_identity` zachovávají stejné bezpečné přepisy přesných, verzovaných
  XML publikovaných URI a Algites URN; nesouvisející identity nesmějí splynout.
- Starší test `test_format_contract_covariance.py` stále odhaluje rozdíl
  mezi očekávanou nominální root `$ref` aliasací a skutečným výstupem.
  Neodstraňovat tento test ani jeho očekávání bez rozhodnutí o sémantice.
- Plná shoda nativních Java/Python kompilátorů vyžaduje spuštění
  TestNG/Gradle parity brány. Samotné úspěšné Python testy nejsou jejím
  ekvivalentem.

### Still requiring a full installed-dependency run

Parity of the complete repository generator cannot be certified until the
Gradle TestNG integration executes with all JVM dependencies. In particular,
compare keyed common interfaces, specialized XML projections, synthetic
namespace contracts, and generated import resolution. Keep deviations visible
in the comparison; do not make the normalizers semantically permissive.


## Ekvivalence skalárních typů a tří formátů

The develop fixtures have distinct roles: the `parity-supported` root and
`parity-supported-builtins` exercise currently supported generation; the
unconstrained `parity-root` and `parity-builtins` are retained separately
under `impl/src/develop/examples/` to exercise rejected XML constructs.
The supported root refers to `parity-child`, which refers to `parity-leaf`.
It also exercises object collections, enums, optional and nullable fields,
scalar collections and basic facets. The first two schema source kinds use
JSON Schema serialization for YAMLDEFS and JSONDEFS; XMLDEFS uses XSD.
The supported root still exposes known parity differences for nullable
values and anonymous XML object types; do not report full three-format
structural equivalence until those tests pass.
The original-semantics `parity-builtins` fixtures in `impl/src/develop/examples/parity-builtins/`
cover all XSD 1.0 built-in datatype families, including the three built-in
list types and `anySimpleType`/`anyType` (46 fields). These test the intentionally
unsupported unconstrained forms. The positive cross-language and cross-format
bootstrap-compatible fixture is `parity-supported-builtins` (46 fields), with
typed stand-ins for the two unsupported cases.

Both Java and Python generator implementations test all three frontends and both
output languages. Comparisons normalize only source identity, resource and source
kind, retaining documentation and every represented constraint. Separate tests
compile generated Java and execute generated Python, checking nested references,
large integers, decimal precision, numeric boundaries, string lengths/patterns,
inline enums, binary content, calendars and missing-versus-null values. The Java
suite also checks fixture XSD validity with the platform SchemaFactory.

### Exact representations

| Schema family | Java output | Python output |
| --- | --- | --- |
| integer and integer subtypes | BigInteger with subtype bounds | int with subtype bounds |
| decimal / JSON number | BigDecimal | Decimal |
| float / double | Float / Double | float; float conversion rounds to binary32 |
| date/time and partial calendars | XMLGregorianCalendar | lexical calendar value with exact year/fraction/timezone |
| duration | javax.xml.datatype.Duration | lexical calendar duration |
| hexBinary / base64Binary | byte[] | bytes |
| scalar strings and QName families | String with retained datatype metadata | str with retained datatype metadata |
| lists | List of the item type | tuple of the item type |

`x-modustro-datatype` carries XSD datatype identity when JSON Schema has no exact
native equivalent (float/double, partial calendars, QName, integer subtypes).
Standard `format` and `contentEncoding` annotations also select the relevant
scalar representation. Standard minimum/maximum/exclusive bounds, string length,
pattern and scalar enum facets are retained and enforced by generated classes.

For exact JSON numbers in applications, use `json.loads(text, parse_float=Decimal)`;
precision already lost by a floating-point JSON parser cannot be reconstructed.
`to_mapping()` deliberately retains Decimal values; use a Decimal-aware JSON
serializer. Java callers now pass BigInteger/BigDecimal where generated records
previously used Long/Double. Existing handwritten Intf property constructors
remain available; new constraint components extend the canonical model API.
Scalar roots generate a typed `value` component instead of an empty record.

### Scope

This is type-preserving generation with basic scalar validation, not a complete
XSD/JSON Schema document validator. The canonical model does not retain inline
object field contracts, arbitrary unions, XSD choices, identity constraints,
attributes, namespace bindings for QName values, totalDigits/fractionDigits or
all XML string normalization and lexical restrictions. Use a schema validator
when full document validation is required. Patterns in the parity fixtures use
the common Java/Python/XSD subset; arbitrary regex dialects are not equivalent.
JSON Schema `format` has annotation semantics by default; the generated calendar
representation follows the explicit XSD datatype family, not every format
assertion rule. Source APIs do not parse XML instance documents.

No new runtime dependency on pub.lib.General is introduced. The Python scalar
support is embedded into generated modules; Java uses the JDK's math and XML
APIs. The runtime resource and its Python source copy must remain byte-identical.


## Omezení a publikační pravidla

**Potvrzené limity nového kanonického backendu:** obecné `patternProperties`,
libovolné `anyOf`/nullable unie, `additionalProperties: true`, XML→MAP,
externí XSD import v samostatném novém frontend režimu, pokročilé XPath
identity constraints, některé skupinové/násobné `xs:choice`, přesné desetinné
enumy a vybrané kardinality kolekcí. Vstupy se mají odmítnout s diagnostikou;
neomezovat tiše deklarovanou sémantiku. Historický `defs.old` může mít širší
ověřené funkce, které nelze automaticky přičítat novému backendu.

**Nedokončené body:** převod interního Java kanonického grafu z 11 ručně
spravovaných recordů na generované SDO, odstranění Python konstrukčních adaptérů,
plné Java/Python funkční paritní testy, úplné Defs→SDO end-to-end a přepnutí
produkčního bootstrapu. Dokud to neprojde, ponechat `.old`.

**Regresní sada:** `impl/src/develop/{java,python}` (frontend, merger/linker,
kontrakty, XML key, union/choice, scalars), `dialect/src/develop/python`
(meta-schema/vocabulary) a `cli/src/develop/java` (vrstvení parametrů).
Testy jsou tříděny podle ověřovaného business pravidla; historická revizní
čísla nejsou součástí nových názvů testových souborů. Specifická pravidla
pojmenování, vstupních artefaktů a dalších generátorů jsou navíc ve společné
`../CODEGEN-REFERENCE.md` a `../CODEGEN-ARTIFACT-INPUTS.md`.

**Údržba:** při každé změně vstupního schématu, vydávaného API, CLI,
podporované funkce nebo diagnostiky aktualizovat příslušnou kapitolu tohoto
`DEFS-CODEGEN-REFERENCE.md` a krátký `README.md`. Nevytvářet poznámkové
`*-STATUS.md`, `*-MIGRATION.md` ani další paralelní manuály.

### Jednotné spouštění z univerzálního bootstrapu (2026-11-04)

Univerzální `devops/bootstrap/generate_sources.py` sestavuje **kvalifikované CLI argumenty**
a volá veřejnou vstupní metodu `AIcDefsCodegenCli.main(args)`. Nevolá přímo
interní `AIcSchemaContractBindingsGenerator.generate_manifest()`. Python SDO se
volá stejným způsobem přes své `main(args)`; Java SDO se spouští přes své
Java CLI až po kompilaci read-only rozhraní (Gradle `bootstrapSdoJava`).
V obou případech zůstávají Defs a SDO zcela nezávislé a nastavují se pro ně
samostatné `codegen_common` + `codegen_defs` / `codegen_sdo` profily.

Přepínač je společný pro obě CLI a všechny cílové technologie:

```sh
bash devops/bootstrap/bootstrap.sh --prepare-only \
  --codegen-validate-one-input-at-a-time-only=false
```

Výchozí `true` zachovává rychlé ukončení při první vstupní chybě. `false`
shromáždí rozpoznané chyby u všech vstupů **jednoho volání CLI** a vypíše
zdrojové soubory a příslušná místa. Při chybách se tato dávka nezapíše do
generovaných výstupů. Politika je předávána prostředím
`MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY` i explicitním CLI
argumentem; jiné hodnoty než `true`/`false` jsou odmítnuty.

**Omezení současného bootstrapu:** vybrané artefakty zpracovává oddělenými
voláními CLI. Výpis není ještě jednou atomickou validační transakcí za všechna
`--root` artefakta. Univerzální bootstrap dál používá `.old` generační backendy,
nikoli dosud neúplný nový kanonický Defs backend. Nezaměňovat změnu vstupní
vrstvy CLI za migraci samotného generátoru.
