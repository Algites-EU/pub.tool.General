# Source-mode dependency bootstrap

The temporary bootstrap in `devops/bootstrap` is identical across Modustro
source repositories. The eventual Modustro Builder will replace this logic.

Set `MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source` to resolve each **product**
`DependencyKind: modustro` from a source checkout. The resolver indexes
`modustro-artifact.yml` files under the selected repository and its sibling
checkouts; it verifies artifact identifiers, `GroupId`, versions and dependency
cycles. It compiles prerequisite artifacts in topological order using the same
repository bootstrap and stages the verified Maven/Python products locally.
Only the originally selected `--root` is eligible for final Cloudsmith upload.

Typical local workflow (with `pub.lib.General` and `pub.tool.General` as
siblings):

```bash
cd pub.tool.General
MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source \
  bash devops/bootstrap/bootstrap.sh --root generators/code --plan-only
MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source \
  bash devops/bootstrap/bootstrap.sh --root generators/code --prepare-only

cd ../pub.lib.General
MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source \
  bash devops/bootstrap/bootstrap.sh --root naming/convention --prepare-only
```

`--plan-only` reports dependency order and never compiles or removes generated
sources. `--prepare-only` verifies and publishes prerequisites to the local
Modustro Maven and Python stores, but does not upload to Cloudsmith.

If repositories are not siblings, define
`MODUSTRO_BOOTSTRAP_SOURCE_REPOSITORIES` as a colon-separated list of checkout
roots, or use the existing explicit source-location environment variables.
The resolver identifies checkouts from `SourceRepository.Id`, not directory
names. Duplicate IDs, missing artifacts, wrong versions and dependency cycles
are fatal. **There is no remote or cached-binary fallback for Modustro source
dependencies.** Gradle is also restricted to the local Maven repository for
Modustro groups found in the source graph, including transitive groups.
External, non-Modustro dependencies continue to follow the normal Gradle
repository policy.

Source-mode Gradle dependency refresh is enabled by default because source
snapshots reuse their `1.1-SNAPSHOT` coordinates. You may explicitly set
`MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES=0` when working offline with known
fresh external caches, but doing so reduces protection against stale metadata.

Limitations of this temporary solution:
- Each prerequisite is bootstrapped separately. A future Builder may instead
  create a single composite build for more efficient execution.
- The resolver targets Java/Python product dependencies. Build-source Python
  generators are still discovered by the existing `generate_sources.py` logic.
- External Java libraries, e.g. Jackson, still require the usual Maven cache
  or repository access.
- No Cloudsmith upload occurs when `--prepare-only` is selected.
