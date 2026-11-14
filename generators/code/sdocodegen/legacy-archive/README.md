# Historický SDO Codegen – zachovaný zdrojový archiv

`ALGITES-LEGACY-SDO-INCOMPATIBLE`

Tento adresář zachovává původní implementace `sdo.old`, CLI, konfigurace
a historické testovací scénáře v nezměněném obsahu původních souborů.
Byly přesunuty mimo aktivní `src/product` a `src/develop` produkčních
artefaktů, protože používají odstraněné metody anotací (`schemaId`,
`namingConvention`, `fingerprint`, `minOccurs` apod.). Samotné přidání
`abstract` nebo `@Deprecated` by je nevyloučilo z kompilace.

Produkční bootstrap spouští `eu.algites.tool.codegen.sdo.impl.cli.AIcSdoCodegenCli`
a používá standardní `--sdo-input-paths`/`--sdo-dependency-paths`.

Historické testovací scénáře zůstávají zde pro postupné převedení do aktivních
Java a Python sad; při převodu zachovat funkční ekvivalenci a pokrytí obou jazyků.
Přemístění není důkazem této parity ani úspěšného celého bootstrapu.

## Rozbalování checkpointů přes stávající checkout

Při pouhém rozbalení `.tgz` přes existující strom se staré soubory
na původních cestách samy neodstraní. Bootstrapový Gradle `sourceSets`
a Python staging proto vylučují i případné takto pozůstalé `sdo.old`.
Pro jejich fyzické odstranění je nutná samostatná migrace pracovního stromu.
