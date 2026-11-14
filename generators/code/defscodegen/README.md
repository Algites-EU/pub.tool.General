# Defs Codegen

Defs Codegen je **první, samostatná fáze** generování DataObject: převádí
XMLDEFS, JSONDEFS a YAMLDEFS na anotovaná **read-only** Java/Python rozhraní
(`AIig*`) a enumy (`AIng*`). Nezávislý SDO Codegen z těchto rozhraní vytváří
zapisovatelná rozhraní a implementace. Defs nevolá SDO a SDO nečte schémata.

**[Úplná referenční příručka](DEFS-CODEGEN-REFERENCE.md)** pokrývá architekturu,
starý a nový backend, CLI/settings, naming profily, kanonický model, podporu
XML/JSON/YAML, typy, klíče, dědičnost, parity testy a omezení.

## Aktuální stav (1.1-SNAPSHOT)

Bootstrap je přesměrován na nové Python kanonické Defs CLI a aktuální SDO CLI,
ale úplný bootstrap **zatím neprochází**, protože kanonický frontend nepodporuje
část konstrukcí skutečných schémat (`const`, `minProperties`/`maxProperties`,
některé `xs:choice`, XPath a omezení indexovaných map). `.old` zůstává
nedotčený kvůli historickým testům. Nový Java backend má rovněž nativní
CLI `AIcDefsCodegenCanonicalCli` se stejnými standardními
`--defs-input-*`, `--defs-dependency-*`, pojmenovacími a výstupními
parametry jako Python. Interní manifesty nejsou součástí veřejného CLI. Jeho kanonická pipeline nyní používá generované SDO typy
z `java.extgen` namísto ručně udržovaných Java modelových DTO; indexované
JSONDEFS/YAMLDEFS mapy s homogenními `properties` zpracovávají oba jazyky
shodně. Cílené Java i Python testy prošly, ale úplný Gradle bootstrap
ani Java CLI v celé produktové závislostní sadě dosud ověřeny nejsou.
Java adaptér generovaného kanonického SDO používá nové pojmenované `TypeContent`,
neměnné `CHOICE` varianty, gettery `*List` a číselné hodnoty `Long`.
Povinné SDO seznamy se inicializují kompletní typovanou hodnotou, aby
neporušily validační omezení při přechodném prázdném stavu.
Žádné změny v `src/product/java.gen` / `src/product/python.gen`
neprovádět ručně; `*.extgen` se regenerují skriptem a verzují v Gitu.

Po změně generátoru aktualizovat odpovídající kapitolu v
`DEFS-CODEGEN-REFERENCE.md` místo vytváření dalších stavových Markdown souborů.

## Přegenerování výstupů

V Javě i Pythonu je `--cleanup-output-folder-before-generation=false`
výchozí nastavení. Přepíší se jen aktuálně generované soubory a ostatní
soubory ve sdílených `*.gen` zůstanou beze změny; manifest pod `build/`
není pro tento režim vyžadován. Samostatné CLI s `true` odstraní jen
zastaralé výstupy tohoto Codegenu evidované v manifestu. Univerzální
bootstrap s `true` naproti tomu vyprázdní celé vybrané `java.gen`/`python.gen`
před oběma generátory. Podrobnosti a omezení jsou v referenční příručce.

Typové pravidlo: veřejné gettery musí být konkrétně typované; neznámé
`ANY` nesmí být při renderingu automaticky převedeno na `Object`/`Any`.
Při rozdílných sémantických signaturách XML/JSON/YAML hlásí současný
Codegen konkrétní nekompatibilitu namísto tichého zahození getteru.
Podrobnosti a známé strukturální rozdíly jsou v `DEFS-CODEGEN-REFERENCE.md`.


### Explicit untyped schema content (1.1-SNAPSHOT)

`additionalProperties: true` / `{}` does not generate `Object` or
`Map<String,Object>` getters. The frontend emits a source-located warning and
suggests a typed `additionalProperties` value schema; omitted
`additionalProperties` remains silent. Keyed homogeneous JSON/YAML arrays
(`x-algites-defscodegen-key` on `type: array`) now use actual typed item fields,
while keyed object maps retain synthetic property-name keys. XML wildcard
`xs:any`/`xs:anyAttribute` uses source-located warnings with a named typed
XML declaration hint when optional; mandatory `xs:any` remains an error.
See DEFS-CODEGEN-REFERENCE.md and the JSONDEFS vocabulary_1.md.
