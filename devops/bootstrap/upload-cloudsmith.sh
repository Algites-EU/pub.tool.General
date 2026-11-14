#!/usr/bin/env bash
set -euo pipefail

# One authenticated upload of already built artifacts. Both technology manifests
# are validated *in full* before the first push; a root may select only Java or
# only Python products. Empty manifests indicate that technology is absent.
[[ "${ALGITES_CLOUDSMITH_SESSION:-}" == 1 ]] || {
    echo 'Run the uploader through algites-cloudsmith --session --' >&2; exit 2;
}
[[ $# == 4 ]] || {
    echo 'Usage: upload-cloudsmith.sh MAVEN_TARGET MAVEN_MANIFEST PYTHON_TARGET PYTHON_MANIFEST' >&2
    exit 2
}
locMavenTarget="$1"
locMavenManifest="$2"
locPythonTarget="$3"
locPythonManifest="$4"
[[ -f "$locMavenManifest" && -f "$locPythonManifest" ]] || {
    echo 'Both publication manifest files must exist (empty allowed for unused technology)' >&2; exit 2;
}
command -v algites-cloudsmith >/dev/null || {
    echo 'algites-cloudsmith is required for upload' >&2; exit 2;
}

locMavenCount=0
while IFS=$'\t' read -r locJar locPom locModule locSources locExtra; do
    [[ -z "$locJar$locPom$locModule$locSources$locExtra" ]] && continue
    [[ -z "$locExtra" && -n "$locJar" && -n "$locPom" && -n "$locModule" && -n "$locSources" ]] || {
        echo 'Malformed Maven manifest record' >&2; exit 2;
    }
    [[ "$locJar" == *.jar && "$locPom" == *.pom && "$locModule" == *.module && "$locSources" == *-sources.jar ]] || {
        echo "Unexpected Maven filename(s): $locJar" >&2; exit 2;
    }
    [[ -s "$locJar" && -s "$locPom" && -s "$locModule" && -s "$locSources" ]] || {
        echo "Missing Maven publication file: $locJar" >&2; exit 2;
    }
    (( locMavenCount += 1 ))
done < "$locMavenManifest"
locPythonCount=0
while IFS=$'\t' read -r locWheel locSdist locExtra; do
    [[ -z "$locWheel$locSdist$locExtra" ]] && continue
    [[ -z "$locExtra" && "$locWheel" == *.whl && "$locSdist" == *.tar.gz ]] || {
        echo "Malformed Python manifest record: $locWheel" >&2; exit 2;
    }
    [[ -s "$locWheel" && -s "$locSdist" ]] || {
        echo "Missing Python publication file: $locWheel" >&2; exit 2;
    }
    (( locPythonCount += 1 ))
done < "$locPythonManifest"
(( locMavenCount + locPythonCount > 0 )) || {
    echo 'Cannot upload empty publication set' >&2; exit 2;
}

while IFS=$'\t' read -r locJar locPom locModule locSources; do
    [[ -z "$locJar$locPom$locModule$locSources" ]] && continue
    algites-cloudsmith push maven "$locMavenTarget" "$locJar" \
        --pom-file "$locPom" --extra-files "$locModule" --sources-file "$locSources"
done < "$locMavenManifest"
while IFS=$'\t' read -r locWheel locSdist; do
    [[ -z "$locWheel$locSdist" ]] && continue
    algites-cloudsmith push python "$locPythonTarget" "$locWheel"
    algites-cloudsmith push python "$locPythonTarget" "$locSdist"
done < "$locPythonManifest"
printf 'Cloudsmith publications uploaded: %s Maven artifacts, %s Python distributions\n' \
    "$locMavenCount" "$locPythonCount"
