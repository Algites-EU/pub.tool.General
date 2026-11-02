from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
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
from eu.algites.tool.codegen.defs.aicd_key_definition import AIcdKeyDefinition

class AIcJsonSchemaReader:
    """Provides json schema reader functionality."""
    def __init__(self) -> None:
        """Initialize this service instance."""
        self.identities = AIcDefinitionIdentityResolver()

    def read(self, root: Mapping[str, Any], request: AIcdDefinitionLoadRequest, source_kind, id_extension, version_extension, name_extension, url_extension=""):
        """Read a JSON-Schema-shaped definition into the normalized canonical model."""
        explicit_version = root.get(version_extension) if isinstance(root.get(version_extension), int) else None
        parsed = self.identities.from_file(request, explicit_version)
        logical_name = str(root.get(name_extension) or parsed.logical_name)
        # JSON Schema $id is a resource URI, not a logical schema identifier.
        identity = str(root.get(id_extension) or parsed.logical_name)
        version = explicit_version if explicit_version is not None else parsed.version
        schema_url = str(root.get(url_extension) or "") if url_extension else ""
        description = root.get("description") if isinstance(root.get("description"), str) else None
        title = root.get("title") if isinstance(root.get("title"), str) else None
        root = dict(root)
        self._validate_choice_placements(root)
        enum_values = self._enum_values(root)
        if enum_values:
            return AIcdCanonicalDefinition(identity, version, logical_name, source_kind, str(request.path), description, AIcdDataType(AInDataTypeKind.ENUM), enum_values, title, schema_url)
        properties = root.get("properties")
        if root.get("type") == "object" or isinstance(properties, Mapping):
            required = set(root.get("required", ()))
            result = tuple(self._property(name, schema, name in required, request) for name, schema in (properties or {}).items())
            return AIcdCanonicalDefinition(identity, version, logical_name, source_kind, str(request.path), description, self._recursive_type(root, request), (), title, schema_url)
        return AIcdCanonicalDefinition(identity, version, logical_name, source_kind, str(request.path), description, self._recursive_type(root, request), (), title, schema_url)

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
                            raise AIxCodegenValidationException(f"Undefined schema reference '{ref}' in {request.path}", 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.') from ex
                else:
                    referenced = self._anchor(document, fragment)
                if not isinstance(referenced, Mapping):
                    raise AIxCodegenValidationException(f"Undefined schema reference '{ref}' in {request.path}", 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
                visited = set() if visited is None else visited
                # Named $defs objects/choices are nominal, even when a child
                # property refers to the containing definition recursively.
                canonical_type = self._recursive_type(schema, request, visited)
                # A single-reference allOf wrapper (typically a named anchor)
                # projects to its nominal contract, not an ungenerated inline type.
                aliases = referenced.get('allOf')
                if (canonical_type.kind is not AInDataTypeKind.REFERENCE
                        and isinstance(aliases, list) and len(aliases) == 1
                        and isinstance(aliases[0], Mapping) and '$ref' in aliases[0]
                        and 'properties' not in referenced and 'type' not in referenced):
                    canonical_type = self._recursive_type(aliases[0],
                        AIcdDefinitionLoadRequest(target_path, request.source_kind,
                            request.naming_profile, request.source_naming_profile), visited)
                if canonical_type.kind is AInDataTypeKind.REFERENCE:
                    return AIcdPropertyDefinition(str(name), canonical_type,
                        AInFieldPresenceKind.REQUIRED if required else AInFieldPresenceKind.ALLOWED,
                        nullable and _accepts_null(referenced),
                        schema.get('description', referenced.get('description')),
                        schema.get('title', referenced.get('title')), None)
                reference_key = (target_path.resolve(), fragment)
                if reference_key in visited:
                    raise AIxCodegenValidationException(f"Circular schema alias '{ref}' in {request.path}", 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
                visited.add(reference_key)
                try:
                    normalized = self._property(name, referenced, required,
                        AIcdDefinitionLoadRequest(target_path, request.source_kind, request.naming_profile, request.source_naming_profile), visited)
                    return AIcdPropertyDefinition(str(name), normalized.data_type,
                        AInFieldPresenceKind.REQUIRED if required else AInFieldPresenceKind.ALLOWED,
                        nullable and normalized.nullable, schema.get('description', normalized.description),
                        schema.get('title', normalized.title), None)
                finally:
                    visited.remove(reference_key)
            target_path = self._reference_path(resource, request)
            parsed = self.identities.from_file(AIcdDefinitionLoadRequest(target_path, request.source_kind, request.naming_profile), None)
            target_kind = self._detect_referenced_kind(target_path)
            nullable = nullable and _accepts_null(load_schema(target_path))
            return AIcdPropertyDefinition(str(name), from_source_hints(AInDataTypeKind.REFERENCE, None, AIcdDefinitionReference(ref, parsed.version, parsed.logical_name, AIcdDataType(target_kind) if target_kind else None), AIcdValueConstraints(), AIcdValueConstraints()), (AInFieldPresenceKind.REQUIRED if required else AInFieldPresenceKind.ALLOWED), nullable, schema.get("description"), schema.get("title"), None)
        if raw_type is None and (self._enum_values(schema) or "const" in schema):
            kind = _non_null_kind(schema)
        else:
            kind = _value_kind(raw_type)
        return AIcdPropertyDefinition(str(name), self._recursive_type(schema, request, visited), (AInFieldPresenceKind.REQUIRED if required else AInFieldPresenceKind.ALLOWED), nullable, schema.get('description'), schema.get("title"), None)

    @staticmethod
    def _local_definition_kind(schema):
        """Classify a named local definition without falsely assuming it is an object."""
        if 'enum' in schema:
            return AInDataTypeKind.ENUM
        if 'x-algites-defscodegen-choice' in schema:
            return AInDataTypeKind.ONE_OF
        if schema.get('type') == 'object' or 'properties' in schema or 'additionalProperties' in schema:
            return AInDataTypeKind.OBJECT
        declared = schema.get('type')
        if isinstance(declared, list):
            non_null = [member for member in declared if member != 'null']
            declared = non_null[0] if len(non_null) == 1 else None
        return _value_kind(declared)

    @staticmethod
    def _validate_choice_shape(schema):
        """Require a named-property choice with standard, portable JSON validation.

        Args:
            schema: Schema node declaring the Algites exclusive-choice marker.

        Raises:
            AIxCodegenValidationException: If the marker or standard constraints
                disagree with the exactly-one-property choice representation.
        """
        variants = schema.get('properties')
        valid = (schema.get('x-algites-defscodegen-choice') is True
                 and schema.get('type') == 'object'
                 and isinstance(variants, Mapping) and len(variants) >= 2
                 and all(isinstance(name, str) and isinstance(value, Mapping)
                         for name, value in variants.items())
                 and type(schema.get('minProperties')) is int
                 and schema['minProperties'] == 1
                 and type(schema.get('maxProperties')) is int
                 and schema['maxProperties'] == 1
                 and schema.get('additionalProperties') is False
                 and not schema.get('patternProperties')
                 and not schema.get('required'))
        if not valid:
            raise AIxCodegenValidationException(
                'Invalid x-algites-defscodegen-choice: expected true, object with at least two '
                'properties, minProperties=1, maxProperties=1, additionalProperties=false',
                'Declare variants in sibling properties and use standard JSON constraints '
                'for exactly one property. Do not use the removed alternatives array.')

    @classmethod
    def _validate_choice_placements(cls, root):
        """Reject new structural types declared inside validation-only branches.

        Args:
            root: The complete JSONDEFS or YAMLDEFS source schema.

        Raises:
            AIxCodegenValidationException: If a choice occurs within a
                validation-only subschema or has an invalid local shape.
        """
        validation_keywords = {'oneOf', 'anyOf', 'allOf', 'not', 'if', 'then',
                               'else', 'contains', 'dependentSchemas',
                               'propertyNames', 'dependencies'}
        def visit(node, blocked=False, path='#'):
            if isinstance(node, list):
                for index, value in enumerate(node):
                    visit(value, blocked, path + '/' + str(index))
            elif isinstance(node, Mapping):
                if 'x-algites-defscodegen-choice' in node:
                    if blocked:
                        raise AIxCodegenValidationException(
                            'Choice declaration is not allowed inside a validation-only subschema at ' + path,
                            'Place the named choice under $defs, properties, items, prefixItems '
                            'or additionalProperties, then reference it from constraints.')
                    cls._validate_choice_shape(node)
                for key, value in node.items():
                    # Schema maps contain named child schemas: do not treat their
                    # arbitrary property names as schema keywords.
                    if key in ('$defs', 'definitions', 'properties', 'patternProperties'):
                        if isinstance(value, Mapping):
                            for child_name, child_schema in value.items():
                                visit(child_schema, blocked, path + '/' + key + '/' + child_name)
                    elif key in ('dependentSchemas', 'dependencies'):
                        if isinstance(value, Mapping):
                            for child_name, child_schema in value.items():
                                visit(child_schema, True, path + '/' + key + '/' + child_name)
                    elif key in ('additionalProperties', 'items', 'prefixItems', 'additionalItems'):
                        visit(value, blocked, path + '/' + key)
                    elif key in validation_keywords or key in ('unevaluatedItems', 'unevaluatedProperties'):
                        visit(value, True, path + '/' + key)
        visit(root)

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
        if 'x-algites-defscodegen-choice' in schema:
            self._validate_choice_shape(schema)
            # Every branch is a one-property object: the property name is the
            # alternative identity, not merely an anonymous payload datatype.
            # This representation also matches XML xs:choice alternatives.
            return AIcdDataType.choice(AInDataTypeKind.ONE_OF,
                (AIcdDataType(AInDataTypeKind.OBJECT,
                    properties=(self._property(name, variant, True, request, visited),))
                 for name, variant in schema['properties'].items()))
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
                    raise AIxCodegenValidationException(f"Undefined schema reference '{ref}' in {request.path}", 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.') from error
            else:
                tokens = []
                resolved = self._anchor(target, unescaped)
            named = (len(tokens) == 2 and tokens[0] in ('$defs', 'definitions')
                     and isinstance(resolved, Mapping)
                     and ('properties' in resolved or resolved.get('type') == 'object'
                          or 'enum' in resolved or 'x-algites-defscodegen-choice' in resolved))
            key = (target_path.resolve(), unescaped)
            entered = key not in visited
            if named:
                stem = self.identities.from_file(AIcdDefinitionLoadRequest(target_path, request.source_kind, request.naming_profile), None)
                from .aic_declared_type_identity import canonical_type_identifier
                profile = request.source_naming_profile
                if not profile:
                    selected = request.naming_profile.recognize_filename(target_path.name)
                    if selected is None:
                        raise AIxCodegenValidationException(f'No source naming profile matches {target_path}', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
                    profile = selected.convention_name
                kebab = canonical_type_identifier(request.naming_profile, profile, tokens[1])
                kind = self._local_definition_kind(resolved)
                if not entered:
                    target_type = None
                elif kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
                    visited.add(key)
                    try:
                        target_type = self._recursive_type(resolved, AIcdDefinitionLoadRequest(
                            target_path, request.source_kind, request.naming_profile, request.source_naming_profile), visited)
                    finally:
                        visited.remove(key)
                else:
                    target_type = AIcdDataType(kind)
                return AIcdDataType(AInDataTypeKind.REFERENCE, reference=AIcdDefinitionReference(
                    ref, stem.version, kebab, target_type))
            if not entered:
                raise AIxCodegenValidationException(f"Circular inline schema alias '{ref}' in {request.path}", 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
            visited.add(key)
            try:
                return self._recursive_type(resolved, AIcdDefinitionLoadRequest(target_path,
                    request.source_kind, request.naming_profile, request.source_naming_profile), visited)
            finally:
                visited.remove(key)
        raw = schema.get('type')
        if isinstance(raw, list):
            raw = next((kind for kind in raw if kind != 'null'), None)
        if raw == 'array' or 'items' in schema or 'prefixItems' in schema:
            modern = schema.get('prefixItems')
            legacy = schema.get('items') if isinstance(schema.get('items'), list) else None
            if modern is not None and not isinstance(modern, list):
                raise AIxCodegenValidationException('prefixItems must be a sequence of positional schemas', 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
            if modern is not None and legacy is not None:
                raise AIxCodegenValidationException('Conflicting modern and legacy tuple declarations', 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
            slots = modern if modern is not None else legacy
            positional_types = tuple(self._recursive_type(item, request, visited)
                                   for item in (slots or ()))
            remainder = (schema.get('items', {}) if modern is not None
                         else schema.get('additionalItems', {}) if legacy is not None
                         else schema.get('items', {}))
            if remainder is False:
                # Empty remainder still needs a defined canonical ARRAY member;
                # the max-items facet and position_types preserve exact topology.
                remainder = {}
            return AIcdDataType(AInDataTypeKind.ARRAY,
                element_type=self._recursive_type(remainder, request, visited),
                position_types=positional_types,
                constraints=from_json(schema, AInDataTypeKind.ARRAY))
        if raw == 'object' or 'properties' in schema or 'additionalProperties' in schema or 'patternProperties' in schema:
            fields = schema.get('properties', {})
            required = set(schema.get('required', ()))
            dynamic = schema.get('additionalProperties')
            patterned = schema.get('patternProperties', {})
            if patterned and not isinstance(patterned, Mapping):
                raise AIxCodegenValidationException('patternProperties must contain schema-valued patterns', 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
            if patterned:
                # Patterns can overlap and can yield different value contracts.
                # Do not silently turn these heterogeneous properties into ANY.
                raise AIxCodegenValidationException('patternProperties requires explicit pattern-index matching and ' +
                                 'compatible value schemas; current KEYED_VALUES supports additionalProperties', 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
            keyed_type = (self._recursive_type(dynamic, request, visited)
                          if isinstance(dynamic, Mapping) else None)
            keys = (AIcdKeyDefinition('json-property-name', ('_getKey',), unique=True, virtual=True),)
            return AIcdDataType(AInDataTypeKind.OBJECT,
                properties=tuple(self._property(name, node, name in required, request, visited)
                                 for name, node in (fields if isinstance(fields, Mapping) else {}).items()),
                keyed_value_type=keyed_type,
                key_definitions=keys if keyed_type is not None else (),
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
                    raise AIxCodegenValidationException(f"Ambiguous local schema reference '{resource}'.", 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
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
            if len(matches) > 1: raise AIxCodegenValidationException(f"Ambiguous local schema identity '{resource}'.", 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
            if repository: break
        raise AIxCodegenValidationException(f"Schema reference '{resource}' has no local canonical definition for {request.path}", 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')

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
        one_of = root.get("oneOf")
        if isinstance(one_of, list):
            for branch in one_of:
                if not isinstance(branch, Mapping) or "const" not in branch or isinstance(branch.get("const"), (dict, list)):
                    continue
                value = AIcJsonSchemaReader._wire_value(branch.get("const"))
                description = branch.get("description") if isinstance(branch.get("description"), str) else None
                descriptions[value] = description
                titles[value] = branch.get("title") if isinstance(branch.get("title"), str) else None
        enum_values = root.get("enum")
        if isinstance(enum_values, list):
            return tuple(AIcdEnumValueDefinition(AIcJsonSchemaReader._wire_value(value), descriptions.get(AIcJsonSchemaReader._wire_value(value)), titles.get(AIcJsonSchemaReader._wire_value(value)))
                         for value in enum_values if value is not None)
        return ()

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
                or 'x-algites-defscodegen-choice' in root):
            return AInDataTypeKind.OBJECT
        return AInDataTypeKind.ANY
