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
`devops/bootstrap` se zatím nemění. Aktualizace funkčnosti patří do
`SDO-CODEGEN-REFERENCE.md`, nikoli do nových statusových souborů.
