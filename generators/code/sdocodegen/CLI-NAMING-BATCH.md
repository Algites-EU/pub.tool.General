# SDO Codegen — YAML naming catalog batch CLI

The legacy single imported-class CLI remains available. The new CLI additionally accepts:

```sh
sdo-codegen \
  --technology-dointf-input-dir=python:src/product/python.gen \
  --technology-dointf-input-naming-profile=python:config/algites-python-name-conventions.yml \
  --technology-sdointf-output-dir=python:src/product/python.gen \
  --technology-sdointf-output-naming-profile=python:config/algites-python-name-conventions.yml \
  --technology-sdoimpl-output-dir=python:src/product/python.gen \
  --technology-sdoimpl-output-naming-profile=python:config/algites-python-name-conventions.yml
```

The Java native CLI takes `java:` values and accepts optional
`--dointf-classpath=<binary-dependencies>`. It compiles the generated AIig
sources and sibling enums in memory, then uses reflection; no prior contract
compilation is required. Python imports its `AIig` modules directly from the
source root and does not invoke Java. Both native CLIs validate generated names
against the loaded `sdointf`/`sdoimpl` output profiles, and restrict cleanup to
those role names. Input and output directories may overlap. `--clean-only`
needs only output root/catalog pairs. Normal generation validates all contracts
**before** deleting recognized stale output; `--check` performs no writes.

The native SDO source renderers now obtain generated primary type names and filenames through the selected YAML catalog compositions (including version captures), including inherited and nested contracts. Their recognition of input `AIig` contracts, the semantic relationships among read/mutable/concrete types, and the setter/getter generation logic remain specific to the Algites SDO model. Arbitrary unrelated container kinds and custom code templates remain outside this migration.

Full reference: [Code Generators Reference Guide](../CODEGEN-REFERENCE.md), section 3.


### Shared structural naming rules

All Algites Java naming profiles share `method_parameter_name = a + UpperCamelCase`
(e.g. `aCustomerAddress`) and `local_variable_name = loc + UpperCamelCase`
(e.g. `locCustomerAddress`). The Python profiles use `a_ + lower_snake_case`
and `loc_ + lower_snake_case` (e.g. `a_customer_address`, `loc_customer_address`).
These fragments are declared once per language catalog and referenced by all
32 profiles, rather than duplicated in each container variant. The suffix of a
full filename is **not** part of a `*-file` stem composition: complete filenames
are built from `file_name_stem + file_name_suffix`, with exactly one `.java` or
`.py` suffix.

With YAML catalogs supplied to SDO Codegen, both native renderers use their
selected catalog for the generated mutable interface / concrete class names,
filenames **and setter-argument names**. Existing protocol method names
(`setName`, `get_Name`, `unset_Name`, etc.) are still determined by the SDO
contract and are not freely renamed through the `method_name` profile entry.
The `local_variable_name` rule is available to generators but does not rewrite
internal local variables of the SDO renderer itself.
