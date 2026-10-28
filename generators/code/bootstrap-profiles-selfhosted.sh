#!/usr/bin/env bash
set -euo pipefail

# Standalone profile-only bootstrap. The actual Defs and SDO generator code is
# neither rebuilt nor published. Naming catalogs are external Maven/Python deps.
locCode="$(cd "$(dirname "$0")" && pwd -P)"
locRepo="$(cd "$locCode/../.." && pwd -P)"
locMode="${1:---upload}"
case "$locMode" in --plan-only|--prepare-only|--upload) ;; --help|-h)
    echo 'Usage: bash generators/code/bootstrap-profiles.sh [--plan-only|--prepare-only|--upload]'
    exit 0 ;;
    *) echo "Unknown action: $locMode" >&2; exit 2;; esac
[[ "$#" -le 1 ]] || { echo 'Only one action is accepted' >&2; exit 2; }
locVersion="${MODUSTRO_CODEGEN_BOOTSTRAP_VERSION:-1.1-SNAPSHOT}"
locPython="${ALGITES_PYTHON_EXECUTABLE:-python3}"
locWork="$locRepo/build/run/codegen-profile-bootstrap"
locDependencyMode="${MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE:-remote}"
case "$locDependencyMode" in remote|local|source) ;; *) echo "Invalid dependency mode: $locDependencyMode" >&2; exit 2 ;; esac
locJavaRepo="${MODUSTRO_CODEGEN_BOOTSTRAP_CLOUDSMITH_REPO:-algites/java-snapshots-pub}"
locPythonRepo="${MODUSTRO_CODEGEN_BOOTSTRAP_PYTHON_CLOUDSMITH_REPO:-algites/python-snapshots-pub}"
# Strictly validate ALL profiles, technology kinds and the four settings each.
"$locPython" - "$locCode" <<'PY'
from pathlib import Path
import sys, yaml
root=Path(sys.argv[1])/'profile'
for profile in ('algites','standardprefix','standardpostfix'):
    module=root/profile
    description=yaml.safe_load((module/'modustro-artifact.yml').read_text())
    if set(description['Artifact']['TechnologyKinds']) != {'java','python'}:
        raise SystemExit(f'{profile} does not support BOTH native technology kinds')
    for language in ('java','python'):
        catalog=(module/'src/product/config/eu/algites/lib/naming/convention'/
                 f'{profile}-{language}-codegen-method-conventions.yml')
        data=yaml.safe_load(catalog.read_text())
        if not data['GeneratedDataObjectMethodNameConventions']['NameConventions']:
            raise SystemExit(f'Empty naming catalog: {catalog}')
        for generator,pkg in [('defscodegen','defs'),('sdocodegen','sdo')]:
            path=module/'src/product/config/eu/algites/tool/codegen'/pkg/f'{generator}-{language}.settings'
            if not path.is_file():
                raise SystemExit(f'Missing profile settings: {path}')
            if '--naming-conventions-file:' not in path.read_text():
                raise SystemExit(f'No naming resources configured by {path}')
print('Validated all three generator profiles for java and python')
PY
if [[ "$locMode" == --plan-only ]]; then
    echo 'Plan: publish ONLY profile.algites, profile.standardprefix and profile.standardpostfix (Maven + Python).'
    echo 'Requires the corresponding pub.lib.General naming profiles published beforehand.'
    exit 0
fi
mkdir -p "$locRepo/build/run"
rm -rf -- "$locWork"
mkdir -p "$locWork/gradle"
cat > "$locWork/gradle/settings.gradle" <<'GRADLE_SETTINGS'
rootProject.name = 'algites-codegen-profile-bootstrap'
['algites','standardprefix','standardpostfix'].each { profile ->
    include ':' + profile
    project(':' + profile).projectDir = new File(System.getenv('MODUSTRO_PROFILE_CODE_ROOT'), 'profile/' + profile)
}
GRADLE_SETTINGS
cat > "$locWork/gradle/build.gradle" <<'GRADLE_BUILD'
subprojects {
    apply plugin: 'java-library'
    apply plugin: 'maven-publish'
    group = 'eu.algites.tool.codegen'
    version = System.getenv('MODUSTRO_PROFILE_BUILD_VERSION') ?: '1.1-SNAPSHOT'
    def buildRoot = new File(System.getenv('MODUSTRO_PROFILE_BUILD_ROOT'), 'gradle-output')
    layout.buildDirectory.set(new File(buildRoot, project.name))
    repositories {
        def mode = System.getenv('MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE') ?: 'remote'
        if (mode != 'remote') maven { name = 'modustro-local'; url = uri(System.getenv('MODUSTRO_LOCAL_MAVEN_REPOSITORY') ?: new File(System.getenv('MODUSTRO_HOME') ?: new File(System.getProperty('user.home'), '.modustro').path, 'artifact-repos/java/maven')) }
        if (mode == 'remote') maven {
            url = uri('https://dl.cloudsmith.io/public/algites/java-snapshots-pub/maven/')
            content { includeGroupByRegex('eu\\.algites\\..*') }
        }
        mavenCentral()

    }
    java { withSourcesJar() }
    sourceSets.main.resources.srcDirs = ['src/product/config', 'src/product/resources']
    dependencies {
        api 'eu.algites.lib.naming:pub.lib.General_naming.convention.' +
                project.name + ':' + version
    }
    publishing {
        repositories { maven { name = 'Bootstrap'; url = uri(new File(System.getenv('MODUSTRO_PROFILE_BUILD_ROOT'), 'maven-repository')) } }
        publications {
            mavenJava(MavenPublication) {
                from components.java
                artifactId = 'pub.tool.General_generators.code.profile.' + project.name
            }
        }
    }
}
GRADLE_BUILD
locGradle=(bash "$locRepo/gradlew")
if [[ -n "${MODUSTRO_GRADLE_EXECUTABLE:-}" ]]; then locGradle=("$MODUSTRO_GRADLE_EXECUTABLE"); fi
locGradleArgs=(--no-daemon --project-dir "$locWork/gradle")
if [[ "${MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES:-$([[ "$locDependencyMode" == remote ]] && echo 1 || echo 0)}" == 1 ]]; then
    locGradleArgs+=(--refresh-dependencies)
fi
MODUSTRO_PROFILE_CODE_ROOT="$locCode" \
MODUSTRO_PROFILE_BUILD_ROOT="$locWork" \
MODUSTRO_PROFILE_BUILD_VERSION="$locVersion" \
MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE="$locDependencyMode" \
    "${locGradle[@]}" "${locGradleArgs[@]}" publishAllPublicationsToBootstrapRepository
locMaven="$locWork/maven-repository"
printf '' > "$locWork/coordinates.tsv"
for profile in algites standardprefix standardpostfix; do
    printf '%s\t%s\t%s\n' 'eu.algites.tool.codegen' \
        "pub.tool.General_generators.code.profile.$profile" "$locVersion" >> "$locWork/coordinates.tsv"
done
"$locPython" "$locRepo/devtools/bootstrap-maven-stage.py" collect \
    --staging "$locMaven" --coordinates "$locWork/coordinates.tsv" --output "$locWork/staged-publications.json"
locBuildPython="${MODUSTRO_BOOTSTRAP_PYTHON_BUILD_EXECUTABLE:-}"
if [[ -z "$locBuildPython" ]]; then
    locVenv="$locWork/python-build-venv"
    "$locPython" -m venv "$locVenv"
    locBuildPython="$locVenv/bin/python"
    "$locBuildPython" -m pip install --disable-pip-version-check 'build>=1,<2' 'setuptools>=69' 'wheel>=0.43' 'pyyaml>=6,<7'
fi
locArgs=(--repository "$locRepo" --maven-version "$locVersion" --only-profiles
         --output "$locWork/python-dist" --manifest "$locWork/python-packages.tsv")
if [[ -n "${MODUSTRO_CODEGEN_BOOTSTRAP_PYTHON_VERSION:-}" ]]; then
    locArgs+=(--python-version "$MODUSTRO_CODEGEN_BOOTSTRAP_PYTHON_VERSION")
fi
"$locBuildPython" "$locCode/bootstrap-python-dist.py" "${locArgs[@]}"
"$locPython" "$locRepo/devtools/bootstrap-maven-stage.py" promote \
    --manifest "$locWork/staged-publications.json" --output "$locWork/packages.tsv"
"$locPython" "$locRepo/devtools/bootstrap-maven-stage.py" verify-gradle \
    --manifest "$locWork/packages.tsv" --gradle "${MODUSTRO_GRADLE_EXECUTABLE:-$locRepo/gradlew}" \
    --work "$locWork/local-gradle-verification"
locLocalPythonRepo="${MODUSTRO_LOCAL_PYTHON_REPOSITORY:-${MODUSTRO_HOME:-$HOME/.modustro}/artifact-repos/python}"
"$locPython" "$locRepo/devtools/modustro-local-python-repo.py" publish --manifest "$locWork/python-packages.tsv" --repository "$locLocalPythonRepo"
locJavaCount="$(wc -l < "$locWork/packages.tsv")"
locPythonCount="$(wc -l < "$locWork/python-packages.tsv")"
echo "Prepared $locJavaCount Maven generator profiles and $locPythonCount Python generator profiles (wheel + sdist): $locWork"
if [[ "$locMode" == --prepare-only || "${MODUSTRO_BOOTSTRAP_PREPARE_ONLY:-0}" == 1 ]]; then exit 0; fi
command -v algites-cloudsmith >/dev/null || { echo 'algites-cloudsmith is required to upload' >&2; exit 2; }
algites-cloudsmith --session -- bash -c '
    set -euo pipefail
    while IFS=$'"'"'\t'"'"' read -r jar pom module sources; do
        args=(--pom-file "$pom" --extra-files "$module")
        [[ -s "$sources" ]] && args+=(--sources-file "$sources")
        cloudsmith push maven "$1" "$jar" "${args[@]}"
    done < "$2"
    while IFS=$'"'"'\t'"'"' read -r wheel sdist; do
        cloudsmith push python "$3" "$wheel"
        cloudsmith push python "$3" "$sdist"
    done < "$4"
' _ "$locJavaRepo" "$locWork/packages.tsv" "$locPythonRepo" "$locWork/python-packages.tsv"
