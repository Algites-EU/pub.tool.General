# SDO Codegen

SDO Codegen je **samostatný** generátor zapisovatelných SmartDataObject
rozhraní (`AIigd*`) a implementací (`AIcgd*`) pro Java/Python. Přijímá
anotované read-only DataObject kontrakty, nikoli XMLDEFS, JSONDEFS,
YAMLDEFS nebo interní model Defs Codegenu.

**[Úplná referenční příručka](SDO-CODEGEN-REFERENCE.md)** popisuje CLI,
katalogy Common/SDO, vrstvení settings, vstupní artefakty, typové API,
dědičnost, mapy, XML, serializaci, omezení a testy obou jazyků.

**Stav:** podporována nezávislá Java/Python CLI a Python Defs → SDO integrační
průchody; plný Java Gradle a úplná aplikační parita ještě nebyly ověřeny.
Bootstrap používá aktuální Java/Python CLI; historické `sdo.old` je uchováno pod `legacy-archive/`. Aktualizace funkčnosti patří do
`SDO-CODEGEN-REFERENCE.md`, nikoli do nových statusových souborů.

## Přegenerování výstupů

V Javě i Pythonu je `--cleanup-output-folder-before-generation=false`
výchozí nastavení. Přepíší se jen aktuálně generované soubory a ostatní
soubory ve sdílených `*.gen` zůstanou beze změny; manifest pod `build/`
není pro tento režim vyžadován. Samostatné CLI s `true` odstraní jen
zastaralé výstupy tohoto Codegenu evidované v manifestu. Univerzální
bootstrap s `true` naproti tomu vyprázdní celé vybrané `java.gen`/`python.gen`
před oběma generátory. Podrobnosti a omezení jsou v referenční příručce.
