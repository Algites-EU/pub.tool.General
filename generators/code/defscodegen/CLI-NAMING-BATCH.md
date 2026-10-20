# Defs Codegen — semantic-role naming CLI (1.1)

The Java and Python native CLIs accept the same **kebab-case** batch options.
Without arguments, the Java CLI loads `algites-defscodegen-java-default.settings`
and the Python CLI loads `algites-defscodegen-python-default.settings` from
the repository checkout or the packaged generator resources. A custom file is
selected with `--settings-file=PATH`; further CLI mappings override settings
mappings for the same technology/role.

## Input and output mapping

```sh
python -m eu.algites.tool.codegen.defs.impl.cli.aic_defs_codegen_cli \
  --repository-root=. \
  --schema-input-dir=jsondefs:src/product/jsondefs \
  --input-schema-naming-convention=jsondefs:my-schema-naming \
  --technology-dointf-output-dir=python:src/product/python.gen \
  --output-interface-technology-naming-convention=python:jsondefs:defsintf=my-contract-naming \
  --output-enum-technology-naming-convention=python:my-enum-naming \
  --naming-conventions-file=config/standard.yml \
  --naming-conventions-file=config/project.yml
```

`--schema-input-dir` accepts `xmldefs`, `yamldefs` and `jsondefs` input roots.
`--input-schema-naming-convention=KIND:ID` chooses the profile for an input
schema kind. `--output-interface-technology-naming-convention=TECH:ROLE:defsintf=ID`
chooses a generated getter-interface profile for each target technology
(`java`, `python`) and semantic role (`common`, `xmldefs_type`,
`xmldefs_element`, `yamldefs`, `jsondefs`). `--output-enum-technology-naming-convention=TECH:ID`
configures enums independently.

`--naming-conventions-file` is repeatable and provides **one combined catalog**.
It accepts filesystem paths and packaged `resource:NAME` entries. Each ID is
looked up in that catalog. File locations and naming IDs are independent.
Conflicting definitions of one ID are rejected; identical repeated definitions
can be merged. No generator requires a particular syntax for user-defined IDs;
Algites chooses `_1` in its supplied catalog as a library-versioning policy.

**A missing output-role naming ID means that role is not generated.** If two
configured roles would create the same relative output path, generation must
fail instead of overwriting a different contract. The input-schema ID and
required dependency roles still have to resolve. If a common getter and a
technology-specific getter are both enabled, the latter can extend the common
contract and its technology marker interface.

Outputs embed the exact selected naming ID in `@AIaDataObject.namingConvention()`
(Java) or `AIcdDataObject.naming_convention` (Python). The generated sources
remain owned by the generator; their directory trees must not be manually
patched. Generated-file ownership state protects unrelated files during
regeneration and `--clean-only`. `--check` compares without writing.

## Defaults

`generators/code/defscodegen/intf/src/product/config/eu/algites/tool/codegen/defs/`
contains **two distinct settings files**: `algites-defscodegen-java-default.settings`
and `algites-defscodegen-python-default.settings`. Each enables only the matching
target technology, while reading the same schema kinds. It references packaged
naming catalogs (`resource:...`) rather than a neighboring library checkout.
Invoking either native CLI with no parameters uses its own technology defaults; explicitly
supplying options without `--settings-file` uses only the supplied options.

Positional legacy CLI invocations are not accepted. Use explicit role mappings
or `--settings-file`; programmatic generation uses the corresponding service API.
