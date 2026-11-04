# Defs Codegen

Defs Codegen je **první, samostatná fáze** generování DataObject: převádí
XMLDEFS, JSONDEFS a YAMLDEFS na anotovaná **read-only** Java/Python rozhraní
(`AIig*`) a enumy (`AIng*`). Nezávislý SDO Codegen z těchto rozhraní vytváří
zapisovatelná rozhraní a implementace. Defs nevolá SDO a SDO nečte schémata.

**[Úplná referenční příručka](DEFS-CODEGEN-REFERENCE.md)** pokrývá architekturu,
starý a nový backend, CLI/settings, naming profily, kanonický model, podporu
XML/JSON/YAML, typy, klíče, dědičnost, parity testy a omezení.

## Aktuální stav (1.1-SNAPSHOT)

Produkční bootstrap stále používá `defs.old`. Nový kanonický Python backend
pracuje s generovanými DataObject/SDO objekty; nový Java backend má funkční
read-only emitter, ale interně stále používá ručně psané kanonické recordy.
Proto **zatím neodstraňovat `.old` ani nepřepínat bootstrap**. Žádné změny
v `src/product/java.gen` / `src/product/python.gen` neprovádět ručně.

Po změně generátoru aktualizovat odpovídající kapitolu v
`DEFS-CODEGEN-REFERENCE.md` místo vytváření dalších stavových Markdown souborů.
