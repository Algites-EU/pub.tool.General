from __future__ import annotations

import re
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind


class AIcGenerationNames:
    """Names generated sources through the supplied YAML-backed catalog."""

    @staticmethod
    def _selected(profile, kind):
        """Resolve a mandatory role supplied explicitly by the active naming profile."""
        if not hasattr(profile, 'selected'):
            raise ValueError(f'No output naming profile configured for role {kind}')
        return profile.selected(kind)

    def render(self, logical_name, version, profile, kind):
        """Render a canonical type or file name using the requested naming role."""
        profile_name = self._selected(profile, kind)
        structure = 'file_name_stem' if kind in (AInDefsNameRole.DATA_TYPE_FILE_STEM,
            AInDefsNameRole.ENUM_TYPE_FILE_STEM, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM,
            AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM,
            AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM) else 'main_container_name'
        values = {'identifier': logical_name}
        if version is not None:
            values['version'] = str(version)
        # A trailing numeric schema-pointer ordinal is a derived identifier fragment,
        # not a separate version. Keep lexical segments unambiguous against _<version>.
        values['identifier'] = re.sub(r'(?<=[a-z])-(?=[0-9]+(?:-|$))', '', values['identifier'])
        return profile.format(profile_name, structure, values, 'lower_kebab_case_1')

    def type_name(self, definition, profile, kind):
        """Return the generated type name for the requested definition."""
        return self.render(definition.logical_name, definition.version, profile, kind)

    def file_stem(self, definition, profile, kind):
        """Return the generated source-file stem according to the naming profile."""
        return self.render(definition.logical_name, definition.version, profile, kind)

    @staticmethod
    def _recognized_source_field(name: str) -> bool:
        """Identify lexical field names supported by the built-in source conventions.

        Arbitrary JSON/YAML property keys (notably ``$schema``) remain legal,
        but naming-catalog errors must never be mistaken for such property keys.
        """
        return any(re.fullmatch(pattern, name) is not None for pattern in (
            r'[A-Z][A-Za-z0-9]*',
            r'[a-z][A-Za-z0-9]*',
            r'[a-z][a-z0-9]*(?:_[a-z0-9]+)+',
            r'[a-z][a-z0-9]*(?:-[a-z0-9]+)+',
        ))

    def _field(self, source_name, profile, structure, source_convention,
               role=AInDefsNameRole.INTERFACE_TYPE):
        """Format a data field; never catch errors raised by its naming profile."""
        selected_role = self._selected(profile, role)
        if not self._recognized_source_field(source_name):
            # Only invalid *source field lexemes* are normalized. A broken or
            # missing profile must fail instead of activating a naming fallback.
            normalized = re.sub(r'[^A-Za-z0-9]+', '-', source_name).strip('-').lower()
            if not normalized or normalized[0].isdigit():
                normalized = 'field-' + normalized
            source_name = normalized
            source_convention = 'lower_kebab_case_1'
        return profile.format(selected_role, structure,
                              {'identifier': source_name}, source_convention)

    @staticmethod
    def _source_field_convention(source_name: str) -> str:
        """Identify input lexical form; output accessor syntax comes from the selected profile."""
        if re.fullmatch(r'[A-Z][A-Za-z0-9]*', source_name):
            return 'upper_camel_case_1'
        if re.fullmatch(r'[a-z][A-Za-z0-9]*', source_name):
            return 'lower_camel_case_1'
        if re.fullmatch(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)+', source_name):
            return 'lower_snake_case_1'
        if re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)+', source_name):
            return 'lower_kebab_case_1'
        return 'upper_camel_case_1'

    def property_name(self, source_name, profile):
        """Convert a canonical field name into a target-language identifier."""
        return self._field(source_name, profile, 'field_name', self._source_field_convention(source_name))

    def getter_name(self, source_name, profile, role=AInDefsNameRole.INTERFACE_TYPE):
        """Name a field getter using the selected profile, not a fixed prefix."""
        return self._field(source_name, profile, 'getter_method_name', self._source_field_convention(source_name), role)

    def setter_name(self, source_name, profile):
        """Name a field setter using the selected profile, not a fixed prefix."""
        return self._field(source_name, profile, 'setter_method_name', self._source_field_convention(source_name))

    def enum_constant(self, source_name, profile):
        """Convert a wire-level enum value into its generated constant name."""
        return self._field(source_name, profile, 'enum_item_name', 'lower_snake_case_1')

    def schema_field_name_constant(self, source_name, profile):
        """Use the chosen constant convention for both parts of a schema-field constant.

        The empty middle component retains the two separators from the existing
        schema-field API, without adding any domain-specific content to the catalog.
        """
        prefix = self._field('_'.join(('schema', 'field', 'name')), profile, 'constant_name', 'lower_snake_case_1')
        field = self._field(source_name, profile, 'constant_name', self._source_field_convention(source_name))
        return '_'.join((prefix, '', field))

    def reference_type(self, ref, profile):
        """Compute the generated type name for a referenced definition."""
        kind = AInDefsNameRole.ENUM_TYPE if ref.targets_enum else AInDefsNameRole.DATA_TYPE
        return self.render(ref.logical_name, ref.version, profile, kind)
