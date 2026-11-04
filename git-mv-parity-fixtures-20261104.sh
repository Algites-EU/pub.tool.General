#!/usr/bin/env bash
# Run from the root of pub.tool.General BEFORE applying the updated source archive.
# This preserves the Git history of the six moved develop-only fixture schemas.
set -euo pipefail
if [[ ! -d .git ]] || [[ ! -f generators/code/defscodegen/impl/modustro-artifact.yml ]]; then
  echo 'Run this script in the pub.tool.General Git repository root.' >&2
  exit 2
fi
base=generators/code/defscodegen/impl/src/develop
for stem in parity-builtins parity-root; do
  for kind in jsondefs yamldefs xmldefs; do
    case "$kind" in
      jsondefs) suffix=jsondef.schema.json ;;
      yamldefs) suffix=yamldef.schema.json ;;
      xmldefs) suffix=xsd ;;
    esac
    old="$base/$kind/${stem}_1.$suffix"
    new="$base/examples/$stem/$kind/${stem}_1.$suffix"
    if [[ -f "$old" && ! -e "$new" ]]; then
      mkdir -p "$(dirname "$new")"
      git mv -- "$old" "$new"
      echo "moved $old -> $new"
    elif [[ ! -e "$old" && -f "$new" ]]; then
      echo "already moved: $new"
    else
      echo "Ambiguous state (or missing fixture): $old / $new" >&2
      exit 3
    fi
  done
done
