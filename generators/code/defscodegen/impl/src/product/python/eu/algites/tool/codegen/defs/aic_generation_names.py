from __future__ import annotations

import re

from eu.algites.lib.naming.conversion.aic_default_name_converter import AIcDefaultNameConverter
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.lib.naming.convention.ain_input_name_kind import AInInputNameKind
from eu.algites.lib.naming.convention.ain_output_name_kind import AInOutputNameKind

class AIcGenerationNames:
    """Provides generation names functionality."""
    def __init__(self):
        """Initialize this service instance."""
        self.converter = AIcDefaultNameConverter()

    def render(self, logical_name, version, profile, kind):
        """Render normalized word tokens using a target naming convention."""
        rule = profile.output_rules[kind]
        converted = self.converter.convert(logical_name, profile.input_conventions[AInInputNameKind.DEFINITION], rule.convention)
        return f"{rule.prefix}{rule.type_marker}{converted}{rule.suffix}{self.converter.render_version(version, profile.output_version_policy)}"

    def type_name(self, definition, profile, kind):
        """Render a generated program type name."""
        return self.render(definition.logical_name, definition.version, profile, kind)

    def file_stem(self, definition, profile, kind):
        """Render a generated source-file stem."""
        return self.render(definition.logical_name, definition.version, profile, kind)

    def property_name(self, source_name, profile):
        """Render a generated property name."""
        rule = profile.output_rules[AInOutputNameKind.PROPERTY]
        return f"{rule.prefix}{rule.type_marker}{self.converter.convert(source_name, profile.input_conventions[AInInputNameKind.PROPERTY], rule.convention)}{rule.suffix}"

    def enum_constant(self, source_name, profile):
        """Render a generated enum constant name."""
        rule = profile.output_rules[AInOutputNameKind.ENUM_CONSTANT]
        return f"{rule.prefix}{rule.type_marker}{self.converter.convert(source_name, profile.input_conventions[AInInputNameKind.ENUM_VALUE], rule.convention)}{rule.suffix}"

    def schema_field_name_constant(self, source_name, profile):
        """Render the stable generated constant that exposes one canonical schema field name."""
        rule = profile.output_rules[AInOutputNameKind.ENUM_CONSTANT]
        converted = self.converter.convert(source_name, profile.input_conventions[AInInputNameKind.PROPERTY], rule.convention)
        identifier = re.sub(r'_+', '_', re.sub(r'[^A-Za-z0-9_]', '_', converted)).strip('_') or 'FIELD'
        return f"SCHEMA_FIELD_NAME__{identifier}"

    def reference_type(self, ref, profile):
        """Render the generated type name of a referenced canonical definition."""
        kind = AInOutputNameKind.ENUM_TYPE if ref.target_kind is AInDefinitionKind.ENUM else AInOutputNameKind.DATA_TYPE
        return self.render(ref.logical_name, ref.version, profile, kind)
