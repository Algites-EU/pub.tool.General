# YAML / JSON / XML schema parity

`yamldefs`, `jsondefs` and `xmldefs` contain five equivalent, documented contracts.
The first two use the repository's JSON Schema serialization for YAML and JSON
wire documents. XML contracts use XSD. `parity-root` refers to `parity-child`,
which refers to `parity-leaf`; the root also has collections of referenced objects
and enums, optional and nullable fields, scalar collections and basic facets.
`parity-builtins` covers all XSD 1.0 built-in datatype families, including the
three built-in list types and `anySimpleType`/`anyType` (46 fields).

Both Java and Python generator implementations test all three frontends and both
output languages. Comparisons normalize only source identity, resource and source
kind, retaining documentation and every represented constraint. Separate tests
compile generated Java and execute generated Python, checking nested references,
large integers, decimal precision, numeric boundaries, string lengths/patterns,
inline enums, binary content, calendars and missing-versus-null values. The Java
suite also checks fixture XSD validity with the platform SchemaFactory.

## Exact representations

| Schema family | Java output | Python output |
| --- | --- | --- |
| integer and integer subtypes | BigInteger with subtype bounds | int with subtype bounds |
| decimal / JSON number | BigDecimal | Decimal |
| float / double | Float / Double | float; float conversion rounds to binary32 |
| date/time and partial calendars | XMLGregorianCalendar | lexical calendar value with exact year/fraction/timezone |
| duration | javax.xml.datatype.Duration | lexical calendar duration |
| hexBinary / base64Binary | byte[] | bytes |
| scalar strings and QName families | String with retained datatype metadata | str with retained datatype metadata |
| lists | List of the item type | tuple of the item type |

`x-modustro-datatype` carries XSD datatype identity when JSON Schema has no exact
native equivalent (float/double, partial calendars, QName, integer subtypes).
Standard `format` and `contentEncoding` annotations also select the relevant
scalar representation. Standard minimum/maximum/exclusive bounds, string length,
pattern and scalar enum facets are retained and enforced by generated classes.

For exact JSON numbers in applications, use `json.loads(text, parse_float=Decimal)`;
precision already lost by a floating-point JSON parser cannot be reconstructed.
`to_mapping()` deliberately retains Decimal values; use a Decimal-aware JSON
serializer. Java callers now pass BigInteger/BigDecimal where generated records
previously used Long/Double. Existing handwritten Intf property constructors
remain available; new constraint components extend the canonical model API.
Scalar roots generate a typed `value` component instead of an empty record.

## Scope

This is type-preserving generation with basic scalar validation, not a complete
XSD/JSON Schema document validator. The canonical model does not retain inline
object field contracts, arbitrary unions, XSD choices, identity constraints,
attributes, namespace bindings for QName values, totalDigits/fractionDigits or
all XML string normalization and lexical restrictions. Use a schema validator
when full document validation is required. Patterns in the parity fixtures use
the common Java/Python/XSD subset; arbitrary regex dialects are not equivalent.
JSON Schema `format` has annotation semantics by default; the generated calendar
representation follows the explicit XSD datatype family, not every format
assertion rule. Source APIs do not parse XML instance documents.

No new runtime dependency on pub.lib.General is introduced. The Python scalar
support is embedded into generated modules; Java uses the JDK's math and XML
APIs. The runtime resource and its Python source copy must remain byte-identical.
