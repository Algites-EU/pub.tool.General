# Modustro migration and generator fixes

Repository descriptors use the current modustro-* names. Settings bootstrap the
compiled Gradleinit plugin; source generation and dependencies are declared in
the descriptors instead of duplicated module Gradle scripts.

YAML and JSON canonical definitions are compared structurally, then their
documentation and origins are merged. Local references, composition and Python
wire-name mapping are covered by regressions. XML definitions use a separate
xmldefs namespace where their contracts differ.

Bootstrap/publish the updated Defs Codegen before the updated Gradleinit plugin,
then activate the governance scripts. Both standalone bootstrap scripts and
artifact coordinates are documented in their repository READMEs. Remote
publication has not been performed.

Validation: 147 Java tests and 4 Python tests passed locally across the three
repositories. Packaging phases passed; external Cloudsmith access returned HTTP
403 during a repeated preflight, so final Python dependency checks use locally
built wheels. This does not establish remote GitHub Actions success.

## Removed repository-relative paths

Descriptor files in this list were renamed to modustro-*; module build scripts
were replaced by descriptor declarations; obsolete resolver scripts were removed.

```text
algites-source-repository.yml
generators/algites-artifact-set.yml
generators/code/algites-artifact-set.yml
generators/code/defscodegen/algites-artifact-set.yml
generators/code/defscodegen/cli/algites-artifact.yml
generators/code/defscodegen/coreimpl/algites-artifact.yml
generators/code/defscodegen/coreintf/algites-artifact.yml
naming/algites-artifact-set.yml
naming/validator/algites-artifact-set.yml
naming/validator/cli/algites-artifact.yml
```
