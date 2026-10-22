from __future__ import annotations
from eu.algites.tool.codegen.defs.impl.standard._source_data_type import from_source_hints
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.impl.standard._schema_loading import load_schema

import json
import re
import os
import yaml
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlsplit
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.impl.standard.aic_definition_identity_resolver import AIcDefinitionIdentityResolver
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_definition_reference import AIcdDefinitionReference
from eu.algites.tool.codegen.defs.aicd_enum_value_definition import AIcdEnumValueDefinition
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.impl.standard._support import _strip_extensions
from eu.algites.tool.codegen.defs.impl.standard._support import _value_kind
from eu.algites.tool.codegen.defs.impl.standard.aic_scalar_constraints import from_json
from eu.algites.tool.codegen.defs.impl.standard._json_nullability import _accepts_null, _non_null_kind
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType

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
        identity = str(root.get("x-algites-schema-id") or root.get(id_extension) or root.get("$id") or parsed.logical_name)
        version = explicit_version if explicit_version is not None else parsed.version
        description = root.get("description") if isinstance(root.get("description"), str) else None
        title = root.get("title") if isinstance(root.get("title"), str) else None
        root = self._structural(root, request, set())
        enum_values = self._enum_values(root)
        if enum_values:
            return AIcdCanonicalDefinition(identity, version, logical_name, source_kind, str(request.path), description, AIcdDataType(AInDataTypeKind.ENUM), enum_values, title)
        properties = root.get("properties")
        if root.get("type") == "object" or isinstance(properties, Mapping):
            required = set(root.get("required", ()))
            result = tuple(self._property(name, schema, name in required, request) for name, schema in (properties or {}).items())
            return AIcdCanonicalDefinition(identity, version, logical_name, source_kind, str(request.path), description, self._recursive_type(root, request), (), title)
        return AIcdCanonicalDefinition(identity, version, logical_name, source_kind, str(request.path), description, self._recursive_type(root, request), (), title)

    def _property(self, name, schema, required, request, visited=None):
        """Normalize one source property definition."""
        if not isinstance(schema, Mapping):
            return AIcdPropertyDefinition(str(name), from_source_hints(AInDataTypeKind.ANY, None, None, AIcdValueConstraints(), AIcdValueConstraints()), (AInFieldPresenceKind.REQUIRED if required else AInFieldPresenceKind.ALLOWED), False, None, None, None)
        raw_type = schema.get("type")
        nullable = _accepts_null(schema)
        if isinstance(raw_type, list):
            values = [value for value in raw_type if value != "null"]
            raw_type = values[0] if values else None
        if isinstance(schema.get("$ref"), str):
            ref = schema["$ref"]
            resource = ref.split("#", 1)[0]
            fragment = unquote(urlsplit(ref).fragment)
            if fragment:
                target_path = self._reference_path(resource, request)
                document = load_schema(target_path)
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
                # Named $defs objects/choices are nominal, even when a child
                # property refers to the containing definition recursively.
                canonical_type = self._recursive_type(schema, request, visited)
                if canonical_type.kind is AInDataTypeKind.REFERENCE:
                    return AIcdPropertyDefinition(str(name), canonical_type,
                        AInFieldPresenceKind.REQUIRED if required else AInFieldPresenceKind.ALLOWED,
                        nullable and _accepts_null(referenced),
                        schema.get('description', referenced.get('description')),
                        schema.get('title', referenced.get('title')), None)
                reference_key = (target_path.resolve(), fragment)
                if reference_key in visited:
                    raise ValueError(f"Circular schema alias '{ref}' in {request.path}")
                visited.add(reference_key)
                try:
                    if "allOf" in referenced:
                        referenced = self._structural(referenced, AIcdDefinitionLoadRequest(target_path, request.source_kind, request.naming_profile), set())
                    normalized = self._property(name, referenced, required,
                        AIcdDefinitionLoadRequest(target_path, request.source_kind, request.naming_profile), visited)
                    return AIcdPropertyDefinition(str(name), normalized.data_type,
                        AInFieldPresenceKind.REQUIRED if required else AInFieldPresenceKind.ALLOWED,
                        nullable and normalized.nullable, schema.get('description', normalized.description),
                        schema.get('title', normalized.title), None)
                finally:
                    visited.remove(reference_key)
            target_path = self._reference_path(resource, request)
            parsed = AIcDefinitionIdentityResolver.parse_versioned_stem(_strip_extensions(target_path.name), None)
            target_kind = self._detect_referenced_kind(target_path)
            nullable = nullable and _accepts_null(load_schema(target_path))
            return AIcdPropertyDefinition(str(name), from_source_hints(AInDataTypeKind.REFERENCE, None, AIcdDefinitionReference(ref, parsed.version, parsed.logical_name, AIcdDataType(target_kind) if target_kind else None), AIcdValueConstraints(), AIcdValueConstraints()), (AInFieldPresenceKind.REQUIRED if required else AInFieldPresenceKind.ALLOWED), nullable, schema.get("description"), schema.get("title"), None)
        if raw_type is None and (self._enum_values(schema) or "const" in schema):
            kind = _non_null_kind(schema)
        else:
            kind = _value_kind(raw_type)
        return AIcdPropertyDefinition(str(name), self._recursive_type(schema, request, visited), (AInFieldPresenceKind.REQUIRED if required else AInFieldPresenceKind.ALLOWED), nullable, schema.get('description'), schema.get("title"), None)

    @staticmethod
    def _presence_any_of_as_min_properties(schema):
        """Recognize only the exact at-least-one-property assertion for a closed object.

        In particular, do not discard arbitrary anyOf validation predicates.
        """
        if schema.get('additionalProperties') is not False:
            return False
        properties = schema.get('properties')
        branches = schema.get('anyOf')
        if not isinstance(properties, Mapping) or not properties or not isinstance(branches, list) or not branches:
            return False
        referenced = []
        for branch in branches:
            if (not isinstance(branch, Mapping) or set(branch) - {'required', 'description', 'title', '$comment'}
                    or not isinstance(branch.get('required'), list) or len(branch['required']) != 1
                    or not isinstance(branch['required'][0], str)):
                return False
            referenced.append(branch['required'][0])
        return set(referenced) == set(properties)

    @staticmethod
    def _local_definition_kind(schema):
        """Classify a named local definition without falsely assuming it is an object."""
        if 'enum' in schema:
            return AInDataTypeKind.ENUM
        if 'oneOf' in schema:
            return AInDataTypeKind.ONE_OF
        if 'anyOf' in schema and not AIcJsonSchemaReader._presence_any_of_as_min_properties(schema):
            return AInDataTypeKind.ANY_OF
        if schema.get('type') == 'object' or 'properties' in schema:
            return AInDataTypeKind.OBJECT
        declared = schema.get('type')
        if isinstance(declared, list):
            non_null = [member for member in declared if member != 'null']
            declared = non_null[0] if len(non_null) == 1 else None
        return _value_kind(declared)

    def _recursive_type(self, schema, request, visited=None):
        """Recursively project arrays, inline objects and exclusive/inclusive choices.

        References deliberately remain reference nodes: they do not recursively inline
        external schemas and thus preserve identity and permit graph cycles.
        """
        if not isinstance(schema, Mapping):
            return AIcdDataType(AInDataTypeKind.ANY)
        visited = set() if visited is None else visited
        # A typed enum can use oneOf solely to document individual const values.
        # Only collapse such a presentation when every alternative is exactly one
        # listed scalar enum member and imposes no additional schema semantics.
        branches = schema.get('oneOf')
        values = schema.get('enum')
        if (isinstance(branches, list) and isinstance(values, list) and values
                and schema.get('type') in ('string', 'integer', 'number', 'boolean')
                and len(branches) == len(values)
                and all(isinstance(branch, Mapping) and 'const' in branch
                        and set(branch).issubset({'const', 'title', 'description'})
                        for branch in branches)
                and len({self._wire_value(branch['const']) for branch in branches}) == len(branches)
                and {self._wire_value(branch['const']) for branch in branches}
                    == {self._wire_value(value) for value in values}):
            kind = _value_kind(schema['type'])
            return AIcdDataType(kind, constraints=from_json(schema, kind))
        if self._presence_any_of_as_min_properties(schema):
            schema = {**schema, 'minProperties': max(1, schema.get('minProperties', 0))}
            schema.pop('anyOf', None)
        for keyword, kind in (('oneOf', AInDataTypeKind.ONE_OF),
                              ('anyOf', AInDataTypeKind.ANY_OF)):
            branches = schema.get(keyword)
            if isinstance(branches, list) and branches:
                return AIcdDataType.choice(kind,
                    (self._recursive_type(branch, request, visited) for branch in branches))
        if '$ref' in schema:
            # References to emitted named objects/enums remain nominal. Expanding
            # them inline would lose their identity and produce nonexistent branch contracts.
            ref = str(schema['$ref'])
            resource, _, fragment = ref.partition('#')
            if not fragment:
                return self._property('reference', schema, False, request).data_type
            target_path = self._reference_path(resource, request)
            target = load_schema(target_path)
            unescaped = unquote(fragment)
            if unescaped.startswith('/'):
                tokens = [token.replace('~1', '/').replace('~0', '~') for token in unescaped[1:].split('/')]
                resolved = target
                try:
                    for token in tokens:
                        resolved = resolved[int(token)] if isinstance(resolved, list) else resolved[token]
                except (KeyError, IndexError, TypeError, ValueError) as error:
                    raise ValueError(f"Undefined schema reference '{ref}' in {request.path}") from error
            else:
                tokens = []
                resolved = self._anchor(target, unescaped)
            named = (len(tokens) == 2 and tokens[0] in ('$defs', 'definitions')
                     and isinstance(resolved, Mapping)
                     and ('properties' in resolved or resolved.get('type') == 'object'
                          or 'enum' in resolved or 'oneOf' in resolved or 'anyOf' in resolved))
            key = (target_path.resolve(), unescaped)
            entered = key not in visited
            if named:
                stem = AIcDefinitionIdentityResolver.parse_versioned_stem(_strip_extensions(target_path.name), None)
                kebab = re.sub(r'[^a-z0-9]+', '-', re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', tokens[1]).lower()).strip('-')
                kind = self._local_definition_kind(resolved)
                if not entered:
                    target_type = None
                elif kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
                    visited.add(key)
                    try:
                        target_type = self._recursive_type(resolved, AIcdDefinitionLoadRequest(
                            target_path, request.source_kind, request.naming_profile), visited)
                    finally:
                        visited.remove(key)
                else:
                    target_type = AIcdDataType(kind)
                return AIcdDataType(AInDataTypeKind.REFERENCE, reference=AIcdDefinitionReference(
                    ref, stem.version, stem.logical_name + '-definition-' + kebab, target_type))
            if not entered:
                raise ValueError(f"Circular inline schema alias '{ref}' in {request.path}")
            visited.add(key)
            try:
                return self._recursive_type(resolved, AIcdDefinitionLoadRequest(target_path,
                    request.source_kind, request.naming_profile), visited)
            finally:
                visited.remove(key)
        raw = schema.get('type')
        if isinstance(raw, list):
            raw = next((kind for kind in raw if kind != 'null'), None)
        if raw == 'array' or 'items' in schema:
            return AIcdDataType(AInDataTypeKind.ARRAY,
                element_type=self._recursive_type(schema.get('items', {}), request, visited),
                constraints=from_json(schema, AInDataTypeKind.ARRAY))
        if raw == 'object' or 'properties' in schema:
            fields = schema.get('properties', {})
            required = set(schema.get('required', ()))
            return AIcdDataType(AInDataTypeKind.OBJECT,
                properties=tuple(self._property(name, node, name in required, request, visited)
                                 for name, node in (fields if isinstance(fields, Mapping) else {}).items()),
                constraints=from_json(schema, AInDataTypeKind.OBJECT))
        if 'enum' in schema or 'const' in schema:
            value_kind = _value_kind(raw) if raw else _non_null_kind(schema)
            return AIcdDataType(value_kind, constraints=from_json(schema, _non_null_kind(schema)))
        kind = _value_kind(raw)
        name = kind.value if kind.value in AInDataTypeKind.__members__ else 'ANY'
        return AIcdDataType(AInDataTypeKind[name], constraints=from_json(schema, kind))

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
                suffix = f'/src/product/{source_kind}/{relative}'
                matches = [path for path in AIcJsonSchemaReader._canonical_reference_files(ancestor) if path.as_posix().endswith(suffix)]
                if len(matches) == 1:
                    return matches[0]
                if len(matches) > 1:
                    raise ValueError(f"Ambiguous local schema reference '{resource}'.")
                break
        for ancestor in request.path.resolve().parents:
            definitions = ancestor.name in ('yamldefs', 'jsondefs')
            repository = (ancestor / 'modustro-source-repository.yml').is_file()
            if not definitions and not repository: continue
            matches = []
            for path in AIcJsonSchemaReader._canonical_reference_files(ancestor):
                if not path.is_file() or not (path.name.endswith('.schema.json') or path.suffix in ('.yaml','.yml')): continue
                if repository and '/src/product/' not in path.as_posix(): continue
                document = load_schema(path)
                if isinstance(document, Mapping) and resource in (document.get('$id'),document.get('x-yamldefs-id'),document.get('x-jsondefs-id')):
                    matches.append(path)
            if len(matches) == 1: return matches[0]
            if len(matches) > 1: raise ValueError(f"Ambiguous local schema identity '{resource}'.")
            if repository: break
        raise ValueError(f"Schema reference '{resource}' has no local canonical definition for {request.path}")

    @staticmethod
    def _canonical_reference_files(root):
        """Walk owned roots, excluding transient/generated copies while retaining source build directories."""
        repository = (root / 'modustro-source-repository.yml').is_file()
        for directory, children, files in os.walk(root):
            parent = Path(directory)
            artifact = (parent / 'modustro-artifact.yml').is_file()
            children[:] = [name for name in children if not (name.startswith('.') or name == '__pycache__'
                or name.endswith(('.gen', '.extgen'))
                or (repository and name in ('build', 'run') and (parent == root or artifact)))]
            for name in files:
                path = parent / name
                if path.is_file():
                    yield path

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
            document = load_schema(target)
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
            branch_properties = branch.get("properties", {})
            if not isinstance(branch_properties, Mapping):
                raise ValueError(f'allOf properties must be a schema object in {request.path}')
            for name, schema in branch_properties.items():
                if name in properties and properties[name] != schema:
                    raise ValueError(f"Conflicting allOf property schema {name!r} in {request.path}")
                properties[name] = schema
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
        titles: dict[str, str | None] = {}
        one_of_values: list[AIcdEnumValueDefinition] = []
        one_of = root.get("oneOf")
        if isinstance(one_of, list):
            for branch in one_of:
                if not isinstance(branch, Mapping) or "const" not in branch or isinstance(branch.get("const"), (dict, list)):
                    continue
                value = AIcJsonSchemaReader._wire_value(branch.get("const"))
                description = branch.get("description") if isinstance(branch.get("description"), str) else None
                descriptions[value] = description
                titles[value] = branch.get("title") if isinstance(branch.get("title"), str) else None
                one_of_values.append(AIcdEnumValueDefinition(value, description, titles[value]))
        enum_values = root.get("enum")
        if isinstance(enum_values, list):
            return tuple(AIcdEnumValueDefinition(AIcJsonSchemaReader._wire_value(value), descriptions.get(AIcJsonSchemaReader._wire_value(value)), titles.get(AIcJsonSchemaReader._wire_value(value)))
                         for value in enum_values if value is not None)
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
    def _detect_referenced_kind(path: Path) -> AInDataTypeKind | None:
        """Determine whether a referenced canonical definition is an enum or data object."""
        if not path.is_file():
            return None
        try:
            if path.suffix.lower() in (".yaml", ".yml"):
                root = load_schema(path)
            else:
                root = load_schema(path)
        except (OSError, ValueError, yaml.YAMLError):
            return None
        if not isinstance(root, Mapping):
            return None
        if AIcJsonSchemaReader._enum_values(root):
            return AInDataTypeKind.ENUM
        if (root.get("type") == "object" or isinstance(root.get("properties"), Mapping)
                or 'oneOf' in root or 'anyOf' in root):
            return AInDataTypeKind.OBJECT
        return AInDataTypeKind.ANY
