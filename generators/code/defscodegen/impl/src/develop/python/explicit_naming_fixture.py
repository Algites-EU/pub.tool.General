"""Explicit Algites naming selection for legacy integration fixture repositories.

Production generators must not load these catalogs implicitly. The test intentionally
selects its own naming profile so that omissions in production still fail fast.
"""
from __future__ import annotations


def explicit_algites_manifest(manifest: dict) -> dict:
    """Return a synthetic repository manifest with all relevant naming roles selected."""
    result = dict(manifest)
    result.setdefault('technology_outputs', {
        'java': 'intf/src/product/java.gen', 'python': 'intf/src/product/python.gen'})
    result.setdefault('schema_input_naming_conventions', {
        'jsondefs': 'algites-jsondef-schema-versioned_1',
        'yamldefs': 'algites-yamldef-schema-versioned_1',
        'xmldefs': 'algites-xmldef-schema-versioned_1',
    })
    output = {}
    for tech in ('java', 'python'):
        base = f'algites-{tech}-gen-intf-versioned_1'
        output[tech] = {
            'common': base, 'jsondefs': f'algites-{tech}-gen-json-intf-versioned_1',
            'yamldefs': f'algites-{tech}-gen-yaml-intf-versioned_1',
            'xmldefs_type': f'algites-{tech}-gen-xml-type-intf-versioned_1',
            'xmldefs_element': f'algites-{tech}-gen-xml-element-intf-versioned_1',
            'xmldefs_namespace': f'algites-{tech}-gen-xml-namespace-intf_1',
        }
    result.setdefault('technology_output_naming_conventions', output)
    result.setdefault('technology_enum_output_naming_conventions', {
        tech: f'algites-{tech}-gen-enum-versioned_1' for tech in ('java','python')})
    result.setdefault('naming_convention_files', [f'resource:{name}' for name in (
        'standard-conventions.yml',
        'algites-java-name-conventions.yml', 'algites-python-name-conventions.yml',
        'algites-jsondef-name-conventions.yml', 'algites-yamldef-name-conventions.yml',
        'algites-xmldef-name-conventions.yml',
    )])
    return result


def explicit_legacy_generic_manifest(manifest: dict) -> dict:
    """Select one generic interface per source kind for older contract tests.

    Newer production profiles may emit both common and technology-specific
    representations. These historical tests expect the generic representation
    only, and now express that selection explicitly instead of relying on defaults.
    """
    result = explicit_algites_manifest(manifest)
    if result.get('artifact') == '.':
        result['technology_outputs'] = {language: f'src/product/{language}.gen'
                                        for language in ('java', 'python')}
    result['technology_output_naming_conventions'] = {
        language: {
            'jsondefs': f'algites-{language}-gen-intf-versioned_1',
            'yamldefs': f'algites-{language}-gen-intf-versioned_1',
            'xmldefs_type': f'algites-{language}-gen-intf-versioned_1',
            'xmldefs_element': f'algites-{language}-gen-xml-element-intf-versioned_1',
            'xmldefs_namespace': f'algites-{language}-gen-xml-namespace-intf_1',
        } for language in ('java', 'python')}
    return result
