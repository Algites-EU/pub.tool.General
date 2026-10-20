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
