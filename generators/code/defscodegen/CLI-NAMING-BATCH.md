# Defs Codegen — semantic-role naming CLI (1.1)

The Java and Python native CLIs accept the same **kebab-case** batch options.
Both native CLIs always resolve layered settings: a packaged language-specific
`defscodegen-LANGUAGE-default.settings`, then an optional classpath
`defscodegen-LANGUAGE.settings`, then `--settings-file=PATH`, then
explicit CLI arguments. Complete qualified setting keys are overlaid as a
stable ordered map. An empty assignment removes the inherited entry.

## Input and output mapping

```sh
python -m eu.algites.tool.codegen.defs.impl.cli.aic_defs_codegen_cli \
  --repository-root=. \
  --schema-input-dir:jsondefs=src/product/jsondefs \
  --input-schema-naming-convention:jsondefs=my-schema-naming \
  --technology-dointf-output-dir:python=src/product/python.gen \
  --output-interface-technology-naming-convention:python:jsondefs:defsintf=my-contract-naming \
  --output-enum-technology-naming-convention:python=my-enum-naming \
  --naming-conventions-file:standard=config/standard.yml \
  --naming-conventions-file:project=config/project.yml
```

`--schema-input-dir:KIND=PATH` accepts `xmldefs`, `yamldefs` and `jsondefs`
input roots. A configured input directory which does not exist is reported
informationally and skipped; the other existing roots are still processed.
If all roots are absent, generation is a non-destructive no-op.
`--input-schema-naming-convention:KIND=ID` chooses the profile for an input
schema kind. `--output-interface-technology-naming-convention:TECH:ROLE:defsintf=ID`
chooses a generated getter-interface profile for each target technology
(`java`, `python`) and semantic role (`common`, `xmldefs_type`,
`xmldefs_element`, `xmldefs_namespace`, `yamldefs`, `jsondefs`). `--output-enum-technology-naming-convention:TECH=ID`
configures enums independently.

`--naming-conventions-file:ENTRY_ID=LOCATION` adds one identifiable entry to the
combined catalog. `ENTRY_ID` is a stable configuration-entry key; settings
layers can override or remove a catalog by this key. `LOCATION` is either a
filesystem path or `classpath:NAME` for a packaged naming catalog. The
`classpath:` prefix is used to distinguish classpath/package resources
from paths relative to the target repository. Each ID is
looked up in that catalog. File locations and naming IDs are independent.
Conflicting definitions of one ID are rejected; identical repeated definitions
can be merged. No generator requires a particular syntax for user-defined IDs;
Algites chooses `_1` in its supplied catalog as a library-versioning policy.

**A missing output-role naming ID means that a contract family is not generated.**
The `xmldefs_namespace` role is different: it configures the names of auxiliary
XML namespace interfaces, which are emitted when XML contracts need them,
not as a separate contract family. When XML namespace support is requested, the active profile must explicitly
provide the corresponding naming role; no Algites naming convention is selected
implicitly. Namespace type names and file stems are rendered through that
selected profile;
no `_xe`/`_x` text replacement is performed. If two
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

## Layered settings

The four precedence levels are: packaged `defscodegen-java-default.settings`
(or Python), optional `defscodegen-java.settings` (or Python) on the
all classpath matches, `--settings-file`, and direct CLI parameters. Settings are merged
using the **entire key before `=`**, including qualifiers separated by `:`.
The higher layer wins; `--key=` removes an inherited entry. Repeatable options
such as `--naming-conventions-file:standard=...` have individually named keys.
Boolean options accept `--check=true` / `--check=false` (bare `--check` is
accepted as `true`). Legacy `--schema-input-dir=KIND:PATH` and other prior
command-line mappings remain accepted for existing callers and are normalized
before layering; use qualified keys in new settings and build scripts.

The neutral generator defaults do not select naming catalogs. The external
codegen profile supplies the `classpath:...` resources and semantic roles. The
setting `--setter-inheritance-policy=INHERIT_AS_GENERIC_PARAMETER` may be
changed by any higher layer to `INHERIT_AS_FIXED_PARAMETER`; there are no
separate `.properties` defaults. It is emitted into the generated read-only
contract's field and type metadata. Explicit model metadata still wins.
Native Java/Python SDO generation also requires an explicitly selected naming
profile, including for handwritten contracts without annotations.

Positional legacy CLI invocations are not accepted. Programmatic calls use
the service API and require explicit naming information; only the configured setter-inheritance
policy has its documented generic-parameter default.

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
