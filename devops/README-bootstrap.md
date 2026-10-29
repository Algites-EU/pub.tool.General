# Descriptor-driven native bootstrap

The `devops/bootstrap/` scripts are repository-independent. Keep them unchanged
when copying to another Modustro source repository. That repository supplies
its own `modustro-source-repository.yml`, artifact (`modustro-artifact.yml` and
`modustro-artifact-set.yml`) descriptors, and shared `devops/bootstrap/modustro-bootstrap.yml`.

`devops/bootstrap/modustro-bootstrap.yml` contains **only four** shared
infrastructure endpoints: `Publication.Maven`, `Publication.Python`,
`DependencyResolution.RemoteMavenUrl` and
`DependencyResolution.RemotePythonIndexUrl`. The file is identical in both
repositories, and contains no credentials. The two publication targets
specify *where artifacts are uploaded*; the remote URLs identify read-only
Maven and Python package indexes for dependency resolution. Both remote URLs
can be overridden by their respective `MODUSTRO_BOOTSTRAP_REMOTE_*` environment
variables. Current native wheel creation does not run `pip install`, so the
Python URL is exported for consumers requiring Python dependency resolution;
it does not silently modify the user's global pip configuration.

The build directory defaults to `build/run/bootstrap`; Java compilation uses
release 17 and Python distribution metadata requires `>=3.11` by default.
The Java/Python requirements can be overridden with
`MODUSTRO_BOOTSTRAP_JAVA_RELEASE` and `MODUSTRO_BOOTSTRAP_PYTHON_REQUIRES`.
The Python distribution name prefix comes from the first two components of
`GroupId` in `modustro-source-repository.yml` (e.g. `eu.algites` ->
`eu-algites`). External Modustro Maven groups are determined from actual
`DependencyKind: modustro` references, rather than a regex.

The bootstrap no longer pins Jackson or other dependencies through a separate
`JavaPreferred` list: the Gradle build instead uses the version intervals
from each `modustro-artifact.yml`. Gradle's selection within an interval may
change as repositories are updated; reproducibility requires dependency
locking in the future Modustro Builder. No Cloudsmith API keys or personal
filesystem locations belong in this config.

Code generation is a **mandatory bootstrap stage** for every repository. The
common `devops/bootstrap/generate_sources.py` discovers Defs source schemas
(`jsondefs`, `yamldefs`, `xmldefs`) and existing `java.gen` / `python.gen`
output roots under the selected `--root`; if none are applicable, it exits
successfully without loading a generator or producing files. The bootstrap
cleans disposable generated roots first. There is no repository-specific runner
or `CodeGeneration.Runner` configuration.

**Interim naming decision:** the bootstrap always selects the Algites naming
profile for Defs inputs, generated types and methods. The matching Algites
naming catalogs and Codegen dependencies are bootstrap-only `build_source`
prerequisites; they must never leak into the published Codegen product's
runtime/API dependencies. When Modustro supports the `build_source` usage and
explicit generation declarations, this temporary selection can move to those
metadata. The generated-source phase uses an auto-cleaned temporary working
directory and does not leave stale installed Python dependencies behind.

Usage from the repository root:

```bash
MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=remote bash devops/bootstrap/bootstrap.sh --plan-only
MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=remote bash devops/bootstrap/bootstrap.sh --prepare-only
MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=remote bash devops/bootstrap/bootstrap.sh --root generators/code --upload
```

`--plan-only` never generates, builds or uploads. `--prepare-only` regenerates,
compiles, verifies Maven JARs and Python wheel/sdist contents and promotes the
verified local packages without uploading to Cloudsmith. `--upload` is the
default and performs the full process.

The Python and Maven artifacts are selected from source metadata beneath
`--root`; internal dependencies outside that root resolve as published/local
external dependencies rather than silently broadening the build scope.
Current `source` and `local` modes both use the configured Modustro-local
Maven repository for *external* dependencies. Dependencies within the selected
source tree always use the current checkout. `remote` mode uses the Maven URL
from the shared bootstrap configuration. Source dependency preparation of *other*
repositories is a separate concern and is not implemented by this script.

Cloudsmith uploads require the user's `algites-cloudsmith` executable in
`PATH`. The common build invokes:

```bash
algites-cloudsmith --session -- bash devops/bootstrap/upload-cloudsmith.sh \
  OWNER/MAVEN-REPO PATH/TO/MAVEN-PACKAGES.tsv \
  OWNER/PYTHON-REPO PATH/TO/PYTHON-PACKAGES.tsv
```

The wrapper obtains the credential from Secret Service once and exports the
session environment to the batch process. The bootstrap does **not** install
or update the Cloudsmith CLI. The user's `update-cloudsmith` utility remains
independent.

Test the portable bootstrap without publishing:

```bash
python3 -m pytest devops/bootstrap-tests -q
```

## Interim universal source generation (Defs → SDO)

The common bootstrap always runs Defs Codegen, followed by Python SDO Codegen.
Java SDO runs in the common Gradle step `bootstrapSdoJava`, after an initial
`classes` pass (Java SDO needs compiled DataObject contracts) and before the
final Maven publication pass. Generated `AIigd` and `AIcgd` sources remain
inside the owning artifact's `src/product/java.gen` and
`src/product/python.gen`, including handwritten DataObject inputs.

An artifact without applicable schema/DataObject sources is a successful no-op.
The bootstrap selects the Algites naming profile as an interim build-source
convention. The native Codegen products themselves do not acquire a production
dependency on any particular naming profile. Once Modustro supports
`build_source` and explicit code-generation phases, replace this temporary
bootstrap orchestration with artifact-declared dependencies and tool execution.

`--plan-only` does not generate or compile. `--prepare-only` performs both
SDO phases but never uploads to Cloudsmith.
