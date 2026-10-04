from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlsplit
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
        root = self._structural(root, request, set())
        enum_values = self._enum_values(root)
        if enum_values:
            return AIcdCanonicalDefinition(identity, version, logical_name, AInDefinitionKind.ENUM, source_kind, str(request.path), description, (), enum_values)
        properties = root.get("properties")
        if root.get("type") == "object" or isinstance(properties, Mapping):
            required = set(root.get("required", ()))
            result = tuple(self._property(name, schema, name in required, request) for name, schema in (properties or {}).items())
            return AIcdCanonicalDefinition(identity, version, logical_name, AInDefinitionKind.OBJECT, source_kind, str(request.path), description, result, ())
        return AIcdCanonicalDefinition(identity, version, logical_name, AInDefinitionKind.SCALAR, source_kind, str(request.path), description)

    def _property(self, name, schema, required, request, visited=None):
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
            fragment = unquote(urlsplit(ref).fragment)
            if fragment:
                target_path = self._reference_path(resource, request)
                document = yaml.safe_load(target_path.read_text(encoding="utf-8"))
                if fragment.startswith("/"):
                    referenced = document
                    for token in fragment[1:].split("/"):
                        key = token.replace("~1", "/").replace("~0", "~")
                        try:
                            referenced = referenced[int(key)] if isinstance(referenced, list) else referenced[key]
                        except (KeyError, IndexError, TypeError, ValueError) as ex:
                            raise ValueError(f"Undefined schema reference '{ref}' in {request.path}") from ex
                else:
                    referenced = self._anchor(document, fragment)
                if not isinstance(referenced, Mapping):
                    raise ValueError(f"Undefined schema reference '{ref}' in {request.path}")
                visited = set() if visited is None else visited
                reference_key = (target_path, fragment)
                if reference_key in visited:
                    raise ValueError(f"Circular schema reference '{ref}' in {request.path}")
                visited.add(reference_key)
                if "allOf" in referenced:
                    referenced = self._structural(referenced, AIcdDefinitionLoadRequest(target_path, request.source_kind, request.naming_profile), set())
                normalized = self._property(name, referenced, required,
                    AIcdDefinitionLoadRequest(target_path, request.source_kind, request.naming_profile), visited)
                return AIcdPropertyDefinition(str(name), normalized.value_kind, required, nullable or normalized.nullable,
                    normalized.item_value_kind, normalized.reference,
                    schema.get("description", normalized.description))
            parsed = AIcDefaultNameConverter().parse_versioned_name(
                _strip_extensions(Path(resource).name),
                None,
                AIcdInputVersionPolicy(AInVersionSource.FILE_NAME_SUFFIX, "_", True, False),
            )
            target_path = self._reference_path(resource, request)
            target_kind = self._detect_referenced_kind(target_path)
            return AIcdPropertyDefinition(
                str(name),
                AInValueKind.REFERENCE,
                required,
                nullable,
                reference=AIcdDefinitionReference(ref, parsed.version, parsed.logical_name, target_kind),
                description=schema.get("description"),
            )
        if raw_type is None and isinstance(schema.get("enum"), list) and all(isinstance(value, str) for value in schema["enum"]):
            kind = AInValueKind.STRING
        else:
            kind = _value_kind(raw_type)
        item_kind = _value_kind(schema.get("items", {}).get("type")) if kind is AInValueKind.ARRAY and isinstance(schema.get("items"), Mapping) else None
        return AIcdPropertyDefinition(str(name), kind, required, nullable, item_kind, description=schema.get("description"))

    @staticmethod
    def _reference_path(resource, request):
        """Map canonical schema URLs to checked-out definition roots without downloading them."""
        if not resource:
            return request.path
        uri = urlsplit(resource)
        if not uri.scheme:
            return (request.path.parent / unquote(resource)).resolve()
        if uri.scheme == "file":
            return Path(unquote(uri.path))
        for source_kind in ("yamldefs", "jsondefs"):
            marker = f"/{source_kind}/"
            if marker not in uri.path:
                continue
            relative = uri.path.split(marker, 1)[1]
            for ancestor in request.path.resolve().parents:
                candidate = (ancestor / relative).resolve()
                if ancestor.name == source_kind and candidate.is_relative_to(ancestor) and candidate.is_file():
                    return candidate
            for ancestor in request.path.resolve().parents:
                if not (ancestor / "modustro-source-repository.yml").is_file():
                    continue
                matches = list(ancestor.glob(f"**/src/product/{source_kind}/{relative}"))
                if len(matches) == 1:
                    return matches[0]
                if len(matches) > 1:
                    raise ValueError(f"Ambiguous local schema reference '{resource}'.")
                break
        raise ValueError(f"Schema reference '{resource}' has no local canonical definition for {request.path}")

    def _structural(self, node, request, visited):
        """Extract object properties and required fields from allOf and referenced roots."""
        result = dict(node)
        branches = []
        ref = node.get("$ref")
        if isinstance(ref, str):
            uri = urlsplit(ref)
            resource = ref.split("#", 1)[0]
            target = self._reference_path(resource, request)
            fragment = unquote(uri.fragment)
            key = (target.resolve(), fragment)
            if key in visited:
                raise ValueError(f"Circular schema composition '{ref}' in {request.path}")
            visited.add(key)
            document = yaml.safe_load(target.read_text(encoding="utf-8"))
            referenced = document
            if fragment.startswith("/"):
                try:
                    for token in fragment[1:].split("/"):
                        key_part = token.replace("~1", "/").replace("~0", "~")
                        referenced = referenced[int(key_part)] if isinstance(referenced, list) else referenced[key_part]
                except (KeyError, IndexError, ValueError, TypeError) as ex:
                    raise ValueError(f"Undefined schema reference '{ref}' in {request.path}") from ex
            elif fragment:
                referenced = self._anchor(document, fragment)
            if not isinstance(referenced, Mapping):
                raise ValueError(f"Undefined schema reference '{ref}' in {request.path}")
            branches.append(self._structural(referenced, AIcdDefinitionLoadRequest(target, request.source_kind, request.naming_profile), visited))
            visited.remove(key)
        branches.extend(self._structural(branch, request, visited) for branch in node.get("allOf", ()))
        branches.append(node)
        properties, required = {}, set()
        for branch in branches:
            properties.update(branch.get("properties", {}))
            required.update(branch.get("required", ()))
            if "type" in branch and "type" not in result:
                result["type"] = branch["type"]
        if properties:
            result["properties"] = properties
        if required:
            result["required"] = sorted(required)
        return result

    @staticmethod
    def _anchor(node, name):
        """Find a named schema anchor within the referenced document."""
        if isinstance(node, Mapping):
            if node.get("$anchor") == name:
                return node
            for value in node.values():
                match = AIcJsonSchemaReader._anchor(value, name)
                if match is not None:
                    return match
        elif isinstance(node, list):
            for value in node:
                match = AIcJsonSchemaReader._anchor(value, name)
                if match is not None:
                    return match
        return None

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
