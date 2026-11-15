# Defs Codegen — referenční příručka (1.1-SNAPSHOT)

> **Platnost a zdroje pravdy.** Tento dokument konsoliduje funkční specifikace a
> ověřená omezení implementací Java/Python; původní přechodové poznámky a lokální
> Přechodné stavové dokumenty nejsou autoritativními příručkami. Bootstrap byl přepojen na kanonické Python Defs CLI a aktuální SDO CLI,
> ale úplné generování stále blokují nepodporované konstrukce schémat.
> `defs.old` zůstává zachován jen pro historické scénáře. Zde popsaná zamýšlená sémantika není
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
| `defs.old` | Historická Java/Python implementace s širší podporou XSD | Zachována pouze jako historický zdroj; její testy byly odstraněny |
| Nový Python kanonický backend | Sedm kindů, merger/linker/normalizátor/emitter nad *generovanými* SDO objekty | Ověřeny cílené JSON/YAML/XML → Defs → samostatný SDO průchody; konstrukční adaptér zatím existuje |
| Nový Java kanonický backend | Frontend, merger, linker, emitter a read-only DataObject výstup | Interně stále používá ruční `AIcdDefsCodegen*` recordy; celý build a SDO průchod neověřeny |
| Produkční builder | Univerzální bootstrap `devops/bootstrap` | Bootstrap volá standardní veřejné Defs CLI; úplné end-to-end ověření není uzavřené |

**Budoucí (dosud neimplementované) uspořádání artefaktů:**
`model.schema → model.do → model.sdo` jako produktové API závislosti,
`intf → model.do`, `impl → model.sdo`; vyžaduje obecnou fázi generování v
builderu 1.1. V tomto snapshotu se soubory nepřesouvají; bootstrap mění pouze volání generátorů a skládání manifestů.

## Kanonický model a realizace

Schémata modelu jsou autoritativní. Sedm strukturálních kindů je `TYPE`,
`ELEMENTLIST`, `ELEMENT`, `LIST`, `MAP`, `SCALAR`, `ENUM`; `REFERENCE` a
`UNDEFINED` jsou pouze dočasné stavy. Vstupní vazby `sourceBindings` musí
uchovat všechny vazby ke konkrétním zdrojovým formátům, identitám a pointerům.
Generator nepřevádí neznámou sémantiku na `ANY` bez explicitního odmítnutí.

**Typová bezpečnost veřejných getterů:** žádný současný Java/Python emitter
nesmí použít `Object`/`Any` jako náhradní typ nevyřešeného pole, ani v
`List`, `Map` či `AIiMultiMappedList`. Kanonické `ScalarKind.ANY` může být
přechodným stavem při čtení vstupu, ale při emisi veřejného DataObject
getteru vyvolá diagnostiku s identitou pole a požadavkem na konkrétní typ.
Totéž platí pro společný kontrakt: slučování XML/JSON/YAML nesmí při
nekompatibilních signaturách getter zahodit. Zastaví se s diagnostikou
konkrétního pole a návratových typů. `Object`/`Any` používané čistě jako
interní typ dynamického parseru nebo runtime cache není tímto zákazem
dotčené.

Původní strukturální rozdíl naming conventions byl opraven ve vstupních
schématech: XSD `IdentifierConventions/IdentifierConvention` a odpovídající
JSONDEFS/YAMLDEFS mají nyní shodný model seznamu objektů s povinným
`name`; stejné pravidlo platí pro `VersionConvention`, `NameFragment`,
`NameComposition`, `NameConvention` a seznam `Rule` s klíčem `kind`.
YAML katalogy používají explicitní seznamy a Java/Python čtečky si teprve
interně vytvářejí indexované mapy. Neřešíme tedy rozdílnou strukturu
netypovaným getterem ani odstraněním getteru ze společného kontraktu.

**Kovariance všech Java kolekčních getterů:** aktivní Defs emitters (Java i
Python backend) generují `java.util.List<? extends T>` a
`AIiMultiMappedList<? extends T>` bez ohledu na původní dialekt XMLDEFS,
JSONDEFS/YAMLDEFS, konkrétní nebo společnou projekci a vnoření seznamu.
U víceúrovňových seznamů se kovariance uplatňuje na každé úrovni.
Výjimka se týká pouze typových argumentů v deklaraci `extends` u samotného
pojmenovaného kolekčního *rozhraní*, kde Java nepřipouští wildcard jako
přímý supertyp; toto není getter. Parametry zapisovacích metod se tím nemění.
Samostatné `additionalProperties: true` bez hodnotového schématu neposkytuje
konkrétní hodnotový typ, proto na veřejném DataObject rozhraní stále nesmí
vzniknout `Map<String,Object>` jako zástupný typ.

**Otevřené bázové schéma pro odvozené profily:** Jestliže rodičovský
JSONDEFS/YAMLDEFS dokument přes `allOf` poskytuje jen pojmenovaná
sémantická pole, neuvádějte na jeho kořeni `additionalProperties: true`.
V JSON Schema je povolení neznámých vlastností výchozím stavem také při
vynechání tohoto klíče; nezakládá však tím žádné další typované pole.
Výslovné `additionalProperties: true` nebo `{}` Codegen ignoruje pro
účely typovaných getterů a vypíše warning s cestou, JSON pointerem, rizikem
ztráty neznámých hodnot a ukázkou typované deklarace. Nevytváří se
`Map<String,Object>` ani jiný getter s hodnotou typu `Object`/`Any`. Nezaměňovat s
`additionalProperties: false`, které mění validaci a může zabránit
rozšíření rodičovského schématu. Pokud se mají neznámé vlastnosti i
uchovávat a serializovat, potřebují explicitně typovanou definici.


Generované kanonické read-only typy jsou v
`intf/src/product/{java,python}.gen`; Python generované interní SDO objekty
jsou v `impl/src/product/python.gen`. Do žádného `.gen` zdroje se ručně
nezasahuje. Třídy `AIig*` jsou zdrojové **read-only kontrakty**, zatímco
`AIigd*` v `model.impl.intf` jsou **samostatná zapisovatelná SDO rozhraní**,
která `AIig*` dědí; `AIcgd*` jsou jejich SDO implementace. Generování
`AIigd*` není druhým průchodem Defs nad stejným schématem. Umístění
`model.impl.intf` je stávající volba `--sdointf-subpackage` v bootstrapu,
nikoli identita kanonického typu. Jeho případná změna musí být provedena
současně v Java/Python SDO výstupech, resolverech a testech; nelze ji
simulovat ručním přesunem `.gen` souborů. Python bootstrap nyní znovu
nepředává již vygenerovaná zapisovatelná rozhraní SDO generátoru jako
read-only vstupy, ani pokud se změní pojmenovací prefix. Pro Java CLI
totéž zajišťuje kontrola dědičnosti `AIiSmartDataObject`.

Handwritten canonical-model implementace v balíku
`eu.algites.tool.codegen.defs.impl.standard.model` používají prefix
`AIcDefsCanonical*` a rozhraní `AIiDefsCanonicalStructure`.
Pro zachování Git historie přejmenování je k dispozici
`devops/migrations/rename-defs-canonical-classes.sh` (`git mv`), který
je vhodné spustit **před** rozbalením přejmenovaného checkpointu. Python již nepoužívá vlastní `canonical_model.py`, Java nadále
používá staré ruční recordy jako přechodný interní model. Nejde o finální stav.

Příklady regenerace / kontroly (se zavedenými zdrojovými závislostmi):

```sh
# Produkční cesta používá pouze současné veřejné Defs CLI:
MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source bash devops/bootstrap/bootstrap.sh \
  --root generators/code/defscodegen/intf --prepare-only
python generators/code/defscodegen/impl/src/develop/python/regenerate_sdo_canonical_fixtures.py --production --check
```

**Aktivní bootstrap a kompatibilita:** `generate-canonical-contracts.py`
používá aktuální veřejné Defs CLI. `generators/code/bootstrap-selfhosted.sh`
a historické `generators/code/regenerate_sources.py generate` jsou pouze
kompatibilní vstupní body přesměrované na společný bootstrap a jeho nová CLI;
nesmějí importovat ani spouštět `defs.old`. Historické implementace zůstávají
pouze pro izolované legacy testy. Oddělené `.extgen` se musí regenerovat
koordinovaně s nezávislým SDO Codegenem.

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
shodovat s výběrem společného profilu. Další vstupy/výstupy a interní pracovní adresáře popisují následující kapitoly.


## Kvalifikované dávkové CLI, vrstvení settings a katalogů

**Rozsah:** veřejné kvalifikované parametry používané kanonickým Defs CLI i bootstrapem. Implementace v `.old` slouží pouze jako historická kompatibilní reference.

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
XMLDEFS, YAMLDEFS, and JSONDEFS **generation inputs**. Use their
`--defs-dependency-artifacts:TECH` counterparts for resolution-only artifacts. See
[CODEGEN-ARTIFACT-INPUTS.md](../CODEGEN-ARTIFACT-INPUTS.md) for Modustro
selectors, PEP 508 constraints and source bootstrap requirements.


## Kanonický kompilátor a jednotné veřejné CLI

**Rozsah:** kanonický backend s veřejným kvalifikovaným CLI. Úplná parita staršího backendu zatím není ověřená.

The canonical compiler now supplies the Python bootstrap entry point, but still supports only a subset of Defs contracts. It uses the independent Java and Python canonical schema frontends, model merger, reference linker and generated-schema validation, followed by a native source emitter. It does **not** call the `defs.old` backend. Bootstrap invokes the same qualified CLI as a direct user invocation; it does not construct public configuration manifests. This does not imply full schema compatibility or successful production bootstrap.

### What it currently emits

- Java interfaces and Python typed abstract interfaces for supported object declarations, preserving source member names through explicitly selected getter/setter naming rules.
- Named reference properties (including recursive references), schema inheritance, unconstrained arrays and supported maps.
- String, boolean and arbitrary-precision integer enums, preserving their typed values and lexical source codes in the canonical model. Java integer enums expose `BigInteger code()`; Python uses integer-valued `Enum` members. Decimal-number enums are rejected until source parsing can preserve exact numeric precision.
- Explicit scalar and supported structured `x-algites-defscodegen-choice` alternatives represented as Java `sealed interface` with same-package `record` variants and Python frozen dataclass variants marked `@final` (a static typing restriction, not a runtime-sealed hierarchy). Structured variants preserve member ordering and catalog-derived typed getters. Their private component names (`field1`, `field2`, etc.) are stable storage positions; required values are checked in variant constructors, while optional members can be `null` / `None`.
- Java and Python outputs separately named through their own selected Common + Defs naming profiles and the external Algites source-code naming catalogs.
- **Local XMLDEFS `xs:key` / `xs:unique` on a directly repeated child of a named or inline complex container**. The enclosing element retains its original referenced nominal TYPE; a key **never creates a new TYPE**. The repeated child getter returns `AIiMultiMappedList<? extends T>`. An index declared on a reference is stored on that reference getter using repeatable Java `@AIaDataObjectListKeyDefinition(selector = "ChildList", ...)` or Python `__scoped_key_definitions__`. The matching runtime index exists only on the particular parsed object instance reached through that reference, not on unrelated occurrences of the same TYPE. Direct-list declarations retain the original Java annotation without a selector and Python `__key_definitions__` metadata. Multiple/composite keys and typed nested scalar field paths (for example `identity/code` → `identity.code`), including terminal XML attributes (`@name`), are supported when every segment resolves without ambiguity. Keyed lists require structured named items. The independent SDO Codegen must preserve selectors and the `AIiMultiMappedList` return type in Java and Python; Python XMLDEFS interfaces emit `__xml_repeated_fields__` for all direct LIST members.

**Unsupported structural inputs are rejected rather than approximated.** Unsupported validation-only JSON Schema conditions are reported with source-path warnings and deferred to marshalling validation; source schemas remain intact. In particular, nested/repeated choice groups, bounded arrays whose constraints cannot be preserved by these contracts, decimal-number enums, **XSD `xs:keyref`, global-element keys, namespace-qualified/descendant/predicate XPath selectors, keys selecting non-direct or multiple collections**, certain JSON Schema validations, and unrestricted SDO accessor/lifecycle generation are not yet implemented end to end. Generated output should not be treated as a drop-in replacement for the previous code generator.

### Independent SDO Codegen

This Defs CLI generates only DataObject interfaces. It does not generate mutable
SDO sources and it never consumes SDO naming conventions. Writable interfaces
and concrete implementations are generated by the separate SDO Codegen from
DataObject interfaces, whether they were generated by Defs or written by hand.
The SDO CLI accepts interface sources/artifacts, not Defs input schemas or the
Defs canonical model. The canonical Defs CLI uses public qualified parameters; `.old` is only historical compatibility code.

### Vstupy, závislosti a spuštění (1.1-SNAPSHOT)

All four source selectors are **qualified by target technology**. No CLI caller,
including bootstrap, creates or supplies an external manifest. Artifact
selectors are interpreted by the Modustro artifact resolver; explicit paths
can denote source directories, schema files and supported packaged archives.
List entries are separated by semicolons (`;`); repeating a list selector adds
entries rather than replacing the earlier list. Java and Python have the same
source-selection semantics, independently of the native implementation language.

| Option | Scope | Meaning |
|---|---|---|
| `--defs-input-artifacts:TECH=LIST` | Java/Python | Packaged schema sources to generate |
| `--defs-input-paths:TECH=LIST` | Java/Python | Local schema sources to generate |
| `--defs-dependency-artifacts:TECH=LIST` | Java/Python | Packaged schemas and previously generated contract definitions to **resolve only** |
| `--defs-dependency-paths:TECH=LIST` | Java/Python | Local schema/contract directories and archives to **resolve only** |

`TECH` is `java` or `python`. An input selection determines what gets
emitted; the dependency collection never expands the set of generated schema
contracts. For each logical TYPE the new generator emits a single common
read-only interface, with independent XMLDEFS/JSONDEFS/YAMLDEFS metadata on
that interface and its getters. External references are linked against these
unified contracts, with independent metadata for each source format. Input and dependency selectors are independent
of the naming selectors; the latter remain available as **ordinary CLI flags**
and as per-generator `.settings` defaults.

Local input paths may be outside the checkout: before compiling, the CLI copies
such sources into its **own invocation UUID worktree**, preserving the
`xmldefs/`, `jsondefs/`, or `yamldefs/` technology directory and the
package-relative source structure. A directly selected schema file still
selects only that file for generation; neighboring files are materialized
only to preserve relative schema imports. Paths selected as dependencies are
used exclusively for resolution and are never promoted to generation inputs.
Source files must retain a technology/package path so naming and package
identity come from the public naming conventions rather than a guessed title.

Example (the selected Algites profile can supply the naming flags from the
ordinary `defscodegen-python.settings` resource):

```sh
python -m eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli \
  --repository-root=. \
  --defs-input-paths:python=naming/convention/intf/src/product/jsondefs \
  --defs-dependency-paths:python=other/module/intf/src/product/python.gen \
  --technology-dointf-output-dir:python=naming/convention/intf/src/product/python.gen \
  --common-codegen-naming-convention:python=algites-python-codegen-common_1 \
  --defs-codegen-naming-convention:python=algites-python-defscodegen-standard_1
```

Java uses `AIcDefsCodegenCanonicalCli` with exactly the same qualified
options. For manual invocations, every `--naming-conventions-file`,
`--input-schema-naming-convention`,
`--output-interface-technology-naming-convention`,
`--output-enum-technology-naming-convention`, Common/Defs profile and output
option remains valid directly on the command line. A `--settings-file=PATH`
merges those options before explicit overrides. The old `--manifest` switch
is **not a public CLI parameter**. The native compiler may create private
short-lived JSON batches under its run-specific `tmp/` workspace; their
structure is not a configuration contract and bootstrap must not create them.

### Isolation, publication, cleanup and parallel builds

For each invocation, Defs allocates the unique path
`<repository>/build/<artifact-relative-path>/defscodegen/<UUID>/` containing
`tmp/`, `staging/`, and `.run.lock`. UUIDs are generated internally. Different
artifacts never share temporary paths; the SDO generator uses a separate
`sdocodegen/` subtree. The generator renders and validates the complete batch
before it publishes. Publication is serialized only for the owning artifact
and generator by an OS file lock at `defscodegen/.publish.lock` and uses a
staging directory plus tracked ownership hashes. By default,
`--cleanup-output-folder-before-generation=false`, a generation run **only
replaces the files it generates in that invocation**. It does not delete
obsolete files or other sources, and works even after unpacking a source
archive without the transient `build/` ownership index. The index is updated
with the newly emitted paths. A changed file at an expected generated path is
replaced deliberately; unrelated paths remain untouched.

With `--cleanup-output-folder-before-generation=true`, previously indexed,
now obsolete outputs **of this generator** are removed along with publication.
The cleanup is scoped by artifact and producer: it must not delete SDO sources
from a `*.gen` directory shared by Defs and SDO. In the universal bootstrap,
this option additionally enables a one-time full cleanup of the selected
`*.gen` source directories *before either generator starts*, never between
Defs and SDO. Without the flag, bootstrap does not empty generated trees.

Use the same unqualified boolean option for **Java and Python** Defs CLIs or
add it to the layered settings file:

```text
--cleanup-output-folder-before-generation=false
```

A normal second invocation replaces only its current output paths, even if
`build/` was not present in an unpacked checkout. Historical stale files are
**not detected by content or name prefix**: when the index is missing, no
obsolete paths can be safely identified by standalone cleanup. An explicit
full cleanup through bootstrap is needed if all legacy `.gen` files must
be removed. Example:

```sh
bash devops/bootstrap/bootstrap.sh --prepare-only \
  --cleanup-output-folder-before-generation=true
```

This removes **every file** from the selected `src/<branch>/java.gen` and
`python.gen` trees, including files not produced by Defs; run it only when
all selected generated sources can be rebuilt. `--root` limits the cleanup
scope. `--plan-only` does not delete anything; `--check` is read-only and is
incompatible with cleanup=true. The `--clean-only` command acts only on this
Codegen's indexed outputs and is not equivalent to full bootstrap cleanup.

Generated code belongs only in the configured `src/product/java.gen` and
`src/product/python.gen` trees. No generator edits these trees by hand.
`--check` compares each expected source against the current file bytes, even
without a build index, and never writes. `--check` and cleanup=true conflict. Publication
backs up previously generated files, renames staged outputs into place and
attempts rollback on ordinary failures, including owned-file deletion and the
index itself. **This is not a crash-proof atomic multi-file transaction:** an
abrupt termination or failed rollback can leave a partial update. The
workspaces protect independent concurrent builds, not simultaneous writers
to the same artifact and output outside the generator-managed transaction.

A successful invocation removes only its own UUID directory. On an ordinary
failure the default is also to remove that directory; diagnostic retention
must be explicitly enabled by the caller. Cleanup walks only UUID children
under the selected artifact/generator, skips those with active `.run.lock`
locks, and never deletes another artifact's workspace. `build/` cleaning must
be orchestrated when no active build is using that directory. Both Java and
Python respect the same artifact/generator lock locations.

**Java canonical model:** the Java frontend, merger, linker and emitters now
use schema-generated SDO model implementations from
`impl/src/product/java.extgen`, through internal `AIcDefsCanonical*` accessors
in `impl.standard.model`. These subclasses store **no additional canonical
fields**: accessors use the generated SDO getters/setters; union variants
are represented by generated sealed choice records and input source bindings
by the generated multi-mapped SDO. The 22 previous public, handwritten
`AIcdDefsCodegen*` DTO/enum/normalizer files and their independent structure
hierarchy were retired. The internal accessors validate constructor invariants
and provide structural equality while keeping the generated schema as the
single canonical structure definition. Java and Python retain independent
implementations of the algorithm and resolver, not duplicate model schemas.

**Java bridge versus generated SDO contract (P14):** Java SDO list getters
use the generated `*List` method names (for example `getChildrenList()`,
`getKeyDefinitionsList()`, `getSourceBindingGroupList()`) and covariant
`List<? extends T>` element types. Generated occurrence/length bounds are
`Long`, with checked conversion to the canonical integer API; the bridge
must not assume `BigInteger` setters. The `Type` object exposes exactly one
named `TypeContent` alternative (structure or `target_identity`) after
resolution, while temporary `REFERENCE`/`UNDEFINED` types may leave `Content`
absent until the linker finishes. `Structure` and `ElementListChild`
choices are **immutable same-package sealed Java record variants** with no
mutable SDO implementation of their own. The Java bridge constructs and
inspects those actual records, never synthetic mutable `Selected*` wrappers.
When a generated SDO list requires at least one item, the bridge initializes
that complete list atomically through the generated SDO mapping constructor;
creating an invalid empty list and later appending items fails SDO cardinality
validation. This applies especially to provenance `BindingList` and its
`SourceBindingGroupList`. These rules have a Java regression test covering
both `TypeContent` variants, pending references, typed keys, list bounds,
choices and source bindings.

JSONDEFS/YAMLDEFS indexed maps now share the same homogeneous-map rule in
both native frontends: explicit `properties` are allowed when every property's
value schema is identical to `additionalProperties`. More specific per-key
constraints remain unsupported and are reported, not discarded. Key IDs and
field names continue to come from `x-algites-defscodegen-key`.


### Remote reference resolution and inheritance

The current canonical Defs Codegen has **independent Python and Java HTTPS
schema resolvers** (`SchemaReferenceResolver` and
`AIcDefsCodegenSchemaReferenceResolver`). A public schema URI retains its
identity regardless of transport. Local declared source roots are consulted
first, followed by the SHA-256-named disk cache and then bounded HTTPS. JSON
references verify `$id`; XSD imports verify `targetNamespace` against the
import declaration. XML DTDs/entities are forbidden. This is a reference
lookup, not permission to emit a duplicate type.

The canonical Defs CLI resolves imports from the **explicit dependency**
selectors documented above. JSON/YAML schema identities (`$id`, source schema
ID/version and URI/JSON Pointer fragments), XML `targetNamespace` and QNames,
and Java/Python format-specific DataObject annotations are used to associate a
schema definition with its already generated contract. A dependency schema
alone is not evidence that a corresponding compiled/interface contract exists;
missing or ambiguous parents are errors, never silently synthesized types.
The resolver may consult the bounded HTTPS schema cache for missing remote
schema resources, but it must not treat remote discovery as new output input.

**Demand-driven contract indexing.** The external-contract index is scoped to
identities *actually referenced by the selected generation inputs*. For XMLDEFS,
this means a resolved `{targetNamespace}localTypeName` QName used with an
imported namespace (for example `xs:extension/@base`); declaring a local named
XSD type does not make it an external dependency. For JSONDEFS/YAMLDEFS,
explicit external schema inheritance references select the corresponding
published schema URL. Unreferenced generated contracts in dependency artefacts
must not cause naming or inheritance conflicts, even when two dependency
roots contain different historical definitions of the same symbol. No external
identities means the contract index is empty; the selected input schemas are
still validated and generated normally.

**Consistent Java source/binary identities.** The index reads `.class` interface
names and parent types as fully qualified binary names; when scanning `.java`
sources it must resolve `import` statements and the source package before
comparing the same interface. A matching source and compiled copy is not a
conflict merely because one declares a short imported parent name. For an
*actually referenced* identity, contradictory copies with the same fully
qualified symbol remain an error and include the identity, both source paths,
and both parent sets. Different, unrelated interfaces sharing one referenced
identity likewise remain ambiguous; the resolver must never silently choose a
random first match. Python source contracts follow the analogous import-aware
parent-name comparison. The paired index regressions in
`test_native_schema_reference_resolver.py` and
`AItcDefsCodegenExternalContractIndexTest.java` cover these cases.

#### Published JAR and wheel dependencies (offline)

Each `--defs-dependency-paths:java` entry may identify a compiled JAR, a
`.class` tree or a checkout; `--defs-dependency-paths:python` may identify a
wheel, a Python module tree or a checkout. An archive is expanded **only** into
the current invocation's UUID `tmp/` directory, never into a shared source
root. The dependency index looks for published XSDs and JSON/YAML schemas by
public identity, not by the presence of a `src/product` layout; it also reads
`@AIaDataObjectXmlSchema`, `@AIaDataObjectJsonSchema` and `@AIaDataObjectYamlSchema` directly
from compiled Java class-file annotations (without loading or initializing a
Java class), and the corresponding Python contract metadata from wheel
modules (without importing or executing them). An external schema reference
becomes an inherited type **only** if its corresponding read-only interface
is resolved unambiguously. Writable SDO contracts must be excluded.

For example, the selected input may be one `child_1.xsd` while the
corresponding parent XSD and Java `.class` live in `dependency.jar` and its
Python read-only interface lives in `dependency.whl`:

```text
--defs-input-paths:python=sample/intf/src/product/xmldefs/example/contracts/child_1.xsd
--defs-dependency-paths:java=/libraries/dependency.jar
--defs-dependency-paths:python=/libraries/dependency.whl
```

The Java-specific identity key is `{targetNamespace}localTypeName` for XSD
types; schema-level JSON/YAML references use the verified public schema URL.
The user does not provide a manual `external_contracts` mapping. Tests
`test_public_defs_archived_dependencies.py` and
`AItcDefsCodegenExternalContractIndexTest` cover the archive/source separation,
XML parent binding and compiled Java metadata. This targeted validation is
**not** a substitute for the full bootstrap and Gradle suite.

Bootstrap's `devops/bootstrap/generate_sources.py` now builds **standard**
`--defs-input-*` and `--defs-dependency-*` argument lists, preserving the
existing profile selectors and output paths. Defs and SDO are invoked by their
own CLIs independently, with no coupled Defs→SDO pipeline. Passing targeted
resolver tests does not prove the complete installed bootstrap; full Java
and Python integration remains an explicit verification gate.

### Verification and migration criteria

Before claiming a working production bootstrap, the canonical backend must implement and test the complete Defs/SDO contract surface (including full multi-mapped identity constraints, mixed choice structures, inheritance and source metadata), run the Gradle/TestNG module test suites and complete Java/Python bootstrap with generated public API compatibility checks. The supported indexed LIST subset has been checked against the actual Java `AIiMultiMappedList` and annotation source contracts and the Python SDO key-metadata tuple format. **The supported XML subset now includes concrete Java/Python mutable SDO emission and verified XML round-trips**, but full schema support, every inherited and restricted SDO lifecycle case, and exact public API parity are still open. The current canonical compiler **does not satisfy all migration criteria**; the bootstrap switch is not yet a successful full build.



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
All read contracts use the common `AIiDataObject` inheritance contract;
no technology-specific DataObject marker is generated. The independent
`AIaDataObjectXmlSchema`, `AIaDataObjectJsonSchema` and
`AIaDataObjectYamlSchema` annotations identify schema representations;
SDO Codegen uses their metadata, not technology-specific superinterfaces.
Named XSD content
types additionally carry the declaration's expanded QName as
`AIaDataObjectXmlSchema(definitionKind=TYPE)` (Python: `__xml_schema__`),
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
Java and Python choice contract remains schema-neutral. XML projections
carry XML schema or field annotations rather than a separate XML DataObject
superinterface. This holds regardless of which source schema is selected
for the common canonical type.

This support applies to the **repository batch** which writes all discovered
compilation units. The single-unit `generate()` preview may contain references
to sibling contracts not created by that individual call. See
[rekurzivní kontrakty a XML](#generování-kontraktů-rekurze-dědičnost-xml-elementy-a-metadatové-vazby)
for XML limitations, `oneOf`/`anyOf` runtime semantics, and remaining deep
runtime validation work.

#### XML member representation

XMLDefs properties preserve `AIcdXmlFieldRepresentation` through the canonical
property model. Generated Java member getters carry `@AIaDataObjectFieldXmlSchema`
and generated Python read interfaces carry `__xml_schema_fields__`, preserving
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
ordered canonical property model: generated getters include `AIaDataObjectFieldXmlSchema.order` to make Java XML
serialization independent of reflection method ordering (Python retains the
same ordinal in `__xml_schema_fields__`). Canonical XML writing
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

#### Unified cardinality metadata (XMLDEFS, JSONDEFS, YAMLDEFS)

The canonical `Element`, `ElementList` and `List` structures carry
`min_item_count` and `max_item_count`; their Java accessors use
`minItemCount()` and `maxItemCount()`. The schema-generated DataObject API
uses `getMinItemCount()` / `getMaxItemCount()`. The common field annotation
uses `minItemCount` / `maxItemCount`, and Python metadata uses
`min_item_count` / `max_item_count`. Unbounded is represented by `-1`.

Format-specific source tokens belong only to schema readers (and schema
serialization/test fixtures): XSD `minOccurs` / `maxOccurs` and JSON Schema
`minItems` / `maxItems` both map onto the same canonical count fields.
The distinct `min_properties` / `max_properties` restrictions still describe
object-member counts, not collection item counts.

For example, `{"type":"array","minItems":2,"maxItems":4}` and
`<xs:element name="item" minOccurs="2" maxOccurs="4"/>` both yield
`min_item_count=2`, `max_item_count=4` for the corresponding collection.
The raw wire tokens must never appear as public metadata fields.

#### XSD restriction safety

For the supported `xs:simpleType` restriction subset, both language frontends
retain string and numeric facets in the canonical scalar and emit the effective
constraints as field annotations. A locally named scalar `xs:simpleType` may
restrict another locally named scalar `xs:simpleType`; aliases may be chained.
The final field gets the intersection of inherited and local length/bound
constraints, including exclusive endpoints, rather than only the last facet.
For example, a base `minLength=2, maxLength=20` narrowed by `minLength=3`
and then `maxLength=8` emits `minLength=3, maxLength=8` in Java and Python.
Cyclic aliases and unsatisfiable intersections fail with a contextual error.
Different nonempty patterns at multiple inheritance levels still require
conjunctive-pattern metadata, so they are rejected rather than silently lost.
Unsupported XML Schema scalar facets are likewise rejected. Attribute-only
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

For production source-checkout regeneration, use the public Defs CLI via
`bash devops/bootstrap/bootstrap.sh --root generators/code/defscodegen/intf
--prepare-only` from `pub.tool.General`, with the sibling `pub.lib.General`
available. The historical helper `generate-canonical-contracts.py` still
imports `defs.old` and **must not be used to refresh the committed read-only
contracts** before its migration. It can reintroduce general
`AIaDataObjectField` annotations onto JSON-specific interfaces even though
the current emitter correctly places them on neutral interfaces only.
Use the native Defs CLI `--check` for reproducibility checks rather than
treating the legacy helper as a parity oracle.

**Historical canonical bootstrap seed (not the new Defs output contract):**
older, generated temporary `.extgen` ABI seeds can still contain separate JSON
technology-specific shadow contracts. They must not be published or selected over
current unified `src/product/{java,python}.gen` DataObject contracts. The
new Defs emitter coalesces compatible declarations into one `AIig…` contract
per logical TYPE and attaches independent JSONDEFS, YAMLDEFS and XMLDEFS
metadata. The corresponding Java/Python external-contract indexers resolve
all three identities to that one interface; the legacy `old` implementation
remains separate and unchanged.

The disposable generation ownership manifest lives at
`build/run/canonical-contracts/generated-canonical-contracts.json`, not in a
source artifact. Each invocation stages its inputs and intermediate files in an
isolated `build/run/canonical-contracts/stage-*` directory, removed on exit.
The manifest is not committed or shipped: on a clean checkout `--check`
compares regenerated contract bytes directly against the generated sources.
Stale-file removal uses previous ownership state only when available; it must
never delete unrelated generated contracts based on name matching.
The source-generation manifest must select a distinct
`technology_enum_output_naming_conventions` entry for each target language;
using the DataObject interface convention for an enum is incorrect. The
canonical Python model loader resolves generated enum/contract/SDO classes by
their **canonical schema identity**, as recorded in generated source metadata,
not by reconstructing package, module or class names from Algites prefixes.
The emitted names therefore remain governed by the selected naming catalog.
The preceding model bootstrap still requires generating read-only canonical
contracts and their independent SDO implementation **before** the native Defs
CLI is imported; merely clearing the `*.gen` roots and importing the CLI cannot
initialize its own model. The ordering of that clean-bootstrap stage remains
an integration issue, not a reason to maintain a second handwritten model.
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

Java collection getter declarations must expose `eu.algites.lib.common.list.AIiMultiMappedList<? extends V>`, **not** `AIcMultiMappedList<V>`. Direct `extends AIiMultiMappedList<V>` on a named collection interface remains invariant as required by Java's supertype syntax. The library implements `AIiMultiMappedList<V> extends java.util.List<V>`, and its key definitions provide `Map<K,List<V>>` live views over the one underlying ordered list. The map's grouped lists are immutable snapshots. Removing a key removes the entire group across all views. Inserting/replacing through maps is forbidden. The collection tracks sublists weakly and synchronizes removals; direct mutation of key-bearing fields while stored is a caller contract violation.

Python declares a matching abstract `AIiMultiMappedList[V]` interface built on `collections.abc.MutableSequence[V]`; `AIcMultiMappedList` implements it. Python grouping map values are immutable `tuple[V,...]` snapshots. Do not expose concrete `AIcMultiMappedList` from generated interfaces.

For overlapping common and format-specific read-only contract getters,
use the covariant return `AIiMultiMappedList<? extends CommonValue>` in the
shared contract and `AIiMultiMappedList<? extends SpecializedValue>` in its
specialization, provided `SpecializedValue extends CommonValue`. Java
invariant type arguments still prohibit overriding a plain
`AIiMultiMappedList<CommonValue>` with `AIiMultiMappedList<SpecializedValue>`;
that is why the wildcard is mandatory for *all generated getters*.
The declared supertype of a named collection interface is not itself a getter
and cannot use a wildcard. Writable SDO members retain their independent
setter and generic type policy.

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

A nested XSD `xs:choice` models structural alternatives, corresponding to explicit JSON/YAML `x-algites-defscodegen-choice: true` (not JSON Schema `oneOf`). Named XML choice types are now emitted independently and share common nominal branch interfaces with matching JSON/YAML `$defs`; exact format-specific XPath and XML element QNames must be preserved. The `NameFragments.Segments` wrapper with one repeated typed `Segment` is recognized as an array, not as an unrelated object. A targeted 208-source generated-output check passed for the naming schema family.

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
**Aktuální implementační vstupy:** `pub.lib.General(20261106-171400).tgz` a `pub.tool.General(20261106-171400).tgz`.

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

The outer `additionalProperties` does not by itself supply a closed typed variant: `oneOf` is validation-only. To generate a structural sum type, declare an explicit `x-algites-defscodegen-choice`;
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

## Kontextové XSD klíče nad sdíleným TYPE (implementace 2026-11-08)

`xs:key` ani `xs:unique` **nemění identitu datového typu**. Následující
schéma deklaruje jediný `common:Entries`; oba elementy odkazují na stejný
TYPE. Index `ByName` je definován jen pro instanci `Entries` uvnitř `Keyed`:

```xml
<xs:element name="Keyed" type="common:Entries">
  <xs:key name="ByName">
    <xs:selector xpath="Entry"/>
    <xs:field xpath="@name"/>
  </xs:key>
</xs:element>
<xs:element name="Unkeyed" type="common:Entries"/>
```

- Kanonický model uchovává oba elementy jako `TYPE` reference na **stejnou**
  definici a deklaraci klíče na příslušném `ELEMENT.key_definitions`.
- Read-only Java getter `getKeyed()` nese
  `@AIaDataObjectListKeyDefinition(name = CONST.KEY_ID__BY_NAME, selector = "Entry",
  fields = {CONST.FIELD_NAME__NAME})`; Python ukládá tutéž vazbu do
  `__scoped_key_definitions__['Keyed']`.
- Getter `getEntryList()` ve sdíleném `Entries` vrací `AIiMultiMappedList<? extends Entry>`;
  objekt `Unkeyed` má stejnou třídu, ale **prázdnou množinu indexů** a dovoluje
  duplicitní hodnoty jména. Objekt `Keyed` vytvoří index `ByName` nad svou
  vlastní instancí seznamu a odmítne duplicitní jména.
- Stejné pravidlo platí pro lokálně deklarované i `xs:import` typy. SDO
  Codegen nepřehodnocuje XSD; Java pouze přenáší také `selector`, Python
  využívá metadata zděděná z read-only DataObject kontraktu.
- Podporován je právě **jeden bezprostřední opakovaný child list** pro každou
  deklaraci klíče. XPath s výběrem napříč několika seznamy a `xs:keyref`
  vyžadují samostatnou implementaci. Pouhá lokální deklarace klíče nesmí
  spouštět vytváření syntetické varianty původního typu.

**Aktuální explicitní choice kontrakt:** naming konvence nyní deklarují
`NameFragmentsSegmentValueContent` jako pojmenovaný typ s `CHOICE` a
`NameFragmentsSegmentValue.Content` jako skutečnou povinnou vlastnost ve
všech třech dialektech. Alternativa `NameRegexp` je také pojmenovaný typ.
Vnější XML `Content` je záměrnou změnou schématu, která byla odsouhlasena
spolu s migrací YAML katalogů; nejde o neexistující obal zavedený emitorem.
Opakované pojmenované položky `NameConvention`, `Rule`, `IdentifierConvention`
atd. jsou deklarovány explicitními typy XSD a `$defs` s `$ref` v JSON/YAML;
syntetické typy nejsou nutné. `xs:key` zůstává na výskytu XML elementu,
zatímco JSON/YAML klíč seznamu se deklaruje na `array/items`; jejich
výsledné kanonické indexy musí mít shodnou sémantiku.

Generování naming ABI seed rozhraní bylo ověřeno přímým voláním standardního
Defs CLI; úplný Gradle/source-dependency bootstrap celé dvojice repozitářů
vyžaduje samostatné integrační ověření.

## Společná definice klíčů a getterů kolekcí

**Autoritativní výstup Defs Codegenu je read-only DataObject API.** Pro
opakované `LIST` pole definuje nyní oddělený společný naming role
`list_getter` název getteru. Algites Java i Python používají kompozici
`get` + `UpperCamelCase(název pole)` + `List`, například XML
`<xs:element name="rule" maxOccurs="unbounded"/>` → `getRuleList()`.
Tato kompozice není v generátoru zakódována; konfiguruje se zvlášť v
Common profilu a je sdílená nezávislými Defs/SDO pipeline.
SDO přebírá přesně stejnou deklaraci metody, metadata `fieldName="rule"`
uchovávají skutečný zdrojový název. Nový SDO generátor nevytváří veřejný
`setRuleList(...)`: mutable kolekce je připojena přes getter.

Defs musí emitovat `AIiMultiMappedList<? extends T>` pouze pro list s
podporovanou definicí indexu. V XMLDEFS se index vyvozuje jen z
`xs:key`/`xs:unique`, kde `xs:selector` vybírá bezprostřední položky **jednoho**
konkrétního seznamu a `xs:field` je typovaně vyhodnotitelné nad touto položkou.
Ostatní selectory mají vést k **WARNING s konkrétním zdrojem a cestou** a
vygenerování obyčejného seznamu bez odpovídajícího indexu; nemají měnit
syntaxi XSD ani znamenat, že byla splněna jeho úplná validační pravidla.

Obecná Java anotace `@AIaDataObjectListKeyDefinition` a Python
`__key_definitions__` jsou společná metadata pro indexy XMLDEFS a výhledově JSONDEFS/YAMLDEFS. Před sjednocením s JSONDEFS a
YAMLDEFS je nutné navrhnout univerzální **DataObject** anotaci a odpovídající
Python metadata; SDO nemá analyzovat zdrojová schémata. Defs musí generovat
konstanty pro identifikátory indexů **i všechny odkazované názvy polí** v
konfigurovaném vnořeném `CONST`, aby deklarace nemusela obsahovat ruční názvy
modelových členů. JSON/YAML klíčované objektové položky musí být při případném
převodu na MultiMappedList zachovány jako syntetický klíč (`_getKey()`) a
syntetická hodnota (`_getValue()`), bez ztráty serializačního tvaru.

Zákaz veřejných setterů pro všechny kolekční `LIST`/`MAP` a interní lazy
inicializace jsou specifikovány v
[SDO Codegen Reference](../sdocodegen/SDO-CODEGEN-REFERENCE.md#kolekční-pole-schválený-cílový-kontrakt-dosud-neimplementováno).
Nejde o současný stav emitorů. Stávající `AIiMultiMappedList` už výslovně
vyžaduje neměnnost klíčových hodnot po vložení; sledování následných mutací
klíčů se **nezavádí**.

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

**Generated CHOICE implementation and SDO boundary:** The read-only Java
choice contract is a `sealed interface`, and its alternatives are immutable
`record` classes generated directly into the same Java package/module as that
interface (as required by Java sealing rules). Python emits immutable
`@final` / `@dataclass(frozen=True)` alternatives. A CHOICE is **not** a
mutable SmartDataObject: SDO Codegen must not generate a mutable interface or
concrete SDO implementation for the choice or its variants. Its payload can
be a separately generated mutable DataObject; callers replace the whole
choice value to select another alternative. The bootstrap must import these
Defs-generated variants from the active generated namespace; they are not
ordinary generated SDO implementation classes. In particular, the canonical
`Structure`, `ElementListChild`, and `TypeContent` alternatives use this
representation. This contract is independent of whether the source schema
uses XSD `xs:choice` or `x-algites-defscodegen-choice` in JSONDEFS/YAMLDEFS.

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
**Kořenový typ JSONDEFS/YAMLDEFS se nesmí pojmenovat podle `title`.**
`title`/`description` jsou dokumentační metadata, zatímco `x-algites-schema-id`
vyjadřuje logickou identitu a `$id` publikovanou URL. Nativní CLI má v manifestu
`input_naming` pro každou zdrojovou technologii; hodnoty `catalog` a `profile`
vybírají existující `SourceStructureNameConventions`. Přes
`file_name_stem` + `file_name_suffix` se ověří **celé** jméno souboru,
včetně explicitně deklarované verze. Z jeho zachyceného `identifier` se
**konverzí podle pravidel katalogu** sestaví `type_name`; `version` se použije
v konvenci výstupního Java/Python typu a souboru. Pokud schéma současně
obsahuje `x-algites-schema-version`, musí odpovídat zachycené verzi.
Chybějící/neodpovídající vstupní konvence je chyba s názvem vstupního souboru,
nikoli důvod odhadovat název z `title` nebo rozdělovat název podle podtržítka.

Například obě schémata
`common-naming-conventions_1.jsondef.schema.json` a
`common-naming-conventions_1.yamldef.schema.json` se při vybraných
Algites profilech převedou na lokální typ `CommonNamingConventions` a
společně vygenerují jediné `AIigCommonNamingConventions_1` pro Javu
a Python. JSONDEFS a YAMLDEFS metadata zůstávají nezávislá. `title` může
nadále znít „Shared naming convention tools“ bez vlivu na názvy.
Lokální jména explicitně deklarovaných `$defs` a XSD typů zůstávají
samostatnými vstupy do `type_name`; nepřejmenovávají se podle názvu souboru.
Verze z vybraného vstupního souboru má přednost před obecnou výchozí verzí
manifestu **pro všechny deklarace vzniklé ze souboru**, včetně vnořených
syntetických typů a pojmenovaných XSD typů. Kanonický frontend musí zapsat
`schema_version` přímo také na každý syntetický `TYPE` (`Origin.SYNTHETIC`),
např. inline `enum`, objektovou vlastnost, položku seznamu nebo variantu
strukturální definice. Pro každou takovou deklaraci je verze převzata z
**jejího vlastního zdrojového dokumentu** identifikovaného `resource`;
jediná generovací dávka smí obsahovat dokumenty různých verzí a verze
se mezi nimi nesmějí přenášet. Konkrétně
`common-naming-conventions_1.jsondef.schema.json` poskytuje syntetickému
`NameFragmentsSegmentValueKind` verzi `1`, stejně jako odpovídající XSD;
jejich společný enum pak může být korektně sloučen do
`AIngNameFragmentsSegmentValueKind_1` v Javě i Pythonu.

Verze se při výběru zdrojového souboru **neodhaduje z Javadoc ani z výsledného
názvu typu**: prochází vstupním pojmenovacím profilem, kanonickým modelem a
emitorem. Pokud explicitní `x-algites-schema-version` odporuje verzi
vyčtené souborovou konvencí, vstupní CLI musí generování odmítnout se
zdrojovou diagnostikou. Slučovač enumů nesmí tento rozpor maskovat
ignorováním chybějící či rozdílné verze.

Více souborů pro tutéž deklaraci
s rozdílnými verzemi nebo explicitní metadatová verze odlišná od verze
souboru představují chybu s diagnostikou zdrojů, nikoliv důvod použít
implicitní `1`.

### Jediné společné read-only rozhraní a nezávislá metadata formátů

Nový Defs Codegen vytváří pro jeden logický `TYPE` právě jedno rozhraní
`AIigXxx` odvozené z vybrané `common` naming konvence, a to v Javě i
Pythonu. Nevytváří potomky `AIigXxx`, `AIigXxx`, `AIigXxx`.
Výjimkou jsou pojmenované enumy: jedná se o samostatné hodnotové typy.

```java
@AIaDataObject(description = "Example")
@AIaDataObjectJsonSchema(schemaId = "urn:example:json",
    schemaVersion = 3, schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/example_3.jsondef.schema.json")
@AIaDataObjectYamlSchema(schemaId = "urn:example:yaml",
    schemaVersion = 7, schemaUrl = "https://defs.dev.algites.eu/api/yamldefs/example_7.yamldef.schema.json")
@AIaDataObjectXmlSchema(definitionKind = AInXmlObjectDefinitionKind.TYPE,
    namespace = "urn:example:xml", namespaceLocalName = "Example")
public interface AIigExample_1 extends AIiDataObject { /* common getters */ }
```

ID, verze ani URL se **nikdy neporovnávají mezi technologiemi**.
Každá technologie má vlastní schématovou identitu. Po dobu migrace mohou
být souběžně emitovány deprecated anotace pro kompatibilitu. Přechod
YAMLDEFS na samostatnou novou anotaci ještě není dokončen; jeho návrh se
nesmí odhadovat implicitním sdílením anotace JSONDEFS. Změna hodnot v jiné
technologii není důvodem k chybě ani k přepsání metadat.

Společné gettery zachovávají odpovídající strukturální typy; formátově
specifická XML QName metadata mohou ležet na těchto stejných getterech.
Pro skutečně nekompatibilní definice polí různých technologií se vyžaduje
samostatná diagnostika či explicitně dohodnuté pravidlo, nikoli náhodné
přepsání posledním souborem. Existující `*.extgen` ABI seed není normativní
vzor veřejného rozhraní a historické `old` generátory nejsou měněny.

### Slučování enumů z XMLDEFS, JSONDEFS a YAMLDEFS

Při definici stejného externě referencovaného enumu ve více dialektech musí být shodný i **lokální název typu**: `xs:simpleType/@name` v XMLDEFS a `type_name` odvozený z názvu kořenového JSONDEFS/YAMLDEFS souboru podle explicitní vstupní naming konvence. Například `defscodegen-structure-kind_1` dává `DefscodegenStructureKind` (nikoli `DefsCodegenStructureKind`). Identické hodnoty enumu samy o sobě k typové kompatibilitě getterů nestačí. Stejné pravidlo platí pro `sdocodegen-structure-kind_1`.

Pojmenovaný enum je **jeden společný hodnotový typ** (například
`AIngElementKind_1`), nikoli tři formátově specifické DataObject
kontrakty. Při současném generování z více schémat může být stejný enum
nalezen v XMLDEFS, JSONDEFS i YAMLDEFS; odlišný text dokumentace a
zdrojové `schemaId` / URL / XML QName **neznamenají** odlišný enum.

Oba Defs CLI při kolizi stejné výstupní cesty porovnávají skutečný
vygenerovaný kontrakt enumu, nikoli doslovně všechny Javadocy/docstringy.
Povoleny jsou pouze rozdílné komentáře a původní schématová metadata
`CANONICAL_SOURCE_ID` / `CANONICAL_SOURCE_RESOURCE`, která u sdíleného
enumu označují reprezentaci, z níž byl vybrán jeho zdrojový zápis.
**Hodnoty enumu, serializované kódy, metody, ostatní konstanty a verze
musí být shodné.** Jinak jde o konflikt obsahující cestu výsledného
souboru a dostupné zdrojové identity obou definic, nikoli o přepsání.

Výběr primární zdrojové reprezentace je deterministický a nezávislý na
pořadí parametrů či souborů. Ostatní shodné zdrojové identity se zapisují
do dokumentace enumu jako `Equivalent enum schema` (výstupy nesoucí fyzickou
cestu schématu) nebo `Equivalent schema identity` (kanonický emitor
poskytující pouze identifikátor a verzi, např. XML QName). Resolver nesmí
vymýšlet fyzickou cestu, kterou zdrojový kontrakt neposkytuje. Python kanonický emitor nově zapisuje `Canonical identity` a verzi také
do dokumentace enumu, stejně jako Java emitor. U byte-identických
výstupů se nevytváří duplicitní deklarace ani nevymýšlí chybějící
provenience. Výstupní enum se publikuje právě jednou. Stejná pravidla platí pro Java i Python
implementaci Defs Codegenu a pro oba cílové jazyky.

Externí XML rodiče se vyhledávají podle `@AIaDataObjectXmlSchema` a
`__xml_schema__` (`definitionKind=TYPE`, `namespace`,
`namespaceLocalName`), **nikoliv** podle `schemaId` v obecné
`AIaDataObject`; JSON/YAML mají vlastní formátové metadatové anotace.
Tím je zaručena nezávislost Defs Codegenu na SDO Codegenu a přitom
kompatibilita jejich read-only vstupního API.

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
dřívější (odstraněná) sada parity testů and feeds it the JVM test classpath
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

Test-only cross-format fixtures reside in `impl/src/develop/examples/`
under the `xmldefs`, `jsondefs`, and `yamldefs` subdirectories.
They are excluded from root-level bootstrap code generation; tests load
them explicitly and retain their relative references.

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
libovolné `anyOf`/nepodporované unie, netypované dodatečné JSON vlastnosti
(ignorují se s warningem), XML→MAP,
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

Výchozí hodnota je **`false`**: CLI projde všechny vstupní soubory v rozsahu
jednoho volání a shromáždí chyby z nezávislých validačních kontrol. Hodnota
**`true`** znamená optimalizované ukončení až **po dokončení kontrol prvního
chybného vstupního souboru**, takže jeho jednotlivé diagnostiky se nevypustí.
V obou režimech se vypisují konkrétní zdrojové soubory a umístění problémů.
Kontroly závislé na neúspěšně parsované části dokumentu nelze smysluplně
provést, dokud se tato chyba neodstraní. Při chybách se tato dávka nezapíše do
generovaných výstupů. Politika je předávána prostředím
`MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY` i explicitním CLI
argumentem; jiné hodnoty než `true`/`false` jsou odmítnuty.


V souhrnném výpisu má každá chyba označení **`[x/n] (a/b)`**:
`x/n` udává pořadí a počet chyb v celé dávce a `a/b` pořadí a počet
chyb v témže zdrojovém souboru (`Source`). Například `[3/5] (2/3)`
označuje třetí z pěti celkových chyb, ale druhou ze tří chyb konkrétního
souboru. Chyba ze souboru, v němž je jediná, má `(1/1)`. Pořadí chyb
se nemění ani tehdy, když jsou chyby různých souborů proložené; každému
záznamu zůstává `Source`, `Location` a `Hint`. Pokud zdroj souboru není
znám, nezaměňují se takové chyby za chyby téhož souboru. Jediná chyba
hlášená samostatně nadále používá dosavadní `VALIDATION ERROR` formát.

**Nedokončené sjednocení projekcí (zachyceno regresním testem):**
`canonical_defs_codegen_cli.py::_merge_common_contract()` zatím používá
průnik kompatibilních getterů. Pokud XSD deklaruje objektové pole a
JSON/YAML ekvivalent jako `AIiMultiMappedList`, může neutrální getter
zmizet, přestože technologická rozhraní jej zachovají. To neodpovídá
odsouhlasené architektuře. Je nutno nejprve sladit samotná schémata a
pak generovat všechny sémantické gettery v neutrálním kontraktu;
`Object`/`Any` ani tiché vynechání nejsou přípustná náhrada. Test
`test_technology_projection_never_introduces_unowned_semantic_getters`
prozatím reprodukuje tento problém v Javě i Pythonu.

**Bootstrap:** `devops/bootstrap/generate_sources.py` používá nový kanonický
Defs Codegen a sestavuje dávku manifestů bez volání `defs.old`. Výpis není
jednou atomickou validační transakcí přes všechna samostatná spuštění
`--root`. Samostatný pomocný skript `generate-canonical-contracts.py` nadále
obsahuje historickou implementaci, která nesmí být zaměňována za hlavní
bootstrap. Jeho odstranění/migrace a regenerace již vytvořených bootstrapových
SDO tříd jsou samostatné nedokončené kroky.

Při chybě vstupního schématu nový kanonický frontend předává výjimku s názvem
zdrojového souboru a s původní podrobností parseru (například JSON Pointer
`#/properties/name` či XML pozice). Konflikt při slučování zdrojových
reprezentací vypisuje kanonickou cestu i původní dokumenty a jejich source
pointers. Tato ochrana nenahrazuje širší požadavek na soubor a místo u všech
warningů a pozdějších chyb linkeru či emiteru.

### Diagnostický kolektor podle závažnosti

Defs Codegen sdílí se SDO Codegenem Java/Python typované severity `DEBUG`,
`INFO`, `WARNING`, `ERROR`. Výpis je řazen od nejnižší severity po nejvyšší;
každá sekce má nezávislé `[x/n]` a `(a/b)` podle souboru. Debug výpis vyžaduje
`ALGITES_CODEGEN_DEBUG=true`; `WARNING` neukončuje generování, `ERROR` ano.
Zachovávají se `Source`, `Location` a případný `Hint`. Nefatální zprávy se
vypíšou na úspěšné cestě, při selhání je výjimka předá diagnostice CLI, která
vytiskne severity včetně warningů a **errory jako poslední**. Konkrétní
warningy pro nepodporované XML selectory budou přidány při implementaci jejich
selektivního ignorování. Podrobné chování a API je popsáno v
`SDO-CODEGEN-REFERENCE.md`.


### Named map indexes across XMLDEFS, JSONDEFS and YAMLDEFS (1.1-SNAPSHOT)

`x-algites-defscodegen-key` is a schema metadata keyword for either a typed
object map (`additionalProperties` with a value schema) or a typed homogeneous
array (`items` with object fields, including a required scalar/enum key). The
value must have exactly two nonempty string members:

```json
"x-algites-defscodegen-key": {
  "id": "UniqueStructureRoles",
  "field-name": "kind"
}
```

The `id` is copied from the corresponding `xs:key/@name`; `field-name` is
copied from the single `xs:field/@xpath`, without its attribute-marker `@`.
For a JSON/YAML map, the logical field replaces the naming-profile fallback
`multi_mapped_list_key_synthetic_getter`; without the keyword the configured
synthetic getter remains the default. `propertyNames` must continue to reference
the named enum schema: this establishes the key's **type** independently of
its source-format representation as a JSON object-property name. XML identity
constraints and JSON/YAML map metadata both use the generic Java annotations
`AIaDataObjectListKeyDefinition` / `AIaDataObjectListKeyDefinitions` in `eu.algites.lib.data.dataobject`.
Their Java constant references are `CONST.KEY_ID__<NAME>` and
`CONST.FIELD_NAME__<FIELD>` (with normalization through the naming catalog).
The canonical emitter for indexed XML LISTs emits both constant families.

**New canonical backend (supported subset).** Both the native Java and Python
frontends lower an explicitly keyed, **homogeneous** JSONDEFS/YAMLDEFS object
map or item-object array into the existing canonical `LIST` node. For arrays
`field-name` names an actual field of `items`, not a synthetic property key; a
matching `required` declaration is needed for an inline item schema. For
object maps the key remains synthesized from the JSON object property name. The list contains a synthetic
object with a typed key field (name from `field-name`, type from
`propertyNames`, including a referenced *string* enum) and a synthetic value
field (from `additionalProperties`). Both language emitters provide an
`AIiMultiMappedList<? extends Item>` accessor and `AIaDataObjectListKeyDefinition` / Python
`__key_definitions__` metadata. The item declares `FIELD_NAME__<FIELD>` and
`FIELD_NAME__VALUE`; the list owner declares `KEY_ID__<ID>`,
`FIELD_NAME__<FIELD>` for the index path, and constants for **all** its other
direct members, whether keyed or not. `CONST` is the naming-convention role;
the concrete nested container name is resolved from the active naming profile.
A JSON/YAML map without the explicit keyword retains its previous MAP/object
contract; the profile's fallback key getter is not used to invent a new key.

For example:

```json
{
  "type": "object",
  "properties": {
    "structureNaming": {
      "type": "object",
      "x-algites-defscodegen-key": {
        "id": "UniqueStructureRoles",
        "field-name": "kind"
      },
      "propertyNames": {"$ref": "#/$defs/StructureKind"},
      "additionalProperties": {"type": "string"}
    }
  },
  "$defs": {
    "StructureKind": {
      "type": "string", "enum": ["standard_getter", "raw_getter"]
    }
  }
}
```

Here the synthetic getter for the key resolves to the typed `getKind()`
under the configured standard getter rule, *not* the `_getKey()` fallback.
The value getter follows the separate
`multi_mapped_list_value_synthetic_getter` convention. An enum defined in
`propertyNames` must be available as a resolved named type to preserve its
identity; converting it to `String` is forbidden.

**Remaining limitations:** Indexed maps with incompatible `properties`, `patternProperties`,
`minProperties` / `maxProperties`, nested property-specific validation or
other unrepresented map constraints are rejected rather than silently
flattened. In particular, some currently published naming convention schemas
mix `properties` with `additionalProperties`: those need an additional,
semantics-preserving projection before they can be emitted by the new backend.
XML `xs:simpleContent` and attributes are still subject to the previously
documented limitations; an identical full XML/JSON public contract has not
been demonstrated. The *legacy* bootstrap backend is unchanged by this update.
Neither Defs nor SDO should be combined into a single pipeline to implement
 the remaining behavior.

**Object-level `oneOf` with independent fields is not an emitted field CHOICE.**
For example, `{"type":"object","properties":{"a":{"type":"string"},
"b":{"type":"string"}},"oneOf":[{"required":["a"]},
{"required":["b"]}]}` requires exactly one of `a` and `b` while still
retaining both property declarations. The Java and Python canonical frontends now preserve the declared object
fields and issue a precise warning that the `oneOf` exclusivity constraint is
not yet enforced by generated DataObjects. That constraint remains present in
the original schema for validation during marshalling. Neither a sealed
variant nor a replacement for the surrounding `properties` may be inferred. The canonical `Type` schema uses the two `required`
branches of `oneOf` directly; its former `not` clauses were logically
redundant, because `oneOf` already enforces exclusive-or.


### XML naming `Rule` shape (2026-11-05)

Naming-map entries in the maintained XSD schemas now use an explicit child
`Value` together with the required XML attribute `kind`, instead of
`xs:simpleContent`. This is a **wire-format change** for XML naming documents;
existing text-only `<Rule kind="…">composition</Rule>` instances require
conversion to `<Rule kind="…"><Value>composition</Value></Rule>` before
validation. JSONDEFS/YAMLDEFS map instances remain unchanged. The existing
`xs:key` (`selector=Rule`, `field=@kind`) retains the same identity semantics.

This adjustment removes the unsupported `xs:simpleContent` construct from
these naming XSDs, but does **not** resolve external XSD imports or
`x-algites-defscodegen-extends` references to contracts in other artifacts.
Those still need offline, explicit cross-artifact schema dependency resolution
without generating duplicate parent contracts.


## Metadatové defaulty, fixed, empty a XML wildcardy (1.1-SNAPSHOT)

Kanonický `Element` má `default_kind`, `default_value` a `is_empty_allowed`.
`default_kind` je prázdný pro nepřítomný default, jinak jedna ze čtyř
konstant `AInDataObjectFieldDefaultKind`. Přítomná hodnota může být sama `""`.
Emitery Java/Python zapisují `order`, `isEmptyAllowed` a vnořený
`AIaDataObjectFieldDefault`/Python ekvivalent na read-only getter. Díky tomu
SDO generátor přečte všechna metadata **z rozhraní** a nepotřebuje XSD ani
kanonický model.

```xml
<xs:attribute name="code" type="xs:string" default="A"/>
<xs:element name="label" type="xs:string" default="Anonymous"/>
<xs:element name="state" type="xs:string" fixed="READY"/>
```

Výsledné politiky jsou `IF_FIELD_VALUE_NOT_PRESENT` (`code`),
`IF_FIELD_VALUE_EMPTY` (`label`) a `CONSTRAINT_DEFAULT` (`state`).
`fixed` je *omezení setteru*, nikoli implicitně vložená raw hodnota. XML
serializace nezapisuje dosazený efektivní default. Pro nepodporované
kombinace (např. `default` současně s `fixed` nebo default na
opakovaném elementu) se generování ukončí diagnostikou, místo tiché ztráty.

`xs:any` ani `xs:anyAttribute` se nestávají generovanými poli. Volitelný
wildcard vytváří `WARNING` a původní XML deklarace je zachována v Javadoc/
docstring vlastníka. Povinný wildcard generování zastaví s `ERROR`.
U `xs:anyAttribute` rozhoduje kontext užití bez vlastního `minOccurs`;
nelze jeho povinnost posuzovat jako u `xs:any`.

**Ověřování:** samostatná regenerace read-only kanonických kontraktů v obou
jazycích proběhla. Kompletní Java SDO generování, synchronizace persistentních
`*.extgen` ze všech čtyř zdrojových sad a end-to-end Gradle bootstrap musí
ještě proběhnout ve vývojovém prostředí se stažitelným Gradle 9.2.1. Do té
doby nelze prohlásit deploy ani úplnou paritu za ověřené.

## Temporary self-hosting bootstrap model (`*.extgen`)

The native Defs compiler depends on its schema-generated canonical model.
The first self-hosted compiler load uses a **versioned source-generated seed**
under `.extgen`; this seed is not developer-maintained code. Its read-only
contracts and independent SDO contracts use a distinct bootstrap namespace.

| Contract layer | Java `*.extgen` | Python `*.extgen` |
|---|---|---|
| Defs read-only interfaces and enum/CHOICE variants (69) | `generators/code/defscodegen/intf/src/product/java.extgen` | `generators/code/defscodegen/intf/src/product/python.extgen` |
| SDO mutable interfaces and concrete implementations (56) | `generators/code/defscodegen/impl/src/product/java.extgen` | `generators/code/defscodegen/impl/src/product/python.extgen` |
| **Current snapshot** | **125 generated files** | **125 generated files** |

A temporary bootstrap policy **only in `pub.tool.General`** checks the
existing compiler `*.extgen` source snapshots on startup (`--prune-seed`)
without relying on historical file-list manifests. Obsolete paths are removed
when complete fresh Defs/SDO outputs replace the source trees after the build. It creates a unique UUID for each build, cleans the selected
`.gen` outputs once before Defs/SDO, and scopes Python and Java ownership
indices to that invocation. After the **entire** Defs/SDO generation and build
complete successfully, `promote-canonical-extgen.py --refresh` reads the two
independent kinds of output from the current Defs input artifact's
`defscodegen/intf/src/product/{java,python}.gen` trees: Defs read-only model
contracts at `model/` and SDO writable/concrete contracts at `model/impl/`.
The independently generated SDO contracts do **not** currently appear under
`defscodegen/impl/src/product/{java,python}.gen`; the bootstrap copies the
`model/impl/` subtree into that artifact's persistent `.extgen` seed. The
promoter verifies both roles in Java and Python, replaces all four `.extgen`
source roots, removes
obsolete source files by replacing complete `*.extgen` trees without writing persistent bootstrap metadata.
If the exchange fails, previously installed roots are restored. No persistent
bootstrap-generated metadata is created or consulted.
A scoped `--root` build does not refresh the canonical seed.

The normal `--check` remains an **explicit diagnostic** and checks the
existing source contents, common DataObject roles, SDO inheritance and
Java/Python symmetry. It does not claim to verify hash provenance against
schema input when fresh `*.gen` sources are unavailable; full `--refresh`
validates freshly generated outputs before replacing the ABI snapshot. It is **not** a prerequisite for an ordinary Tool
bootstrap invocation. `--refresh-defs` remains a specialized manual recovery
operation when the SDO compiler cannot yet run; it preserves independently
produced SDO output and validates compatibility. Neither helper edits the
`.gen` trees, and all `.extgen` sources must come from Defs/SDO generators.
The normal standalone CLIs and other repositories retain their own lifecycle
policies; the tool-only bootstrap mode does not change them.

**Historický P4 ABI seed regression (2026-11-10; ne normativní nová projekce):** a partial refresh of only the read-only Defs
bootstrap model leaves SDO implementations tied to old neutral contracts.
For example, the JSON selected alternative `AIigStructureSelectedScalar_1`
requires `AIigStructureScalar_1`, but stale `AIigdStructureScalar_1`
previously extended `AIigStructureScalar_1` instead. The Python canonical
frontend then failed with `Expected AIigStructureScalar_1 choice value`.
Regenerate **both** neutral and JSON SDO roles in Java and Python through the
independent SDO CLIs before promoting a complete snapshot. The snapshot validation and
`--check` reject an inconsistent SDO inheritance without a hash manifest;
`devops/bootstrap-tests/test_extgen_bootstrap.py` reproduces the original
Python choice construction and validates both language hierarchies. The
verified P4 snapshot has 370 files total (185 per language). The Python
bootstrap of `naming/convention/intf` generated 164 Defs and 42 SDO files;
the full Gradle bootstrap still requires an environment with current Java
library dependencies and Gradle available.


Canonical compiler-ABI snapshots are maintained by the standard independent
Defs and SDO CLIs. The selected Defs artifact is generated from all matching
XMLDEFS, JSONDEFS, and YAMLDEFS inputs in one combined run, with the final
`eu.algites.tool.codegen.defs.model` package and its associated generated
`defs.impl` and `defs.naming` packages. The generated `*.gen` source is the
authoritative output; no `bootstrap.model` package or post-processing rename
is permitted.

After both generators succeed and their outputs pass validation, the selected
artifact's persistent Java/Python read-only and writable `*.extgen` snapshots
are **completely replaced** from the corresponding `*.gen` files. The copy
preserves relative paths and source bytes exactly, without modifying packages,
annotations, method signatures, field metadata, or other content. Failed
validation leaves previous snapshots intact. The normal bootstrap still
compiles the current source and verifies the resulting artifacts.

The generator must produce the correct bounded and indexed collection types,
modern XML/JSON/YAML schema annotations, and getter-only list APIs. Generated
source errors must be corrected in the generators and never patched in
`*.extgen` after generation.

The naming convention for generated enums is read from the existing
`--output-enum-technology-naming-convention:java|python=…` lines in the selected
Defs `.settings` files. The corresponding file-stem composition is resolved
from the selected source-code naming catalog (no hardcoded `AIng`/`AIig` prefix).

### Ověření k 6. 11. 2026 (Java/Python parity)

Připraveny jsou nové role `list_getter`, `raw_empty_setter`,
`raw_empty_checker_method`, anotace defaultů a změny obou kanonických frontendů.
Zdrojová syntaktická kontrola Java 21 prošla; to **není** důkaz úspěšné
kompilace. Regenerace persistentních `*.extgen` zdrojů vyžaduje všechny
čtyři sady (read-only a SDO pro Java/Python). Dokud tato fáze není provedena,
kanonický model nemůže garantovat nové `default_kind`, `default_value` a
`is_empty_allowed` v běhové podobě. Java Gradle 9.2.1 není v tomto offline
prostředí dostupný. Žádný první deploy neproběhl; deprecated API zůstává.


### Anonymous enumerations (XMLDEFS, JSONDEFS and YAMLDEFS)

The new Defs Codegen emits a distinct canonical ENUM and Java/Python enum
when `xs:element` or `xs:attribute` has an inline restricted `xs:simpleType`
containing `xs:enumeration`, or when a JSONDEFS/YAMLDEFS object `properties`
member declares an inline `enum` or scalar `const`. The
`synthetic_inline_enum_type` role names these nominal enums uniformly from the
containing type and member name (e.g. `NameFragmentsSegmentValueKind` or
`PersonStatus`). It is configurable in every Defs naming profile; the getter
uses the nominal enum instead of the underlying scalar. The same role is used
for an inline JSON/YAML `propertyNames` enum on an indexed object-keyed list.
Anonymous object properties still use `synthetic_property_type`. Explicit
named XSD simpleType and JSON/YAML `$defs` enumeration references preserve
their declared type identity and never synthesize a duplicate enum type.

### XML `CHOICE` discriminator metadata for nested groups

The new Defs Codegen emits immutable, closed `CHOICE` variants rather than
representing an exclusive XML alternative as a bag of nullable properties.
A variant beginning with a transparent nested `SEQUENCE` is selected by the
first **actual serialized XML QName** of that sequence, never by its synthetic
DataObject type name or by a nonexistent wrapper element.

For the Python target, each XML variant may expose
`__xml_choice_first_qnames__ = ('{namespace}FirstElement', ...)`. Java records
expose the equivalent immutable `xmlFirstQNames()` set. These declarations are
derived from the linked canonical XML structure, including references to named
and synthetic types; they are not manually maintained `.gen` metadata. The
runtime checks the candidate's prefix *before* requesting any concrete SDO
implementation for a nested branch. An unrelated alternative therefore does
not require its implementation to be registered. A selected nested alternative
still requires its concrete SDO binding and fails with a diagnostic if missing.

Python additionally emits lazy `__xml_scalar_type_imports__` entries for
schema-generated nominal enums. The XML deserializer resolves the actual enum
type and maps the lexical wire value through the member's contractual
`AIiEnumItem.code()` (falling back to standard `Enum.value` only for ordinary
enums), matching the XML serializer. These runtime hints do **not** replace
XSD validation and do not create additional serializable elements or types.

### Artefaktové závislosti generovaných Java/Python kontraktů (P0)

Generování read-only rozhraní ani kanonických SDO kontraktů **nepřidává závislosti
za uživatele**. Každý cílový Modustro artefakt deklaruje své přímé knihovní
závislosti v `modustro-artifact.yml`. Pokud veřejná signatura (včetně rodičů,
typů getterů, generik nebo veřejných anotací) používá typ z jiného artefaktu,
jeho závislost patří do `Dependencies` s `Usages: [product_api]`. Typy používané
pouze uvnitř implementace patří do `product_implementation`. Externí odvozené
typy se nesmí považovat za automaticky dostupné pouze proto, že jejich zdrojové
schéma bylo nalezeno v závislostním resolveru.

Příklady důležitých přímých závislostí:

- `defscodegen.intf` používá `common.util`, `naming.convention.intf`
  a `data.dataobject.intf` pro veřejnou vrstvu.
- `defscodegen.impl` má ve vygenerovaných SDO kontraktech přímé reference
  na `data.smartdataobject.intf` a `factory.cpdiscovery.intf`. Jejich přímé
  API závislosti jsou potřebné i při samostatném sestavování artefaktu.
- `sdocodegen.intf` vystavuje při generování pojmenovacích kontraktů
  `AIiMultiMappedList` z `pub.lib.General_common.util` a rodičovská
  `AIigCommonNamingConventions_1` z `pub.lib.General_naming.convention.intf`.

Nativní bootstrap v `devops/bootstrap/prepare.py` překládá `product_api`
na Gradle `api` (a závislost Python distribuce), `product_implementation`
na Gradle `implementation`. Závislosti artefaktů sloužící k *načtení*
zdrojů během generování (`--defs-dependency-*`) jsou jiné než knihovní
závislosti nutné pro **kompilaci již vygenerovaného zdrojového kódu**;
obě množiny musí být korektně deklarované.

Kontrolní test `devops/bootstrap/test_artifact_dependency_descriptors.py`
ověřuje kritické přímé závislosti, výsledné Gradle konfigurace a (jsou-li
přítomny oba repozitáře) všechny známé přímé Java odkazy mezi artefakty.
Test záměrně kontroluje i `java.extgen` a `java.gen`, které se ručně neupravují.

U Pythonu platí totéž: importy v `python.gen` i v původních veřejných
kontraktech určují přímé závislosti distribučního balíčku. Například veřejné
legacy request kontrakty v `defscodegen.intf` ještě přímo používají
`AIcNameConventionCatalog` z `naming.convention.impl`. Kanonické Defs CLI
**nesmí** importovat SDO CLI; pro katalogy používá vlastní Defs pomocnou
funkci se stejným chováním. Její aktuální umístění v `defs.old` je přechodový
implementační detail, nikoli nové veřejné CLI či požadavek na SDO.

## Anotace: přechodný dvojí formát a umístění v modelu (1.1-SNAPSHOT)

**Dočasná veřejná kompatibilita:** nové `AIaDataObjectJsonSchema`,
`AIaDataObjectXmlSchema`, `AIaDataObjectFieldXmlSchema` jsou zavedeny vedle
existujících `AIaDataObjectJsonSchema`, `AIaDataObjectYamlSchema`, `AIaDataObjectXmlSchema`,
`AIaDataObjectFieldXmlSchema` (staré anotace jsou `@Deprecated(forRemoval=false)`;
Python obdoby mají `__deprecated__`). Staré atributy se nemažou a nevracejí
se ani odstraněné `schemaId`, `schemaVersion`, `fingerprint` do obecného
`AIaDataObject`. JSONDEFS používá novou `AIaDataObjectJsonSchema`,
YAMLDEFS má zatím samostatné metadata `AIaDataObjectYamlSchema` (přechodný
nedokončený bod migrace na nové schématové anotace). Metadata se nesmějí
přepisovat mezi technologiemi.
Nový Defs emitor přechodně zapisuje vedle nových metadat také odpovídající
starou formátovou anotaci / Python metadata pro starší konzumenty.

**Závazná projekce:** `AIaDataObject` a `AIaDataObjectField` včetně
strukturálních omezení patří na jediné `AIigXxx` rozhraní a jeho gettery.
Na témže rozhraní se nezávisle ukládají formátové schématové anotace;
XML QName anotace může být přímo na příslušném getteru. Python runtime
používá `__xml_schema__` a `__xml_schema_fields__`, s přechodnými deprecated
poli emitovanými pouze pro kompatibilitu se staršími konzumenty.

```java
@AIaDataObject(description = "Example")
@AIaDataObjectXmlSchema(definitionKind = AInXmlObjectDefinitionKind.TYPE,
    namespace = "urn:example", namespaceLocalName = "Example")
interface AIigExample_1 extends AIiDataObject {
    @AIaDataObjectField(dataFieldName = "Code")
    @AIaDataObjectFieldXmlSchema(namespaceLocalName = "code",
        valueKind = AInXmlValueKind.ATTRIBUTE)
    String getCode();
}
```

**Otevřená integrační mezera, nevyřešená touto migrací:** společná projekce
je zatím průnik kompatibilních členů všech vstupních formátů. Pole existující
jen v jedné reprezentaci (`additionalProperties` u JSON/YAML oproti XML)
proto nelze bez dalšího kontraktu opatřit obecnou `AIaDataObjectField`,
pokud má být tato anotace *výhradně* na `AIig…` rozhraních. Takové pole
může být bez deklarace pro SDO neviditelné. Nepřidávat proto automaticky
generování takových polí do produkčního SDO, dokud nebude odsouhlasena
bezpečná projekce formátově specifických společných polí; zejména se
nesmí obcházet pravidlo umístění obecných anotací.

**Kontrola Java/Python parity:** test tří reálných `CommonNamingConventions`
zdrojů ověřuje Java kompilaci, dědičnost obou vrstev a umístění anotací.
Úplná semantická parita historických testů stále není dosažena (viz níže).



### Rozsah parity regresních scénářů — audit P0

Statická inventura testů (9. 11. 2026) v `src/develop`: Java
**55 souborů / 169 metod `@Test`**, Python **89 souborů / 465 funkcí
`test_*`**. Počty nezohledňují parametrizaci a nejsou důkazem
funkční ekvivalence; zároveň jasně ukazují, že historické testovací
scénáře nejsou dosud všechny zrcadlené. Nová párová regresní sada metadat
má 5 scénářů na jazyk. Dále je ověřeno umístění anotací na skutečných
XML/JSON/YAML `CommonNamingConventions` včetně kompilace Java výstupů.
Doplnění zbývajících stovek jazykově specifických testů je samostatná
otevřená práce před označením parity za splněnou; nelze ji nahradit
úspěšným během menší cílené sady.

## Umístění nových schématových anotací

**Umístění nových anotací (Java/Python):**

| Anotace | Java package | Python modul |
|---|---|---|
| `AIaDataObjectJsonSchema` | `eu.algites.lib.data.dataobject.jsonschema` | `eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema` |
| `AIaDataObjectXmlSchema` | `eu.algites.lib.data.dataobject.xmlschema` | `eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema` |
| `AIaDataObjectFieldXmlSchema` | `eu.algites.lib.data.dataobject.xmlschema` | `eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema` |

Původní formátové anotace (`AIaDataObjectJsonSchema`, `AIaDataObjectYamlSchema`,
`AIaDataObjectXmlSchema`, `AIaDataObjectFieldXmlSchema`) zůstávají v dosavadních
`jsondefs`, `yamldefs` a `xmldefs` packages jako deprecated; jejich veřejná
signatura se nemění. Obecné `AIaDataObject` / `AIaDataObjectField` zůstávají
v `eu.algites.lib.data.dataobject` a náleží výhradně společným `AIig…`
kontraktům. Při generování se importy nových anotací vytvářejí pro nové
packages; pro kompatibilitu se nadále emitují i původní anotace.


### Vyhledávání externích kontraktů po přesunu anotací (P0)

Externí Defs kontrakt se identifikuje **každou nezávislou formátovou**
schématovou anotací na témže společném read-only `AIig...` rozhraní.
Obecná `AIaDataObject` neidentifikuje žádné konkrétní schéma.
Indexery čtou jednotlivé anotace ze zdrojových `.java`,
Python modulů a binárních `.class` v závislostních artefaktech. Při dočasné
kompatibilitě přijímají rovněž původní `AIaDataObjectJsonSchema`,
`AIaDataObjectYamlSchema` a `AIaDataObjectXmlSchema`; původní anotace však není podmínkou
pro indexování. Python pole `__json_schema__` / `__xml_schema__` se čtou
vedle historických `__json_schema__`, `__yaml_schema__` a
`__xml_schema__`.

Index používá jednotlivé, navzájem nezávislé URL pro JSONDEFS a
YAMLDEFS a XML QName `{namespace}localName` pro XMLDEFS TYPE. Jejich
identifikátory a verze se nikdy vzájemně neporovnávají. Dočasná
`*.extgen`/`build/lib` ABI kopie nesmí přebít novou `*.gen` definici.
Když má jedna společná třída všechny tři anotace, resolver indexuje
všechny tři identity na stejný typ. Při konfliktech dvou skutečně
odlišných `*.gen` rozhraní zůstává chyba ambiguity.

Při spuštění z bootstrapu se přes `--schema-locations-property-file`
předává UTF-8 mapovací soubor ve formátu
`https://host/path/example_1.jsondef.schema.json=/absolute/path/example_1.jsondef.schema.json`.
Pravidlo platí analogicky pro `.yamldef.schema.json` a `.xsd`; při
předání mapy není povolen náhradní síťový download. CLI bez tohoto
parametru zachovává dosavadní samostatné HTTPS/cache vyhodnocování.

 Pole XML se nadále anotují
`AIaDataObjectFieldXmlSchema` z package `dataobject.xmlschema` (s fallbackem
na deprecated `AIaDataObjectFieldXmlSchema`). Není přípustné přidávat
`AIaDataObject` na technologické rozhraní pouze kvůli indexování.

Trvalé párové testy `test_migrated_schema_metadata_indexed_without_generic_annotation`
a `testModernSchemaPackagesWithoutRepeatedGenericAnnotation` ověřují
Java/Python zdrojové indexování; `test_new_annotation_class_reader_without_generic_marker`
a `testModernCompiledSchemaPackagesWithoutGenericAnnotation` ověřují
binární Java anotace. Testy pracují i bez historických schématových anotací.

## Testovací brány pro neutrální kontrakty a jazykovou paritu

Dohodnutá pravidla jsou kontrolována v
`devops/bootstrap-tests/test_contract_architecture_audit.py` nad **opravdu
publikovanými** `src/product/{java,python}.gen` a `*.extgen` obou sousedních
repozitářů. Kontrola úmyslně nevyžaduje lokální `build/` manifest a nepovažuje
jeho nepřítomnost za důvod k přeskočení testů.

Testy jednotlivě kontrolují:

- všechny `@AIaDataObjectField` a obecné anotace pouze na neutrálních `AIig…`;
- jedno read-only `AIig…` rozhraní na logický TYPE a nezávislé
  JSONDEFS/YAMLDEFS/XMLDEFS anotace na něm;
- zachování `? extends` u `List` a `AIiMultiMappedList` na společném
  rozhraní;
- odpovídající Java/Python metody, sémantické anotace a struktury návratových
  typů včetně typů položek kolekcí;
- existenci neutrálního předka pro každou technologickou specializaci.

Spuštění (z kořene `pub.tool.General` se sousedním `pub.lib.General`):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
    devops/bootstrap-tests/test_contract_architecture_audit.py
```

**Červený výsledek je platný nález**, nikoli důvod test přeskočit nebo změnit
jeho očekávání. Při dosavadní P9 migraci byly v již uložených `.gen` zdrojích
zjištěny například obecné anotace na JSON/XML specializacích a některé
ne-kovariantní seznamové gettery. Tyto nálezy vyžadují opravu emitování
kontraktů a čisté přegenerování v **obou** jazycích; ruční úprava `.gen` či
změkčení testů není řešení. Testy vykazují přesné cesty problematických zdrojů.

Integrační test tříformátové neutrální projekce je v
`generators/code/defscodegen/impl/src/develop/python/test_canonical_common_projection.py`.
Samostatná sada `devops/bootstrap-tests/test_canonical_sdo_lifecycle_parity.py`
ověřuje skutečný `set`/`get`/`isPresent`/`unset` v Pythonu a v Javě po
zkompilování aktuálních SDO zdrojů; Java běh vyžaduje
`ALGITES_PARITY_JAVA_CLASSPATH` s cestami k závislostním JAR souborům.
Nepřítomný Java classpath znamená explicitní `SKIP`, nikoli úspěšně prokázanou
funkční paritu.

Pro **úplný** oddělený source bootstrap obou repozitářů existuje
`devops/bootstrap-tests/verify_full_bootstrap.py`. Nejde o `--plan-only`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
    devops/bootstrap-tests/verify_full_bootstrap.py \
    --output build/run/bootstrap/full-verification \
    --timeout-seconds 900 --dependency-mode source
```

Skript vytvoří vedle sebe izolované kopie obou repozitářů, spustí na každé
`--prepare-only --cleanup-output-folder-before-generation=false`, zaznamená
výstup a návratový kód a zapíše `summary.json`. Plánovací režim `--plan-only`
lze použít zvlášť, ale jeho úspěch není důkazem kompilace a generování.
Není-li dostupný Gradle 9.2.1 nebo externí závislosti, výsledkem plného testu
je *failed* či *timeout* s konkrétní diagnostikou; takový běh se **nesmí**
vykazovat jako úspěšný bootstrap.


## Untyped JSON/YAML additional properties and XML wildcards

Explicit `additionalProperties: true`, `{}`, or otherwise unrestricted
JSON/YAML additional values are **ignored for typed getter generation**, with a
warning containing source file, JSON pointer, possible roundtrip loss, and a
typed example (`"additionalProperties":{"type":"string"}` or a `$ref`).
A missing `additionalProperties` also produces no untyped getter but does not
warn by default; JSON Schema still permits unknown properties. With a concrete
additional-properties value schema, a typed collection remains supported.
No public `Object`/`Any` getters or `Map<String,Object>` getters are allowed.

`x-algites-defscodegen-key` supports typed JSON/YAML object maps (virtual
property-name key) and typed homogeneous arrays (`items` object with a required
scalar/enum `field-name` or a named object reference). Both become indexed
canonical LISTs; array keys refer to actual item fields and object-map keys
are synthesized. Neither representation becomes an untyped map.

For XML, optional `xs:any` and `xs:anyAttribute` wildcards are likewise ignored
with warnings citing the source and the XML declaration plus hints to declare
explicit named, typed `xs:element` or `xs:attribute`. Their data may be lost in
a DataObject roundtrip. Required `xs:any` remains a hard error with a hint,
since silently dropping a required field would violate the schema.

## External contracts in source and staged Python distributions

For imported schema identities, Defs resolves read-only external contracts from
explicit source checkouts and explicitly selected published dependency roots.
For an entire source checkout, the contract indexer inspects current
`src/product/java.gen` and `src/product/python.gen` sources, not old Gradle or
setuptools staging trees. In particular, files in
`build/run/bootstrap/<run-id>/.../build/lib`, `build/classes`, `*.extgen`,
Python caches and other disposable build directories **never** become
implicit contract candidates. This also holds if a particular schema has no
current read-only contract: a previous bootstrap run is not a fallback.

An independently supplied, unpacked wheel/JAR or compiled dependency root
remains supported, even without a source checkout. When live source and an
explicit compiled ABI representation are both supplied, the current source is
authoritative for that schema identity. Two unrelated **current source**
contracts with the same format-specific identity remain an error; the
resolver must not suppress genuine ambiguity or prefer a contract by its
name. This rule belongs to Defs Codegen and applies outside bootstrap.


## Generation lifecycle diagnostics

The native Defs Codegen CLIs (Java and Python) print a flushed `Defs Codegen
START` line on entering generation and a matching `Defs Codegen END` line on
completion, including validation failure. One pair is emitted per selected
output technology for each artifact. The common fields are `artifact`
(repository-relative directory), `technology` (`java` or `python`), `at`
(ISO-8601 local date/time with UTC offset), and `epochMillis` (Unix epoch
milliseconds). `END` additionally includes `durationMs` and `durationSec`
computed from a monotonic clock, not by subtracting wall-clock timestamps.
The events belong to the generator, not the bootstrap driver, and also appear
in standalone CLI runs. CLI configuration failures before an output artifact
can be determined are reported as ordinary configuration errors.
