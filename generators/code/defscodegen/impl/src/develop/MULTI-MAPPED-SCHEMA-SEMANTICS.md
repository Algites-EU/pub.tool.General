# Defs Codegen: keyed collection and patterned-property semantics

**Status:** design specification with explicit implementation status below.  
**Author:** linhart1  
**Baseline:** `pub.lib.General(20261030-061855).tgz` and `pub.tool.General(20261030-061856).tgz`.

This document defines the **intended contract**, including behaviors not yet
fully implemented. A partial parser must never imply that serialization,
validation, Java/Python generator parity, or SDO support has been verified.
The four independent field roles remain `NAMED_VALUE`, `KEYED_VALUES`,
`POSITION_TYPED_VALUE`, and `SEQUENTIAL_VALUES`.

## 1. JSON/YAML dynamically named members

A JSON object's member name is a **key**, not part of its member value:

```json
{
  "all_lower_1": {"Regexp": "[a-z]+"},
  "upper_camel_1": {"Regexp": "[A-Z][a-zA-Z]*"}
}
```

Schema:

```json
{
  "type": "object",
  "propertyNames": {"minLength": 1},
  "additionalProperties": {
    "type": "object",
    "properties": {"Regexp": {"type": "string", "minLength": 1}},
    "required": ["Regexp"],
    "additionalProperties": false
  }
}
```

Each keyed value implements a generated **interface**, with the configured
`multi_mapped_list_key_synthetic_getter` (default `_getKey()`). The getter
returns `all_lower_1` or `upper_camel_1` without adding a `Key` field to the
serialized value. The map is an `AIiMultiMappedList<V>` and can be addressed
using its typed `AIiKeyDefinition<V,K>`; a JSON object member name is unique.

For scalar or array-valued members, there is also a generated virtual
`multi_mapped_list_value_synthetic_getter` (default `_getValue()`):

```json
{"S_name": "Anna", "I_age": 35}
```

An explicitly declared variant contract can produce a string-value interface
with `_getValue(): String` and an integer-value interface with
`_getValue(): BigInteger`, plus `_getKey(): String` on both. The synthetic
value getter is *not* serialized as an inner object property. The same applies
to Python interfaces (`str` / `int`), subject to actual generated support for
closed variants.

**Neither getter is used for an XML key**: its fields are already explicitly
declared as real attributes/elements.

### 1.1 `properties` and `additionalProperties` together

These are orthogonal, and the dynamic values can themselves be arrays:

```json
{
  "type": "object",
  "properties": {"Description": {"type": "string"}},
  "additionalProperties": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {"something": {"type": "string"}},
      "required": ["something"],
      "additionalProperties": false
    }
  }
}
```

Valid YAML data:

```yaml
Description: Example mappings
aaa:
  - something: else
bbb:
  - something: first
  - something: second
```

There are two map entries (`aaa` and `bbb`), **not** three; the value of `bbb`
is *one array* of two objects. A virtual `_getValue()` exposes that array.
`Description` remains a normal named field. Do not flatten an array-valued
entry into multiple separately keyed entries.

## 2. `patternProperties` is a constraint, not a structural field declaration

JSON Schema requires **all** matched patterns to hold; the first match does
not win. A `properties` rule and a `patternProperties` rule can both apply.
In the *same schema object*, `additionalProperties` applies only to names not
matched by either of the other two keywords. Ignoring that qualification would
silently change JSON Schema semantics.

A schema that is **valid JSON Schema but is not by itself a valid source of a
single typed `KEYED_VALUES` contract**:

```json
{
  "type": "object",
  "patternProperties": {
    "^S_": {"type": "string"},
    "^I_": {"type": "integer"}
  },
  "additionalProperties": false
}
```

It can validate values such as `{"S_name":"Anna","I_age":35}`, but the
patterns alone define heterogeneous value types. Do **not** invent generated
fields or allow a silent `Object`/`Any` fallback.

### 2.1 Equivalent structural rewrite

Declare the value variants in `additionalProperties` and put the *additional*
name-specific restrictions in a separate `allOf` subschema. This is semantically
slightly **broader** than the preceding schema if unprefixed keys are allowed;
to preserve the original rejection of those keys, include the final
`propertyNames` restriction as shown:

```json
{
  "type": "object",
  "propertyNames": {"pattern": "^(S_|I_)"},
  "additionalProperties": {
    "oneOf": [{"type": "string"}, {"type": "integer"}]
  },
  "allOf": [{
    "patternProperties": {
      "^S_": {"type": "string"},
      "^I_": {"type": "integer"}
    }
  }]
}
```

The outer `additionalProperties` supplies a closed typed variant;
`patternProperties` is only a constraint. The expression `^(S_|I_)` enforces
that no other names occur. **Important:** this is a target-supported modeling
pattern, not a claim that the current Defs frontend has implemented general
`allOf` constraint projection, overlapping-pattern validation or typed scalar
variant wrappers. These steps must be tested before enabling this schema in a
published codegen build.

An overlapping pattern example:

```json
{
  "type": "object",
  "properties": {"S_name": {"type": "string", "minLength": 5}},
  "patternProperties": {
    "^S_": {"type": "string", "maxLength": 20},
    "_name$": {"pattern": "^[A-Z]"}
  },
  "additionalProperties": {"type": "boolean"}
}
```

`S_name` must satisfy **all three** applicable constraints. There must be no
implicit precedence or disjointness assumption.

## 3. XML keyed collections

```xml
<IdentifierConventions>
  <IdentifierConvention name="all_lower_1"><Regexp>[a-z]+</Regexp></IdentifierConvention>
  <IdentifierConvention name="upper_camel_1"><Regexp>[A-Z][a-zA-Z]*</Regexp></IdentifierConvention>
</IdentifierConventions>
```

XSD (simplified, with unqualified local elements):

```xml
<xs:element name="IdentifierConventions">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="IdentifierConvention" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType>
          <xs:sequence><xs:element name="Regexp" type="xs:string"/></xs:sequence>
          <xs:attribute name="name" type="xs:string" use="required"/>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
  <xs:key name="IdentifierByName">
    <xs:selector xpath="IdentifierConvention"/>
    <xs:field xpath="@name"/>
  </xs:key>
</xs:element>
```

A single `xs:key` supplies one unique map view; multiple `xs:key` declarations
supply *multiple independent map views*, all enforced, not merely a warning
for secondary keys. Unlike JSON dynamic property names, the XML `@name`
attribute remains a normal field of the value interface.

### 3.1 Composite keys

```xml
<xs:key name="ByLanguageAndRegion">
  <xs:selector xpath="Translation"/>
  <xs:field xpath="@language"/>
  <xs:field xpath="@region"/>
</xs:key>
```

This is **one** key consisting of an ordered pair. A generated Java record or
frozen Python dataclass can supply stable equality and hash semantics. The
keyed list has one map *per xs:key*, not per `xs:field`.

### 3.2 Nullable nested paths: null-safe lookup is mandatory

```xml
<xs:key name="EmployeeByCode">
  <xs:selector xpath="Employee"/>
  <xs:field xpath="Properties/Identity/CommonPart/Code"/>
</xs:key>
```

The extraction contract must guard **every** intermediate level:

```java
EmployeeProperties properties = employee == null ? null : employee.getProperties();
Identity identity = properties == null ? null : properties.getIdentity();
CommonPart commonPart = identity == null ? null : identity.getCommonPart();
String key = commonPart == null ? null : commonPart.getCode();
```

This is illustrative Java with hypothetical application type names. Returning
`null` from extraction avoids a null-pointer failure but **does not make an
`xs:key` valid**: XSD requires key fields to be present and not nil. The map
must reject a missing key (via a diagnostic), preferably before any list
mutation. `xs:unique` differs: absent values may be permitted. An XPath that
selects multiple values for a single key field is invalid.

### 3.3 Selectors across several descendant lists

```xml
<Company>
  <Department><Employee id="101"/></Department>
  <Department><Employee id="102"/></Department>
</Company>
```

```xml
<xs:key name="CompanyEmployeeId">
  <xs:selector xpath=".//Employee"/>
  <xs:field xpath="@id"/>
</xs:key>
```

The key belongs to the **scope of Company**, not to just one department. The
target design creates one aggregated map view for that `xs:key`; deletion
through the view must remove values from their actual source collection.
Insertion through the aggregate requires an unambiguous destination and may
otherwise be unsupported. Changes in child collections must be visible in the
aggregate. The current frontend does **not** implement this entire mechanism;
reject rather than project such an XPath as a direct list silently.

### 3.4 `xs:keyref`: validation-only and intentionally ignored

An `xs:keyref` checks **referential integrity**, not a data storage shape.
Defs Codegen deliberately **ignores** it while projecting structural contracts.
It does not create a field, an index definition, a map, a relationship, or
runtime referential validation; its presence never blocks structural generation.
Supported `xs:key` declarations in the same element are still projected.
This does **not** imply that an XML document is valid. A separate full XSD
validator must enforce the original `xs:keyref` constraints when requested.

For example, these XSD constraints define a key and a reference:

```xml
<xs:key name="EmployeeById">
  <xs:selector xpath="Employees/Employee"/>
  <xs:field xpath="@id"/>
</xs:key>
<xs:keyref name="AssignmentEmployee" refer="EmployeeById">
  <xs:selector xpath="Assignments/Assignment"/>
  <xs:field xpath="@employeeId"/>
</xs:keyref>
```

The generated data objects can represent the following XML, even though
`employeeId="999"` is an invalid reference in the original XSD:

```xml
<Company>
  <Employees><Employee id="101"/></Employees>
  <Assignments><Assignment employeeId="999"/></Assignments>
</Company>
```

An external validating XML parser must detect the missing referenced employee.
There is no implicit foreign-key association, cascade deletion, or insertion
restriction. If relationship modeling is ever desired, it requires an explicit
separate design, not silent inference from `xs:keyref`. `xs:unique` is a
**separate** case and presently remains an error in the keyed collection
projection; it is not being changed by this decision.

### 3.5 Multiple selector element kinds are not automatically projected

```xml
<xs:key name="PersonById">
  <xs:selector xpath="Employee|Contractor"/>
  <xs:field xpath="@id"/>
</xs:key>
```

This is legal XSD, but it selects different element kinds and is **outside the
automatic multi-mapped-list projection**. It must not degenerate to
`AIiMultiMappedList<Object>`.

If the intended data model has a shared person contract, a supported modeling
alternative is to represent both kinds with the *same XML element name* and
`xsi:type` selecting derived XML types:

```xml
<People xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:tns="urn:people">
  <Person id="101" xsi:type="tns:EmployeeType"><Salary>500</Salary></Person>
  <Person id="102" xsi:type="tns:ContractorType"><ContractNumber>C-9</ContractNumber></Person>
</People>
```

The corresponding `Person` element has an abstract base `PersonType`, and
`EmployeeType` / `ContractorType` extend it. An XSD key can then use
`<xs:selector xpath="tns:Person"/>`. This rewrite is **not wire-identical** to
distinct `Employee` and `Contractor` element names, and XSD polymorphic
serialization/runtime support must be verified separately.

## 4. Collection API and mutation contract

```java
AIiMultiMappedList<Employee> employees = ...;
Map<String, List<Employee>> byCity = employees.mapByKeyType(BY_CITY);
List<Employee> pragueSnapshot = byCity.get("Prague");
byCity.remove("Prague");
```

- `AIiMultiMappedList<V>` extends `List<V>`; its primary list preserves
  insertion/index order. It is **not** an ordered map.
- `mapByKeyType()` returns the **cached live map** for the exact registered
  `AIiKeyDefinition<V,K>` instance.
- Each `Map` value is a **non-backed immutable snapshot** (`List<V>` for Java,
  `tuple[V,...]` for Python). It is not a modifiable insertion route.
- Map `remove(key)` deletes the **whole matching group** from the primary list,
  every other map and all living tracked sublists.
- Map `put`, `putAll`, `compute`, replacement and insertion are unsupported.
- Tracked `subList` does not acquire newly added parent elements, but loses
  elements deleted by any route. Released sublists are weakly referenced.
- Modification of a key-bearing field while its value is stored is a **caller
  contract violation**, analogously to mutable hash-map keys. It is not
  tracked automatically.
- Null keys or duplicate values for a **unique** key definition are rejected
  before the affected list mutation becomes visible.

## 5. Feature verification gates

| Area | Intended behavior | Current verified level |
|---|---|---|
| Four canonical field roles | Typed, independent of source format | Partial implementation |
| Direct XML `xs:key`, multiple keys | Keyed collection with all index definitions | Python reader regressions |
| Nested XML `xs:field` path | Typed components, nullable intermediate access | Python field-path recognition tests; Java extractor/runtime pending |
| Descendant `xs:selector` (`.//Employee`) | Live aggregated index scoped by ancestor | Design only; must reject unsupported case |
| Union selector (`Employee\|Contractor`) | No automatic projection | Explicitly unsupported by design |
| JSON `additionalProperties` | Typed dynamic values and synthetic key | Canonical reader and interface generation |
| Configurable `_getValue()` | Typed synthetic scalar/array getter | Python-driven Java/Python interface generation tests |
| `patternProperties` | All matching validation constraints, never structural field definitions | Not yet end-to-end; unsupported instances fail explicitly |
| Java/Python source frontend parity | Identical canonical semantics | Incomplete |
| DO/SDO runtime round-trip | Preserve keys, values, choice and XML order | Not yet verified end-to-end |

All generated Java interfaces, records, constants, methods, parameters,
return types and exceptions must have substantive Javadoc; annotate public
Java types with `@author linhart1`. Java and Python parameter/local names
must start with lowercase letters (or underscores where conventions explicitly
require them) and follow each language's selected naming conventions.
Do not manually modify `java.gen` or `python.gen`.

## Native Java parser parity and unresolved aggregate-key design

The native Java reader now recognizes the same direct keyed shape as Python:

```xml
<xs:element name="Employees">
  <xs:complexType><xs:sequence>
    <xs:element name="Employee" maxOccurs="unbounded">
      <xs:complexType><xs:sequence>
        <xs:element name="Identity" minOccurs="0">
          <xs:complexType><xs:sequence>
            <xs:element name="Code" type="xs:string"/>
          </xs:sequence></xs:complexType>
        </xs:element>
      </xs:sequence></xs:complexType>
    </xs:element>
  </xs:sequence></xs:complexType>
  <xs:key name="ByCode">
    <xs:selector xpath="Employee"/>
    <xs:field xpath="Identity/Code"/>
  </xs:key>
</xs:element>
```

The unprefixed XPath steps above assume **unqualified local elements**. In
a schema declaring `elementFormDefault="qualified"`, use `tns:Employee`
and `tns:Identity/tns:Code` instead. Java and Python frontends reject
namespace mismatches rather than silently mapping by local name.

The distinct descendant-selector case is still outstanding:

```xml
<xs:element name="Company">
  <!-- Company/Department/Employee has its own repeated occurrence. -->
  <xs:key name="AllEmployeeIds">
    <xs:selector xpath=".//Employee"/>
    <xs:field xpath="@id"/>
  </xs:key>
</xs:element>
```

This constraint is scoped to `Company`, not to an individual department.
Preserving it as a live indexed **aggregate** requires tracking modifications
in every nested employee collection and mapping removals to the correct
original parent. A parser that merely records the name cannot claim to have
implemented the corresponding live `AIiMultiMappedList`. As of this
checkpoint such selectors are rejected and not silently flattened.
