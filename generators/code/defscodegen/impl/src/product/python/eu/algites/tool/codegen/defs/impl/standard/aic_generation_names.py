from __future__ import annotations

import re
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind


class AIcGenerationNames:
    """Names generated sources through the supplied YAML-backed catalog."""

    @staticmethod
    def _technology(profile) -> str:
        if any(name.startswith('algites-java-') for name in profile.names):
            return 'java'
        if any(name.startswith('algites-python-') for name in profile.names):
            return 'python'
        raise ValueError('Missing Java/Python naming roles in catalog')

    def render(self, logical_name, version, profile, kind):
        """Render a canonical type or file name using the requested naming role."""
        role = ('enum' if kind in (AInDefsNameRole.ENUM_TYPE, AInDefsNameRole.ENUM_TYPE_FILE_STEM)
                else 'xml-element-intf' if kind in (AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE, AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM)
                else 'xml-namespace-intf' if kind in (AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE, AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM)
                else 'intf' if kind in (AInDefsNameRole.INTERFACE_TYPE, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
                else 'data-class' if kind in (AInDefsNameRole.DATA_TYPE, AInDefsNameRole.DATA_TYPE_FILE_STEM)
                else None)
        if role is None:
            raise ValueError(f'Unsupported type-name role: {kind}')
        profile_name = (profile.selected(kind) if hasattr(profile, 'selected') else
            f'algites-{self._technology(profile)}-gen-{role}' + ('-versioned_1' if version is not None else '_1'))
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

    def _field(self, source_name, profile, structure, source_convention,
               role=AInDefsNameRole.INTERFACE_TYPE):
        role = (profile.selected(role) if hasattr(profile, 'selected') else
            f'algites-{self._technology(profile)}-gen-intf-versioned_1')
        try:
            return profile.format(role, structure, {'identifier': source_name}, source_convention)
        except ValueError:
            # JSON-Schema system properties such as $schema are legal data keys,
            # but not program-language identifiers; normalize them at this boundary.
            normalized = re.sub(r'[^A-Za-z0-9]+', '-', source_name).strip('-').lower()
            if not normalized or normalized[0].isdigit():
                normalized = 'field-' + normalized
            return profile.format(role, structure, {'identifier': normalized}, 'lower_kebab_case_1')

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
