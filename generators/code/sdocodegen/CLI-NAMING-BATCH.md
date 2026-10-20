# SDO Codegen — semantic-role naming CLI (1.1)

The Java and Python SDO CLIs use **kebab-case** options. They generate mutable
`AIigd` and concrete `AIcgd` types from annotated read-only DataObject
contracts. They do not need the original YAML/JSON/XML schema files.

## Named input/output roles

```sh
python -m eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli \
  --repository-root=. \
  --technology-dointf-input-dir=python:src/product/python.gen \
  --technology-sdointf-output-dir=python:src/product/python.gen \
  --technology-sdoimpl-output-dir=python:src/product/python.gen \
  --input-technology-naming-convention=python:yamldefs:defsintf=my-getter \
  --output-technology-naming-convention=python:yamldefs:sdointf=my-mutable,sdoclass=my-implementation \
  --sdointf-subpackage=impl.intf \
  --sdoclass-subpackage=impl \
  --naming-conventions-file=config/standard.yml \
  --naming-conventions-file=config/project.yml
```

Supported roles are `common`, `xmldefs_type`, `xmldefs_element`, `yamldefs`
and `jsondefs`. The technology prefix is `java` or `python`, depending on the
native CLI being invoked. The mapping declares exact naming-convention IDs;
none is inferred from an `AIig` prefix. If a role is omitted, it is not
generated. `AIaDataObject.namingConvention` or Python `naming_convention`
identifies the input convention used for reverse parsing. Semantic roles are
selected from DataObject technology-marker interfaces and XML object metadata,
not guessed from the name.

`--naming-conventions-file` can repeat and loads one catalog from filesystem
and/or packaged `resource:NAME` inputs. The generator imposes no naming-ID
version suffix policy. In Algites defaults the IDs end in `_1`.

## Java binary inputs

The Java CLI also accepts repeatable selectors:

- `--dointf-input-class=fully.qualified.Contract` for one compiled class;
- `--dointf-input-artifact=PATH` for all eligible DataObject contracts in a
  JAR or directory containing `.class` files;
- `--dointf-classpath=PATHS` for supporting binary dependencies, separated
  with the operating-system path separator.

The last option is **dependency classpath only**, not a selector. Module JARs
can be inspected as classpath entries for generation, bypassing JPMS module
encapsulation at build time. Resulting generated packages must still be
compatible with actual named JPMS modules at runtime.

Both native CLIs also accept input source roots (`--technology-dointf-input-dir`).
Handwritten DataObject types with explicit metadata are valid inputs even
when their class and filename do not follow the standard Algites names.

## Output packages, settings, and verification

`--sdointf-subpackage` and `--sdoclass-subpackage` independently append a
validated suffix to the input type's package. Leaving either unspecified
preserves the original package. For separate Java named modules use distinct
packages, not a common suffix. The stock Algites settings select `impl.intf`
and `impl` respectively.

With no arguments the CLI loads
`generators/code/sdocodegen/intf/src/product/config/eu/algites/tool/codegen/sdo/`
from the checkout or packaged resources. The Java CLI selects
`algites-sdocodegen-java-default.settings`, while the Python CLI selects
`algites-sdocodegen-python-default.settings`. `--settings-file=PATH` chooses a
custom file; further CLI mappings override its values for corresponding
technology/role keys. Each settings file enables all five semantic role families for **one** target
technology only. A dual-technology artifact runs both native generators
independently, each with its corresponding settings file. A custom settings
file may still target one or both languages explicitly.

`--check` verifies generated outputs without changes, and `--clean-only`
performs the generator's output cleanup without regenerating. Positional single-contract CLI entry points have been removed. For an individual
contract, use `--dointf-input-class` (Java) or a source directory and role mapping.
