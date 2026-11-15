# SDO Codegen — referenční příručka (1.1-SNAPSHOT)

> SDO Codegen je **samostatný** Java/Python generátor zapisovatelného
> SmartDataObject API. Vstupem jsou anotovaná read-only DataObject rozhraní,
> ať už ručně psaná, nebo vytvořená Defs Codegenem. SDO nečte XMLDEFS,
> JSONDEFS, YAMLDEFS, ani interní kanonický model Defs.
>
> Tento dokument je autoritativní náhradou za dřívější modulové README a
> přechodové CLI poznámky. Každá funkční změna aktualizuje přímo tuto příručku.

## Úloha a hranice artefaktů

- `sdocodegen.intf`: veřejné generátorové API.
- `sdocodegen.impl`: reflexe vstupních typů, emitery zapisovatelných rozhraní
  (`AIigd*`) a konkrétních implementací (`AIcgd*`).
- `sdocodegen.cli`: nezávislý Java/Python CLI adaptér s kvalifikovanými volbami.
- Vstup je DO kontrakt označený DataObject metadaty, nikoli zdrojové schéma.
- Read-only rozhraní patří prvnímu stupni; SDO nesmí psát jeho soubory.
- `src/product/java.gen` a `src/product/python.gen` jsou pouze generované výstupy.
- V self-hosted bootstrapu mohou `java.extgen` / `python.extgen` dočasně
  sloužit **výhradně jako kompilátorové ABI**. Nejsou vstupem SDO. Java SDO
  dostává aktuální read-only rozhraní z `java.gen` zdrojovým režimem existujícího
  CLI; ten je kompiluje v paměti. Adresáře zkompilovaných ABI tříd jsou pouze
  závislosti classpath, nesmějí být současně předány jako plošně skenované
  `--sdo-input-paths:java`.
- Pokud nejsou k dispozici vygenerovaná read-only rozhraní, může bootstrap
  předat přesné názvy ručně psaných DO kontraktů ze `src/product/java`.
  Nepřebírá žádná formátová rozhraní technologicky oddělená rozhraní
  ze starého ABI; není zaveden žádný zvláštní filtr těchto prefixů.

**Stav:** cílené Python Defs → SDO JSON/YAML/XML integrační testy prošly,
stejně jako nezávislý CLI, naming profily a nové XML/JSON/YAML binding round-tripy.
Java read-only vstupní kontrakty lze sestavit s `javac`; plný Java Gradle/TestNG
a celý bootstrap stále vyžadují samostatné ověření. Produkční bootstrap používá novou implementaci; historická `.old` je mimo aktivní zdrojové sady v `legacy-archive`.

## Regresní testy nového a archivovaného SDO

Aktivní Python SDO testy používají výhradně nové getterové anotace
`@AIaDataObjectField(dataFieldName=...)`, formátová metadata v oddělených
`__json_schema__`/`__xml_schema__` a neutrální runtime `impl.common`.
Ručně psané DO vstupy se testují přímo přes současné nezávislé SDO CLI,
nikoliv importem funkcí ze starého generátoru.

Historické scénáře `test_generated_xml_typed_deserialization.py` a
`test_sdo_named_mapped_collection.py` zkoumají staré `from_xml()` API,
starý Defs generator a staré namapované modelové typy. Jsou zachovány
v `legacy-archive/impl/src/develop/python`, nikoliv vymazány nebo
adaptovány přidáním legacy API do nového runtime. Jejich aktuální
protipóly pokrývají `test_new_sdo_codegen_runtime_binding.py`,
`test_sdo_mapped_covariant_inheritance.py` a formátové
`test_sdo_format_roundtrip.py`. Převod původních sledovaných cest
v Git repozitáři zachovává historii pomocí `git mv`.

Checkpoint kontrola Pythonu: 141 testů prošlo, šest upozornění na
validaci JSON Schema `oneOf`. Komplexní Gradle/TestNG průchod tím
není nahrazen.

## Efektivní metadata zděděných polí a XML projekcí (Java/Python)

SDO Codegen sestaví **jediný efektivní popis pole** ještě před emitováním
zapisovatelného rozhraní a konkrétní implementace. Identita pole vychází z getteru read-only DO kontraktu a konfigurovaného
naming katalogu, nikoliv z XML QName. Neutrální deklarace
`@AIaDataObjectField` (také na Python getteru, s `dataFieldName`) zůstává zdrojem
kardinality, omezení a výchozích hodnot; specializovaný XML getter může dodat
konkrétnější návratový typ a XML QName bez opakování obecné anotace.

XML provider čte pouze **explicitní XML vazby** z anotací a vnořené
implementace vybírá přes účelově omezenou SDO binding registry. SDO Codegen
již negeneruje `xmlNestedTypes()` ani přímé odkazy na konkrétní XML potomky.
Neutrální getter bez XML vazby se automaticky nestane XML elementem. Pokud
má neutrální DataObject explicitní XML vazbu na daném getteru, je použitelný
bez technologicky specifického markeru; resolver ověří typovou kompatibilitu
vybrané implementace. Neznámé nebo rozporné XML projekce musí stále selhat.
Stejná pravidla platí pro Java i Python a pro všechny formátové providery.

## Sjednocené naming profily a CLI

Stejné pravidlo platí pro Java a Python, pouze se mění jazykové ID:

```text
--naming-conventions-file:codegen_common=classpath:algites-java-common-codegen-conventions.yml
--naming-conventions-file:codegen_sdo=classpath:algites-java-sdo-codegen-conventions.yml
--common-codegen-naming-convention:java=algites-java-codegen-common_1
--sdo-codegen-naming-convention:java=algites-java-sdocodegen-standard_1
```

Dvojice profilů musí odkazovat na shodný `CommonNamingConvention`. Defs
vybírá samostatný `codegen_defs`, SDO samostatný `codegen_sdo`; nic z Defs
specifických rolí se do SDO nedostává. Katalogové a settings vrstvy se
slučují přes úplné kvalifikované klíče.


## Vlastnictví vygenerovaných souborů a volitelný cleanup

Java i Python SDO CLI podporují nekvalifikovaný parametr
`--cleanup-output-folder-before-generation=true|false`, výchozí hodnota je
`false`. V běžném režimu se přepisují pouze soubory z aktuálně generované
množiny; ostatní soubory včetně starších generovaných výstupů zůstávají.
Tento režim funguje také po rozbalení zdrojového archivu, v němž není
pracovní manifest z `build/`. `--check` porovnává soubory přímo bez závislosti
na manifestu a nemění je.

Při `true` se odstraňují zastaralé výstupy evidované jako vlastnictví tohoto
konkrétního generátoru pro daný artefakt. SDO **nesmí** mazat výstupy Defs
Codegenu ze sdíleného adresáře `python.gen`/`java.gen`. Bootstrap má pro
výslovně zapnutý cleanup vlastní jednorázové čištění zvolených `*.gen`
adresářů před spuštěním obou generátorů. `--check` a `true` jsou vzájemně
neslučitelné. Pracovní indexy patří výhradně pod `build/`.

Parametr je nekvalifikovaný a společný pro **Java i Python** SDO CLI;
v defaultním settings souboru má tento zápis:

```text
--cleanup-output-folder-before-generation=false
```

Bez manifestu (`generated-files.json` v Pythonu,
`generated-files-java.properties` v Javě) lze standardně přepsat přesně
požadované soubory, ale **nelze spolehlivě zjistit staré výstupy**, které již
nemají vzniknout. Jejich odstranění proto neprovádí běžné spuštění ani režim
`--check`. `--clean-only` odstraní pouze dříve evidované SDO výstupy; není
ekvivalentem kompletního vyprázdnění `*.gen`.

Při spuštění univerzálního bootstrapu s
`--cleanup-output-folder-before-generation=true` se naopak před generováním
vyprázdní **celé** vybrané `src/<branch>/java.gen` a `python.gen` včetně
případných cizích souborů. Volba se propaguje k oběma CLI; proto ji používej
pouze tam, kde lze všechny soubory obnovit. Bootstrap `--root` omezuje rozsah,
`--plan-only` nemění nic a symlinkové cíle výstupu jsou odmítnuty.

Není zaručena atomická aktualizace celé sady při přerušení procesu (např.
`SIGKILL`); při běžné chybě se publikace snaží obnovit předchozí soubory.
Opakované generování identického obsahu zachovává časy modifikace existujících
výstupů.

**Dočasná výjimka `pub.tool.General` bootstrapu:** samostatná SDO CLI
nadále používá uvedený výchozí přepínač `false`, ale Tool bootstrap nyní
vyžaduje `true`, předem vyprázdní vybrané `.gen` adresáře a předává oběma
implementacím jedno UUID běhu pro oddělené indexy vlastnictví. Po úspěšném
**úplném** Defs+SDO sestavení synchronizuje všechny čtyři sady kanonických
`.extgen` z čerstvých `.gen`, včetně odstranění starých souborů a obnovy
manifestu. Není to změna SDO CLI ani bootstrapů ostatních repozitářů.

## Native CLI: vstupy, role, settings a ověřování

The Java and Python SDO CLIs use **kebab-case** options. They generate mutable
`AIigd` and concrete `AIcgd` types from annotated read-only DataObject
contracts. They do not need the original YAML/JSON/XML schema files.

### Schema-neutral input/output naming roles

The current SDO CLI takes **read-only DataObject interfaces**, not schema
inputs. One naming role `common` covers annotated read-only interfaces
regardless of whether Defs Codegen produced them from XMLDEFS, JSONDEFS or
YAMLDEFS. In particular, it does not accept the historical
`--input-technology-naming-convention:TECH:FORMAT:defsintf` or
`--output-technology-naming-convention:TECH:FORMAT:ROLE` options.

```sh
python -m eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli \
  --repository-root=. \
  --sdo-input-paths:python=src/product/python.gen \
  --technology-sdointf-output-dir:python=src/product/python.gen \
  --technology-sdoimpl-output-dir:python=src/product/python.gen \
  --dointf-naming-convention:python=algites-python-gen-intf-versioned_1 \
  --sdointf-naming-convention:python=algites-python-gen-data-intf-versioned_1 \
  --sdoimpl-naming-convention:python=algites-python-gen-data-class-versioned_1 \
  --common-codegen-naming-convention:python=algites-python-codegen-common_1 \
  --sdo-codegen-naming-convention:python=algites-python-sdocodegen-standard_1 \
  --naming-conventions-file:codegen_common=classpath:algites-python-common-codegen-conventions.yml \
  --naming-conventions-file:codegen_sdo=classpath:algites-python-sdo-codegen-conventions.yml \
  --sdointf-subpackage=impl.intf \
  --sdoclass-subpackage=impl
```

The technology qualifier is `java` or `python` according to the native CLI.
These are separate CLI processes: SDO never needs the original schema
files and never infers a format-specific read-interface naming family.
`--naming-conventions-file:ENTRY_ID=LOCATION` identifies catalog resources
using stable keys; `classpath:NAME.yml` resolves a packaged catalog.
The selected convention IDs are data, not hard-coded filename prefixes.

### Separate Common and SDO codegen conventions

SDO Codegen selects a shared Common naming profile and a distinct SDO-only
profile, independently of the incoming read-interface and output type naming:

```text
--naming-conventions-file:codegen_common=classpath:algites-java-common-codegen-conventions.yml
--naming-conventions-file:codegen_sdo=classpath:algites-java-sdo-codegen-conventions.yml
--common-codegen-naming-convention:java=algites-java-codegen-common_1
--sdo-codegen-naming-convention:java=algites-java-sdocodegen-standard_1
```

For Python use `:python` with `algites-python-*` filenames and IDs.
`CommonCodegenNameConventions` supplies the standard getter/setter names and
schema metadata. `SdoCodegenNameConventions` supplies only the raw getter,
raw presence checker and raw unsetter; it identifies its Common dependency
through `CommonNamingConvention`. Both IDs and both catalog entries
(`codegen_common`/`codegen_sdo`) are required as a pair. A mismatched family
or inconsistent Common reference is an error. Defs-specific names are not
consumed by SDO Codegen.

The old `--generated-dataobject-method-naming-convention:TECH=ID` is retained
only as an explicit alternative for callers not yet migrated. The stock SDO
`*.settings` files exclusively use the separate Common/SDO parameters.

### Explicit Java and Python inputs and dependencies

Use the four **technology-qualified** public selectors below. All accept
semicolon-separated lists and additive repetition of a selector. The selected
input list alone controls which annotated read-only DO interfaces produce
SDOs. The dependency lists supply their inherited or referenced DO contracts
and required runtime imports but **never become additional SDO targets**.

| Parameter | Meaning |
|---|---|
| `--sdo-input-artifacts:TECH=LIST` | JARs/wheels/distributions to generate from |
| `--sdo-input-paths:TECH=LIST` | Local input source trees, compiled class trees, JAR/wheel files |
| `--sdo-dependency-artifacts:TECH=LIST` | Packaged dependency contracts, resolution only |
| `--sdo-dependency-paths:TECH=LIST` | Direct dependency source/class paths and archives, resolution only |

`TECH` is `java` or `python`. Java reads interfaces from source or bytecode
according to the selected path; Python reads annotated, importable classes
from source trees or wheels. A direct
`--sdo-input-paths:python=/path/to/file.py` or
`--sdo-input-paths:java=/path/to/Interface.java` selects only the specified
source file, not sibling contracts. Python retains the containing `python` or
`python.gen` import root to load dependencies; Java source compilation also
resolves required referenced types. Direct `.py` dependency paths likewise
add only their import root, never a new generation target. If the input selection is empty, there is no
implicit scan of all available dependencies. Naming convention selection is
independent of where the input came from. `--dointf-input-classes` is a
legacy additional explicit filter and is not a substitute for an input root.

The former `--technology-dointf-input-dir`, `--dointf-input-artifacts`,
`--dointf-input-paths` and `--dointf-classpath` forms are superseded by these
four selectors; bootstrap must use only the new public names. Importable
support dependencies may still require standard Java/Python classloader paths
from the build environment in addition to the configured selectors.

### Private workspaces, publication and parallelism

Every SDO invocation creates a unique
`<repository>/build/<artifact-relative-path>/sdocodegen/<UUID>/` workspace
with `tmp/`, `staging/` and an active `.run.lock`. All temporary expansions,
source preparation and generated outputs are staged there. Its dedicated
`<repository>/build/<artifact-relative-path>/sdocodegen/.publish.lock`
serializes final publication only for
this artifact/generator, not unrelated artifacts or Defs runs. The source
set is tracked with hashes, and non-owned or externally changed generated
files are never overwritten. The commit renames staged files after validation
and attempts rollback if an ordinary I/O failure interrupts it; it is **not**
a guaranteed atomic multi-file transaction after a power failure or process
termination. Successful invocations remove their own UUID workspace.

Cleanup of temporary workspaces is scoped to the artifact/generator tree and
skips UUIDs whose run locks are active; cleaning a whole `build/` tree while
another process is running is not safe. `--check` does not publish; `--clean-only`
removes only generated outputs owned by this generator. These rules apply to
Java and Python alike and do not require extra CLI arguments. See the Defs
reference for the corresponding independent workspace layout.

A format-specific read-only contract may extend a common read-only contract.
The generated mutable interface retains the corresponding read-only and
mutable inheritance rules, but each newly generated concrete SDO uses the
single `impl.common.AIcSmartDataObject` runtime (or a generated non-final
concrete parent where inheritance permits). XML/JSON/YAML marshalling is
provided by independently discovered format-binding providers, not by
technology-specific SDO bases or static `xmlNestedTypes()` maps. Every new
concrete implementation declares `AIaSmartDataObjectImplementationBinding`
with its read-only contract. A parent SDO is generated only if its read-only
contract is part of explicit SDO input selection; dependency-only contracts
do not silently trigger generation.

### Output packages, settings, and verification

`--sdointf-subpackage` and `--sdoclass-subpackage` independently append a
validated suffix to the input type's package. Leaving either unspecified
preserves the original package. For separate Java named modules use distinct
packages, not a common suffix. The stock Algites settings select `impl.intf`
and `impl` respectively.

The settings loader uses four layers for each native target language: packaged
`algites-sdocodegen-LANGUAGE-default.settings`, one selected profile-family
classpath resource `sdocodegen-LANGUAGE.settings`, `--settings-file=PATH`, and
explicit CLI options. Installed naming families (Algites, Standard Prefix,
Standard Postfix) are alternatives, never simultaneously active. Explicit naming
profile IDs select one family; an ambiguous selection fails with a diagnostic.
If the same family is present more than once (for example, current source
settings together with an older published profile JAR in `source` mode),
its identity is the qualified Common + SDO naming profile IDs; the resource
with the highest classpath priority wins. A changed input/output-interface
naming selector alone does **not** create another family. Different Common/SDO
families remain incompatible without an unambiguous explicit selection;
there is no fallback to merging Algites and Standard Prefix/Postfix profiles.
The native Java and Python settings loaders enforce the same rules, even
outside bootstrap. All settings use qualified
`--key:IDENTIFIER=value` entries and merge by the full key before `=`.
An empty value removes an inherited entry; repeatable lists have named entries.
Bare `--check` remains supported, as do `--check=true` and `--check=false`.
The **new** SDO CLI does not translate obsolete format-qualified naming
selectors. If an old published profile JAR is present alongside a current
source profile, the Java and Python settings loaders discard the outdated
profile overlay and choose the current compatible profile. When only outdated
profile overlays are available, they raise an explicit diagnostic rather than
silently applying removed options. Explicit invalid CLI/settings-file options
are still validated normally. In `source` bootstrap mode, the shared Java
bootstrap locates the source profile in the owning sibling checkout and puts
its configuration resources ahead of published tool JARs; `remote` mode never
silently imports source settings. Legacy `old` implementations are unchanged.

`--setter-inheritance-policy` is supported by both SDO native CLIs, with
`INHERIT_AS_GENERIC_PARAMETER` as the packaged default. The setting is used
only for handwritten or generated input contracts whose field and owner
annotations do not supply a concrete policy. `--setter-inheritance-policy`
never overrides explicit field or type metadata.

An explicitly selected but missing SDO input path or artifact is an error. A dual-target
artifact runs the Java and Python generators independently with their respective
language defaults.

`--check` verifies generated outputs without changes, and `--clean-only`
performs the generator's output cleanup without regenerating. Positional
single-contract CLI entry points have been removed. For an individual contract,
use `--dointf-input-classes:java` (legacy filter) or a selected input path and role mapping.

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



## Generovaná rozhraní, implementace a runtime chování


## Kontrakty, dědičnost, XML a integrace Defs

`pub.tool.General:1.1-SNAPSHOT` contains a second, **schema-independent** generator.
It accepts annotated `AIig*` read contracts through either a class object or
its generated source file. It never reads YAML, JSON Schema, XSD or the
canonical-definition model. For Java, source-based generation uses the JDK
compiler **in memory** and inspects the compiled interfaces through ordinary
reflection; it does not require a separate Java compile task. Python imports
fresh source modules and reflects over the annotated types.

The `intf` artifact exposes the generation API, `impl` generates mutable contracts
(`AIigd*`, or a different configured marker) and concrete implementations
(`AIcgd*`), and `cli` is the adapter used by build orchestration.

The CLI now uses **semantic-role options** and named settings, rather than
positional class/output arguments. With no arguments it reads the packaged
`sdocodegen-java-default.settings` or
`sdocodegen-python-default.settings`, selected by native CLI.

Java (processing a binary JAR):

```sh
java -cp "$CLASSPATH" eu.algites.tool.codegen.sdo.impl.cli.AIcSdoCodegenCli \
    --settings-file=config/my-sdocodegen.settings \
    --sdo-input-artifacts:java=eu.example:read-contracts:1.1-SNAPSHOT \
    --sdo-dependency-paths:java=build/libs/dependencies
```

Python (using the native source loader):

```sh
python -m eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli \
    --settings-file=config/my-sdocodegen.settings
```

The settings file defines independent technology-role mappings, input source
roots and output roots; see [nastavení CLI a naming katalogů](#native-cli-vstupy-role-settings-a-ověřování).
Both CLIs support `--check` for non-mutating verification. Java dependencies
of source contracts must be visible on the process classpath or via
`--dointf-classpath`; Python modules must be importable from the configured
source root. Handwritten contracts are supported without schema generation.

Inheritance is preserved in both the mutable interface and the concrete class.
Inherited fields are implemented by the generated base class, and declared
fields by the child. Conflicting inherited metadata fails explicitly.

Nested direct `AIig*` value getters are overridden covariantly in the generated
`AIigd*` interface and are paired with an `AIigd*`-typed setter and raw getter.
The concrete `AIcgd*` class implements the same typed signatures and continues
to use the normal `get_EffectiveField`, `get_RawField`, and `set_RawField`
mechanisms; it does not wrap or convert the nested object. Python also preserves
explicit nullable nested return types (`AIig* | None` -> `AIigd* | None`).
The Defs read-only contracts now expose lists as `List<? extends AIig*>`
or `AIiMultiMappedList<? extends AIig*>`, including technology-specific
getters. This makes a narrower mutable list return type potentially legal
when its elements implement the read-only item type. SDO must still retain
the required runtime collection semantics and setter policy; list narrowing
is not automatically guaranteed for every handwritten contract. Types from
handwritten read contracts are supported.

When a format-specific getter overrides the neutral
`List<? extends BaseRule>` with
`AIiMultiMappedList<? extends FormatRule>`, Java SDO generic setter
inheritance must preserve **both** the element bound and the indexed
collection type. The generated mutable parent uses
`List<? extends TRuleList>`; its derived XML/JSON/YAML interface uses
`AIiMultiMappedList<? extends TRuleList>` with a bound referring to the
format-specific mutable item. The generated concrete getter must use a
compatible `AIiMultiMappedList` return type too. Flattening the specialized
getter to `List`, or excluding it from the inherited generic-argument map,
produces respectively an invalid Java override or an incorrectly missing
`TRuleList` argument. The generator regression
`AItcSdoMappedCovariantInheritanceTest` compiles the complete parent/child
mutable hierarchy and implementations from the emitted source.

#### XML QName deserialization in generated implementations

For XML contracts, both native generators now emit a class-level convenience
parser: `AIcgd*.fromXml(String)` on Java and `AIcgd*.from_xml(str)` on Python.
The entry point delegates to the namespace-aware, order-tolerant parser in
`pub.lib.General`. Java maps nested `AIig*` getter return types
(including `List<? extends AIig*>`) to generated `AIcgd*` classes using an
explicit field-name/class mapping. Python emits `__xml_repeated_fields__` on
mutable contracts, resolves fields from reflected getter and source-property
annotations, and stores lazy module-qualified nested implementation bindings
on concrete classes. Lazy resolution prevents import cycles between generated
SDO types and supports inherited bindings. Both generators preserve the original
expanded XML QName metadata; they do not infer XML namespaces from Python
attribute names or Java getters.

The generated `fromXml`/`from_xml` methods parse structural fields and known
scalar lexicals; strict XSD validation, wildcard materialization and correlated
choices remain the responsibility of the separate schema-validation layer.
The XML runtime does enforce known field-level `minOccurs`/`maxOccurs` wire
intervals; those do not substitute for the full XSD content-model grammar. Unknown XML members fail explicitly rather
than being dropped. The generated XML wrapper is not an XSD validator.


The SDO mutable and implementation output roots may coincide when their
actual generated relative paths are distinct. For JPMS, configure distinct
output subpackages if separate named modules will own the two output roles.
`defscodegen` owns read contracts; `sdocodegen` owns mutable contracts and
concrete implementations. Source trees under `.gen`
are generated outputs and should never be committed or packaged as handwritten
source archives.

Use `./generators/code/bootstrap.sh` to build without loading a
Builder plugin that may itself depend on these generators.

Batch CLI options, role-based cleanup and native Java/Python prerequisites are
documented in [Code Generators Reference Guide](../CODEGEN-REFERENCE.md).

### Defs 1.1 integration: field restrictions and nominal XML elements

The SDO generator consumes `AIaDataObjectField.fieldName`, `presence`
(`REQUIRED`, `ALLOWED`, `FORBIDDEN`), `allowsNull`, and `namingConvention`
metadata. Human-readable labels are resolved through `AIaFieldLabel`;
default values are expressed by the separate getter annotation
`AIaDataObjectFieldDefault` with `kind`, `defaultValueFactory` and
`defaultArguments`. The factory is selected by the CPDiscovery specialized
`factoryInterface`, optional `factoryCategory` and provider ID; no legacy
`AIaFieldDefault` resolver is generated. XML-specific QNames belong to `AIaDataObjectXmlSchema` and
`AIaDataObjectFieldXmlSchema` and are copied to the mutable contract. Inherited
fields may be restricted, but the implementation rejects relaxation of
required/forbidden presence or nullability. XML element contracts use the
specialized `_xe` naming profiles for Java and Python (`__xe_` for Python
source files). **Closed `CHOICE` contracts are immutable by design.** Defs Codegen
creates a `sealed` Java read-only interface with one concrete `record` for
each alternative in the same Java package/module; the records directly
implement the sealed interface. The Python equivalent is a closed set of
immutable (`@final`, `@dataclass(frozen=True)`) read-only variants. Neither
language may generate a mutable `AIigd*` choice interface nor a mutable
`AIcgd*` implementation for the CHOICE itself. SDO Codegen handles mutable
**payload DataObjects** referenced by those variants and can store a complete
immutable choice as a field value; it must not synthesize setters or an
implementation for individual choice-variant components. Changing the chosen
alternative means replacing the containing field with a new immutable variant,
not mutating an existing choice. A referenced mutable payload remains a normal
SDO and retains its own mutation/validation rules. This distinction applies to
`Structure`, `ElementListChild`, `TypeContent` and all other generated CHOICE
contracts. A missing mutable choice class is expected, not a regeneration
error. The source-generated records/classes are owned by Defs Codegen and
must be preserved by the bootstrap without relocating them.

Java closed-choice records remain in the Defs Codegen sealing
module; SDO does not relocate them. When a field refers to a closed-choice
helper, its writable getter, setter, and any generic type bound must retain
the exact **read-only choice interface** (`AIig*`). Generating an `AIigd*`
name for a helper with no eligible DataObject annotation produces a missing
Java type and is invalid, even if the helper happens to extend a DataObject
marker for compatibility. Only annotated DataObjects and eligible neutral
descendants are transformed into mutable nested references.

Generated writable DataObject interfaces extend the **common**
`AIiSmartDataObject` interface and their implementations use the common
`AIcSmartDataObject` runtime, rather than technology-specific SDO classes. Remaining limitations are documented in
[Defs Codegen recursive types](../defscodegen/DEFS-CODEGEN-REFERENCE.md).

### Separate Common and SDO naming conventions (1.1-SNAPSHOT)

Defs and SDO Codegen have **independent, role-specific naming catalogs** and
share only the `codegen_common` conventions used to keep the read-only getter
names compatible with the generated writable API. The SDO-specific
`codegen_sdo` profile defines SDO-only methods, including the raw getter,
presence checker, unsetter, and synthetic map-entry getters. These are not
selected from one combined Defs/SDO profile.

For Java, the native SDO CLI accepts the following options (Python uses the
corresponding `:python` qualifier and catalog IDs):

```text
--naming-conventions-file:codegen_common=classpath:algites-java-common-codegen-conventions.yml
--naming-conventions-file:codegen_sdo=classpath:algites-java-sdo-codegen-conventions.yml
--common-codegen-naming-convention:java=algites-java-codegen-common_1
--sdo-codegen-naming-convention:java=algites-java-sdocodegen-standard_1
```

The selected SDO profile's `CommonNamingConvention` must reference the selected
Common profile. The Defs stage separately selects `codegen_defs`, and its
own profile must reference the same Common convention when generating read
contracts to be consumed by SDO.

The generated field-specific names use configured `NameCompositions`; technical
`_` prefixes are part of those compositions rather than hard-coded in the
generators. The fixed SmartDataObject system API is unaffected by naming
profiles. `_toMapping(AInSdoFieldValueLoadingMode)` and
`_getValidationIssues(AInSdoFieldValueLoadingMode)` require an explicit raw
versus effective value-loading mode.

The new SDO generator accepts annotated read-only DataObject interfaces
independently of Defs. It does **not** consume XMLDEFS/JSONDEFS/YAMLDEFS,
canonical records, or any Defs-specific compiler model. Generated SDO classes
support synthetic JSON/YAML map-entry `_getKey()` and `_getValue()` methods;
full Java integration and production bootstrap coverage still require
independent verification. Interface/implementation packages can be configured
separately with `--sdointf-subpackage` and `--sdoclass-subpackage`.


## Kolekční pole: schválený kontrakt (implementace, integrace dosud neověřena)

**Stav:** Java/Python runtime a emitery nového SDO generátoru jsou upravené
pro živý getter, indexované seznamy a vynechání veřejného `setX(list)`.
Cílené Python runtime testy prošly, úplný Java Gradle build a samostatný
end-to-end integrační bootstrap obou jazyků však zatím chybí.

### Getter, inicializace, `unset` a náhrada kolekce

- Pro pole `LIST` i `MAP` **negenerovat veřejný setter**, který by dovolil
  přiřadit cizí kolekci (`setRules(List<...>)`, `setRules(Map<...>)` ani
  setter přijímající pole). Uživatel mění obsah přes **živou kolekci** získanou
  getterem; její konkrétní implementaci vlastní SDO runtime.
- První `getX()` interně založí prázdnou kolekci odpovídající metadatům
  konkrétního pole. Může použít soukromou `initX()` (jméno a umístění je
  implementační detail), nikoli veřejnou generovanou inicializační metodu.
  Indexovaný seznam je vždy vytvořen jako `AIiMultiMappedList` se všemi
  registrovanými definicemi indexů, ne jako libovolný `List`.
- `_unsetX()` odstraní **vazbu vlastníka** na danou instanci kolekce. Dříve
  vrácený seznam může nadále existovat a být samostatně upravován, ale nesmí
  již měnit vlastníka. Následující `getX()` vytvoří novou, prázdnou a nezávislou
  instanci se správnými definicemi indexů. Stejná pravidla platí v Pythonu.
- Interní načítání XML/JSON/YAML může novou kolekci založit a naplnit přímo;
  nesmí proto potřebovat generovaný veřejný setter ani přijmout cizí indexový
  objekt jako finální uloženou hodnotu. Žádné `put` do indexové mapy:
  zdrojem pravdy zůstává seznam a jeho podporované operace.
- Sémantiku `isSetX()` / `_isPresent_X()` vzhledem k **pouhému prvnímu volání
  prázdného getteru** je nutné před implementací definitivně určit; samotná
  alokace v paměti a přítomnost položky v serializovaných datech nemusí být
  totéž. Nelze tiše změnit význam `minOccurs=0` nebo `ALLOWED`.
- `AIig*` read-only API nesmí dovolit modifikaci kolekce přes `remove`,
  `clear`, iterátor či `subList`. Pouhá generická Java deklarace
  `List<? extends T>` toto runtime omezení **nezaručuje**; SDO vrací
  zapisovatelný, skutečně živý pohled se stejnou sémantikou v Pythonu.

**Příklad cílového API (typový kontrakt; konkrétní getter určuje naming profil):**

```java
// Defs: indexovaný seznam; bez indexu by byl návratový typ List<? extends Rule>.
AIiMultiMappedList<? extends AIigRule> getRuleList();

// SDO: přístup k položkám je zapisovatelný; žádný setRuleList(...).
AIiMultiMappedList<AIigdRule> getRuleList();
void _unsetRuleList();
```

`AIiMultiMappedList<T>` již rozšiřuje `List<T>`; následný typ může getter
kovariantně zpřesnit z `List<? extends AIigRule>` na
`AIiMultiMappedList<? extends AIigRule>` (při zachování kompatibility
položkových typů). Naopak tím nelze garantovat indexy u libovolné implementace
původního rodičovského rozhraní.

### Pojmenování getteru seznamu

Defs a SDO musejí sdílet jednu **Common** naming konvenci pro listové gettery
odlišnou od běžného skalárního getteru. Požadovaná vlastnost je, aby bylo ze
jména metody zřejmé, že jde o kolekci. Možné kompozice jsou např.:

```text
identifier=Rule → getRuleList()   # identifier + "List"
identifier=Rule → getRules()      # pluralizace ("s" jen u jednoduchého případu)
```

**Preferována byla varianta `getRuleList()` před anglickou pluralizací; nový samostatný naming role pro tuto variantu však ještě není kompletně zaveden do obou generačních stupňů.**
Pro komplexní pluralizaci není bezpečné slepě připojovat `s` (např. `Category`,
`Person`). Při zavedení se musí aktualizovat metadata pole, getter matching,
Defs i SDO emitter a profilové konvence **současně** pro Java/Python.

### Indexy, identita a neměnnost klíčů

`AIiMultiMappedList` podporuje více nezávislých mapových pohledů. Indexy
zůstávají synchronní při **operacích nad seznamem a podporovaných mapových
pohledech**, ale **není požadováno sledování následných mutací klíčových polí
již vložených objektů**. Hodnoty klíče, jejich `equals`/`hashCode` a identita
musí při uložení zůstat stabilní, stejně jako klíče v běžné hash mapě. Tento
zákaz už platí v aktuálních Java/Python runtime kontraktech; žádné přepočítávání
indexů po `rule.setKind(...)` se nemá zavádět.

Dnes existuje Java `@AIaDataObjectListKeyDefinition(name, fields, required)`
(opakovatelná přes `@AIaDataObjectListKeyDefinitions`) na getteru opakovaného XML pole;
Python read-only kontrakty uchovávají obdobný popis v
`__key_definitions__`. SDO Java metadata přenáší; SDO Python podporuje
příslušné XML metadata. **Dosud nejde o univerzální deklaraci pro všechny
technologie.** Současný runtime Java používá `mapByKeyType(...)` a
`keyDefinition(...)`, Python `map_by_key_type(...)` a `key_definition(...)`;
`mapByKeyId`/`map_by_key_id` jsou nyní implementované a kontrolují registraci klíče.

Cílem je **technologicky neutrální anotace definice indexu** na getteru
kolekce, převzatá nezávislým SDO z Defs výstupu; XML/JSON/YAML původ je pouze
zdroj informace pro Defs. Vstupní XML `xs:selector` lze převést na index jen
tehdy, pokud jednoznačně vybírá **přímé položky jediného seznamu**;
`xs:field` se převádí na typované přístupové cesty nad položkou. Ostatní
selectory se nepřevádějí na index a mají vyvolat samostatný WARNING (nikoli
ztrátu dat ani tvrzení, že proběhla plná XSD validace). U `xs:keyref` se
indexové API nevytváří; XSD validátor může tato omezení vyžadovat nezávisle.

Generované `CONST` musí poskytovat **identifikátory indexů i identifikátory
použitých datových polí**, včetně jednoznačných odkazů na složené cesty. Anotace
nemají obsahovat ručně psané řetězce, pokud jde o generované modelové členy.
Následující příklad je **návrh API, nikoli existující anotace**:

```java
// Příklad budoucí technologicky neutrální anotace na getteru.
@AIaDataObjectKeyDefinition(
    name = CONST.UNIQUE_STRUCTURE_ROLES,
    fields = {AIigRule.CONST.FIELD_KIND},
    required = true)
AIiMultiMappedList<? extends AIigRule> getRuleList();
```

Pro JSONDEFS/YAMLDEFS objektově klíčované položky je nejprve potřeba zachovat
syntetické `_getKey()` a `_getValue()` ze stávajícího modelu. Pokud je možné
položky vyjádřit jako seznam s indexem dle `_getKey()`, lze použít tentýž
`AIiMultiMappedList`. **Není ale dovoleno mechanicky zaměňovat JSON `object`
a XML seznam:** převod musí zachovat originální klíče, hodnoty, serializaci,
unicitu a přítomnost polí. Obecná XML projekce na `MAP` zůstává odložená.

### Defaulty a explicitní empty při generování

SDO generátor přebírá metadata `AIaDataObjectField` z anotovaného read-only
kontraktu; samostatná anotace `AIaDataObjectFieldDefault.kind` obsahuje `DECLARATION_ONLY`,
`IF_FIELD_VALUE_NOT_PRESENT`, `IF_FIELD_VALUE_EMPTY`, případně
`CONSTRAINT_DEFAULT` (přepis XSD `fixed`). Pro explicitně povolené empty
SDO generuje technické `_setEmpty_Xxxx()` a `_isEmpty_Xxxx()` podle
**SDO naming konvence**, jinak je negeneruje. `setXxx("")` je běžný řetězec;
`_setEmpty_Xxxx()` zapisuje sentinel, který v XML vytváří prázdný element.
Při fixed nepřijímá SDO jinou hodnotu ani explicitní empty. Pro číselné
`CONSTRAINT_DEFAULT` se hodnota kontroluje v deklarovaném typu, nikoli lexikálně;
např. `fixed="1"` dovolí integer 1, ale nikoli Boolean `true`. V Javě proto
runtime při volání generovaného setteru boxuje primitivní typ getteru pro
reflektivní typovou kontrolu. Raw serializace nepřepisuje nepřítomná nebo
prázdná pole efektivními defaulty. Metadata fieldu ukládají samotnou
anotaci (včetně factoryInterface/kategorie a argumentů). Runtime při potřebě
vyhodnocení zavolá CPDiscovery znovu; její registr již drží objevené
factory instance, takže nedochází k novému ServiceLoader scanování.
Výsledek factory se necacheuje: `Optional.empty()` znamená explicitní
`null`, který není totéž co chybějící anotace ani raw nepřítomnost.

SDO nevytváří nový kanonický model a nečte Defs schémata. Kanonický bootstrap
zůstává generovaný ve vlastní vrstvě, ne ručně přepisovaný. Až po ověření
prvního deploye se smí odstranit deprecated kompatibilní deklarace.

### Testy požadované před zavedením

Ověřit v **Javě i Pythonu**: absence veřejného setteru pro `LIST`/`MAP`, správný
typ getteru, první inicializace, opakované gettery, `_unsetX()` a oddělení starého
a nového seznamu, prázdné a chybějící pole, XML/JSON/YAML serializace,
úniky mutací přes read-only kontrakt, více indexů, duplicitní klíč, změnu položek
přes `add`/`remove`/`clear`, a selektor ignorovaný s warningem. Výsledek
ověřit skutečným Defs → SDO generačním průchodem, nikoli jen porovnáním textu.

### Sjednocení diagnostiky podle závažnosti (implementováno)

Společný Java/Python kolektor Codegenu umí strukturované úrovně `DEBUG`, `INFO`,
`WARNING`, `ERROR` s původní zprávou, zdrojovým souborem, umístěním a volitelným
`Hint` (u `ERROR` povinným). Události se ukládají v pořadí vzniku a vypisují
**podle rostoucí severity**: `DEBUG` → `INFO` → `VALIDATION WARNINGS` →
`VALIDATION ERRORS`. Debug události se vypisují pouze při
`ALGITES_CODEGEN_DEBUG=true`; upozornění sama o sobě generování nezastaví.

Každá neprázdná skupina má vlastní počitadlo `[x/n]` a počitadlo konkrétního
zdrojového souboru `(a/b)`; chyby bez známého zdroje se neslučují do jedné
fiktivní skupiny. V rámci jedné severity zůstává pořadí záznamů stabilní.
Dojde-li k validační chybě, kolektor zachová dříve sebrané zprávy nižších
úrovní a poslední vypíše chyby. Nečekané programátorské výjimky nepřekládá
na validační chyby. Při `codegen-validate-one-input-at-a-time-only=true` se
nejprve dokončí validace prvního chybného souboru v dostupném rozsahu kontrol.

V Pythonu se používá `AIcCodegenValidationBatch.warning(...)`, `.info(...)`,
`.debug(...)`, případně `.add_diagnostic(...)`. V Javě analogicky
`AIcCodegenValidationBatch.addDiagnostic(AInCodegenDiagnosticSeverity, ...)`.
`finish()` ukončuje běh pouze kvůli ERROR. Na úspěšné cestě se nefatální záznamy
vypíšou pomocí `report_non_errors(...)` (Python) nebo
`reportNonErrors(...)` (Java). U výjimky se o kompletní výpis postará
společný handler CLI. Zavedení konkrétních warningů k ignorovaným XML
selectorům je samostatná změna Defs frontendu; kolektor ji nyní umožňuje,
ale nesmí být zaměňována za implementovanou podporu selectorů.

## Parita Java/Python a zachování funkčnosti

| Oblast | Java | Python | Podmínka parity |
| --- | --- | --- | --- |
| Vstupní DO kontrakty | `.class`, JAR nebo zdrojové `.java` přes in-memory JDK compiler | importovatelné anotované `.py` | Výběr podle anotací, ne prefixu `AIig` |
| Common/SDO profily | `:java` | `:python` | stejné sémantické role a vazba Common |
| Výstupy | `AIigd*`, `AIcgd*` | `AIigd*`, `AIcgd*` | stejné typované getter/setter/isSet/unset principy |
| Dědičnost a metadata | anotace, generované base typy | metadata Python DataObject | neztrácet identity/presence/nullability/QNames |
| Virtuální map entry | `_getKey()`, `_getValue()` | `_getKey()`, `_getValue()` | neserializovat jako vnořené hodnotové pole |
| XML | `fromXml` | `from_xml` | podporované QName a wire cardinality, nikoli plná XSD validace |
| Ověření | TestNG + Gradle (stále nutné celé spustit) | pytest + Defs→SDO CLI | u změn doplnit scénáře v obou implementacích |

Zásadní není mechanicky stejná syntaxe jazyků, nýbrž **shodné typované
programátorské API** s generovanými metodami `setName()`, `isSetName()`,
`unsetName()` a odpovídajícími gettery. Python nesmí být převeden na obecné
string-based `is_set('name')` / `unset('name')` místo metod na kontraktu.

## Funkční omezení a bezpečné zavedení

SDO není XSD/JSON Schema validátor. Generované XML parsery nepokrývají
všechny kombinace wildcard/choice/identity constraints; neznámé XML členy
se nemají potichu zahazovat. Před publikací jsou nutné integrační testy
skutečně zkompilovaných Java typů, nejen generování textu, a stejný základní
rozsah scénářů v Pythonu.

Univerzální `devops/bootstrap` zachovat až do rozšíření builderu 1.1 o
standardní fázi zdrojového generování; neimplementovat speciální bootstrap.
Budoucí modelové artefakty `model.schema`, `model.do`, `model.sdo` dosud
neexistují a nejsou předmětem této verze.

### Regresní scénáře

- `impl/src/develop/java`: DataObject introspekce, generování, setter-policy,
  dědičnost a XML deserializace (historická i současná implementace podle testu).
- `impl/src/develop/python`: oddělené profily, CLI/settings, typové kontrakty,
  virtual map entry, XML parsing, diamond inheritance, metadata a runtime.
- `cli/src/develop/java`: vrstvení nastavení, naming katalogy a výběr vstupních
  tříd/artefaktů.

Po změnách udržovat tuto `SDO-CODEGEN-REFERENCE.md` a krátký `README.md`;
nepřidávat další průběžné stavové dokumenty.

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

**Omezení současného bootstrapu:** vybrané artefakty zpracovává oddělenými
voláními CLI. Výpis není ještě jednou atomickou validační transakcí za všechna
`--root` artefakta. Univerzální bootstrap dál používá `.old` generační backendy,
nikoli dosud neúplný nový kanonický Defs backend. Nezaměňovat změnu vstupní
vrstvy CLI za migraci samotného generátoru.

### Gettery kolekcí odvozené z Common profilu (list_getter)

SDO Codegen převezme `getRuleList()` z read-only DataObject kontraktu a
připojí k němu živou kolekci; nevytváří nový název podle vlastního pravidla,
nepoužívá `setRuleList(...)` a nezaměňuje `fieldName="rule"` s názvem metody.
Zdrojová kompozice je definovaná v Common naming profilu a platí stejně
pro Javu i Python. Historické bootstrapované implementace ještě musejí být
regenerovány před odpojením kompatibilního přechodového kódu.

### Artefaktové závislosti, kompilace a paralelní Gradle úlohy (P0)

SDO CLI pracuje odděleně s generačními vstupy (`--sdo-input-*`) a se zdroji
používanými pouze pro dohledání dědičnosti (`--sdo-dependency-*`). Tyto volby
**nenahrazují** knihovní závislosti cílového artefaktu v `modustro-artifact.yml`.
Když se typ z cizího artefaktu objeví ve veřejném Java/Python kontraktu,
jeho artefakt je přímá závislost `product_api`. Pro interní implementační
odkazy se použije `product_implementation`.

Zejména `generators/code/sdocodegen/intf` vyžaduje přímé `product_api`
závislosti na `pub.lib.General_naming.convention.intf` (společné read-only rozhraní
`AIigCommonNamingConventions_1`) a `pub.lib.General_common.util`
(`AIiMultiMappedList`). Bez nich může izolované `compileJava` selhat,
i když generátor úspěšně vytvořil zdroje a jiné artefakty již byly sestaveny.
Nativní Gradle bootstrap převádí `product_api` na `api`; nespoléhá se na
tranzitivní `implementation` závislosti jiných artefaktů.

Při paralelním Gradle buildu zůstávají pracovní UUID adresáře a publikování
oddělené pro každý artefakt podle pravidel v této příručce. Tato izolace
pracovních souborů **neřeší** závislostní graf; Gradle musí mít všechny
přímé závislosti v artefaktových deskriptorech, aby správně naplánoval
kompilaci a publikování.

Kontrola přímých závislostí probíhá také pro Python importy mezi Modustro
artefakty. Počet nalezených odkázaných typů není počet závislostí: jeden
artefakt se v deskriptoru uvede jednou, s odpovídající kategorií použití.
`naming.convention.intf` obsahuje v současném bootstrapu také generované
mutable Python kontrakty, které přímo importují `data.smartdataobject.intf`;
tento typový provider je tedy přímou `product_api` závislostí cílového
artefaktu, nikoli pouze transitivní závislostí přes runtime implementaci.

## Kompatibilní anotace DataObject a projekce společných polí

Aktuální SDO zpracovává jedno společné read-only `AIig…` rozhraní pro
každý logický typ. `AIaDataObject` a `AIaDataObjectField` jsou přímo
na tomto rozhraní a jeho getterech; samostatná technologická rozhraní
se v novém Defs Codegenu negenerují. Formátové anotace na společném
rozhraní určují serializační vazby a jejich ID, verze i URL jsou nezávislé. Přechodně jsou
zachovány staré `AIaDataObjectJsonSchema` / `AIaDataObjectYamlSchema` /
`AIaDataObjectXmlSchema` / `AIaDataObjectFieldXmlSchema` jako deprecated a současně
existují `AIaDataObjectJsonSchema`, `AIaDataObjectXmlSchema`,
`AIaDataObjectFieldXmlSchema`. Nová SDO implementace má používat autoritativní moderní metadata;
YAMLDEFS dosud postrádá samostatnou novou schématovou anotaci a aktuální
implementace proto přechodně používá `AIaDataObjectYamlSchema`. To je
otevřený migrační bod, nikoli povolení porovnávat hodnoty s JSONDEFS.
Neprovádí se porovnání ID, verzí ani URL napříč technologiemi.

XML parser v Pythonu používá `__xml_schema__` a `__xml_schema_fields__`
s fallbackem na staré `__xml_schema__` a
`__xml_schema_fields__`. Java metadata scanner propojuje
`AIaDataObjectField` na společném getteru s XML QName na
odpovídajícím getteru společného rozhraní; test `AItcModernXmlSchemaOverlayTest` ověřuje
přechod i bez starých anotací. Python `test_xml_qname_deserialization.py`
obsahuje zrcadlový test nových metadat a roundtripu.

**P0 otevřené:** rozdílné sady polí mezi XML/JSON/YAML vyžadují explicitní
model projekce formátově specifických generických getterů. Současný průnik
společných polí není dostatečný k zachování všech formátově specifických
DataObject vlastností, pokud obecné anotace smějí být pouze na společných
rozhraních. Jakýkoliv návrh doplnění struktury dědičnosti musí být předem
odsouhlasen. Historické `sdo.old` se zatím nadále nachází ve zdrojovém
stromu a jeho nesoulad s novou podobou anotací zůstává možným blokátorem
plného Gradle sestavení.



### Rozsah parity regresních scénářů — audit P0

Statická inventura testů (9. 11. 2026): SDO Java
**12 souborů / 32 metod `@Test`**, Python **16 souborů / 57 funkcí
`test_*`**. K tomu SmartData runtime Java **17 souborů / 42 `@Test`**,
Python **17 souborů / 74 `test_*`**. Nejde o sémantický převod všech
scénářů; mimo nové párové testy zůstávají historická pokrytí nevyrovnaná.
Existující `sdo.old` fixture také používají odstraněné vlastnosti
`AIaDataObject`/`AIcdDataObject` a mohou selhat ještě před ověřením
současného SDO API. Regresní parity nelze deklarovat hotové pouze na
základě kompilace aktuální služby.

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


### Importy nových anotací a role technologických rozhraní

SDO Java CLI musí rozpoznat XML element/type přes `AIaDataObjectXmlSchema`
(`eu.algites.lib.data.dataobject.xmlschema`) a pro historické kontrakty také
přes deprecated `AIaDataObjectXmlSchema`. JSON/YAML technologie se rozlišují podle
základního DataObject rozhraní, nikoli podle společné anotace
`AIaDataObjectJsonSchema`, kterou sdílejí. Python SDO používá importy
`eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema`,
`eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema` a
`eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema`.
Tyto cesty mají odpovídající deklarace v `pub.lib.General`.


Při Java SDO generování se XML metadata typu/getteru nyní čtou přednostně
z `AIaDataObjectXmlSchema` / `AIaDataObjectFieldXmlSchema` ve správném
`dataobject.xmlschema` package. Původní `AIaDataObjectXmlSchema` a
`AIaDataObjectFieldXmlSchema` jsou podporované jako vstupní fallback; při duální
přítomnosti se musí shodovat XML QName a druh definice. Generovaný mutable
kontrakt dočasně obsahuje obě schématové anotace. Toto pravidlo platí i při
vstupu obsahujícím pouze nové anotace, bez nutnosti ručního doplnění
historických deklarací.

## P0: Oddělení historického SDO generatoru a přechod bootstrapu

Po migrační kontrole se historické zdroje `sdo.old` uchovávají doslova v
`generators/code/sdocodegen/legacy-archive/`; nejsou už součástí zdrojových sad
`src/product` ani automaticky spuštěných historických testů. Důvodem jsou
nekompatibilní odkazy na odstraněné vlastnosti obecného `AIaDataObject` a
`AIaDataObjectFieldXmlSchema`. Marker archivu: `ALGITES-LEGACY-SDO-INCOMPATIBLE`.
Žádné odstraněné atributy se kvůli historickému generátoru nevracejí.

`devops/bootstrap/sdo-java.gradle` používá veřejné Java CLI z aktuálního
namespace `eu.algites.tool.codegen.sdo.impl.cli.AIcSdoCodegenCli`, výběr
`--sdo-input-paths:java` a `--sdo-dependency-paths:java` se seznamy cest
oddělenými středníkem a explicitním seznamem tříd.
Při Java source-input režimu SDO kompiluje read-only rozhraní v paměti.
`--sdo-dependency-paths:java` smí obsahovat pouze existující JAR soubory
nebo existující adresáře s třídami a resources. Gradle proto předává stejný
ověřený seznam existujících cest v `java -cp` i v uvedeném parametru;
neexistující volitelné výstupní adresáře vynechá, avšak chybějící JAR odmítne.
Při přímém volání CLI způsobí chybějící závislost jedinou konkrétní validační
chybu uvádějící její cestu, nikoli opakované chyby pro každé vstupní rozhraní.
 Příprava Gradle buildů
a zdrojové publikování ponechává původní hranice artefaktů.

Historické Java/Python testy jsou zachované v archivu a tvoří seznam scénářů
k převedení do aktivních testů. Toto opatření samo o sobě neprokazuje jejich
kompletní paritu ani úspěšný Gradle bootstrap.

## Regrese skutečných SDO kontraktů a obou runtimů

`devops/bootstrap-tests/test_canonical_sdo_lifecycle_parity.py` nad skutečnou
`.extgen` generací ověřuje základní životní cyklus typovaného pole:
počáteční `isPresent=false`, `setInputKind(JSONDEFS)`, shodné `getInputKind`,
a následné `unsetInputKind` s návratem na `isPresent=false`. Tentýž scénář
se provádí v Pythonu i v Javě, nikoli jen textovým porovnáním emitovaných
metod. Java část sestavuje aktuální zdrojové SDO třídy pomocí `javac --release 17`
a přebírá externí třídy z classpath (proměnná
`ALGITES_PARITY_JAVA_CLASSPATH`, seznam JAR oddělený dvojtečkami).
Nedostupná Java závislost se nesmí vykazovat jako úspěšná parita.

Celkovou strukturální shodu read-only Defs/SDO hranice ověřuje
`devops/bootstrap-tests/test_contract_architecture_audit.py`; jeho testy
jsou úmyslně striktní i vůči dříve odeslaným `.gen`/`.extgen` zdrojům.
Samotné SDO generování nesmí přidávat nové sémantické pole do
technologicky specifické projekce: při nalezení takového getteru musí být
nejprve opraven neutrální Defs kontrakt, nikoli pouze schována chyba
v generátoru nebo runtime.

The matching Python regression is
`test_sdo_mapped_covariant_inheritance.py`. It generates the same four-level
read-only/mutable contract family, checks inherited `TRuleList` and
`AIiMultiMappedList[TRuleList]`, compiles/imports the generated Python sources,
and verifies that the concrete JSON child returns a stable indexed collection.
The Python generator itself is unchanged: the test protects semantic parity
without requiring Java-style wildcard syntax in Python.

### JSONDEFS and YAMLDEFS schema metadata independence

JSONDEFS and YAMLDEFS schema identifiers, versions, URLs and instance-document
metadata are **format-local**. Even when both describe the same DataObject,
SDO Codegen must not compare their values, require them to match or copy one
format's identity into the other. `AIaDataObjectJsonSchema` / `__json_schema__`
is the new authoritative schema descriptor; it is emitted once. Deprecated
`AIaDataObjectJsonSchema` / `AIaDataObjectYamlSchema` descriptors are retained only as
independent transition-time compatibility descriptors, not as a source of
validation constraints. The standalone Codegen CLI is responsible for
validation and diagnostics; bootstrap only invokes it and must not label those
messages as `Bootstrap Codegen`.


## Input boundary for XML choices and generation timing

Defs may emit auxiliary XML choice/union marker interfaces and variant
records or classes. These are valid read-only representation types, but are
**not independent DataObject contracts**: they do not declare the
schema-neutral `@AIaDataObject` / `__data_object__` descriptor. Java and
Python SDO source discovery must select only the declaring, annotated read-only
DataObject interfaces. Recognizable filenames such as `AIigNameFragmentsSegmentChoice_1`
alone are insufficient. The variants remain available to typed field signatures
and on the compilation/dependency classpath; do not synthesize annotations on
them or relax the check used by explicit `generate()` calls. A descendant of
an annotated schema-neutral DataObject is eligible even if it inherits the
annotation rather than declaring it again. An inherited-only XML/JSON/YAML
projection marker, however, is not a second independent SDO generation input.
During source discovery, naming conventions **never** select DataObject
candidates: only verified type ancestry and `@AIaDataObject` / `__data_object__`
metadata decide eligibility. Naming conventions parse eligible interfaces
only after that verification.

Both native Java/Python SDO CLI entry points print `SDO Codegen START` and
`SDO Codegen END` for the selected artifact and target technology, even when
generation fails after starting. Both records include `artifact`, `technology`,
`at` (ISO-8601 date and time with timezone offset), and `epochMillis`.
The `END` record additionally carries `durationMs` and `durationSec`, measured
monotonically. Logging is generator functionality, not a bootstrap-only step.
