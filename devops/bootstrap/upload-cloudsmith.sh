#!/usr/bin/env bash
set -euo pipefail

# Shared uploader. Invoke only through algites-cloudsmith --session -- so the
# Secret Service credential is resolved once for both publication ecosystems.
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
[[ -s "$locMavenManifest" && -s "$locPythonManifest" ]] || {
    echo 'Both verified publication manifests must exist and be nonempty' >&2; exit 2;
}
command -v algites-cloudsmith >/dev/null || {
    echo 'algites-cloudsmith is required for upload' >&2; exit 2;
}

locMavenCount=0
while IFS=$'\t' read -r locJar locPom locModule locSources; do
    [[ -n "$locJar" && -n "$locPom" && -n "$locModule" && -n "$locSources" ]] || {
        echo 'Malformed Maven manifest record' >&2; exit 2;
    }
    [[ -s "$locJar" && -s "$locPom" && -s "$locModule" && -s "$locSources" ]] || {
        echo "Missing Maven publication file: $locJar" >&2; exit 2;
    }
    algites-cloudsmith push maven "$locMavenTarget" "$locJar" \
        --pom-file "$locPom" --extra-files "$locModule" --sources-file "$locSources"
    (( locMavenCount += 1 ))
done < "$locMavenManifest"

locPythonCount=0
while IFS=$'\t' read -r locWheel locSdist; do
    [[ -n "$locWheel" && -n "$locSdist" && -s "$locWheel" && -s "$locSdist" ]] || {
        echo "Missing or malformed Python publication: $locWheel" >&2; exit 2;
    }
    algites-cloudsmith push python "$locPythonTarget" "$locWheel"
    algites-cloudsmith push python "$locPythonTarget" "$locSdist"
    (( locPythonCount += 1 ))
done < "$locPythonManifest"
printf 'Cloudsmith publications uploaded: %s Maven artifacts, %s Python distributions\n' \
    "$locMavenCount" "$locPythonCount"
