"""Regression tests for the role-scoped public naming catalog contract."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from eu.algites.lib.naming.convention.aii_name_convention_catalog import AIiNameConventionCatalog
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.impl.standard.aic_selected_naming_catalog import AIcSelectedNamingCatalog


class _Catalog:
    """Minimal catalog delegate that records calls without implementation internals."""

    names = ('type-profile',)
    generated_method_profile = 'methods'

    def with_generated_method_profile(self, profile):
        result = _Catalog()
        result.generated_method_profile = profile
        return result

    def generated_method_reference(self, role):
        return 'getValue' if role == 'raw_getter' else None

    def profile_value(self, name, section, key):
        return {'multi_mapped_list_value_synthetic_getter': 'getValue',
                'multi_mapped_list_key_synthetic_getter': 'getKey'}.get(key, '')

    def schema_metadata_fields(self, profile):
        return {'data_source_schema_url': '$schema'}

    def identifier_convention(self, profile, structure):
        return 'camel'

    def composition_reference(self, profile, role):
        return 'composition'

    def convert_identifier(self, value, source, target):
        return value.upper()

    def format(self, *args, **kwargs):
        return 'formatted'

    def parse(self, *args, **kwargs):
        return {'x': 'y'}

    def matches(self, *args, **kwargs):
        return True


def test_selected_catalog_implements_public_contract():
    """The adapter must be substitutable for the public interface."""
    catalog = AIcSelectedNamingCatalog(_Catalog(), {})
    assert isinstance(catalog, AIiNameConventionCatalog)
    assert catalog.generated_method_profile == 'methods'
    assert catalog.generated_method_reference('raw_getter') == 'getValue'
    assert catalog.generated_method_reference('raw_unsetter') is None
    assert catalog.schema_metadata_fields('methods')['data_source_schema_url'] == '$schema'
    assert catalog.profile_value('methods', 'StructureNaming', 'x') == ''
    assert catalog.identifier_convention('type-profile', 'x') == 'camel'
    assert catalog.composition_reference('methods', 'raw_getter') == 'composition'
    assert catalog.convert_identifier('name', 'lower', 'upper') == 'NAME'
    assert catalog.format('type-profile', 'x', {}) == 'formatted'
    assert catalog.parse('type-profile', 'x', 'test') == {'x': 'y'}
    assert catalog.matches('type-profile', 'x', 'test') is True
    assert catalog.multi_mapped_list_value_synthetic_getter() == 'getValue'
    assert catalog.multi_mapped_list_key_synthetic_getter() == 'getKey'
    updated = catalog.with_generated_method_profile('other-methods')
    assert isinstance(updated, AIiNameConventionCatalog)
    assert updated.generated_method_profile == 'other-methods'
    assert catalog.generated_method_profile == 'methods'


def test_selected_catalog_rejects_unknown_role_profile():
    """Unknown role target IDs must never receive fallback conventions."""
    role = next(iter(AInDefsNameRole))
    with pytest.raises(ValueError, match='Unknown naming convention'):
        AIcSelectedNamingCatalog(_Catalog(), {role: 'missing'})
