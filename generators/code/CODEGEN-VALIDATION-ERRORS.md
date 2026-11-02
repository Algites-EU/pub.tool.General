# Codegen validation errors — Java and Python

The Defs and SDO generators share an explicit **message + hint** contract for
expected schema, naming, configuration, output and input-artifact errors.

## Contract

The **message** is the exact previous validation text. Do not prepend a code,
translate it, or replace it with a generic summary. The **hint** is a second,
mandatory field on the exception and must tell the user which source/configuration
to inspect and how to correct it. Optional source and location identify the file,
artifact, JSON Pointer or XPath when known. Never guess a fix based on a regular
expression over the message at rendering time.

**Java** (`pub.tool.General_generators.code.common`):

```java
throw new AIxCodegenValidationException(
    "Unversioned schema is not allowed: " + schema,
    "Add the version required by the selected input naming profile, "
    + "or explicitly enable unversioned schemas.");
```

`AIxCodegenValidationException` extends `IllegalArgumentException`, preserves
`getMessage()` and offers `getHint()`, `getSource()` and `getLocation()`.
Constructors also permit an optional original cause.

**Python** (same artifact):

```python
raise AIxCodegenValidationException(
    f'Unversioned schema is not allowed: {schema}',
    'Add the version required by the selected input naming profile, '
    'or explicitly enable unversioned schemas.',
    source=str(schema))
```

`AIxCodegenValidationException` extends `ValueError`; `str(error)` is the
original message. The separate attributes are `message`, `hint`, `source`,
`location`. The Python exception can use `raise ... from original` to retain
causes.

Both standalone CLIs and the Python bootstrap invocation render, for example:

```text
  VALIDATION ERROR - Defs Codegen

  Message: 'credentialProfile' does not match algites-jsondef-schema-versioned_1/type_name
  Source: credential-profiles_1.jsondef.schema.json
  Location: #/$defs/credentialProfile

  Hint: Rename the $defs type according to the selected type_name naming
        convention and update all $ref references.
```

These messages remain plain text without terminal control characters, so
Cloudsmith build logs, CI output and redirected stderr are readable.

A typed validation exception exits a standalone CLI with status 2. Unexpected
failures (e.g. `NullPointerException`, `TypeError`, `IndexError`) are not
converted into user errors and retain normal stack traces. Set
`ALGITES_CODEGEN_DEBUG=1` to also print a stack trace for a validation error.

## Writing new validation checks

1. Raise/throw the shared exception at the **site of detection** and pass the
   original message as the first argument, a contextual correction as the second.
2. Identify the actual schema, role, catalog, QName, `xs:key` field, contract or
   artifact in the hint where that information is available; do not suggest
   blindly deleting data or altering generated `java.gen` / `python.gen` files.
3. Preserve causes when wrapping library errors; use optional `source`/`location`
   for precise pointers without altering the original message.
4. Keep programming errors and invalid internal invariants as ordinary
   exceptions; **only expected input/configuration incompatibilities** are
   Codegen validation failures.
5. Add tests that assert the original message and hint independently, then
   check that the Java/Python CLI output displays both and that an unexpected
   exception still produces a stack trace.

The initial migration covers explicit validation sites in both Defs and SDO
implementations, their CLI settings parsers, public contract validators and
the common artifact resolver. External library exceptions that are not yet
wrapped at a Codegen validation boundary still propagate normally; do not
silently classify arbitrary `ValueError` or `IllegalArgumentException`
messages as validation errors.
