# Codegen qualified artifact inputs — implementation checkpoint

Date: 2026-11-01. Baselines: pub.tool.General r10 and pub.lib.General r11.

## Implemented

- Removed legacy `qualifier:value` translation in Java and Python layered settings.
- All native CLIs consume complete qualified keys directly.
- Added common Python/Java artifact resolver under `generators/code/common`,
  which both Codegen CLI modules depend upon.
- Added `--defs-input-artifacts:java` and `:python`, source schema extraction from
  selected JARs and wheels, and preservation of explicit schema directory roots.
- Added `--dointf-input-artifacts:java` and `:python`, plus
  `--dointf-input-classes:java` and `:python`; Python accepts importable
  `module:Class` selectors and loads wheel input contracts.
- Added `--dointf-input-paths:java` and `:python` and technology-qualified
  supporting `--dointf-classpath`.
- New artifact selectors accept Maven GAV, Python requirements (without
  environment markers), and portable Modustro ID@version. Lists are separated
  by semicolons and replace earlier lists under the same qualified key.
- Source bootstrap propagates an allowlist of prepared source dependencies and
  rejects input artifact selectors that would implicitly use an undeclared
  internal binary dependency. No source-build reuse optimization was added.
- Updated common bootstrap scripts in both repositories identically.
- Added regression tests and user-facing CLI reference document.

## Verified

- Python CLI/configuration, explicit Python class selection, selected wheel
  generation, and resolver tests pass (targeted suites).
- Java common artifact resolver and both Java settings modules compile on JDK 21.
- Both modified Java CLI sources compile against isolated Java type stubs;
  the exercise verifies Java syntax/type signatures in the changed CLI code
  but not compatibility with every actual dependency.
- Independent Java settings and resolver regression methods passed.
- Python syntax and Bash bootstrap syntax checks passed.
- The shared bootstrap files match byte-for-byte between repositories.

## Not verified / known restrictions

- Full Gradle/Java TestNG builds were **not** run: Gradle 9.2.1 is unavailable
  locally and the wrapper cannot resolve services.gradle.org to download it.
- Some broad legacy Python test suites fail on missing packaged naming resource
  fixtures or tests that assume an unrelated profile layout; separate focused
  regression suites pass. Do not claim complete regression success.
- A selected artifact must actually contain source schemas (Defs) or importable
  DataObject contracts (SDO). Artifact identity alone cannot reconstruct inputs.
- Resolvers are intentionally local-only. Source mode requires build-time
  dependencies declared in Modustro descriptors; selectors do not download or
  build undeclared source artifacts by themselves.
- Inline PEP 508 environment markers, extras, and URLs are not accepted.
- The existing artifact tree has not been physically reorganized into distinct
  `defsintf` and `sdo` artifacts; the new selectors enable doing that separately.

See `generators/code/CODEGEN-ARTIFACT-INPUTS.md` for the CLI contract and examples.
