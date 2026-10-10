# SDO Codegen

`pub.tool.General:1.1-SNAPSHOT` contains a second, **schema-independent** generator.
It reads annotated, compiled (Java) or imported (Python) `AIig*` read contracts.
It never reads YAML, JSON Schema, XSD or the canonical-definition model.

The `intf` artifact exposes the generation API, `impl` generates mutable contracts
(`AIigd*`, or a different configured marker) and concrete implementations
(`AIcgd*`), and `cli` is the adapter used by build orchestration.

Java:

```sh
java -cp "$CLASSPATH" eu.algites.tool.codegen.sdo.AIcSdoCodegenCli \
    example.contracts.AIigRoot_1 /path/to/intf/src/product/java.gen \
    /path/to/impl/src/product/java.gen d
```

Python:

```sh
python -m eu.algites.tool.codegen.sdo.aic_sdo_codegen_cli \
    example.contracts.aiig_root_1:AIigRoot_1 \
    /path/to/intf/src/product/python.gen \
    /path/to/impl/src/product/python.gen --marker d
```

Both CLIs support `--check` for non-mutating verification. The Java interface
must be on the classpath; the Python module must be importable. This is not a
schema dependency: handwritten contracts with the same annotations are supported.

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


Do not merge the two output roots. `defscodegen` owns read contracts, `sdocodegen`
owns mutable contracts and concrete implementations. Source trees under `.gen`
are generated outputs and should never be committed or packaged as handwritten
source archives.

Use `./generators/code/sdocodegen/bootstrap.sh` to build without loading a
Builder plugin that may itself depend on these generators.
