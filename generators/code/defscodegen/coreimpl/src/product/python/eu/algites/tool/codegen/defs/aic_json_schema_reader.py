from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import Any, Mapping
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.lib.naming.conversion.aic_default_name_converter import AIcDefaultNameConverter
from eu.algites.tool.codegen.defs.aic_definition_identity_resolver import AIcDefinitionIdentityResolver
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_definition_reference import AIcdDefinitionReference
from eu.algites.tool.codegen.defs.aicd_enum_value_definition import AIcdEnumValueDefinition
from eu.algites.lib.naming.convention.aicd_input_version_policy import AIcdInputVersionPolicy
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind
from eu.algites.lib.naming.convention.ain_version_source import AInVersionSource
from eu.algites.tool.codegen.defs._support import _strip_extensions
from eu.algites.tool.codegen.defs._support import _value_kind

class AIcJsonSchemaReader:
    """Provides json schema reader functionality."""
    def __init__(self) -> None:
        """Initialize this service instance."""
        self.identities = AIcDefinitionIdentityResolver()

    def read(self, root: Mapping[str, Any], request: AIcdDefinitionLoadRequest, source_kind, id_extension, version_extension, name_extension):
        """Read a JSON-Schema-shaped definition into the normalized canonical model."""
        explicit_version = root.get(version_extension) if isinstance(root.get(version_extension), int) else None
        parsed = self.identities.from_file(request, explicit_version)
        logical_name = str(root.get(name_extension) or parsed.logical_name)
        identity = str(root.get(id_extension) or root.get("$id") or parsed.logical_name)
        version = explicit_version if explicit_version is not None else parsed.version
        description = root.get("description") if isinstance(root.get("description"), str) else None
        enum_values = self._enum_values(root)
        if enum_values:
            return AIcdCanonicalDefinition(identity, version, logical_name, AInDefinitionKind.ENUM, source_kind, str(request.path), description, (), enum_values)
        properties = root.get("properties")
        if root.get("type") == "object" or isinstance(properties, Mapping):
            required = set(root.get("required", ()))
            result = tuple(self._property(name, schema, name in required, request) for name, schema in (properties or {}).items())
            return AIcdCanonicalDefinition(identity, version, logical_name, AInDefinitionKind.OBJECT, source_kind, str(request.path), description, result, ())
        return AIcdCanonicalDefinition(identity, version, logical_name, AInDefinitionKind.SCALAR, source_kind, str(request.path), description)

    def _property(self, name, schema, required, request):
        """Normalize one source property definition."""
        if not isinstance(schema, Mapping):
            return AIcdPropertyDefinition(str(name), AInValueKind.ANY, required)
        raw_type = schema.get("type")
        nullable = False
        if isinstance(raw_type, list):
            nullable = "null" in raw_type
            values = [value for value in raw_type if value != "null"]
            raw_type = values[0] if len(values) == 1 else None
        if isinstance(schema.get("$ref"), str):
            ref = schema["$ref"]
            resource = ref.split("#", 1)[0]
            parsed = AIcDefaultNameConverter().parse_versioned_name(
                _strip_extensions(Path(resource).name),
                None,
                AIcdInputVersionPolicy(AInVersionSource.FILE_NAME_SUFFIX, "_", True, False),
            )
            target_path = (request.path.parent / resource).resolve() if resource else request.path
            target_kind = self._detect_referenced_kind(target_path)
            return AIcdPropertyDefinition(
                str(name),
                AInValueKind.REFERENCE,
                required,
                nullable,
                reference=AIcdDefinitionReference(ref, parsed.version, parsed.logical_name, target_kind),
                description=schema.get("description"),
            )
        kind = _value_kind(raw_type)
        item_kind = _value_kind(schema.get("items", {}).get("type")) if kind is AInValueKind.ARRAY and isinstance(schema.get("items"), Mapping) else None
        return AIcdPropertyDefinition(str(name), kind, required, nullable, item_kind, description=schema.get("description"))

    @staticmethod
    def _enum_values(root: Mapping[str, Any]) -> tuple[AIcdEnumValueDefinition, ...]:
        """Normalize enum values and per-value descriptions from JSON-Schema-shaped input."""
        descriptions: dict[str, str | None] = {}
        one_of_values: list[AIcdEnumValueDefinition] = []
        one_of = root.get("oneOf")
        if isinstance(one_of, list):
            for branch in one_of:
                if not isinstance(branch, Mapping) or "const" not in branch or isinstance(branch.get("const"), (dict, list)):
                    continue
                value = AIcJsonSchemaReader._wire_value(branch.get("const"))
                description = branch.get("description") if isinstance(branch.get("description"), str) else None
                descriptions[value] = description
                one_of_values.append(AIcdEnumValueDefinition(value, description))
        enum_values = root.get("enum")
        if isinstance(enum_values, list):
            return tuple(AIcdEnumValueDefinition(AIcJsonSchemaReader._wire_value(value), descriptions.get(AIcJsonSchemaReader._wire_value(value))) for value in enum_values)
        return tuple(one_of_values)

    @staticmethod
    def _wire_value(value: Any) -> str:
        """Render one scalar JSON/YAML enum value in the canonical wire-value form."""
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "null"
        return str(value)

    @staticmethod
    def _detect_referenced_kind(path: Path) -> AInDefinitionKind | None:
        """Determine whether a referenced canonical definition is an enum or data object."""
        if not path.is_file():
            return None
        try:
            if path.suffix.lower() in (".yaml", ".yml"):
                root = yaml.safe_load(path.read_text(encoding="utf-8"))
            else:
                root = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, yaml.YAMLError):
            return None
        if not isinstance(root, Mapping):
            return None
        if AIcJsonSchemaReader._enum_values(root):
            return AInDefinitionKind.ENUM
        if root.get("type") == "object" or isinstance(root.get("properties"), Mapping):
            return AInDefinitionKind.OBJECT
        return AInDefinitionKind.SCALAR
