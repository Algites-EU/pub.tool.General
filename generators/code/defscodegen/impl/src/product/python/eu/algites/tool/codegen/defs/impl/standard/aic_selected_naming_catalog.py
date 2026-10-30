"""Role-scoped naming adapter for explicit CLI semantic-role selection."""
from __future__ import annotations

from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole


class AIcSelectedNamingCatalog:
    """Bind the semantic generated names to exact identifiers in a shared catalog."""

    def __init__(self, catalog, roles: dict[AInDefsNameRole, str]):
        self.catalog = catalog
        self.roles = dict(roles)
        for identity in self.roles.values():
            if identity not in catalog.names:
                raise ValueError(f'Unknown naming convention {identity!r}')

    @property
    def names(self):
        return self.catalog.names

    def selected(self, role: AInDefsNameRole) -> str:
        """Return the exact configured name or report the absent output role."""
        try:
            return self.roles[role]
        except KeyError as error:
            raise ValueError(f'No naming profile configured for {role.name}') from error

    def format(self, *args, **kwargs):
        return self.catalog.format(*args, **kwargs)

    def parse(self, *args, **kwargs):
        return self.catalog.parse(*args, **kwargs)

    def matches(self, *args, **kwargs):
        return self.catalog.matches(*args, **kwargs)

    def multi_mapped_list_value_synthetic_getter(self):
        """Return the configured getter for an unwrapped JSON/YAML keyed value.

        Returns:
            The nonempty identifier configured by the selected method profile.

        Raises:
            ValueError: If the generated-method profile or getter is unavailable.
        """
        import re
        profile = getattr(self.catalog, '_generated_method_profile', None)
        name = self.catalog.profile_value(profile, 'StructureNaming',
            'multi_mapped_list_value_synthetic_getter') if profile else ''
        if not name or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name) is None:
            raise ValueError('Missing/invalid multi_mapped_list_value_synthetic_getter in method profile')
        return name

    def multi_mapped_list_key_synthetic_getter(self):
        """Return the required literal getter of JSON/YAML synthetic map keys.

        Returns:
            Configured valid Java/Python identifier from the method profile.

        Raises:
            ValueError: Missing profile, missing role or invalid identifier.
        """
        import re
        profile = getattr(self.catalog, '_generated_method_profile', None)
        result = self.catalog.profile_value(profile, 'StructureNaming',
                    'multi_mapped_list_key_synthetic_getter') if profile else ''
        if not result or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', result) is None:
            raise ValueError('Missing/invalid multi_mapped_list_key_synthetic_getter in method profile')
        return result
