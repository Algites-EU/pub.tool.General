"""Role-scoped naming adapter for explicit CLI semantic-role selection."""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException

from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.lib.naming.convention.aii_name_convention_catalog import AIiNameConventionCatalog


class AIcSelectedNamingCatalog(AIiNameConventionCatalog):
    """Bind the semantic generated names to exact identifiers in a shared catalog."""

    def __init__(self, catalog, roles: dict[AInDefsNameRole, str]):
        self.catalog = catalog
        self.roles = dict(roles)
        for identity in self.roles.values():
            if identity not in catalog.names:
                raise AIxCodegenValidationException(f'Unknown naming convention {identity!r}', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')

    @property
    def names(self):
        return self.catalog.names

    def selected(self, role: AInDefsNameRole) -> str:
        """Return the exact configured name or report the absent output role."""
        try:
            return self.roles[role]
        except KeyError as error:
            raise AIxCodegenValidationException(f'No naming profile configured for {role.name}', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.') from error

    @property
    def generated_method_profile(self) -> str | None:
        """Return the selected generated-method profile of the underlying catalog."""
        return self.catalog.generated_method_profile

    def generated_method_reference(self, role: str) -> str | None:
        """Resolve a generated-method role through the underlying catalog."""
        return self.catalog.generated_method_reference(role)

    def with_generated_method_profile(self, profile: str) -> AIiNameConventionCatalog:
        """Return a new role-scoped adapter with the named method profile."""
        return AIcSelectedNamingCatalog(self.catalog.with_generated_method_profile(profile), self.roles)

    def identifier_convention(self, profile_name: str, structure: str) -> str | None:
        """Return the identifier convention declared for a structure."""
        return self.catalog.identifier_convention(profile_name, structure)

    def convert_identifier(self, value: str, source: str, target: str) -> str:
        """Convert an identifier through the underlying catalog."""
        return self.catalog.convert_identifier(value, source, target)

    def profile_value(self, name: str, section: str, key: str) -> str:
        """Resolve a literal profile value from the underlying catalog."""
        return self.catalog.profile_value(name, section, key)

    def composition_reference(self, profile: str, role: str) -> str:
        """Resolve a named composition reference through the underlying catalog."""
        return self.catalog.composition_reference(profile, role)

    def schema_metadata_fields(self, profile: str) -> dict[str, str]:
        """Return configured schema metadata names without introducing defaults."""
        return self.catalog.schema_metadata_fields(profile)

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
        profile = self.generated_method_profile
        name = self.catalog.profile_value(profile, 'StructureNaming',
            'multi_mapped_list_value_synthetic_getter') if profile else ''
        if not name or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name) is None:
            raise AIxCodegenValidationException('Missing/invalid multi_mapped_list_value_synthetic_getter in method profile', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
        return name

    def multi_mapped_list_key_synthetic_getter(self):
        """Return the required literal getter of JSON/YAML synthetic map keys.

        Returns:
            Configured valid Java/Python identifier from the method profile.

        Raises:
            ValueError: Missing profile, missing role or invalid identifier.
        """
        import re
        profile = self.generated_method_profile
        result = self.catalog.profile_value(profile, 'StructureNaming',
                    'multi_mapped_list_key_synthetic_getter') if profile else ''
        if not result or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', result) is None:
            raise AIxCodegenValidationException('Missing/invalid multi_mapped_list_key_synthetic_getter in method profile', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
        return result
