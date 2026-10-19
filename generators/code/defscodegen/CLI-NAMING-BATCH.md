# Defs Codegen — YAML naming catalog batch CLI

The native Java and Python CLIs accept their existing single-definition positional syntax, plus the new explicit batch syntax:

```sh
defs-codegen \
  --schema-input-dir=yamldefs:src/product/yamldefs \
  --schema-input-dir=jsondefs:src/product/jsondefs \
  --schema-input-dir=xmldefs:src/product/xmldefs \
  --schema-input-naming-profile=yamldefs:config/algites-yamldef-name-conventions.yml \
  --schema-input-naming-profile=jsondefs:config/algites-jsondef-name-conventions.yml \
  --schema-input-naming-profile=xmldefs:config/algites-xmldef-name-conventions.yml \
  --technology-dointf-output-dir=java:src/product/java.gen \
  --technology-dointf-output-dir=python:src/product/python.gen \
  --technology-dointf-output-naming-profile=java:config/algites-java-name-conventions.yml \
  --technology-dointf-output-naming-profile=python:config/algites-python-name-conventions.yml
```

Add `--repository-root=<root>` when paths are relative to another source-repository root. Multiple input roots of the same schema kind are permitted. The output must have exactly one directory and catalog for each selected technology. `--check` verifies outputs without writing. `--clean-only` requires only output root/catalog pairs and removes only recognized generated `dointf` and enum source files. Standard generation validates all input definitions, canonical identities, inherited references and target collisions **before** cleaning the owned output files. Therefore invalid input or a semantic collision leaves prior outputs intact; disk I/O failures during writing are not transactional. `--allow-unversioned-schemas` permits the unversioned schema naming profiles; otherwise the versioned profile is required when input catalogs are provided.

The current repository generation engine still reuses its established canonical-schema readers, equivalence merger, reference resolution, and direct contract renderer. Output type and file prefixes are taken from YAML via the transitional adapter. Java and Python implementations are native, independent. The adaptor currently assumes versioned standard Algites compositions and simple identifiers; arbitrary custom version-variable remapping in the rendering backend remains future work.

Full reference: [Code Generators Reference Guide](../CODEGEN-REFERENCE.md), particularly sections 2.3–2.5.

## XML element naming and choice compilation units

The 1.1 XML element role uses the `_xe` marker in Java types, and the additional underscore in Python file names (`aiig__xe_payment_1.py`). Both CLI and repository batch generation must emit all closed-choice wrapper compilation units. See [RECURSIVE-TYPES-AND-XML-ELEMENTS.md](RECURSIVE-TYPES-AND-XML-ELEMENTS.md).
