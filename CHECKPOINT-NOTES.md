# Defs Codegen Java XML contract test updates

Created: 2026-10-21 14:45:36 CEST
Baseline: `pub.tool.General-schema-field-constant-naming-20261021.tgz`

## Changes

- Updated `AItcSchemaContractGenerationTest.java` to expect three XML generated contracts per language (content type, global element, and XML namespace interface); the test now checks the emitted `@namespace/urn:example:xml:1` manifest record, XML namespace URI, marker superinterface, and name under the default `xmldefs_namespace` naming profile.
- Updated Java getter assertions from the obsolete `name()` / `count()` format to the active `getter_method_name` output `getName()` / `getCount()`. The inheritance regression also checks that the child does not redeclare the inherited `getName()` getter.
- No product code, naming catalogs, CLI configuration, or generated source directories were changed.

## Verification

- 22 Python parity/XML namespace tests passed.
- Generated the same XSD shape as the failing Java manifest test using the equivalent Python generator: verified all six manifest entries, namespace contracts for Java and Python, and Java getter names.
- Java TestNG/Gradle suite NOT verified in this environment: Gradle 9.2.1 is absent and the Gradle wrapper cannot download it (`UnknownHostException: services.gradle.org`). Run `:impl:test` in the existing Defs Codegen bootstrap build to confirm.

## File delta relative to baseline

Changed (2, including checkpoint notes):
- `generators/code/defscodegen/impl/src/develop/java/eu/algites/tool/codegen/defs/impl/standard/AItcSchemaContractGenerationTest.java`
- `CHECKPOINT-NOTES.md`

Added (0): none.
Removed (0): none.

---

# Schema-field constant naming convention fix

Created: 2026-10-21 12:46:32 CEST
Baseline: modustro-three-repositories-getter-setter-naming-final-20261021.zip

## Changes

- Removed the domain-specific `SCHEMA_FIELD_NAME__` literal from the generic `constant-name_1` composition in both Java and Python naming catalogs (`pub.lib.General`). The composition now contains only one identifier segment formatted with `upper_snake_case_1`.
- Defs Codegen now constructs the schema-field semantic designation from the `schema`, `field`, `name` words and renders it through `constant_name`, just like the actual source field identifier (`pub.tool.General`, Java and Python).
- The two rendered portions are joined with an **empty middle component**. The default output remains `SCHEMA_FIELD_NAME__OPTIONAL_TEXT`, preserving the double underscore and existing API compatibility.
- A custom `upper_camel_case_1` constant formatter produces `SchemaFieldName__OptionalText`; the generator does not force uppercase output spelling.
- Added regressions for the generic catalog and custom naming in both Java and Python test sources.
- `pub.gov.Algites` is unchanged. No source files in `java.gen` or `python.gen` were edited.

## Verification

- 23 naming catalog Python tests PASSED.
- 26 schema-parity and schema-object-bindings Python tests PASSED.
- 27 Defs, XML namespace and wildcard Python tests PASSED.
- 15 definition-format and lineage Python tests PASSED.
- **91 Python tests PASSED in total, no failures**, across the listed individual invocations.
- Java `AIcGenerationNames.java` and required Java interfaces compiled with `javac` 21 using minimal external-dependency stubs; a Java execution check verified default and custom naming outputs.
- Complete Gradle/Java TestNG build was not run in this container (Gradle 9.2.1 unavailable); do not interpret the Java smoke check as a full build.

## File delta relative to baseline

Changed (7):
- `pub.lib.General/naming/convention/profile/algites/src/develop/python/test_name_convention_catalog_1.py`
- `pub.lib.General/naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/algites-java-name-conventions.yml`
- `pub.lib.General/naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/algites-python-name-conventions.yml`
- `pub.tool.General/generators/code/defscodegen/impl/src/develop/java/eu/algites/tool/codegen/defs/impl/standard/AItcSchemaParityTest.java`
- `pub.tool.General/generators/code/defscodegen/impl/src/develop/python/test_schema_parity.py`
- `pub.tool.General/generators/code/defscodegen/impl/src/product/java/eu/algites/tool/codegen/defs/impl/standard/AIcGenerationNames.java`
- `pub.tool.General/generators/code/defscodegen/impl/src/product/python/eu/algites/tool/codegen/defs/impl/standard/aic_generation_names.py`

Added (0):
- None

Removed (0):
- None
