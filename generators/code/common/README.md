# Shared code-generation naming configuration

The `GeneratedDataObjectMethodNameConventions.NameConventions` profiles are
shared by Defs and SDO Codegen and refer to existing `NameCompositions`.
`SourceStructureNameConventions.NameConventions` continues to describe source
structure/file profiles; the two families use disjoint profile namespaces.

The generated methods use only the configured compositions; technical `_`
prefixes are part of the default compositions, not hard-coded by Codegen.

### XML Schema parity for naming profiles

The `src/product/xmldefs` tree also publishes XSD definitions for
`generated-dataobject-method-kind_1` and `data-object-naming-conventions_1`.
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
