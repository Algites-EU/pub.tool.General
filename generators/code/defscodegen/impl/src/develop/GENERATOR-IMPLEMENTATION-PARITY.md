# Defs Codegen: Java / Python implementation parity

The Java and Python Defs Codegen implementations must implement **the same
canonical pipeline**. Their differences should be implementation-language
syntax and unavoidable runtime concerns, never alternative rules for schema
identity, source-name parsing, or emitted Java/Python declarations.

## Runtime architecture

1. Read the explicitly selected input naming catalog and profile.
2. Parse the schema filename using `file_name_stem` and `file_name_suffix`.
   Do not guess the version from underscores or other delimiters.
3. Validate globally named XSD types and named `$defs` entries with the same
   `type_name` rule. Convert a declared type's *local* name with the naming
   catalog. Keep source identity (XML QName or JSON URI + JSON Pointer) separate
   from that local name.
4. Build the canonical, format-neutral definition and resolve references.
5. Generate the requested Java **and** Python sources via each native generator;
   check the complete file set and exact lexical content apart from whitespace.

`AIcDeclaredTypeIdentity.java` and `aic_declared_type_identity.py` implement
stage 3 with the same validation and round-trip checks. The JVM schema reader
and repository binding generator both use the Java helper for named `$defs`;
the XML frontend uses it for global XSD types.

## Mandatory parity tests

`AItcGeneratorImplementationParityTest.java` is a TestNG test under the usual
`src/develop/java` source set. It launches the artifact-local Python
`generator_implementation_parity.py` suite and feeds it the JVM test classpath
and JVM-generated fixtures. Consequently **the normal Gradle Java test task**
executes both native implementations and fails if they disagree. No separate
parity script or bootstrap action is needed.

- Each native generator independently runs the *same* declarative repository
  manifest with both `java` and `python` outputs enabled.
- Generated manifest results and every generated path must match. It is not
  sufficient for a single target language, one file, or an empty result to pass.
- Java and Python contents are token-compared, preserving syntax, declarations,
  string literals, comments, indentation structure, and statement boundaries.
  Whitespace-only differences are tolerated.
- `--check` mode is exercised for both generators; an intentionally deleted
  generated file must make both checkers fail.
- A second layer independently generates 30 first-stage fixtures: three schema
  formats, two target languages, five source schemata. These include real
  examples of nested types, scalars, enum values, collections, restrictions and
  cross-schema references.
- The two parity-specific XSD fixtures `parity-supported` and
  `parity-supported-builtins` avoid explicit `xs:anyType` / `xs:anySimpleType`,
  which the frontend intentionally rejects; existing unsupported-type tests and
  original parity examples remain intact.
- `AItcDeclaredTypeIdentityTest.java` and the existing Python named-type tests
  also verify canonical source-name mapping and rejection of malformed names.

On a properly configured Modustro/Gradle build, `check` is expected to run the
normal Java and Python verification tasks. JVM parity tests require the resolved
`MODUSTRO_ARTIFACT_DIRECTORY`, `MODUSTRO_PYTHON_TEST_EXECUTABLE`, and
`MODUSTRO_PYTHON_TEST_PATH` values supplied by the Gradle test configuration.
Missing inputs fail the test rather than silently disabling parity.

## Still requiring a full installed-dependency run

Parity of the complete repository generator cannot be certified until the
Gradle TestNG integration executes with all JVM dependencies. In particular,
compare keyed common interfaces, specialized XML projections, synthetic
namespace contracts, and generated import resolution. Keep deviations visible
in the comparison; do not make the normalizers semantically permissive.
