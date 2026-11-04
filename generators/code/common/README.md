# Shared code-generation naming configuration

For 1.1-SNAPSHOT the generated DataObject naming settings are divided into
three domains, rather than one combined Defs/SDO profile:

* `codegen_common`: common source naming (`standard_getter`, etc.) used by
  both Defs and SDO and maintained independently of any specific generator.
* `codegen_defs`: settings specific to Defs read-only contract generation.
* `codegen_sdo`: settings specific to SDO writable interface and concrete
  implementation generation, including raw method names and synthetic
  JSON/YAML map-entry accessors.

Defs selects `--naming-conventions-file:codegen_common` and
`--naming-conventions-file:codegen_defs` with corresponding
`--common-codegen-naming-convention:<technology>` and
`--defs-codegen-naming-convention:<technology>` IDs. SDO selects the Common
and `codegen_sdo` catalogs with `--common-codegen-naming-convention` and
`--sdo-codegen-naming-convention` IDs. The generator-specific profile must
reference the selected Common profile by `CommonNamingConvention`.

All composed names use the existing `NameCompositions` catalog. Technical
`_` prefixes, when wanted, belong to the chosen composition and are not
injected by the code generators. `SourceStructureNameConventions` remains a
distinct concern for naming source structures and files.

### XML Schema parity for naming profiles

The `src/product/xmldefs` tree also publishes XSD definitions for
`generated-dataobject-structure-kind_1` and `data-object-naming-conventions_1`.
The latter imports `pub.lib.General`'s shared
`common-naming-conventions_1.xsd` as its common XSD base. Publication metadata
(`.xsd.meta.yml`) is supplied for both definitions. The corresponding JSON/YAML
schema definitions remain the authoritative mapping representation for dynamic
profile-name keys; the XSD uses `xs:anyType` for those extensible maps.

The standalone generator bootstrap publishes this shared module as
`pub.tool.General_generators.code.common` for Java and as
`eu-algites-pub-tool-general-generators-code-common` for Python. Both
codegen implementations depend on the shared artifact. Python catalogs are
shipped under the `eu.algites.lib.naming.convention` namespace and resolved
via `importlib.resources`, without depending on source-checkout paths.
