"""Map explicitly named source types to canonical local identifiers.

A schema URI or XML QName remains the source identity. This helper converts only
its declared local type name by the selected, validated naming profile.
"""


def canonical_type_identifier(catalog, profile: str, name: str) -> str:
    """Validate one declared type and obtain its round-trippable logical name.

    Args:
        catalog: Selected source naming catalog supporting parse/conversion.
        profile: Source schema naming profile provided by the generator.
        name: Exact declared type name from XSD or a JSON Schema ``$defs`` key.
    Returns:
        Local canonical logical name (not the schema-qualified identity).
    Raises:
        ValueError: Invalid declared name, incomplete naming rules or lossy
            identifier conversion.
    """
    parsed = catalog.parse(profile, 'type_name', name)
    lexical = catalog.identifier_convention(profile, 'type_name')
    if not lexical:
        raise ValueError(f'Source type naming profile has no identifier convention: {profile}')
    result = catalog.convert_identifier_by_declared_style(parsed['identifier'], lexical,
        'lower_kebab_case_1')
    restored = catalog.convert_identifier_by_declared_style(result,
        'lower_kebab_case_1', lexical)
    if restored != parsed['identifier']:
        raise ValueError(f'Non-round-trippable declared type name {name!r}: {restored!r}')
    return result
