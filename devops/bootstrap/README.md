# Universal repository bootstrap

This `devops/bootstrap` directory is the common Algites/Modustro bootstrap
implementation. `pub.lib.General` is the baseline to copy into other
repositories; common files should remain byte-identical across repositories.

Invoke `bash devops/bootstrap/bootstrap.sh --prepare-only` to build and verify
without uploading. The normal bootstrap discovers source artifacts from their
`modustro-artifact.yml` descriptors. Its Defs and SDO stages are no-ops when
there is no eligible input. It does not require any code generator to be present
in an ordinary library repository. XML Schema documents containing only
built-in scalar global elements (such as an annotation vocabulary's
``xs:element name="title" type="xs:string"``) do not define a DataObject
TYPE and are excluded from Defs source generation. Named or complex types,
unsupported global constructions and malformed XSDs still reach Defs for
normal validation; no invalid input is silently accepted.

Repository-specific generator bootstrap helpers may be added alongside the
common files, but must not change the common algorithm. For example,
`pub.tool.General` additionally provides `promote-canonical-extgen.py` and
`generate-canonical-contracts.py`. The shared `generate.sh` checks for the
optional provenance validator before running it.

**Self-hosting:** the optional `generate-canonical-contracts.py` uses the
current qualified Defs CLI. The historical `generators/code/bootstrap-selfhosted.sh`
is now only a compatibility alias of the common descriptor-driven bootstrap;
it cannot invoke `defs.old`. Likewise, `generators/code/regenerate_sources.py`
retains its historical clean/list operations but delegates generation to the
same standard Defs/SDO CLI. The `defs.old` source tree is retained only for
historical regression coverage; it is not an executable bootstrap backend.

All temporary configuration files and invocation staging directories belong
under the repository's `build/` tree. Disposable invocation state is removed
after use; build artifacts and diagnostic manifests may remain for inspection. Generated
`src/product/{java,python}.gen` sources are the intentional generator outputs,
not temporary bootstrap state. The `*.extgen` sources in the Defs generator are
an exceptional, committed self-hosting seed. Only configured self-hosting
artifacts copy complete freshly generated `*.gen` sources into `*.extgen` after
successful builds. They can be retired only after the initial compiler build
has another reliable source of the canonical model.

## Výstupní adresáře a bezpečné přegenerování (1.1-SNAPSHOT)

Bootstrap přebírá přepínač
`--cleanup-output-folder-before-generation=true|false` (bez technologického
kvalifikátoru). **Výchozí hodnota je dána jediným souborem
`devops/bootstrap/bootstrap-specializations.yml`** (pokud chybí, `false`).
V `pub.lib.General` je `false`, v `pub.tool.General` je pro self-hosting
`true` a povinná. Při `false`:
Defs/SDO Codegen pouze nahradí soubory, které v aktuálním běhu skutečně
generují. Ostatní soubory v `*.gen` nechají na místě, včetně dřívějších
výstupů již nevybíraných schémat. To funguje i po rozbalení zdrojového
archivu bez `build/` manifestu vlastnictví.

```sh
# Standardní nečisticí režim, bez publikování artefaktů:
bash devops/bootstrap/bootstrap.sh --prepare-only

# Explicitně úplná regenerace vybraného artefaktu:
bash devops/bootstrap/bootstrap.sh --root naming/convention/intf \
  --prepare-only --cleanup-output-folder-before-generation=true

# Pouze plán; nemění vygenerované zdroje ani při cleanup=true:
bash devops/bootstrap/bootstrap.sh --plan-only \
  --cleanup-output-folder-before-generation=true
```

**Pozor na rozdíl mezi CLI a bootstrapem:** samostatné Defs/SDO CLI
při `true` smaže pouze již evidované **zastaralé výstupy svého generátoru**.
Bootstrap při `true` napřed vyprázdní **celé vybrané**
`src/<branch>/{java,python}.gen` stromy, jednou před Defs a SDO generováním.
Soubory uložené ručně v těchto adresářích budou také odstraněny. Proto do
`*.gen` nepatří ručně udržované zdroje. `config.gen` ani `.extgen` se tímto
bootstrap krokem nemažou. Parametr `--root` omezuje zásah na zvolenou větev
repozitáře; bootstrap odmítá symlinkové výstupní kořeny.

Při opakovaném bootstrapu s nastaveným `false` mohou v `python.gen`
současně existovat read-only kontrakty z Defs a zapisovatelná rozhraní či
implementace z předchozího SDO běhu. Python SDO bootstrap předává jako
vstup **jen read-only DataObject kontrakty**. Vlastní SDO výstupy se znovu
nepovažují za vstupy, a to ani při nepřímé dědičnosti a nezávisle na
konfigurovatelných prefixech jejich názvů. Rozlišení používá stabilní
provenienční hlavičky generátoru a explicitní SmartDataObject markery;
připravené vstupy se izolují pod `build/<artifact-path>/sdocodegen/<UUID>/`.

Hodnota je do obou Java/Python Codegenů propagována prostřednictvím
`MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION` a odpovídajícího
CLI parametru. Zadej vždy `true` nebo `false`; neplatná hodnota se odmítne.
Operace `--check` jednotlivých Codegenů je pouze čtecí a nesmí se kombinovat
s `cleanup=true`.

Manifesty (`generated-files.json` pro Python a
`generated-files-java.properties` pro Javu) a zámky/UUID staging vznikají
**jen v `build/<artifact-path>/{defscodegen|sdocodegen}/`**; nejsou
součástí přenosných `.tgz` archivů a nejsou zdrojem pravdy o schématech.
Bez manifestu lze aktualizovat očekávané soubory, ale samostatné CLI nemá
spolehlivý seznam historických výstupů, které by mohlo odstranit.

See `bootstrap.sh`, `build.sh`, and the generator-specific `*-REFERENCE.md`
documents for implementation details.

### Naming SDO bootstrap snapshot (temporary self-hosting)

Only `pub.lib.General/naming/convention/intf` owns this bootstrap workaround.
`promote-naming-extgen.py --refresh` atomically copies the complete, already
**generated** Java/Python Defs+SDO trees to the compiler `*.extgen` source
snapshots, without writing any persistent manifest. `--check` validates both
language trees directly (roles, required common names, and absence of
obsolete technology-specific projections). It does not manufacture Java SDO sources and refuses missing
interfaces or implementations. Never edit generated source trees by hand.

The source-dependency first-stage naming ABI requires that complete seed;
it cannot silently fall back to a broken Defs-only ABI. Bootstrap source
selection treats the naming ABI seed and real Defs/SDO output as mutually
exclusive roots in both languages. The first compiler
pass (`MODUSTRO_BOOTSTRAP_SDO_ABI_SEED=1`) compiles/packages only `*.extgen`;
a later pass with complete generated SDO sources uses only `*.gen`. When full
SDO output is missing, the compiler seed remains available. Python wheel/sdist
staging follows the same rule and never merges conflicting versions of a
naming module from `python.extgen` and `python.gen`. The Java SDO phase takes
**fresh read-only contracts from `src/product/java.gen` as source inputs** and
compiles them in memory via the existing SDO CLI.
The Gradle launcher passes only materialized classpath entries to Java SDO:
its `-cp` and `--sdo-dependency-paths:java` lists are derived from the same
existing files. A not-yet-created Gradle output directory (for example an
optional `build/resources/main`) is not a compiler dependency. A missing JAR
is an error rather than a silently skipped required artifact. The SDO CLI
independently validates explicitly provided dependency paths once before
processing input contracts and reports the missing path, not one repeated
source-tree error for every DataObject.
 Although Gradle may still
use `java.extgen` to compile temporary ABI dependencies at that point, the
seed classes are only classpath dependencies, never independently scanned SDO
inputs. The final Gradle publish recompiles the finished `java.gen` including
SDO-generated mutable interfaces and concrete classes. Unrelated duplicate
product resources are still rejected. Other modules keep their ordinary source
roots. After a successful non-seed naming build the seed is refreshed.
This is intentionally bootstrap-only, pending the general builder.

**Initial creation of Java naming SDO sources still requires a compatible Java
SDO CLI and its external libraries.** If the bootstrap is attempted before
that initial snapshot has been produced, the `--check` stage fails clearly.

### Generator self-hosting and schema closure (shared engine)

The same scripts and bootstrap commands are used by both repositories. The
optional `devops/bootstrap/bootstrap-specializations.yml` is the **only
repository-specific bootstrap policy**: it contains the naming and generator
ABI seed snapshot phases, the source-compiler dependency cycle, generated
source selection, and the default cleanup/freshness settings. An ordinary
repository may omit this file. A self-hosting source compiler is selected by
`CliArtifactId`, `SeedArtifactIds`, `TriggerArtifactIds` and
`RebuildAfterCliArtifactIds`; no naming/SDO artifact IDs are embedded in the
universal `source-dependencies.py`.

`pub.tool.General` declares the Defs canonical-model seed at
`generators/code/defscodegen/intf`. The optional configured
`promote-canonical-extgen.py --prune-seed` keeps the minimal compiler ABI before
generation; after a successful complete bootstrap, `--refresh` atomically
replaces its committed Java/Python `*.extgen` trees with verified fresh `*.gen`
outputs. Partial-root bootstrap does not refresh this complete seed.

A bootstrap invocation pre-resolves schema identities from the selected
`--root` artifacts and their transitive Modustro product and schema-only
development dependencies. Each `src/product/{xmldefs,jsondefs,yamldefs}` schema
uses its publication `.meta.yml` identity. The resulting
`build/run/schema-locations/<UUID>.properties` maps each public schema URL to
its local absolute filename and is passed as
`--schema-locations-property-file` to Defs Codegen. Missing declarations are
errors rather than silently downloading different remote content. A
`develop_implementation` dependency used only to locate an XSD annotation
vocabulary does not become an unrelated Python runtime dependency.

For documentation labels, XMLDEFS uses the imported `algdoc:title` vocabulary
from `documentation/intf`; JSONDEFS and YAMLDEFS already have the standardized
JSON Schema `title` and `description` keywords and need no analogous external
documentation schemas. The XML Schema built-in `xs:documentation` supplies its
standard description.

`--upload-prepared` is separate from normal `--upload`: it skips generation
and building, verifies the complete prepared Maven snapshot and newest
matching Python wheel and sdist for the selected root before uploading, and
then uses the existing Cloudsmith publication adapter.
