# Building and Processing 25 — conventions, metadata, and optional SDO accessors

Date: 2026-10-26 (Europe/Prague)

## Implemented

- Generated DataObject/SDO method roles are `standard_getter`, `standard_setter`, `raw_getter`, `raw_presence_checker_method`, and `raw_unsetter` (the obsolete trailing `_name` is removed from role keys).
- The Java and Python codegen method catalogs declare all six source/data schema metadata names. Defaults: `$id`, `$x-algites-schema-id`, `$x-algites-schema-version` for schema-source; `$schema`, empty, empty for data-source. The literal `$` prefixes on Algites extension fields are intentional.
- The source naming catalogs and method naming catalogs validate that no enabled data-source mapping lacks its corresponding schema-source mapping. Empty or missing optional raw roles omit generated declarations and implementations of those accessors.
- Defs contract generators and SmartDataObject renderers respect optional source annotations and independent optional instance-document header fields; the output method profile can disable metadata independently of the input profile. A declared `schemaId` must not be synthesized from `$id`.
- XMLDEFS remains separate from JSON/YAML wire-header conventions; selecting a generated method profile does not require XML schemas to contain JSON header fields.
- Data/setting YAML root declarations migrated from `$schema` to `$schema`. `# yaml-language-server: $schema=...` is intentionally unchanged; JSON Schema's root `$schema` dialect declaration also remains unchanged.
- `generated-dataobject-method-kind_1` and `data-object-naming-conventions_1` are retained: the first is the enumerated role vocabulary referenced by the second, which defines an entire method-naming configuration document. Removing either would break the cross-schema reference.

## Verification in this environment

- 240 Defs Codegen Python tests passed in independently run batches (116 + 55 + 69), before the XML-specific adjustment; 5 focused metadata integration tests passed after that adjustment, including a newly introduced XMLDEFS regression. Therefore there are 241 distinct passing Defs tests across those runs.
- 96 Python tests for `pub.lib.General` passed after the final changes.
- 38 SDO Codegen tests and 29 common-codegen naming/schema tests passed in the latest fast suite (98 tests when including 31 library naming tests already counted in the 96).
- Combined count of distinct successful Python tests: 241 + 96 + 38 + 29 = 404; these were run in separately scoped invocations, not as one Gradle pipeline.
- Java Compiler API parsed 457 non-generated Java source units successfully with Java 21: zero syntax errors. This is a syntax check, **not type-checking or classpath-aware compilation**.
- Parsed 109 YAML documents, 35 JSON Schema files, and 17 XSDs successfully (excluding generated directories). Both default method catalogs also passed six-field checks.

## Explicit limitations and required follow-up on the target build host

- Full Gradle/Java/TestNG bootstrap was **not** executed. The required Gradle 9.2.1 distribution is unavailable in this isolated environment. Compilation/linking and end-to-end Java integration must be verified using the actual Gradle bootstrap in a normal network/build environment.
- Existing `src/product/java.gen` and `src/product/python.gen` content is retained unchanged. It must be recreated by the project's normal clean/regeneration pipeline before building; never manually patch generated files.
- The XML naming schema retains its extensible `xs:any` profile container (XSD 1.0 cannot impose named fields on arbitrarily named map entries). The field constraints and optional metadata pairing are enforced by JSONDEFS/YAMLDEFS schemas and the Java/Python catalog runtime; XSD documentation describes these rules.
- Do not treat this archive as a fully Gradle-verified release until Java compilation, bootstrap and regeneration pass on the build host.
