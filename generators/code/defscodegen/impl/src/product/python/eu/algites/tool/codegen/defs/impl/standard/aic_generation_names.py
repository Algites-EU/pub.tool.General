from __future__ import annotations

import re
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind


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
        role = ('enum' if kind in (AInDefsNameRole.ENUM_TYPE, AInDefsNameRole.ENUM_TYPE_FILE_STEM)
                else 'intf' if kind in (AInDefsNameRole.INTERFACE_TYPE, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
                else 'data-class' if kind in (AInDefsNameRole.DATA_TYPE, AInDefsNameRole.DATA_TYPE_FILE_STEM)
                else None)
        if role is None:
            raise ValueError(f'Unsupported type-name role: {kind}')
        profile_name = f'algites-{self._technology(profile)}-gen-{role}' + ('-versioned' if version is not None else '')
        structure = 'file_name_stem' if kind in (AInDefsNameRole.DATA_TYPE_FILE_STEM,
            AInDefsNameRole.ENUM_TYPE_FILE_STEM, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM) else 'main_container_name'
        values = {'identifier': logical_name}
        if version is not None:
            values['version'] = str(version)
        # A trailing numeric schema-pointer ordinal is a derived identifier fragment,
        # not a separate version. Keep lexical segments unambiguous against _<version>.
        values['identifier'] = re.sub(r'(?<=[a-z])-(?=[0-9]+(?:-|$))', '', values['identifier'])
        return profile.format(profile_name, structure, values, 'lower_kebab_case')

    def type_name(self, definition, profile, kind):
        return self.render(definition.logical_name, definition.version, profile, kind)

    def file_stem(self, definition, profile, kind):
        return self.render(definition.logical_name, definition.version, profile, kind)

    def _field(self, source_name, profile, structure, source_convention):
        role = f'algites-{self._technology(profile)}-gen-intf-versioned'
        try:
            return profile.format(role, structure, {'identifier': source_name}, source_convention)
        except ValueError:
            # JSON-Schema system properties such as $schema are legal data keys,
            # but not program-language identifiers; normalize them at this boundary.
            normalized = re.sub(r'[^A-Za-z0-9]+', '-', source_name).strip('-').lower()
            if not normalized or normalized[0].isdigit():
                normalized = 'field-' + normalized
            return profile.format(role, structure, {'identifier': normalized}, 'lower_kebab_case')

    def property_name(self, source_name, profile):
        return self._field(source_name, profile, 'field_name', 'upper_camel_case')

    def enum_constant(self, source_name, profile):
        return self._field(source_name, profile, 'enum_item_name', 'lower_snake_case')

    def schema_field_name_constant(self, source_name, profile):
        name = self._field(source_name, profile, 'constant_name', 'upper_camel_case')
        return 'SCHEMA_FIELD_NAME__' + (re.sub(r'_+', '_', re.sub(r'[^A-Za-z0-9_]', '_', name)).strip('_') or 'FIELD')

    def reference_type(self, ref, profile):
        kind = AInDefsNameRole.ENUM_TYPE if ref.target_kind is AInDefinitionKind.ENUM else AInDefsNameRole.DATA_TYPE
        return self.render(ref.logical_name, ref.version, profile, kind)
