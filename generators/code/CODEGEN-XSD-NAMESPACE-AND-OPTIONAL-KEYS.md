# XML namespace publication identities and optional identity constraints

The generated Java/Python DataObject naming rules are unchanged by this policy.

## Global XSD namespace

Every production XSD carries a stable `GlobalPublicationPathId` in its adjacent
`.xsd.meta.yml`. Its `xs:schema/@targetNamespace` is exactly the publication URL:

```
https://defs.dev.algites.eu/api/xmldefs/{GlobalPublicationPathId}
```

For example, `GlobalPublicationPathId:
eu/algites/lib/security/credentials/core/credentials_1.xsd` corresponds to
`https://defs.dev.algites.eu/api/xmldefs/eu/algites/lib/security/credentials/core/credentials_1.xsd`.

The identity is sourced from the metadata, not the checkout path. Moving an XSD
between repositories does not change its XML namespace provided that the metadata
ID remains stable. Updating only `targetNamespace` without fixing namespace
bindings, `xs:import` declarations, type references, identity-constraint XPath
steps, and XML documents is insufficient. Existing documents in an old namespace
need an explicit migration; the new namespace is a different XML QName.

The namespace URI is an identifier and may also be the schema publication URL.
Consumers should nevertheless resolve schema locations using a controlled resolver
or catalog, not assume that arbitrary HTTP requests always work.

XSD files *without* a target namespace remain supported by the general Defs
frontend. Only published Algites product schemas follow the publication-URL
policy above.

## Identity constraints

`xs:key` and `xs:unique` both enforce unique **complete** keys.
The difference is whether every selected entry must have a complete key:

- `xs:key`: required; a missing component causes validation failure.
- `xs:unique`: optional; missing components exclude that entry from uniqueness
  enforcement. The runtime may expose such entries via the `null`/`None` group.

For example:

```xml
<xs:unique name="ByDepartmentCode">
  <xs:selector xpath="tns:Employee"/>
  <xs:field xpath="@Department"/>
  <xs:field xpath="@Code"/>
</xs:unique>
```

Entries lacking either attribute all belong to the *missing-key group*;
complete duplicate `(Department, Code)` keys are rejected. In Java use
`mapByKeyType(definition).get(null)`; in Python use
`map_by_key_type(definition)[None]`. Both Java and Python `MultiMappedList`
may remove the missing-key group just like any other group. Their indexes
remain atomic on failed mutations. No sentinel object or per-key-type special
resolver is necessary, and no `Id`-specific behavior exists.

For named generated XML methods, the `AIaXmlKeyDefinition` metadata provides a
`required` boolean. The canonical `AIcdKeyDefinition` preserves the same bit,
and Java/Python XML readers set the runtime `AIcKeyDefinition.required` flag.
The old required-only constructor remains valid and defaults to `true`.

## Cross-format compatibility

An XML `xs:key` on an `@Id` attribute does **not** imply that this attribute
is logically identical to a JSON/YAML `additionalProperties` key. The two
representations maintain their own specialized typed contract. When one
representation contains a keyed map and another a collection or container,
the common-role intersection must not invent an implicit field-to-map binding;
that representation-specific keyed view remains outside the common API until
an explicit schema binding declares their equivalence.

XML publication URLs are compared against format-neutral logical identities
only when the URL's exact repository-independent path, package, logical schema
name and version agree. Unrelated namespace URLs never match merely because
some types happen to be named alike.

## Verification

Run the XML schema validation suite, optional-key runtime tests, XMLDEFS
frontend tests (namespaced and namespace-free), and a full local bootstrap
before publishing. The latter is needed to validate all downstream Java
and Python compilation and distribution metadata.
