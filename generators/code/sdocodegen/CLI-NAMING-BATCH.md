# SDO Codegen — semantic-role naming CLI (1.1)

The Java and Python SDO CLIs use **kebab-case** options. They generate mutable
`AIigd` and concrete `AIcgd` types from annotated read-only DataObject
contracts. They do not need the original YAML/JSON/XML schema files.

## Named input/output roles

```sh
python -m eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli \
  --repository-root=. \
  --technology-dointf-input-dir:python=src/product/python.gen \
  --technology-sdointf-output-dir:python=src/product/python.gen \
  --technology-sdoimpl-output-dir:python=src/product/python.gen \
  --input-technology-naming-convention:python:yamldefs:defsintf=my-getter \
  --output-technology-naming-convention:python:yamldefs:sdointf=my-mutable \
  --output-technology-naming-convention:python:yamldefs:sdoclass=my-implementation \
  --sdointf-subpackage=impl.intf \
  --sdoclass-subpackage=impl \
  --naming-conventions-file:standard=config/standard.yml \
  --naming-conventions-file:project=config/project.yml
```

Supported roles are `common`, `xmldefs_type`, `xmldefs_element`, `yamldefs`
and `jsondefs`. The technology prefix is `java` or `python`, depending on the
native CLI being invoked. The mapping declares exact naming-convention IDs;
none is inferred from an `AIig` prefix. If a role is omitted, it is not
generated. `AIaDataObject.namingConvention` or Python `naming_convention`
identifies the input convention used for reverse parsing. Semantic roles are
selected from DataObject technology-marker interfaces and XML object metadata,
not guessed from the name.

`--naming-conventions-file:ENTRY_ID=LOCATION` selects catalog entries by stable
configuration keys for overriding/deleting inherited entries. A filesystem
path is resolved relative to the repository; `classpath:NAME` explicitly
loads a catalog packaged in the naming library, independently of checkout paths. The generator imposes no naming-ID
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

The settings loader uses four layers for each native target language: packaged
`algites-sdocodegen-LANGUAGE-default.settings`, optional classpath resource
`algites-sdocodegen-LANGUAGE.settings`, `--settings-file=PATH`, and explicit CLI
options. No layer disables any preceding one. All settings use qualified
`--key:IDENTIFIER=value` entries and merge by the full key before `=`.
An empty value removes an inherited entry; repeatable lists have named entries.
Bare `--check` remains supported, as do `--check=true` and `--check=false`.
Old unqualified command-line mappings remain recognized as compatibility inputs.

`--setter-inheritance-policy` is supported by both SDO native CLIs, with
`INHERIT_AS_GENERIC_PARAMETER` as the packaged default. The setting is used
only for handwritten or generated input contracts whose field and owner
annotations do not supply a concrete policy. `--setter-inheritance-policy`
never overrides explicit field or type metadata.

If a configured source DataObject directory does not exist, SDO generation
reports that fact and skips the absent directory without failing. A dual-target
artifact runs the Java and Python generators independently with their respective
language defaults.

`--check` verifies generated outputs without changes, and `--clean-only`
performs the generator's output cleanup without regenerating. Positional
single-contract CLI entry points have been removed. For an individual contract,
use `--dointf-input-class` (Java) or a source directory and role mapping.

## Portable classpath catalog locations

`--naming-conventions-file:ENTRY_ID=classpath:NAME.yml` selects a naming
catalog from **every** matching Java classloader resource or Python source.
Python searches package resources through `importlib.resources` and also scans
all direct `sys.path` directories. Catalogs are **combined**, not replaced:
each distinct file contributes its naming definitions. Identical shared
identifiers are deduplicated; conflicting definitions of the same naming ID
are rejected by the naming catalog loader rather than silently overridden.
A relative filesystem path without a prefix remains relative to the repository.

Python reads referenced sibling catalogs such as `StandardConventionsFile`
from the same source as the referring YAML file, including ZIP resources.
Java uses each resource's own JAR/directory for referenced sibling catalogs.
Classpath references accept only a simple YAML filename, not path traversal.
The previous `resource:NAME.yml` spelling remains a compatibility alias.
