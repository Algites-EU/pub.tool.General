#!/usr/bin/env bash
# Relocate historical tests that explicitly import Defs Codegen old or old XML runtime.
# Execute in a Git checkout of pub.tool.General; keep the original source histories.
set -euo pipefail
cd "$(dirname "$0")/../../../.."
for name in test_generated_xml_typed_deserialization.py test_sdo_named_mapped_collection.py; do
  git mv "generators/code/sdocodegen/impl/src/develop/python/$name" \
      "generators/code/sdocodegen/legacy-archive/impl/src/develop/python/$name"
done
