# SDO Codegen

`pub.tool.General:1.1-SNAPSHOT` contains a second, **schema-independent** generator.
It accepts annotated `AIig*` read contracts through either a class object or
its generated source file. It never reads YAML, JSON Schema, XSD or the
canonical-definition model. For Java, source-based generation uses the JDK
compiler **in memory** and inspects the compiled interfaces through ordinary
reflection; it does not require a separate Java compile task. Python imports
fresh source modules and reflects over the annotated types.

The `intf` artifact exposes the generation API, `impl` generates mutable contracts
(`AIigd*`, or a different configured marker) and concrete implementations
(`AIcgd*`), and `cli` is the adapter used by build orchestration.

The CLI now uses **semantic-role options** and named settings, rather than
positional class/output arguments. With no arguments it reads the packaged
`sdocodegen-java-default.settings` or
`sdocodegen-python-default.settings`, selected by native CLI.

Java (processing a binary JAR):

```sh
java -cp "$CLASSPATH" eu.algites.tool.codegen.sdo.impl.cli.AIcSdoCodegenCli \
    --settings-file=config/my-sdocodegen.settings \
    --dointf-input-artifact=build/libs/my-read-contracts.jar \
    --dointf-classpath=build/libs/dependencies
```

Python (using the native source loader):

```sh
python -m eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli \
    --settings-file=config/my-sdocodegen.settings
```

The settings file defines independent technology-role mappings, input source
roots and output roots; see [CLI-NAMING-BATCH.md](CLI-NAMING-BATCH.md).
Both CLIs support `--check` for non-mutating verification. Java dependencies
of source contracts must be visible on the process classpath or via
`--dointf-classpath`; Python modules must be importable from the configured
source root. Handwritten contracts are supported without schema generation.

Inheritance is preserved in both the mutable interface and the concrete class.
Inherited fields are implemented by the generated base class, and declared
fields by the child. Conflicting inherited metadata fails explicitly.

Nested direct `AIig*` value getters are overridden covariantly in the generated
`AIigd*` interface and are paired with an `AIigd*`-typed setter and raw getter.
The concrete `AIcgd*` class implements the same typed signatures and continues
to use the normal `get_EffectiveField`, `get_RawField`, and `set_RawField`
mechanisms; it does not wrap or convert the nested object. Python also preserves
explicit nullable nested return types (`AIig* | None` -> `AIigd* | None`).
Java invariant generic collections (`List<AIig*>`, etc.) retain their original
type to avoid an invalid covariant override; this narrowing applies to **direct**
nested object fields. Types from handwritten read contracts are supported.

### XML QName deserialization in generated implementations

For XML contracts, both native generators now emit a class-level convenience
parser: `AIcgd*.fromXml(String)` on Java and `AIcgd*.from_xml(str)` on Python.
The entry point delegates to the namespace-aware, order-tolerant parser in
`pub.lib.General` checkpoint 19. Java maps nested `AIig*` getter return types
(including `List<? extends AIig*>`) to generated `AIcgd*` classes using an
explicit field-name/class mapping. Python emits `__xml_repeated_fields__` on
mutable contracts, resolves fields from reflected getter and source-property
annotations, and stores lazy module-qualified nested implementation bindings
on concrete classes. Lazy resolution prevents import cycles between generated
SDO types and supports inherited bindings. Both generators preserve the original
expanded XML QName metadata; they do not infer XML namespaces from Python
attribute names or Java getters.

The generated `fromXml`/`from_xml` methods parse structural fields and known
scalar lexicals; strict XSD validation, wildcard materialization and correlated
choices remain the responsibility of the separate schema-validation layer.
The XML runtime does enforce known field-level `minOccurs`/`maxOccurs` wire
intervals; those do not substitute for the full XSD content-model grammar. Unknown XML members fail explicitly rather
than being dropped. The generated XML wrapper is not an XSD validator.


The SDO mutable and implementation output roots may coincide when their
actual generated relative paths are distinct. For JPMS, configure distinct
output subpackages if separate named modules will own the two output roles.
`defscodegen` owns read contracts; `sdocodegen` owns mutable contracts and
concrete implementations. Source trees under `.gen`
are generated outputs and should never be committed or packaged as handwritten
source archives.

Use `./generators/code/bootstrap.sh` to build without loading a
Builder plugin that may itself depend on these generators.

Batch CLI options, role-based cleanup and native Java/Python prerequisites are
documented in [Code Generators Reference Guide](../CODEGEN-REFERENCE.md).

## Defs 1.1 integration: field restrictions and nominal XML elements

The SDO generator consumes `AIaDataObjectField.fieldName`, `presence`
(`REQUIRED`, `ALLOWED`, `FORBIDDEN`), `allowsNull`, and `namingConvention`
metadata. Human-readable labels are resolved through `AIaFieldLabel`;
default values are expressed separately through `AIaFieldDefault` and its
factory-based resolver. XML-specific QNames belong to `AIaXmlDataObject` and
`AIaXmlDataObjectField` and are copied to the mutable contract. Inherited
fields may be restricted, but the implementation rejects relaxation of
required/forbidden presence or nullability. XML element contracts use the
specialized `_xe` naming profiles for Java and Python (`__xe_` for Python
source files). Java closed-choice records remain in the Defs Codegen sealing
module; SDO does not relocate them. The generated mutable interface inherits
from `AIiXmlSmartDataObject`, `AIiJsonSmartDataObject`, or
`AIiYamlSmartDataObject`, and the corresponding concrete implementation
inherits from the technology-specific `AIc*SmartDataObject` implementation
base. These base classes may be behaviorally empty but establish the final
extension hierarchy. Remaining limitations are documented in
[Defs Codegen recursive types](../defscodegen/RECURSIVE-TYPES-AND-XML-ELEMENTS.md).

## Shared generated DataObject method naming

Both Defs Codegen and SDO Codegen accept one `GeneratedDataObjectMethodNameConventions.NameConventions`
profile, defined in the shared `generators/code/common` artifact. The five method roles are
`standard_getter`, `standard_setter`, `raw_getter`,
`raw_presence_checker_method`, and `raw_unsetter`.
The profile refers to the established `NameCompositions` catalog, not to a second
method-name formatting implementation. By default the raw methods begin with `_`;
this prefix is a part of the selected composition and is not injected by the generator.
Existing source-structure naming profiles remain separately available under
`SourceStructureNameConventions.NameConventions`.

The name profiles affect only generated field-specific method names, never the fixed
system-level SDO API. `_toMapping(AInSdoFieldValueLoadingMode)` and
`_getValidationIssues(AInSdoFieldValueLoadingMode)` explicitly require either
`RAW_VALUES` or `EFFECTIVE_VALUES`. A future SDO marshaller will likewise require
an explicit loading mode; unmarshalling records only physically present source values.

The same method profile must be selected for a Defs-generated DO contract and its
SDO generation, especially when these are built in separate artifacts. The default
settings files include the packaged shared Java/Python profiles. Java and Python
SDO interface and implementation packages can independently be adjusted through
`--sdointf-subpackage` and `--sdoclass-subpackage`; an empty suffix uses the
original DO package.
