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

**Stav:** cílené Python Defs → SDO JSON/YAML/XML integrační testy prošly,
Java read-only vstupní kontrakty lze sestavit s `javac`; plný Java
Gradle/TestNG a úplné round-trip scénáře ještě nebyly dokončeny. Produkční
bootstrap dosud používá historickou implementaci `.old`.

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


## Native CLI: vstupy, role, settings a ověřování

The Java and Python SDO CLIs use **kebab-case** options. They generate mutable
`AIigd` and concrete `AIcgd` types from annotated read-only DataObject
contracts. They do not need the original YAML/JSON/XML schema files.

### Named input/output roles

```sh
python -m eu.algites.tool.codegen.sdo.old.impl.cli.aic_sdo_codegen_cli \
  --repository-root=. \
  --technology-dointf-input-dir:python=src/product/python.gen \
  --technology-sdointf-output-dir:python=src/product/python.gen \
  --technology-sdoimpl-output-dir:python=src/product/python.gen \
  --input-technology-naming-convention:python:yamldefs:defsintf=my-getter \
  --output-technology-naming-convention:python:yamldefs:sdointf=my-mutable \
  --output-technology-naming-convention:python:yamldefs:sdoclass=my-implementation \
  --sdointf-subpackage=impl.intf \
  --sdoclass-subpackage=impl \
  --naming-conventions-file:standard=config/standard.yml \
  --naming-conventions-file:project=config/project.yml
```

Supported roles are `common`, `xmldefs_type`, `xmldefs_element`, `yamldefs`
and `jsondefs`. The technology prefix is `java` or `python`, depending on the
native CLI being invoked. The mapping declares exact naming-convention IDs;
none is inferred from an `AIig` prefix. If a role is omitted, it is not
generated. `AIaDataObject.namingConvention` or Python `naming_convention`
identifies the input convention used for reverse parsing. Semantic roles are
selected from DataObject technology-marker interfaces and XML object metadata,
not guessed from the name.

`--naming-conventions-file:ENTRY_ID=LOCATION` selects catalog entries by stable
configuration keys for overriding/deleting inherited entries. A filesystem
path is resolved relative to the repository; `classpath:NAME` explicitly
loads a catalog packaged in the naming library, independently of checkout paths. The generator imposes no naming-ID
version suffix policy. In Algites defaults the IDs end in `_1`.

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

### Explicit Java and Python inputs

Both native CLIs accept `--dointf-input-artifacts:TECH=LIST`,
`--dointf-input-classes:TECH=LIST` and `--dointf-input-paths:TECH=LIST`.
Items in a list are separated by semicolons. The explicit class selector is
`fully.qualified.JavaClass` in Java and `importable.module:PythonClass` in
Python. Java artifacts are JARs or directories of `.class` files; Python
artifacts are distributions with importable source contracts. The supporting
`--dointf-classpath:TECH=PATHS` affects loading and is never scanned as an
additional set of contracts. See
[CODEGEN-ARTIFACT-INPUTS.md](../CODEGEN-ARTIFACT-INPUTS.md) for complete
selector grammar and source-mode behavior.

Both native CLIs also accept a source root via
`--technology-dointf-input-dir:TECH=PATH`. Handwritten DataObject contracts
are supported without a generated filename prefix when they have the
appropriate type metadata.

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
profile IDs select one family; an ambiguous selection fails with a diagnostic. All settings use qualified
`--key:IDENTIFIER=value` entries and merge by the full key before `=`.
An empty value removes an inherited entry; repeatable lists have named entries.
Bare `--check` remains supported, as do `--check=true` and `--check=false`.
Old unqualified command-line mappings remain recognized as compatibility inputs.

`--setter-inheritance-policy` is supported by both SDO native CLIs, with
`INHERIT_AS_GENERIC_PARAMETER` as the packaged default. The setting is used
only for handwritten or generated input contracts whose field and owner
annotations do not supply a concrete policy. `--setter-inheritance-policy`
never overrides explicit field or type metadata.

If a configured source DataObject directory does not exist, SDO generation
reports that fact and skips the absent directory without failing. A dual-target
artifact runs the Java and Python generators independently with their respective
language defaults.

`--check` verifies generated outputs without changes, and `--clean-only`
performs the generator's output cleanup without regenerating. Positional
single-contract CLI entry points have been removed. For an individual contract,
use `--dointf-input-class` (Java) or a source directory and role mapping.

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
    --dointf-input-artifacts:java=eu.example:read-contracts:1.1-SNAPSHOT \
    --dointf-classpath:java=build/libs/dependencies
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
Java invariant generic collections (`List<AIig*>`, etc.) retain their original
type to avoid an invalid covariant override; this narrowing applies to **direct**
nested object fields. Types from handwritten read contracts are supported.

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
default values are expressed separately through `AIaFieldDefault` and its
factory-based resolver. XML-specific QNames belong to `AIaXmlDataObject` and
`AIaXmlDataObjectField` and are copied to the mutable contract. Inherited
fields may be restricted, but the implementation rejects relaxation of
required/forbidden presence or nullability. XML element contracts use the
specialized `_xe` naming profiles for Java and Python (`__xe_` for Python
source files). Java closed-choice records remain in the Defs Codegen sealing
module; SDO does not relocate them. The generated mutable interface inherits
from `AIiXmlSmartDataObject`, `AIiJsonSmartDataObject`, or
`AIiYamlSmartDataObject`, and the corresponding concrete implementation
inherits from the technology-specific `AIc*SmartDataObject` implementation
base. These base classes may be behaviorally empty but establish the final
extension hierarchy. Remaining limitations are documented in
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
