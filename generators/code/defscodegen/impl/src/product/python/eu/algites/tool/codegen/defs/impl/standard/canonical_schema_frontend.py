"""Independent YAMLDEFS/JSONDEFS/XMLDEFS canonical frontend for the next Defs generator.

Input syntax becomes seven canonical node kinds; temporary references use a
resolution state, never another kind. The legacy ``.old`` implementation is
not imported. No XML->MAP mapping or patternProperties support. Local and global
xs:key/xs:unique are supported for direct typed child lists; xs:keyref
remains unsupported.
"""
from __future__ import annotations

from collections.abc import Mapping
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import replace
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET
import warnings
import re

from eu.algites.tool.codegen.common.naming_profiles import AIcdCodegenNamingProfile
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdElement_1 as Element, AIcgdElementList_1 as ElementList,
    AIcgdList_1 as ListNode, AIcgdMap_1 as MapNode,
    AIcgdScalar_1 as Scalar, AIcgdEnum_1 as EnumNode,
    AIcgdEnumValue_1 as EnumValue, AIcgdType_1 as TypeNode,
    AIcgdSourceBinding_1 as Binding,
    AIcgdKeyDefinition_1 as KeyDefinition,
    AIcgdXmlWireName_1 as XmlWire,
    AIngComposition_1 as Composition, AIngMapKind_1 as MapKind,
    AIngResolutionState_1 as Resolution, AIngScalarKind_1 as ScalarKind,
    AIngSourceInputKind_1 as SourceKind, AIngTypeOrigin_1 as Origin,
    AIngElementKind_1 as ElementKind, freeze_bindings)

XS_URI = 'http://www.w3.org/2001/XMLSchema'
XS = '{' + XS_URI + '}'
# Facets of a named key's map value do not change its data storage shape.
# They remain in the input schema and can be validated during marshalling.
INDEXED_VALUE_VALIDATION_FACETS = frozenset({
    'minLength', 'maxLength', 'pattern', 'format', 'minimum', 'maximum',
    'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf', 'minItems',
    'maxItems', 'uniqueItems', 'minProperties', 'maxProperties',
    'enum', 'const', 'required', 'title', 'description', 'examples', 'default',
})

SCALAR_TYPES = {'string': ScalarKind.STRING, 'integer': ScalarKind.INTEGER,
                'number': ScalarKind.NUMBER, 'boolean': ScalarKind.BOOLEAN,
                'null': ScalarKind.NULL}


def _pointer(name: str) -> str:
    """Escape one JSON Pointer segment, preserving the exact property location."""
    return name.replace('~', '~0').replace('/', '~1')


class AIcDefsCodegenCanonicalSchemaFrontend:
    """Constructs canonical immutable nodes with configured synthetic type names."""

    def __init__(self, naming: AIcdCodegenNamingProfile,
                 external_xsd_types: frozenset[str] = frozenset(),
                 external_xsd_documents: Mapping[str, bytes] | None = None):
        if not isinstance(naming, AIcdCodegenNamingProfile):
            raise TypeError('A resolved Common and Defs naming profile is required')
        self.naming = naming
        self.external_xsd_types = external_xsd_types
        self.external_xsd_documents = external_xsd_documents or {}
        # Each nested/synthetic TYPE inherits the version of its own source document.
        # A frontend may process several differently versioned documents in one run.
        self._source_versions: dict[str, str] = {}
        self._external_xsd_complex_types = {}
        for uri, xml in self.external_xsd_documents.items():
            root, scopes = self._parse_xsd_scopes(xml)
            namespace = root.get("targetNamespace", "")
            for declaration in root:
                if declaration.tag == XS + "complexType" and declaration.get("name"):
                    identity = "{" + namespace + "}" + declaration.get("name") if namespace else declaration.get("name")
                    self._external_xsd_complex_types[identity] = (declaration, scopes, namespace, uri)

    @staticmethod
    def _binding(kind, resource, pointer, representation):
        return freeze_bindings({kind: [Binding(resource, pointer, representation)]})

    def _synthetic(self, owner, name, pointer, role, structure, kind, resource, index=None):
        """Synthesize a TYPE before normalization and retain its semantic path."""
        return TypeNode(resource + pointer + '#synthetic:' + role,
            self.naming.synthetic_type_name(role, owner, name, index), Origin.SYNTHETIC,
            (owner, role, name) + (() if index is None else (str(index),)),
            (), structure, Resolution.RESOLVED, self._binding(kind, resource, pointer, role),
            schema_version=self._source_versions.get(resource, ""))

    @staticmethod
    def _validate_choice_placements(schema: Mapping[str, Any]):
        """Keep Algites CHOICE strictly outside JSON Schema validation branches.

        Args:
            schema: The entire JSONDEFS/YAMLDEFS source tree.

        Raises:
            ValueError: A structural CHOICE was declared inside a validation-only
                subschema, where it must never generate storage or inheritance.
        """
        validation = {'oneOf', 'anyOf', 'allOf', 'not', 'if', 'then', 'else',
                      'contains', 'dependentSchemas', 'dependencies', 'propertyNames'}
        def visit(node, blocked=False, path='#'):
            if isinstance(node, Mapping):
                if blocked and 'x-algites-defscodegen-choice' in node:
                    raise ValueError('Structural choice inside validation-only branch at ' + path)
                for name, value in node.items():
                    visit(value, blocked or name in validation, path + '/' + _pointer(str(name)))
            elif isinstance(node, list):
                for index, item in enumerate(node):
                    visit(item, blocked, path + '/' + str(index))
        visit(schema)

    def load_json_or_yaml(self, source: Mapping[str, Any], resource: str, kind: SourceKind,
                          *, root_name: str = "", source_version: str = ""):
        """Return one declared TYPE; JSONDEFS and YAMLDEFS follow identical rules."""
        if kind not in (SourceKind.JSONDEFS, SourceKind.YAMLDEFS):
            raise ValueError('Source family must be JSONDEFS or YAMLDEFS')
        if not isinstance(source, Mapping):
            raise TypeError('Schema must be a mapping')
        self._validate_choice_placements(source)
        self._source_versions[resource] = str(source.get("x-algites-schema-version") or source_version)
        # Direct frontend callers fall back to the source filename, never to `title`.
        # The production CLI supplies root_name from the configured naming profile.
        stem = re.sub(r'_\d+$', '', PurePosixPath(resource).name.split('.')[0])
        inferred = ''.join(token[0].upper() + token[1:] for token in re.split(r'[-_ ]+', stem) if token)
        name = root_name or inferred
        if not name:
            raise ValueError('Cannot derive root name from source filename: ' + resource)
        # The physical JSON/YAML document has no XML element QName. For a
        # deliberately shared cross-format DO, its contract may explicitly
        # match an XML root ELEMENT whose wire name differs from the filename.
        # Without the opt-in, the selected naming profile remains authoritative.
        override = source.get('x-algites-defscodegen-root-type-name')
        if override is not None:
            if not isinstance(override, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', override):
                raise ValueError('Invalid x-algites-defscodegen-root-type-name at #')
            name = override
        identity = str(source.get('x-algites-schema-id') or source.get('$id') or resource)
        inherited = tuple(dict.fromkeys(
            [x['$ref'] for x in source.get('allOf', ())
             if isinstance(x, Mapping) and isinstance(x.get('$ref'), str)] +
            list(source.get('x-algites-defscodegen-extends', ()))))
        node = self._json_node(source, name, '#', kind, resource)
        return TypeNode(identity, name, Origin.DECLARED, (name,),
            inherited, node, Resolution.RESOLVED, self._binding(kind, resource, '#', 'root'),
            schema_version=str(source.get('x-algites-schema-version') or source_version),
            description=str(source.get('description') or ''))

    def load_json_or_yaml_types(self, source: Mapping[str, Any], resource: str,
                                kind: SourceKind, *, root_name: str = "",
                                source_version: str = ""):
        """Load every named $defs declaration plus the optional document root.

        A library schema containing only $defs produces only its named definitions;
        a normal schema produces its root first, followed by ordered declarations.
        No declaration is overwritten by another definition with a similar name.
        """
        if not isinstance(source, Mapping):
            raise TypeError('Schema must be a mapping')
        if kind not in (SourceKind.JSONDEFS, SourceKind.YAMLDEFS):
            raise ValueError('Source family must be JSONDEFS or YAMLDEFS')
        self._validate_choice_placements(source)
        self._source_versions[resource] = str(source.get("x-algites-schema-version") or source_version)
        roots = []
        root_ref = source.get('$ref')
        local_defs = source.get('$defs')
        direct_local_alias = (isinstance(root_ref, str)
                              and root_ref.startswith('#/$defs/')
                              and '/' not in root_ref[len('#/$defs/'):]
                              and isinstance(local_defs, Mapping)
                              and root_ref[len('#/$defs/'):] in local_defs
                              and not any(field in source for field in (
                                  'type', 'properties', 'additionalProperties', 'items',
                                  'prefixItems', 'oneOf', 'anyOf', 'enum', 'const',
                                  'required', 'minItems', 'maxItems', 'allOf', 'not',
                                  'if', 'then', 'else', 'patternProperties', 'contains',
                                  'propertyNames', 'minProperties', 'maxProperties',
                                  'unevaluatedProperties')))
        if not direct_local_alias and (
                any(field in source for field in (
                    'type', 'properties', 'additionalProperties', 'items', 'prefixItems',
                    '$ref', 'oneOf', 'anyOf', 'enum', 'required', 'minItems',
                    'maxItems', 'allOf', 'const'))
                or not ('$defs' in source or 'definitions' in source)):
            roots.append(self.load_json_or_yaml(source, resource, kind,
                root_name=root_name, source_version=source_version))
        for container in ('$defs', 'definitions'):
            definitions = source.get(container, {})
            if not isinstance(definitions, Mapping):
                raise ValueError('Expected named definitions in ' + container)
            for name, definition in definitions.items():
                pointer = '#/' + container + '/' + _pointer(str(name))
                structure = self._json_node(definition, str(name), pointer, kind, resource)
                logical_source_id = str(source.get('x-algites-schema-id') or
                                        source.get('$id') or resource)
                definition_id = (str(definition.get('x-algites-schema-id') or
                                     definition.get('$id'))
                                 if isinstance(definition, Mapping) and
                                 (definition.get('x-algites-schema-id') or definition.get('$id'))
                                 else logical_source_id + pointer)
                inherited = tuple(dict.fromkeys(
                    [part['$ref'] for part in definition.get('allOf', ())
                     if isinstance(part, Mapping) and isinstance(part.get('$ref'), str)] +
                    list(definition.get('x-algites-defscodegen-extends', ()))))
                roots.append(TypeNode(definition_id, str(name),
                    Origin.DECLARED, (str(name),), inherited, structure, Resolution.RESOLVED,
                    self._binding(kind, resource, pointer, container),
                    schema_version=str(definition.get('x-algites-schema-version',
                        source.get('x-algites-schema-version', source_version))),
                    description=str(definition.get('description') or '')))
        return tuple(roots)

    def _json_indexed_map(self, obj, owner, path, kind, resource):
        """Project a homogeneous explicitly keyed JSON/YAML map to an indexed LIST.

        Preserve the JSON object-key wire semantics in the provenance of the
        synthetic fields; only the homogeneous subset is lossless here.
        Per-property overrides need a richer constraint model and are rejected.
        """
        key = obj['x-algites-defscodegen-key']
        if (not isinstance(key, Mapping) or set(key) != {'id', 'field-name'} or
                any(not isinstance(key[name], str) or not key[name].strip()
                    for name in ('id', 'field-name'))):
            raise ValueError('Invalid x-algites-defscodegen-key at ' + path)
        if obj.get('type', 'object') != 'object' or not isinstance(obj.get('additionalProperties'), Mapping):
            raise ValueError('An indexed JSON/YAML map requires object/additionalProperties at ' + path)
        # JSON Schema `properties` describes *values under specific keys*, not
        # the map keys themselves. It is equivalent to `additionalProperties`
        # for those keys only when its full schemas are identical. In that
        # lossless case, do not synthesize separate item types per property.
        # Unequal constraints (including descriptions/annotations) must be
        # preserved by a richer constraint model before we accept them.
        explicit = obj.get('properties', {})
        if not isinstance(explicit, Mapping):
            raise ValueError('Indexed map properties must be an object at ' + path)
        def storage_shape(node):
            if not isinstance(node, Mapping):
                return node
            result = {key: storage_shape(value) for key, value in node.items()
                      if key not in INDEXED_VALUE_VALIDATION_FACETS}
            # A nullable value still has the same scalar storage shape: null
            # is an allowed runtime field state, not a different accessor type.
            declared = result.get('type')
            if (isinstance(declared, list) and len(declared) == 2
                    and 'null' in declared and isinstance(declared[0 if declared[1] == 'null' else 1], str)):
                result['type'] = next(item for item in declared if item != 'null')
            return result
        base_shape = storage_shape(obj['additionalProperties'])
        for name, definition in explicit.items():
            if storage_shape(definition) != base_shape:
                raise NotImplementedError('Indexed map value has a different structural type '
                                          'at ' + path + '/properties/' + _pointer(str(name)))
            if definition != obj['additionalProperties']:
                warnings.warn('Validation-only indexed map key constraints are not enforced '
                              'by generated DataObjects at ' + resource + path
                              + '/properties/' + _pointer(str(name)),
                              UserWarning, stacklevel=2)
        forbidden = set(obj) - {'type', 'additionalProperties', 'propertyNames',
                                'properties', 'x-algites-defscodegen-key',
                                'description', 'title'}
        validation_only = set(INDEXED_VALUE_VALIDATION_FACETS)
        if 'allOf' in forbidden and isinstance(obj['allOf'], list) and all(
                isinstance(part, Mapping) and set(part) <= {'if', 'then', 'else'}
                for part in obj['allOf']):
            validation_only.add('allOf')
        structural = forbidden - validation_only
        if structural:
            raise NotImplementedError('Indexed map structural constraints unsupported at '
                                      + path + ': ' + ', '.join(sorted(structural)))
        if forbidden:
            warnings.warn('Validation-only indexed map constraints are not enforced by '
                          'generated DataObjects at ' + resource + path + ': '
                          + ', '.join(sorted(forbidden)), UserWarning, stacklevel=2)
        key_schema = obj.get('propertyNames', {'type': 'string'})
        if not isinstance(key_schema, Mapping):
            raise ValueError('Indexed map propertyNames must be a schema at ' + path)
        key_path = path + '/propertyNames'
        # JSON object keys are strings. An external propertyNames $ref only
        # restricts which string keys validate; it is not a field type and
        # must not introduce a cross-package data-object dependency. Local
        # references still resolve to typed enums as before.
        external_key_ref = key_schema.get('$ref')
        if isinstance(external_key_ref, str) and external_key_ref.startswith('https://'):
            warnings.warn('Validation-only external propertyNames is not enforced '
                          'by generated DataObjects at ' + resource + key_path + ': '
                          + external_key_ref, UserWarning, stacklevel=2)
            key_type = Scalar(ScalarKind.STRING)
        else:
            key_type = self._json_node(key_schema, owner, key_path, kind, resource)
        if isinstance(key_type, EnumNode):
            # A propertyNames enum is an inline nominal enum, not a generic
            # synthetic object property. Keep XML/JSON/YAML naming symmetric.
            key_type = self._synthetic(owner, key['field-name'], key_path,
                'synthetic_inline_enum_type', key_type, kind, resource)
        if not isinstance(key_type, (Scalar, TypeNode)):
            raise NotImplementedError('Indexed map propertyNames must resolve to a scalar or enum: ' + path)
        val_path = path + '/additionalProperties'
        value_type = self._json_node(obj['additionalProperties'], owner, val_path, kind, resource)
        if isinstance(value_type, ElementList):
            value_type = self._synthetic(owner, 'value', val_path,
                'synthetic_map_value_type', value_type, kind, resource)
        if not isinstance(value_type, (Scalar, TypeNode)):
            raise NotImplementedError('Indexed map values require a scalar or named TYPE at ' + path)
        fields = ElementList(Composition.SEQUENCE, (
            Element(key['field-name'], key_type, min_item_count=1,
                    source_bindings=self._binding(kind, resource, key_path, 'synthetic_map_key')),
            Element('value', value_type, min_item_count=1,
                    source_bindings=self._binding(kind, resource, val_path, 'synthetic_map_value'))))
        # Different keyed properties of one owner need distinct item types.
        # Feed the logical member identifier into the selected naming role
        # rather than reusing the literal 'item' for every indexed collection.
        member = path.rsplit('/', 1)[-1].replace('~1', '/').replace('~0', '~')
        item = self._synthetic(owner, member, path, 'synthetic_list_item_type', fields, kind, resource)
        # Parent properties replace the provisional selector with the actual
        # public field name, so indexed paths resolve without source ambiguity.
        return ListNode(member, item, 0, -1,
            key_definitions=(KeyDefinition(key['id'], member, path + '/x-algites-defscodegen-key',
                                           (key['field-name'],), True),))

    def _json_keyed_array(self, obj, owner, path, kind, resource):
        """Attach a named key to a typed array, not an indexed JSON object map.

        Array keys select a real field on each item; object-map keys use the
        property name as a synthetic field and follow _json_indexed_map.
        """
        key = obj['x-algites-defscodegen-key']
        location = resource + path + '/x-algites-defscodegen-key'
        if (not isinstance(key, Mapping) or set(key) != {'id', 'field-name'} or
                any(not isinstance(key[name], str) or not key[name].strip()
                    for name in ('id', 'field-name'))):
            raise ValueError('Invalid x-algites-defscodegen-key at ' + location)
        if 'prefixItems' in obj or not isinstance(obj.get('items'), Mapping):
            raise ValueError('Keyed array needs a homogeneous items schema at ' + location)
        item = obj['items']
        if '$ref' not in item:
            if item.get('type') != 'object' or not isinstance(item.get('properties'), Mapping):
                raise ValueError('Keyed array item must be an object or typed $ref at ' + location)
            field = key['field-name']
            if field not in item['properties']:
                raise ValueError('Keyed array item is missing field ' + field + ' at ' + location)
            if field not in item.get('required', []):
                raise ValueError('Keyed array requires field ' + field + ' in items.required at ' + location)
            field_schema = item['properties'][field]
            if not isinstance(field_schema, Mapping) or (
                    '$ref' not in field_schema and not any(name in field_schema
                        for name in ('enum', 'const', 'allOf')) and
                    field_schema.get('type') not in ('string', 'number', 'integer', 'boolean')):
                raise ValueError('Keyed array field must be a typed scalar/enum at ' + location)
        plain = {name: value for name, value in obj.items()
                 if name != 'x-algites-defscodegen-key'}
        node = self._json_node(plain, owner, path, kind, resource)
        if not isinstance(node, ListNode):
            raise ValueError('Keyed JSON/YAML array did not resolve to a LIST at ' + location)
        member = path.rsplit('/', 1)[-1].replace('~1', '/').replace('~0', '~')
        return replace(node, name=member, key_definitions=(KeyDefinition(
            key['id'], member, path + '/x-algites-defscodegen-key',
            (key['field-name'],), True),))

    @classmethod
    def _json_inline_scalar_allof(cls, obj, path):
        """Intersect only losslessly representable inline scalar allOf branches.

        Each branch contributes an independent type assertion or scalar facet.
        Object/array composition and references remain unsupported until the
        canonical model represents those intersections explicitly.

        Args:
            obj: Complete JSON/YAML schema containing inline ``allOf``.
            path: Source pointer used in diagnostics.

        Returns:
            Canonical scalar carrying every effective supported restriction.

        Raises:
            ValueError: Contradictory scalar types or facet bounds.
            NotImplementedError: Non-scalar intersections that cannot be emitted.
        """
        parts = obj['allOf']
        if not isinstance(parts, list) or not parts:
            raise ValueError('allOf requires a nonempty array at ' + path)
        outer = {key: val for key, val in obj.items() if key != 'allOf'}
        sources = [outer, *parts]
        permitted = {'type', 'minLength', 'maxLength', 'pattern', 'format',
                     'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
                     'multipleOf', 'title', 'description'}
        types = []
        for part in sources:
            if not isinstance(part, Mapping) or set(part) - permitted:
                raise NotImplementedError('Inline non-scalar allOf requires canonical intersection at ' + path)
            current_type = part.get('type')
            if current_type is not None:
                if current_type not in ('string', 'number', 'integer', 'boolean', 'null'):
                    raise NotImplementedError('Inline non-scalar allOf requires canonical intersection at ' + path)
                types.append(current_type)
        if not types:
            raise NotImplementedError('Untyped inline allOf cannot be represented as a scalar at ' + path)
        final_type = ('integer' if set(types) <= {'integer', 'number'} and 'integer' in types
                      else 'number' if set(types) == {'number'} else types[0])
        if any(t != final_type and not (final_type == 'integer' and t == 'number') for t in types):
            raise ValueError('Unsatisfiable scalar allOf types at ' + path)
        if 'format' in outer or any('format' in part for part in parts):
            if final_type not in ('string', 'number', 'integer'):
                raise NotImplementedError('format on an untyped or non-scalar schema at ' + path)
        kind = SCALAR_TYPES[final_type]
        merged = None
        for part in sources:
            fmt = part.get('format', '')
            if not isinstance(fmt, str):
                raise ValueError('format must be a string at ' + path)
            current = Scalar(kind, fmt, **cls._scalar_facets(part, kind, path))
            if merged is None:
                merged = current
            else:
                if merged.format and current.format and merged.format != current.format:
                    raise NotImplementedError('Multiple different allOf formats need conjunctive validation at ' + path)
                merged = cls._intersect_scalar_facets(merged, current, path)
        return merged

    def _json_node(self, obj, owner, path, kind, resource):
        if not isinstance(obj, Mapping):
            raise ValueError('Expected inline schema mapping at ' + path)
        # JSON Schema oneOf/anyOf are validation, never structural CHOICE.
        # Keep the schema unchanged; emit a location-specific diagnostic while
        # retaining every independently declared property and type reference.
        for assertion in ('oneOf', 'anyOf'):
            if assertion in obj:
                variants = obj[assertion]
                if not isinstance(variants, list) or not variants or not all(
                        isinstance(v, (Mapping, bool)) for v in variants):
                    raise ValueError('Invalid ' + assertion + ' at ' + path)
                warnings.warn('Validation-only JSON Schema ' + assertion + ' is not '
                              'enforced by generated DataObjects at ' + resource + path,
                              UserWarning, stacklevel=2)
        if 'x-algites-defscodegen-key' in obj:
            if obj.get('type') == 'array':
                return self._json_keyed_array(obj, owner, path, kind, resource)
            return self._json_indexed_map(obj, owner, path, kind, resource)
        validation_only = {'not', 'if', 'then', 'else', 'contains',
            'unevaluatedItems', 'unevaluatedProperties', 'dependentSchemas',
            'propertyNames', 'dependencies', 'contentEncoding', 'contentMediaType',
            'contentSchema', 'dependentRequired', 'minContains', 'maxContains',
            'readOnly', 'writeOnly'} & obj.keys()
        for keyword in sorted(validation_only):
            warnings.warn('Validation-only JSON Schema keyword ' + keyword
                          + ' is not enforced by generated DataObjects at '
                          + resource + path, UserWarning, stacklevel=2)
        unsupported = {'patternProperties', '$dynamicRef', '$recursiveRef',
                       'additionalItems'} & obj.keys()
        if unsupported:
            raise NotImplementedError('Unsupported structural schema keywords at '
                                      + path + ': ' + ', '.join(sorted(unsupported)))
        allof = obj.get('allOf', ())
        conditional_allof = ('allOf' in obj and isinstance(allof, list) and bool(allof)
                             and all(isinstance(part, Mapping) and bool(part)
                                     and set(part) <= {'if', 'then', 'else', 'contains',
                                         'minContains', 'maxContains', 'not'}
                                     for part in allof))
        if conditional_allof:
            warnings.warn('Validation-only allOf assertions are not enforced by '
                          'generated DataObjects at ' + resource + path,
                          UserWarning, stacklevel=2)
        elif 'allOf' in obj and any(not isinstance(part, Mapping) or '$ref' not in part
                                    for part in allof):
            return self._json_inline_scalar_allof(obj, path)
        # A referenced value is resolved after parsing. Until the canonical
        # intersection model can combine sibling constraints with that target,
        # never silently ignore such constraints (JSON Schema 2019-09+ permits them).
        if isinstance(obj.get('$ref'), str):
            constrained = {'minLength', 'maxLength', 'pattern', 'format',
                           'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
                           'multipleOf', 'minItems', 'maxItems', 'uniqueItems',
                           'minProperties', 'maxProperties', 'const', 'enum',
                           'properties', 'items', 'additionalProperties', 'required'} & obj.keys()
            if constrained:
                raise NotImplementedError('Ref sibling constraints need canonical intersection at '
                                          + path + ': ' + ', '.join(sorted(constrained)))
            ref = obj['$ref']
            return TypeNode(ref, ref.rsplit('/', 1)[-1], Origin.DECLARED,
                (owner, ref), (), None, Resolution.REFERENCE,
                self._binding(kind, resource, path, '$ref'))
        t = obj.get('type')
        if isinstance(t, list):
            # A typed field can already represent null as a runtime value.
            # Nullable's validation is deferred; unrelated type unions would
            # change the accessor/storage type and therefore remain unsupported.
            if len(t) == 2 and 'null' in t and all(isinstance(part, str) for part in t):
                t = next(part for part in t if part != 'null')
                warnings.warn('Nullable JSON Schema type is represented as ' + t
                              + '; null validation is deferred at ' + resource + path,
                              UserWarning, stacklevel=2)
            elif len(t) != 1 or not isinstance(t[0], str):
                raise NotImplementedError('JSON Schema incompatible type unions '
                                          'are not structurally representable at ' + path)
            else:
                t = t[0]
        if t is not None and (not isinstance(t, str) or t not in
                              ('object', 'array', 'string', 'integer', 'number', 'boolean', 'null')):
            raise ValueError('Unknown JSON Schema type at ' + path + ': ' + repr(t))
        # Reject constraints that would otherwise vanish on an incompatible
        # object/array branch. JSON Schema facets are conditional on type, not
        # type assertions themselves: silently converting them changes meaning.
        families = (
            ({'minLength', 'maxLength', 'pattern'}, 'string',
             t == 'string'),
            ({'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
              'multipleOf'}, 'number', t in ('integer', 'number')),
            ({'minItems', 'maxItems', 'uniqueItems'}, 'array',
             t == 'array' or (t is None and ('items' in obj or 'prefixItems' in obj))),
            ({'minProperties', 'maxProperties'}, 'object',
             t == 'object' or (t is None and ('properties' in obj or 'additionalProperties' in obj))),
        )
        for keys, family, applicable in families:
            incompatible = keys.intersection(obj)
            if incompatible and not applicable:
                raise NotImplementedError('Conditional ' + family + ' constraints require an explicit '
                                          'compatible type at ' + path + ': ' + ', '.join(sorted(incompatible)))
        if 'format' in obj and t not in ('string', 'number', 'integer'):
            raise NotImplementedError('format on an untyped or non-scalar schema at ' + path)
        # JSON Schema `const` is exactly a one-element enum for scalar values.
        # Reuse the existing canonical ENUM kind so the fixed value survives
        # through linking, merging and Java/Python emission. Do not discard
        # any conjunctive restriction that the canonical model cannot retain.
        if 'const' in obj:
            # Scalar restrictions on a singleton enum are logically redundant
            # *provided the sole member satisfies them*. Validate before
            # projecting to the canonical ENUM; never silently lose a facet.
            conjuncts = {'minItems', 'maxItems', 'uniqueItems',
                         'minProperties', 'maxProperties', 'format'} & obj.keys()
            if conjuncts:
                raise NotImplementedError('Scalar const with additional constraints needs canonical '
                                          'intersection at ' + path + ': ' + ', '.join(sorted(conjuncts)))
            value = obj['const']
            if isinstance(value, (Mapping, list)):
                raise NotImplementedError('Structured JSON Schema const needs a '
                                          'structured-value constraint model at ' + path)
            if '$ref' in obj or 'allOf' in obj:
                raise NotImplementedError('Combined const/reference/composition constraints '
                                          'need canonical intersection at ' + path)
            actual = self._infer_scalar(value)
            base = SCALAR_TYPES[t] if t in SCALAR_TYPES else actual
            if base is not actual and not (base is ScalarKind.NUMBER and
                                           actual is ScalarKind.INTEGER):
                raise ValueError('JSON Schema const conflicts with declared type at ' + path)
            if 'enum' in obj:
                members = obj['enum']
                if not isinstance(members, list) or not any(
                    (isinstance(member, (int, float)) and not isinstance(member, bool) and
                     isinstance(value, (int, float)) and not isinstance(value, bool) and
                     member == value) or
                    (type(member) is type(value) and member == value)
                    for member in members):
                    raise ValueError('JSON Schema const is not allowed by enum at ' + path)
            # A numeric `type:number` and an integer literal still constrain
            # precisely one integer. Preserve that exact type for emission.
            if base is ScalarKind.NUMBER and actual is ScalarKind.INTEGER:
                base = ScalarKind.INTEGER
            self._assert_literal_facets(obj, base, value, path)
            if base is ScalarKind.NULL:
                raise NotImplementedError('Null const needs a nullable literal '
                                          'representation at ' + path)
            if base is ScalarKind.NUMBER:
                raise NotImplementedError('Non-integer numeric const needs exact '
                                          'decimal ENUM emission at ' + path)
            wire = (str(value).lower() if isinstance(value, bool) else str(value))
            return EnumNode(base, (EnumValue(wire),))
        if isinstance(obj.get('items'), bool):
            raise NotImplementedError('Boolean items constraints are not yet canonicalized at ' + path)
        if 'enum' in obj:
            if 'format' in obj:
                raise NotImplementedError('Enum format assertions require format-aware validation at ' + path)
            items = obj['enum']
            if not isinstance(items, list) or not items:
                raise ValueError('Empty or invalid enum at ' + path)
            if t in ('object', 'array'):
                raise NotImplementedError('Structured enum values cannot be canonicalized at ' + path)
            base = SCALAR_TYPES[t] if t in SCALAR_TYPES else self._infer_scalar(items[0])
            for item in items:
                actual = self._infer_scalar(item)
                if actual is not base and not (base is ScalarKind.NUMBER and actual is ScalarKind.INTEGER):
                    raise ValueError(f'Mixed or incompatible enum scalar kinds at {path}: '
                                     f'{base.value} versus {actual.value}')
                self._assert_literal_facets(obj, base, item, path)
            return EnumNode(base, tuple(EnumValue(str(item).lower() if isinstance(item, bool)
                                                  else str(item)) for item in items))
        if t == 'object' or 'properties' in obj or 'additionalProperties' in obj:
            if 'patternProperties' in obj:
                raise NotImplementedError('patternProperties is intentionally deferred')
            members = []
            properties = obj.get('properties', {})
            if not isinstance(properties, Mapping):
                raise ValueError('Expected object properties mapping at ' + path)
            required = obj.get('required', [])
            if (not isinstance(required, list) or any(not isinstance(name, str) for name in required)
                    or len(set(required)) != len(required)):
                raise ValueError('Expected unique string required-property names at ' + path)
            if set(required) - set(properties):
                raise NotImplementedError('Required properties without definitions cannot be represented at ' + path)
            # These are instance-document metadata, not DataObject fields.
            # The names come exclusively from the selected naming convention.
            reserved = {value for role, value in self.naming.schema_metadata.items()
                        if role in ('data_source_schema_url',
                                    'data_source_schema_identifier',
                                    'data_source_schema_version') and value}
            for name, child in properties.items():
                if name in reserved:
                    continue
                pointer = path + '/properties/' + _pointer(str(name))
                node = self._json_node(child, owner, pointer, kind, resource)
                if isinstance(node, ListNode) and node.key_definitions:
                    # An explicitly keyed JSON object is a logical LIST member
                    # with its own synthetic key/value item; no Map<String,V>
                    # accessor is permitted for this representation.
                    members.append(replace(node, name=str(name),
                        key_definitions=tuple(replace(key, selector=str(name))
                                              for key in node.key_definitions)))
                    continue
                if isinstance(node, (ElementList, EnumNode)) and not obj.get('x-algites-defscodegen-choice'):
                    # Only inline enums use the enum-specific naming role;
                    # anonymous objects still use synthetic_property_type.
                    role = ('synthetic_inline_enum_type' if isinstance(node, EnumNode)
                            else 'synthetic_property_type')
                    node = self._synthetic(owner, str(name), pointer,
                        role, node, kind, resource)
                default_kind, lexical = '', ''
                if isinstance(child, Mapping) and 'default' in child:
                    literal = child['default']
                    if isinstance(literal, bool):
                        lexical = str(literal).lower()
                    elif literal is None:
                        lexical = 'null'
                    elif isinstance(literal, (str, int, float)):
                        lexical = str(literal)
                    else:
                        raise NotImplementedError('Structured JSON/YAML defaults require typed canonical metadata at ' + pointer)
                    default_kind = 'DECLARATION_ONLY'
                members.append(Element(str(name), node,
                    source_bindings=self._binding(kind, resource, pointer, 'properties'),
                    min_item_count=int(name in required), max_item_count=1,
                    description=str(child.get('description') or '') if isinstance(child, Mapping) else '',
                    default_kind=default_kind, default_value=lexical))
            additional = obj.get('additionalProperties')
            # JSON Schema accepts arbitrary JSON values for true or {}.
            # No public Object/Any (including Map<String,Object>) is allowed.
            unrestricted = (additional is True or
                isinstance(additional, Mapping) and not
                (set(additional) - {'title', 'description', 'examples', 'default', '$comment'}))
            if unrestricted:
                warnings.warn(
                    'WARNING [DEFS-UNTYPED-ADDITIONAL-PROPERTIES] at ' + resource +
                    path + '/additionalProperties: unconstrained additionalProperties '
                    'are ignored by typed DataObject code generation; unknown instance '
                    'values may be lost on roundtrip. Hint: declare a typed value '
                    'schema, e.g. "additionalProperties": {"$ref": "#/$defs/Item"} '
                    'or {"type": "string"}.', UserWarning, stacklevel=2)
            if isinstance(additional, Mapping) and not unrestricted:
                pointer = path + '/additionalProperties'
                value = self._json_node(additional, owner, pointer, kind, resource)
                if isinstance(value, Scalar) and value.scalar_kind is ScalarKind.ANY:
                    warnings.warn('WARNING [DEFS-UNTYPED-ADDITIONAL-PROPERTIES] at ' + resource +
                        pointer + ': no concrete additionalProperties value type; '
                        'ignoring untyped values. Hint: use '
                        '"additionalProperties": {"type": "string"} or a typed $ref.',
                        UserWarning, stacklevel=2)
                    value = None
                if value is not None:
                    if isinstance(value, (ElementList, EnumNode)):
                        value = self._synthetic(owner, 'additionalProperties', pointer,
                            'synthetic_map_value_type', value, kind, resource)
                    key = Scalar(ScalarKind.STRING)
                    # Integrated property maps remain typed direct ELEMENTLIST children.
                    members.append(MapNode('additionalProperties',
                        MapKind.INTEGRATED_PROPERTY_MAP, key, value,
                        self._binding(kind, resource, pointer, 'additionalProperties')))
            low = self._bound(obj, 'minProperties', path) if 'minProperties' in obj else -1
            high = self._bound(obj, 'maxProperties', path) if 'maxProperties' in obj else -1
            if high >= 0 and low > high:
                raise ValueError('minProperties exceeds maxProperties at ' + path)
            explicit_choice = obj.get('x-algites-defscodegen-choice', None)
            if explicit_choice is not None:
                if (explicit_choice is not True or t != 'object'
                        or len(properties) < 2 or required
                        or low != 1 or high != 1
                        or obj.get('additionalProperties') is not False):
                    raise ValueError('Invalid x-algites-defscodegen-choice at ' + path
                        + ': requires an object with >=2 variants, minProperties=1, '
                          'maxProperties=1, additionalProperties=false, no required fields')
                # The explicit marker is the *only* JSON/YAML source of CHOICE.
                # Wrap named variant types in generated records so every branch
                # has its own stable declaration and can carry a typed value.
                selected = []
                for i, item in enumerate(members):
                    pointer = path + '/properties/' + _pointer(item.name)
                    # A *declared*, named $defs choice matches XSD's named
                    # complexType/choice: even scalar branches have an explicit
                    # selected-field wrapper. Keep the established inline choice
                    # behavior (records for scalar/inline object alternatives).
                    # Neither wrapper introduces a JSON/YAML wire level.
                    named_choice = path.startswith('#/$defs/') and path.count('/') == 2
                    structure = item.structure
                    if (named_choice or
                            isinstance(structure, TypeNode) and
                            structure.resolution_state is Resolution.REFERENCE):
                        structure = ElementList(Composition.SEQUENCE,
                            (Element(item.name, structure, min_item_count=1,
                                source_bindings=self._binding(kind, resource, pointer, 'choice_value')),))
                    variant = self._synthetic(owner, item.name, pointer,
                        'synthetic_choice_variant_type', structure, kind, resource, i)
                    selected.append(replace(item, structure=variant))
                members = selected
            return ElementList(Composition.CHOICE if explicit_choice else Composition.SEQUENCE,
                               tuple(members), min_properties=low, max_properties=high)
        if 'x-algites-defscodegen-choice' in obj:
            raise ValueError('Invalid x-algites-defscodegen-choice at ' + path
                             + ': choice must be an explicitly declared object')
        if t == 'array' or 'items' in obj or 'prefixItems' in obj:
            unique = obj.get('uniqueItems', False)
            if type(unique) is not bool:
                raise ValueError('uniqueItems must be boolean at ' + path)
            minimum = obj.get('minItems', 0)
            maximum = obj.get('maxItems', -1)
            if 'maxItems' in obj and maximum == -1:
                raise ValueError('maxItems requires a nonnegative integer at ' + path)
            if (type(minimum) is not int or type(maximum) is not int
                    or minimum < 0 or maximum < -1 or (maximum != -1 and maximum < minimum)):
                raise ValueError('Invalid minItems/maxItems bounds at ' + path)
            if 'prefixItems' in obj and ('minItems' in obj or 'maxItems' in obj or unique):
                raise NotImplementedError('Tuple minItems/maxItems constraints require a tuple-length model at ' + path)
            items = []
            for i, child in enumerate(obj.get('prefixItems', ())):
                pointer = f'{path}/prefixItems/{i}'
                node = self._json_node(child, owner, pointer, kind, resource)
                synthetic = self._synthetic(owner, 'item', pointer,
                    'synthetic_positional_item_type', node, kind, resource, i)
                getter = self.naming.method_name('positional_item_synthetic_getter',
                    position=str(self.naming.positional_number(i)))
                items.append(Element(getter, synthetic,
                    source_bindings=self._binding(kind, resource, pointer, 'prefixItems')))
            if isinstance(obj.get('items'), Mapping):
                pointer = path + '/items'
                node = self._json_node(obj['items'], owner, pointer, kind, resource)
                if isinstance(node, (ElementList, EnumNode)):
                    node = self._synthetic(owner, 'item', pointer,
                        'synthetic_list_item_type', node, kind, resource)
                rest = ListNode('items', node, minimum, maximum, unique_items=unique)
                if not items:
                    return rest
                items.append(rest)
            if not items:
                # In Draft 2020-12 an unconstrained array still allows items.
                return ListNode('items', Scalar(ScalarKind.ANY), minimum, maximum, unique_items=unique)
            if 'items' not in obj:
                # Prefix items do not close the tuple; additional items are allowed.
                items.append(ListNode('items', Scalar(ScalarKind.ANY)))
            return ElementList(Composition.SEQUENCE, tuple(items))
        if 'required' in obj:
            raise ValueError('required is valid only for object schemas at ' + path)
        if {'minItems', 'maxItems', 'uniqueItems'}.intersection(obj):
            raise ValueError('Array constraints require an array schema at ' + path)
        if {'minProperties', 'maxProperties'}.intersection(obj):
            raise ValueError('Object constraints require an object schema at ' + path)
        scalar_kind = SCALAR_TYPES.get(t, ScalarKind.ANY)
        return Scalar(scalar_kind, str(obj.get('format') or ''),
                      **self._scalar_facets(obj, scalar_kind, path))

    @staticmethod
    def _bound(obj, key, path):
        """Read a JSON Schema nonnegative integer facet without converting booleans."""
        value = obj.get(key, -1)
        if type(value) is not int or value < 0:
            raise ValueError(f'{key} requires a nonnegative integer at {path}')
        return value

    @classmethod
    def _scalar_facets(cls, obj, scalar_kind, path, *, xml_lexical=False):
        """Preserve supported string and number restrictions in canonical Scalar."""
        from decimal import Decimal, InvalidOperation
        string_keys = {'minLength', 'maxLength', 'pattern'}
        numeric_keys = {'minimum', 'maximum', 'exclusiveMinimum',
                        'exclusiveMaximum', 'multipleOf'}
        if string_keys.intersection(obj) and scalar_kind is not ScalarKind.STRING:
            raise NotImplementedError('String constraints require a string schema at ' + path)
        if numeric_keys.intersection(obj) and scalar_kind not in (ScalarKind.INTEGER, ScalarKind.NUMBER):
            raise NotImplementedError('Numeric constraints require a numeric schema at ' + path)
        lower = cls._bound(obj, 'minLength', path) if 'minLength' in obj else -1
        upper = cls._bound(obj, 'maxLength', path) if 'maxLength' in obj else -1
        if upper >= 0 and lower > upper:
            raise ValueError('minLength exceeds maxLength at ' + path)
        pattern = obj.get('pattern', '')
        if not isinstance(pattern, str):
            raise ValueError('pattern must be a string at ' + path)
        try:
            import re
            if pattern: re.compile(pattern)
        except re.error as e:
            raise ValueError('Invalid pattern at ' + path) from e
        result = dict(min_length=lower, max_length=upper, pattern=pattern,
                      minimum='', maximum='', exclusive_minimum=False,
                      exclusive_maximum=False, multiple_of='')
        for key, target in (('minimum', 'minimum'), ('maximum', 'maximum'),
                            ('multipleOf', 'multiple_of')):
            if key in obj:
                raw = obj[key]
                if isinstance(raw, bool) or not isinstance(raw, (int, float)) and not (xml_lexical and isinstance(raw, str)):
                    raise ValueError(key + ' must be numeric at ' + path)
                try:
                    number = Decimal(str(raw))
                except InvalidOperation as e:
                    raise ValueError('Invalid ' + key + ' at ' + path) from e
                if not number.is_finite() or (key == 'multipleOf' and number <= 0):
                    raise ValueError('Invalid ' + key + ' at ' + path)
                result[target] = str(raw)
        for key, base, flag in (('exclusiveMinimum', 'minimum', 'exclusive_minimum'),
                                ('exclusiveMaximum', 'maximum', 'exclusive_maximum')):
            if key in obj:
                raw = obj[key]
                if isinstance(raw, bool):
                    # Draft-04 boolean exclusivity modifies `minimum` / `maximum`.
                    if raw and not result[base]:
                        raise ValueError(key + ' needs ' + base + ' at ' + path)
                    result[flag] = raw
                elif isinstance(raw, (int, float)) or xml_lexical and isinstance(raw, str):
                    try:
                        exclusive = Decimal(str(raw))
                    except InvalidOperation as error:
                        raise ValueError('Invalid ' + key + ' at ' + path) from error
                    if not exclusive.is_finite():
                        raise ValueError('Invalid ' + key + ' at ' + path)
                    inclusive = Decimal(result[base]) if result[base] else None
                    tighter = (inclusive is None or exclusive >= inclusive) if base == 'minimum' else (inclusive is None or exclusive <= inclusive)
                    if tighter:
                        result[base] = str(raw)
                        result[flag] = True
                else:
                    raise ValueError(key + ' must be numeric or boolean at ' + path)
        if result['minimum'] and result['maximum']:
            minimum = Decimal(result['minimum'])
            maximum = Decimal(result['maximum'])
            if minimum > maximum or (minimum == maximum and
                    (result['exclusive_minimum'] or result['exclusive_maximum'])):
                raise ValueError('Unsatisfiable numeric bounds at ' + path)
        return result

    @staticmethod
    def _intersect_scalar_facets(parent, child, path):
        """Conjoin facet restrictions of a named XSD simpleType chain.

        A derived restriction cannot weaken its base. The canonical field
        annotation stores the effective intersection, not only the last hop.
        Independent regular expressions need a model with multiple patterns;
        reject those instead of accidentally dropping either constraint.

        Raises:
            ValueError: The combined limits are contradictory.
            NotImplementedError: Different nonempty patterns require a compound constraint.
        """
        from decimal import Decimal
        if parent.scalar_kind != child.scalar_kind:
            raise ValueError('XSD simpleType scalar kind mismatch at ' + path)
        if parent.pattern and child.pattern and parent.pattern != child.pattern:
            raise NotImplementedError('Multiple inherited XSD patterns require conjunctive pattern annotations at ' + path)
        low = max(parent.min_length, child.min_length)
        highs = [v for v in (parent.max_length, child.max_length) if v >= 0]
        high = min(highs) if highs else -1
        if high >= 0 and low > high:
            raise ValueError('Unsatisfiable inherited XSD length bounds at ' + path)
        def tighter_lower():
            if not parent.minimum:
                return child.minimum, child.exclusive_minimum
            if not child.minimum:
                return parent.minimum, parent.exclusive_minimum
            a, b = Decimal(parent.minimum), Decimal(child.minimum)
            if a > b:
                return parent.minimum, parent.exclusive_minimum
            if a < b:
                return child.minimum, child.exclusive_minimum
            return parent.minimum, parent.exclusive_minimum or child.exclusive_minimum
        def tighter_upper():
            if not parent.maximum:
                return child.maximum, child.exclusive_maximum
            if not child.maximum:
                return parent.maximum, parent.exclusive_maximum
            a, b = Decimal(parent.maximum), Decimal(child.maximum)
            if a < b:
                return parent.maximum, parent.exclusive_maximum
            if a > b:
                return child.maximum, child.exclusive_maximum
            return parent.maximum, parent.exclusive_maximum or child.exclusive_maximum
        minimum, lower_exclusive = tighter_lower()
        maximum, upper_exclusive = tighter_upper()
        if minimum and maximum:
            lower_value, upper_value = Decimal(minimum), Decimal(maximum)
            if lower_value > upper_value or lower_value == upper_value and (lower_exclusive or upper_exclusive):
                raise ValueError('Unsatisfiable inherited XSD numeric bounds at ' + path)
        multiple = parent.multiple_of or child.multiple_of
        if parent.multiple_of and child.multiple_of:
            # A conjunction of divisibility constraints is itself a multipleOf
            # restriction. Normalize exact finite decimals before taking the LCM.
            from math import gcd
            a, b = Decimal(parent.multiple_of), Decimal(child.multiple_of)
            # Decimal arithmetic and normalize() use the current context
            # precision (normally 28 digits). Derive an exact integer for each
            # terminating decimal, and render the result from integer digits.
            # This matches Java BigDecimal/BigInteger even above 28 digits.
            scale_digits = max(0, -a.as_tuple().exponent, -b.as_tuple().exponent)
            def scaled_integer(value):
                parts = value.as_tuple()
                coefficient = int(''.join(map(str, parts.digits)))
                return coefficient * 10 ** (parts.exponent + scale_digits)
            ai, bi = scaled_integer(a), scaled_integer(b)
            digits = str(abs(ai // gcd(ai, bi) * bi))
            if scale_digits:
                digits = digits.zfill(scale_digits + 1)
                digits = (digits[:-scale_digits] + '.' + digits[-scale_digits:]).rstrip('0').rstrip('.')
            multiple = digits
        return Scalar(child.scalar_kind, parent.format or child.format,
                      min_length=low, max_length=high,
                      pattern=child.pattern or parent.pattern,
                      minimum=minimum, maximum=maximum,
                      exclusive_minimum=lower_exclusive,
                      exclusive_maximum=upper_exclusive,
                      multiple_of=multiple)

    @classmethod
    def _assert_literal_facets(cls, facets, scalar_kind, literal, path, *, xml_lexical=False):
        """Allow enum/const intersections only when every literal satisfies them.

        A finite enum already implies a scalar restriction satisfied by all
        members. This is the only lossless way to project the intersection
        without extending the generated canonical ENUM contract.

        Raises:
            ValueError: An enum member violates a declared restriction.
            NotImplementedError: A facet has incompatible scalar semantics.
        """
        from decimal import Decimal, InvalidOperation
        bounds = cls._scalar_facets(facets, scalar_kind, path,
                                     xml_lexical=xml_lexical)
        if scalar_kind is ScalarKind.STRING:
            text = str(literal)
            if (bounds['min_length'] >= 0 and len(text) < bounds['min_length'] or
                    bounds['max_length'] >= 0 and len(text) > bounds['max_length']):
                raise ValueError('Enum/const literal violates length constraint at ' + path)
            if bounds['pattern']:
                import re
                matcher = re.fullmatch if xml_lexical else re.search
                if matcher(bounds['pattern'], text) is None:
                    raise ValueError('Enum/const literal violates pattern at ' + path)
        elif scalar_kind in (ScalarKind.INTEGER, ScalarKind.NUMBER):
            try:
                number = Decimal(str(literal))
            except InvalidOperation as error:
                raise ValueError('Invalid numeric enum/const literal at ' + path) from error
            if not number.is_finite():
                raise ValueError('Nonfinite numeric enum/const literal at ' + path)
            if bounds['minimum']:
                minimum = Decimal(bounds['minimum'])
                if number < minimum or (number == minimum and bounds['exclusive_minimum']):
                    raise ValueError('Enum/const literal violates minimum at ' + path)
            if bounds['maximum']:
                maximum = Decimal(bounds['maximum'])
                if number > maximum or (number == maximum and bounds['exclusive_maximum']):
                    raise ValueError('Enum/const literal violates maximum at ' + path)
            if bounds['multiple_of'] and number % Decimal(bounds['multiple_of']) != 0:
                raise ValueError('Enum/const literal violates multipleOf at ' + path)

    @staticmethod
    def _infer_scalar(value):
        if isinstance(value, bool):
            return ScalarKind.BOOLEAN
        if isinstance(value, int):
            return ScalarKind.INTEGER
        if isinstance(value, (float,)):
            return ScalarKind.NUMBER
        if value is None:
            return ScalarKind.NULL
        return ScalarKind.STRING

    @staticmethod
    def _parse_xsd_scopes(text: str | bytes):
        """Read one XSD preserving the namespace context of each declaration."""
        xml = text.encode('utf-8') if isinstance(text, str) else text
        parser = ET.iterparse(BytesIO(xml), events=('start-ns', 'start', 'end'))
        scopes = {}
        stack = []
        pending = {}
        for event, value in parser:
            if event == 'start-ns':
                prefix, uri = value
                pending[prefix or ''] = uri
            elif event == 'start':
                scope = dict(stack[-1]) if stack else {}
                scope.update(pending)
                pending.clear()
                stack.append(scope)
                scopes[id(value)] = scope
            else:
                stack.pop()
        return parser.root, scopes

    def load_xsd(self, text: str | bytes, resource: str, *, source_version: str = ""):
        """Read named XSD types while retaining sequence/all/choice and list semantics.

        XML→MAP and keyref interpretation are intentionally not performed.
        Local xs:key/xs:unique rules bind to the containing element occurrence
        and select a direct repeated member of its referenced or inline TYPE.
        Global and local element keys use the same indexed-list projection;
        unsupported XPath expressions fail closed.
        """
        # Use the same scoped namespace parser for local and imported XSDs.
        schema, scopes = self._parse_xsd_scopes(text)
        if schema.tag != XS + 'schema':
            raise ValueError('Expected an xs:schema')
        # Global ELEMENT declarations and reusable named TYPE declarations
        # belong to distinct XML Schema symbol spaces. Both are loaded.
        if any(node.tag in (XS + 'keyref', XS + 'identityConstraint') for node in schema.iter()):
            raise NotImplementedError('XSD keyref/identityConstraint needs a dedicated resolver')
        for child in schema:
            if child.tag in (XS + 'include', XS + 'redefine', XS + 'override'):
                raise NotImplementedError('XSD include/redefine/override requires explicit composition support')
            if child.tag == XS + 'import' and not child.get('schemaLocation'):
                raise ValueError('XSD import requires a schemaLocation for deterministic resolution')
        if schema.get('elementFormDefault', 'unqualified') not in ('qualified', 'unqualified') or schema.get('attributeFormDefault', 'unqualified') not in ('qualified', 'unqualified'):
            raise ValueError('Invalid XSD element/attribute form default')
        self._source_versions[resource] = str(schema.get('x-algites-schema-version') or source_version)
        self._xml_element_form = schema.get('elementFormDefault', 'unqualified')
        self._xml_attribute_form = schema.get('attributeFormDefault', 'unqualified')
        named = [child for child in schema if child.tag in (XS + 'complexType', XS + 'simpleType')
                 and child.get('name')]
        declared = {child.get('name') for child in named}
        namespace = schema.get('targetNamespace', '')
        # Named scalar restrictions do not describe DataObject interfaces.
        # Inline their resolved scalar metadata at each consuming field, where
        # the field-specific string/numeric annotations can be generated.
        # Named enumeration types remain nominal and are emitted as ENUMs.
        self._xml_simple_types = {
            ('{' + namespace + '}' + child.get('name') if namespace else child.get('name')): child
            for child in named if child.tag == XS + 'simpleType'
        }
        self._xml_resolving_simple_types = set()
        # Local xs:key/xs:unique belong to the element occurrence, not the
        # reusable named complexType. Imported declarations are inspected only
        # for selector validation and are never copied into the output model.
        # Global xs:group declarations are a separate XSD symbol space. A
        # named group may provide a reusable semantic TYPE or name an outer
        # repeated-group list; neither introduces an XML wrapper element.
        self._xml_groups = {
            ('{' + namespace + '}' + child.get('name') if namespace else child.get('name')): child
            for child in schema if child.tag == XS + 'group' and child.get('name')
        }
        self._xml_resolving_groups = set()
        self._xml_complex_types = {
            ('{' + namespace + '}' + child.get('name') if namespace else child.get('name')): child
            for child in named if child.tag == XS + 'complexType'
        }
        group_types = [child for child in schema if child.tag == XS + 'group'
                       and child.get('name') and self._xml_list_group(child) is None]
        # A named group is a semantic TYPE only when it describes one item.
        # A list wrapper such as CoordinatesGroupList names a field instead.
        overlap = set(declared) & {group.get('name') for group in group_types}
        if overlap:
            raise ValueError('XSD named group/type identity conflict: ' + ', '.join(sorted(overlap)))
        declared.update(group.get('name') for group in group_types)
        named.extend(group_types)
        result = []
        for child in named:
            name = child.get('name')
            self._xml_wildcard_comments = []
            node = self._xml_node(child, name, '/schema/' + name, resource,
                                  declared, namespace, scopes)
            if child.tag == XS + 'simpleType' and isinstance(node, Scalar):
                # A simple scalar alias cannot be emitted as a DO interface;
                # its restrictions are preserved on all consuming fields.
                continue
            identity = ('{' + namespace + '}' + name) if namespace else name
            inherited_list = []
            for group in child.findall(XS + 'complexContent'):
                for derivation in group:
                    if derivation.tag not in (XS + 'extension', XS + 'restriction') or not derivation.get('base'):
                        continue
                    source, target = self._xml_type_reference(
                        derivation, derivation.get('base'), declared, namespace, scopes)
                    if source == 'declared':
                        inherited_list.append(target)
                    elif target not in ('anyType', 'anySimpleType'):
                        raise NotImplementedError('XSD built-in extension base ' + target + ' is unsupported')
            inherited = tuple(inherited_list)
            result.append(TypeNode(identity, name, Origin.DECLARED, (name,), inherited,
                node, Resolution.RESOLVED,
                self._binding(SourceKind.XMLDEFS, resource, '/schema/' + name, child.tag[len(XS):]),
                schema_version=str(child.get('x-algites-schema-version') or
                    schema.get('x-algites-schema-version') or source_version),
                description='\n'.join(filter(None, (
                    self._xsd_description(child), *self._xml_wildcard_comments)))))
        # A global XML ELEMENT is a first-class DataObject declaration, not
        # merely a QName assigned to the named TYPE it happens to reference.
        # Reuse the same _xml_node() and xs:key logic as for local elements.
        # Scalar-only global elements have no object contract to expose.
        global_elements = [child for child in schema if child.tag == XS + 'element']
        global_names = set()
        for global_element in global_elements:
            name = global_element.get('name')
            if not name:
                raise ValueError('Global xs:element requires a name at ' + resource)
            if name in global_names:
                raise ValueError('Duplicate global xs:element ' + name + ' at ' + resource)
            global_names.add(name)
            pointer = '/schema/element/' + name
            self._xml_wildcard_comments = []
            occurrence = self._xml_node(global_element, name, pointer,
                                         resource, declared, namespace, scopes)
            if not isinstance(occurrence, Element):
                raise ValueError('Global xs:element is not an object occurrence at ' + resource + pointer)
            structure = occurrence.structure
            if isinstance(structure, TypeNode):
                if structure.resolution_state is Resolution.REFERENCE or structure.target_identity:
                    reference_identity = structure.target_identity or structure.identity
                    declaration = self._xml_complex_types.get(reference_identity)
                    if declaration is not None:
                        structure = self._xml_node(declaration, name, pointer + '/@type',
                                                   resource, declared, namespace, scopes)
                    else:
                        # Imported named types may already be linked through an
                        # external interface. Resolve those separately; never
                        # invent an empty structure for an unknown schema.
                        imported = self._external_xsd_complex_types.get(reference_identity)
                        if imported is not None:
                            decl, remote_scopes, remote_ns, remote_resource = imported
                            remote_names = {identity.rsplit('}', 1)[-1]
                                            for identity in self._external_xsd_complex_types
                                            if identity.startswith('{' + remote_ns + '}')}
                            structure = self._xml_node(decl, name, pointer + '/@type',
                                                      remote_resource, remote_names,
                                                      remote_ns, remote_scopes)
                else:
                    structure = structure.structure
            if isinstance(structure, (Scalar, EnumNode)):
                # Simple XML element declarations are not DataObjects.
                # Their scalar type can still be used by typed complex content.
                if occurrence.key_definitions:
                    raise ValueError('Scalar global element cannot own xs:key at ' + pointer)
                continue
            if not isinstance(structure, ElementList):
                raise NotImplementedError('Global XML ELEMENT requires a resolvable complex type: '
                                          + resource + pointer)
            if occurrence.key_definitions:
                keyed = {}
                for definition in occurrence.key_definitions:
                    if definition.selector in keyed:
                        raise ValueError('Multiple global keys for the same selected LIST require indexed collection multi-key support: '
                                         + definition.selector)
                    keyed[definition.selector] = definition
                children = []
                for child in structure.children:
                    if isinstance(child, ListNode) and child.name in keyed:
                        if child.key_definitions:
                            raise ValueError('Conflicting key definitions for ' + child.name)
                        child = replace(child, key_definitions=(keyed.pop(child.name),))
                    children.append(child)
                if keyed:
                    raise ValueError('Unbound global XML key selectors at ' + pointer + ': '
                                     + ', '.join(sorted(keyed)))
                structure = replace(structure, children=tuple(children))
            # XSD permits a global element and a named type with the same QName.
            # Keep both declarations, but disambiguate their generated Java/Python
            # interface names while retaining the actual element wire QName.
            collides = name in declared
            type_name = name + 'Element' if collides else name
            identity = ('{' + namespace + '}' + name if namespace else name)
            if collides:
                identity += '#element'
            result.append(TypeNode(identity, type_name, Origin.DECLARED, (type_name,),
                (), structure, Resolution.RESOLVED,
                self._binding(SourceKind.XMLDEFS, resource, pointer, 'xs:element'),
                schema_version=str(global_element.get('x-algites-schema-version') or
                    schema.get('x-algites-schema-version') or source_version),
                description='\n'.join(filter(None, (
                    self._xsd_description(global_element), *self._xml_wildcard_comments)))))
        return tuple(result)

    @staticmethod
    def _xml_list_group(declaration):
        """Recognize a named xs:group wrapping one repeated named group.

        The outer group is a list *name*, not an extra object or wire
        element. All other named xs:group declarations are ordinary reusable
        semantic structures. The inner group must be a reusable item type.
        """
        children = [child for child in declaration if child.tag != XS + 'annotation']
        if len(children) != 1 or children[0].tag != XS + 'sequence':
            return None
        particles = [child for child in children[0] if child.tag != XS + 'annotation']
        if len(particles) != 1 or particles[0].tag != XS + 'group' or not particles[0].get('ref'):
            return None
        repeated = particles[0]
        maximum = repeated.get('maxOccurs', '1')
        if maximum == '1':
            return None
        return repeated

    def _xml_group_identity(self, element, raw_name, namespace, scopes, resource, pointer):
        """Resolve a group QName in the group symbol space, never as a TYPE."""
        prefix, separator, name = raw_name.partition(':')
        uri = scopes[id(element)].get(prefix if separator else '', '')
        if separator and not uri:
            raise ValueError(f'{resource}{pointer}: undefined group prefix {prefix!r}')
        identity = ('{' + uri + '}' + (name if separator else prefix)
                    if uri else name if separator else prefix)
        if identity not in self._xml_groups:
            raise NotImplementedError(f'{resource}{pointer}: unsupported or unresolved xs:group ref {raw_name!r}')
        return identity

    def _xml_group_ref(self, element, owner, pointer, resource, declared, namespace, scopes):
        """Project a reference to either a named list or embedded group item."""
        raw_name = element.get('ref', '')
        identity = self._xml_group_identity(element, raw_name, namespace, scopes, resource, pointer)
        definition = self._xml_groups[identity]
        label = definition.get('name')
        minimum = self._xml_occurs(element.get('minOccurs', '1'), pointer, False)
        maximum = self._xml_occurs(element.get('maxOccurs', '1'), pointer, True)
        inner = self._xml_list_group(definition)
        if inner is not None:
            if maximum != 1:
                raise NotImplementedError(f'{resource}{pointer}: repeated outer named list group needs '
                                          'an explicit enclosing structural definition')
            item_id = self._xml_group_identity(inner, inner.get('ref'), namespace,
                                                scopes, resource, pointer)
            if item_id == identity or self._xml_list_group(self._xml_groups[item_id]):
                raise ValueError(f'{resource}{pointer}: cyclic or nested named list group {label}')
            item_name = self._xml_groups[item_id].get('name')
            item = TypeNode(item_id, item_name, Origin.DECLARED, (owner, label), (), None,
                            Resolution.REFERENCE,
                            self._binding(SourceKind.XMLDEFS, resource, pointer, 'xs:group/@ref'))
            inner_minimum = self._xml_occurs(inner.get('minOccurs', '1'), pointer, False)
            inner_maximum = self._xml_occurs(inner.get('maxOccurs', '1'), pointer, True)
            return ListNode(label, item, 0 if minimum == 0 else inner_minimum,
                            inner_maximum)
        item = TypeNode(identity, label, Origin.DECLARED, (owner, label), (), None,
                        Resolution.REFERENCE,
                        self._binding(SourceKind.XMLDEFS, resource, pointer, 'xs:group/@ref'))
        if maximum == -1 or maximum > 1:
            return ListNode(label, item, minimum, maximum)
        return Element(label, item,
                       source_bindings=self._binding(SourceKind.XMLDEFS, resource, pointer, 'xs:group'),
                       min_item_count=minimum, max_item_count=maximum,
                       element_kind=ElementKind.EMBEDDED)

    def _xml_type_reference(self, element, qname, declared, target_namespace, scopes):
        """Resolve an XSD QName using the actual prefix binding at its location."""
        if not qname:
            raise ValueError('Empty XSD type QName')
        prefix, separator, local_name = qname.partition(':')
        if separator:
            uri = scopes[id(element)].get(prefix)
            if uri is None:
                raise ValueError(f'Undeclared XSD QName prefix {prefix!r} in {qname!r}')
        else:
            local_name = prefix
            uri = scopes[id(element)].get('', '')
        if uri == XS_URI:
            return 'builtin', local_name
        if local_name in declared and uri in ('', target_namespace):
            return ('declared', ('{' + target_namespace + '}' + local_name)
                    if target_namespace else local_name)
        external = '{' + uri + '}' + local_name
        if external in self.external_xsd_types:
            return 'declared', external
        raise NotImplementedError(f'Unresolved or external XSD QName {qname!r} (namespace {uri!r})')

    @staticmethod
    def _xml_default(element, value, *, attribute: bool = False):
        """Project XSD default/fixed into schema-generated canonical field metadata.

        XML element defaults apply to explicit empty content, while XML attribute
        defaults apply to omission. XSD fixed imposes a value restriction on
        mutable assignments rather than materializing a default in raw storage.
        """
        if 'default' in element.attrib and 'fixed' in element.attrib:
            raise ValueError('XSD default and fixed are mutually exclusive')
        allowed = isinstance(value, Scalar) and value.scalar_kind is ScalarKind.STRING
        if 'fixed' in element.attrib:
            kind = 'CONSTRAINT_DEFAULT'
            lexical = element.attrib['fixed']
        elif 'default' in element.attrib:
            kind = ('IF_FIELD_VALUE_NOT_PRESENT' if attribute
                    else 'IF_FIELD_VALUE_EMPTY')
            lexical = element.attrib['default']
        else:
            kind, lexical = '', ''
        if kind and not isinstance(value, (Scalar, TypeNode, EnumNode)):
            raise NotImplementedError('XML default/fixed on structured values needs typed content handling')
        return {'default_kind': kind, 'default_value': lexical,
                'is_empty_allowed': allowed}

    def _xml_node(self, element, owner, pointer, resource, declared, namespace, scopes,
                  optional_context: bool = False):
        """Project an XML declaration; reject mandatory and document optional wildcards."""
        kind = SourceKind.XMLDEFS
        tag = element.tag[len(XS):]
        if tag in ('any', 'anyAttribute'):
            # xs:anyAttribute has no minOccurs; an attribute wildcard only
            # permits otherwise undeclared attributes and never requires one.
            optional = (tag == 'anyAttribute' or optional_context or
                        element.get('minOccurs', '1') == '0')
            original = ET.tostring(element, encoding='unicode').strip()
            if not optional:
                raise NotImplementedError('Required XML wildcard xs:' + tag +
                    ' cannot be represented as DataObject field at ' + resource + pointer +
                    '. Hint: replace the wildcard with a named, typed xs:element or xs:attribute declaration.')
            hint = ('<xs:attribute name="Extra" type="xs:string"/>' if tag == 'anyAttribute'
                    else '<xs:element name="Extra" type="xs:string" minOccurs="0"/>')
            comment = ('Ignored optional XML wildcard xs:' + tag + ' at ' + resource +
                       pointer + ': ' + original + '. Hint: declare explicit typed '
                       'fields instead, e.g. ' + hint + '; arbitrary wildcard values '
                       'are not represented in DataObject and may be lost on roundtrip.')
            warnings.warn(comment, UserWarning, stacklevel=2)
            self._xml_wildcard_comments.append(comment)
            return None
        if tag == 'group':
            if element.get('ref'):
                return self._xml_group_ref(element, owner, pointer, resource,
                                           declared, namespace, scopes)
            if not element.get('name'):
                raise ValueError(f'{resource}{pointer}: xs:group requires name or ref')
            particles = [child for child in element if child.tag != XS + 'annotation']
            if len(particles) != 1 or particles[0].tag not in (
                    XS + 'sequence', XS + 'choice', XS + 'all'):
                raise NotImplementedError(f'{resource}{pointer}: named xs:group requires one compositor')
            return self._xml_node(particles[0], owner, pointer + '/group', resource,
                                  declared, namespace, scopes, optional_context)
        if tag == 'simpleType':
            restriction = element.find(XS + 'restriction')
            if restriction is not None:
                supported = {'enumeration', 'annotation', 'minLength', 'maxLength',
                             'length', 'pattern', 'minInclusive', 'maxInclusive',
                             'minExclusive', 'maxExclusive'}
                unsupported = [child.tag[len(XS):] for child in restriction
                               if child.tag.startswith(XS) and child.tag[len(XS):] not in supported]
                if unsupported:
                    raise NotImplementedError('Unsupported XML restriction facets: ' + ', '.join(unsupported))
                values = restriction.findall(XS + 'enumeration')
                source, value = self._xml_type_reference(
                    restriction, restriction.get('base'), declared, namespace, scopes)
                inherited_scalar = None
                if source == 'declared':
                    parent = self._xml_simple_types.get(value)
                    if parent is None:
                        raise NotImplementedError('XSD simpleType restriction base is not a local scalar: ' + value)
                    if value in self._xml_resolving_simple_types:
                        raise ValueError('Cyclic XSD simpleType restriction at ' + pointer + ': ' + value)
                    self._xml_resolving_simple_types.add(value)
                    try:
                        inherited = self._xml_node(parent, owner, pointer + '/base',
                                                   resource, declared, namespace, scopes)
                    finally:
                        self._xml_resolving_simple_types.remove(value)
                    if not isinstance(inherited, Scalar):
                        raise NotImplementedError('Restriction of an XSD enum base needs explicit enum narrowing: ' + pointer)
                    inherited_scalar = inherited
                    scalar = inherited.scalar_kind
                else:
                    scalar = self._xsd_scalar(value)
                if scalar is ScalarKind.ANY and value not in ('anyType', 'anySimpleType'):
                    raise NotImplementedError('Unsupported XSD scalar base ' + value)
                facets = {}
                for child in restriction:
                    if not child.tag.startswith(XS) or child.tag in (XS+'annotation', XS+'enumeration'):
                        continue
                    facet = child.tag[len(XS):]
                    literal = child.get('value')
                    if literal is None:
                        raise ValueError('Missing XSD facet value for ' + facet)
                    if facet == 'length':
                        facets['minLength'] = facets['maxLength'] = int(literal)
                    elif facet in ('minLength', 'maxLength', 'pattern'):
                        if facet in facets:
                            raise NotImplementedError('Repeated XSD facet ' + facet + ' at ' + pointer)
                        facets[facet] = (int(literal) if facet != 'pattern' else literal)
                    elif facet in ('minInclusive', 'minExclusive'):
                        if 'minimum' in facets or 'exclusiveMinimum' in facets:
                            raise NotImplementedError('Conflicting XSD minimum facets at ' + pointer)
                        facets['minimum'] = literal
                        if facet == 'minExclusive': facets['exclusiveMinimum'] = True
                    elif facet in ('maxInclusive', 'maxExclusive'):
                        if 'maximum' in facets or 'exclusiveMaximum' in facets:
                            raise NotImplementedError('Conflicting XSD maximum facets at ' + pointer)
                        facets['maximum'] = literal
                        if facet == 'maxExclusive': facets['exclusiveMaximum'] = True
                if values:
                    for item in values:
                        self._assert_literal_facets(facets, scalar, item.get('value', ''),
                                                    pointer, xml_lexical=True)
                    return EnumNode(scalar, tuple(EnumValue(item.get('value', '')) for item in values))
                # Numeric XML facets are lexical decimals, unlike JSON numeric tokens.
                # Convert only after validating the complete lexical representation.
                from decimal import Decimal, InvalidOperation
                for bound in ('minimum', 'maximum'):
                    if bound in facets:
                        try:
                            numeric = Decimal(facets[bound])
                        except InvalidOperation as e:
                            raise ValueError('Invalid XML ' + bound + ' at ' + pointer) from e
                        if not numeric.is_finite():
                            raise ValueError('Nonfinite XML ' + bound + ' at ' + pointer)
                        facets[bound] = str(numeric)
                local_scalar = Scalar(scalar, **self._scalar_facets(
                    facets, scalar, pointer, xml_lexical=True))
                return (self._intersect_scalar_facets(inherited_scalar, local_scalar, pointer)
                        if inherited_scalar is not None else local_scalar)
            if any(child.tag != XS + 'annotation' for child in element):
                raise NotImplementedError('Unsupported XML simpleType without xs:restriction at ' + pointer)
            return Scalar(ScalarKind.ANY)
        if tag in ('sequence', 'all', 'choice'):
            composition = {'sequence': Composition.SEQUENCE, 'all': Composition.ALL,
                           'choice': Composition.CHOICE}[tag]
            children = []
            for i, child in enumerate(element):
                if child.tag in (XS + 'element', XS + 'sequence', XS + 'all', XS + 'choice', XS + 'any', XS + 'group'):
                    child_node = self._xml_node(child, owner,
                        pointer + '/' + tag + '/' + str(i), resource, declared, namespace,
                        scopes, optional_context or element.get('minOccurs', '1') == '0')
                    if child_node is not None:
                        # A nested compositor is an embedded member; it does
                        # not introduce a new XML element or replace its TYPE.
                        if isinstance(child_node, ElementList) and composition is not Composition.CHOICE:
                            group_label = child.tag[len(XS):].title()
                            group_path = pointer + '/' + tag + '/' + str(i)
                            named_group = self._synthetic(owner, group_label, group_path,
                                'synthetic_group_type', child_node, kind, resource, i)
                            child_node = Element(group_label + str(i + 1), named_group,
                                element_kind=ElementKind.EMBEDDED,
                                min_item_count=0 if child_node.min_item_count == 0 else 1,
                                source_bindings=self._binding(kind, resource, group_path, 'embedded_group'))
                        children.append(child_node)
                elif child.tag != XS + 'annotation':
                    raise NotImplementedError('Unsupported XML group child ' + str(child.tag) + ' at ' + pointer)
            minimum = self._xml_occurs(element.get('minOccurs', '1'), pointer, False)
            maximum = self._xml_occurs(element.get('maxOccurs', '1'), pointer, True)
            if composition is Composition.CHOICE and (minimum, maximum) == (1, 1):
                # xs:choice is structural. Its direct elements must be nominal
                # alternatives, like explicit JSON/YAML choice, not raw
                # fields erroneously rejected by the sealed-variant emitter.
                selected = []
                for i, field in enumerate(children):
                    if isinstance(field, ElementList) and field.composition is Composition.SEQUENCE:
                        # XSD choice can select a sequence of fields as one atomic
                        # alternative (e.g. Name+Regexp). Preserve the pair.
                        if not field.children or not all(isinstance(part, Element)
                                                          for part in field.children):
                            raise NotImplementedError('Nested XML choice sequence requires fields at '
                                                      + resource + pointer)
                        group_name = ''.join(part.name for part in field.children)
                        field = Element(group_name, self._synthetic(
                            owner, group_name, pointer + '/' + tag + '/' + str(i),
                            'synthetic_group_type', field, kind, resource),
                            element_kind=ElementKind.EMBEDDED)
                    if not isinstance(field, Element) or field.max_item_count != 1:
                        raise NotImplementedError('XML choice requires single-valued element '
                                                  'alternatives at ' + pointer)
                    variant_path = pointer + '/' + tag + '/' + str(i)
                    variant = self._synthetic(owner, field.name, variant_path,
                        'synthetic_choice_variant_type',
                        ElementList(Composition.SEQUENCE, (field,)), kind, resource, i)
                    selected.append(replace(field, structure=variant,
                                            min_item_count=0, max_item_count=1))
                children = selected
            return ElementList(composition, tuple(children), minimum, maximum)
        if tag in ('complexType', 'complexContent', 'extension', 'restriction'):
            groups = []
            for child in element:
                if child.tag in (XS + 'sequence', XS + 'all', XS + 'choice',
                                 XS + 'complexContent', XS + 'extension', XS + 'restriction', XS + 'group'):
                    group = self._xml_node(child, owner, pointer + '/' + child.tag[len(XS):],
                                           resource, declared, namespace, scopes, optional_context)
                    if group is not None:
                        groups.append(group)
                elif child.tag == XS + 'attribute':
                    groups.append(self._xml_node(child, owner, pointer + '/attribute/' + child.get('name', '?'),
                                                 resource, declared, namespace, scopes, optional_context))
                elif child.tag == XS + 'anyAttribute':
                    self._xml_node(child, owner, pointer + '/anyAttribute',
                                   resource, declared, namespace, scopes, optional_context)
                elif child.tag != XS + 'annotation' and child.tag.startswith(XS):
                    raise NotImplementedError('Unsupported XML complexType child: ' + child.tag[len(XS):])
            if len(groups) == 1 and isinstance(groups[0], ElementList):
                return groups[0]
            # xs:attribute siblings of xs:sequence/all are direct properties of
            # the same complexType, not a second nested DataObject group.
            # Preserve the original group when it has special occurrence/choice
            # semantics, rather than incorrectly flattening such a structure.
            particles = [group for group in groups if isinstance(group, ElementList)]
            if particles:
                # A choice together with attributes is legal XSD 1.0: the
                # attribute belongs to the containing complexType while one
                # of its child element branches is selected. Preserve the
                # choice as a transparent embedded semantic field, so we do
                # not flatten it into nonexclusive optional properties.
                if (len(particles) == 1 and
                        particles[0].composition is Composition.CHOICE and
                        (particles[0].min_item_count, particles[0].max_item_count) == (1, 1)):
                    choice = self._synthetic(owner, 'Choice', pointer + '/choice',
                                             'synthetic_group_type', particles[0], kind, resource)
                    embedded = Element('Choice', choice, element_kind=ElementKind.EMBEDDED,
                        source_bindings=self._binding(kind, resource, pointer + '/choice', 'embedded_group'))
                    return ElementList(Composition.SEQUENCE, (embedded,) + tuple(
                        group for group in groups if not isinstance(group, ElementList)))
                if (len(particles) != 1 or particles[0].composition not in
                        (Composition.SEQUENCE, Composition.ALL) or
                        (particles[0].min_item_count, particles[0].max_item_count) != (1, 1)):
                    raise NotImplementedError('XML group plus attributes requires an unbounded '
                                              'SEQUENCE/ALL-compatible field model at ' + pointer)
                flattened = tuple(child for group in groups for child in
                                  (group.children if isinstance(group, ElementList) else (group,)))
                return ElementList(particles[0].composition, flattened)
            return ElementList(Composition.SEQUENCE, tuple(groups))
        if tag == 'attribute':
            if element.get('ref'):
                raise NotImplementedError('Referenced XML attribute requires resolver at ' + pointer)
            name = element.get('name')
            if not name:
                raise ValueError('Local XSD attribute requires a name at ' + pointer)
            usage = element.get('use', 'optional')
            if usage not in ('required', 'optional'):
                raise NotImplementedError('Unsupported XSD attribute use ' + usage + ' at ' + pointer)
            wire = self._xml_wire(element, name, namespace, 'ATTRIBUTE')
            if element.get('type'):
                source, type_name = self._xml_type_reference(element, element.get('type'), declared, namespace, scopes)
                if source == 'declared':
                    definition = self._xml_simple_types.get(type_name)
                    resolved = (self._xml_node(definition, owner, pointer, resource,
                                declared, namespace, scopes) if definition is not None else None)
                    value = resolved if isinstance(resolved, Scalar) else TypeNode(
                        type_name, element.get('type').rsplit(':', 1)[-1], Origin.DECLARED,
                        (owner, name), (), None, Resolution.REFERENCE,
                        self._binding(kind, resource, pointer, 'xs:attribute/@type'))
                else:
                    scalar = self._xsd_scalar(type_name)
                    if scalar is ScalarKind.ANY:
                        raise NotImplementedError('Unsupported XSD attribute scalar ' + type_name + ' at ' + pointer)
                    value = Scalar(scalar)
            elif element.find(XS + 'simpleType') is not None:
                value = self._xml_node(element.find(XS + 'simpleType'), owner, pointer,
                                       resource, declared, namespace, scopes)
            else:
                value = Scalar(ScalarKind.STRING)
            if isinstance(value, EnumNode) and not element.get('type'):
                value = self._synthetic(owner, name, pointer,
                    'synthetic_inline_enum_type', value, kind, resource)
            return Element(name, value, source_bindings=self._binding(kind, resource, pointer, 'xs:attribute'),
                           min_item_count=1 if usage == 'required' else 0, max_item_count=1,
                           description=self._xsd_description(element), xml_wire=wire,
                           **self._xml_default(element, value, attribute=True))
        if tag == 'element':
            if element.get('nillable', 'false') != 'false':
                raise NotImplementedError('Nillable XSD elements require null semantics at ' + pointer)
            if 'substitutionGroup' in element.attrib:
                raise NotImplementedError('XSD substitutionGroup requires an element resolver at ' + pointer)
            key_nodes = [child for child in element if child.tag in (XS + 'key', XS + 'unique')]
            if any(child.tag in (XS + 'keyref', XS + 'identityConstraint') for child in element):
                raise NotImplementedError('XSD keyref/identityConstraint unsupported at ' + pointer)
            if element.get('ref'):
                raise NotImplementedError('External XML element declaration references require an element resolver')
            name = element.get('name') or element.get('ref') or 'unnamed'
            raw_type = element.get('type', '')
            nested = None
            if raw_type:
                source, type_name = self._xml_type_reference(
                    element, raw_type, declared, namespace, scopes)
                if source == 'declared':
                    definition = self._xml_simple_types.get(type_name)
                    resolved = (self._xml_node(definition, owner, pointer, resource,
                                declared, namespace, scopes) if definition is not None else None)
                    value = resolved if isinstance(resolved, Scalar) else TypeNode(
                        type_name, raw_type.rsplit(':', 1)[-1], Origin.DECLARED,
                        (owner, name), (), None, Resolution.REFERENCE,
                        self._binding(kind, resource, pointer, 'xs:element/@type'))
                else:
                    builtin = self._xsd_scalar(type_name)
                    if builtin is ScalarKind.ANY and type_name not in ('anyType', 'anySimpleType'):
                        raise NotImplementedError(
                            f'Unsupported XSD built-in type {type_name!r} at {resource}{pointer}')
                    value = Scalar(builtin)
            else:
                nested = element.find(XS + 'complexType')
                if nested is None:
                    nested = element.find(XS + 'simpleType')
                value = (self._xml_node(nested, owner, pointer, resource, declared, namespace, scopes)
                         if nested is not None else Scalar(ScalarKind.ANY))
            if isinstance(value, EnumNode) and not raw_type:
                value = self._synthetic(owner, name, pointer,
                    'synthetic_inline_enum_type', value, kind, resource)
            scoped_keys = []
            if key_nodes:
                # xs:key and xs:unique constrain an *occurrence* of this element,
                # never the nominal complex type referred to by its @type.
                # Read the declaration solely to validate the selector. Do not
                # replace `value` or emit a synthetic clone of the shared TYPE.
                validation_group = value if isinstance(value, ElementList) else None
                if isinstance(value, TypeNode):
                    declaration = self._xml_complex_types.get(value.identity)
                    if declaration is not None:
                        validation_group = self._xml_node(
                            declaration, owner, pointer + '/@type', resource,
                            declared, namespace, scopes)
                    else:
                        imported = self._external_xsd_complex_types.get(value.identity)
                        if imported is not None:
                            declaration, imported_scopes, imported_ns, imported_resource = imported
                            imported_declared = {
                                identity.rsplit('}', 1)[-1]
                                for identity in self._external_xsd_complex_types
                                if identity.startswith('{' + imported_ns + '}')}
                            validation_group = self._xml_node(
                                declaration, owner, pointer + '/@type', imported_resource,
                                imported_declared, imported_ns, imported_scopes)
                if not isinstance(validation_group, ElementList):
                    raise NotImplementedError('Local XSD keys require a resolved object TYPE at '
                                              + resource + pointer + ': ' + raw_type)
                for key_index, constraint in enumerate(key_nodes):
                    identifier = constraint.get('name', '')
                    selector_nodes = constraint.findall(XS + 'selector')
                    fields = constraint.findall(XS + 'field')
                    if len(selector_nodes) != 1 or not fields or not identifier:
                        raise ValueError('XSD key/unique requires a name, selector and fields at '
                                         + resource + pointer)
                    selector = selector_nodes[0].get('xpath', '')
                    if not selector or any(not field.get('xpath') for field in fields):
                        raise ValueError('Missing XSD key XPath at ' + resource + pointer)
                    selected = selector.removeprefix('./')
                    # XPath prefixes are expanded using the namespace scope
                    # of the selector declaration, not by silently stripping
                    # lexical prefixes. Reject axes/predicates and mismatches.
                    if '/' in selected or '[' in selected or '*' in selected or '(' in selected:
                        raise NotImplementedError('Unsupported XSD key XPath selector ' + selector
                                                  + ' at ' + resource + pointer)
                    if ':' in selected:
                        prefix, local = selected.split(':', 1)
                        uri = scopes.get(id(selector_nodes[0]), scopes.get(id(constraint), {})).get(prefix)
                        if not uri or not local:
                            raise ValueError('Unbound XSD key selector prefix: ' + selector
                                             + ' at ' + resource + pointer)
                    else:
                        local, uri = selected, ''
                    matches = [child for child in validation_group.children
                               if isinstance(child, ListNode) and child.name == local
                               and (child.xml_wire.namespace_uri if child.xml_wire else '') == uri]
                    if len(matches) != 1:
                        raise NotImplementedError('XSD key selector must target exactly one directly '
                                                  'repeated element: ' + selector + ' at '
                                                  + resource + pointer)
                    scoped_keys.append(KeyDefinition(
                        identifier, local,
                        pointer + '/' + constraint.tag[len(XS):] + '/' + str(key_index),
                        tuple(field.get('xpath') for field in fields),
                        constraint.tag == XS + 'key'))
                if len(scoped_keys) != len({key.identifier for key in scoped_keys}):
                    raise ValueError('Repeated XSD key identity within ' + resource + pointer)
            if nested is not None and isinstance(value, ElementList):
                value = self._synthetic(owner, name, pointer,
                    'synthetic_property_type', value, kind, resource)
            minimum = self._xml_occurs(element.get('minOccurs', '1'), pointer, False)
            maximum = self._xml_occurs(element.get('maxOccurs', '1'), pointer, True)
            wire = self._xml_wire(element, name, namespace, 'ELEMENT')
            if maximum == -1 or maximum > 1:
                if scoped_keys:
                    raise NotImplementedError('Contextual XSD keys on a repeated owner element '
                                              'require a separate owner scope at ' + resource + pointer)
                if 'default' in element.attrib or 'fixed' in element.attrib:
                    raise NotImplementedError('XML repeated element defaults/fixed require per-item metadata: ' + pointer)
                return ListNode(name, value, minimum, maximum, xml_wire=wire)
            return Element(name, value, key_definitions=tuple(scoped_keys),
                           source_bindings=self._binding(kind, resource, pointer, 'xs:element'),
                           min_item_count=minimum, max_item_count=maximum, description=self._xsd_description(element),
                           xml_wire=wire, **self._xml_default(element, value))
        raise ValueError('Unsupported XML schema node: ' + tag)

    def _xml_wire(self, element, name, target_namespace, kind):
        """Resolve local element/attribute wire QName from schema form defaults."""
        default = self._xml_element_form if kind == 'ELEMENT' else self._xml_attribute_form
        form = element.get('form', default)
        if form not in ('qualified', 'unqualified'):
            raise ValueError('Invalid XML form for ' + name + ': ' + form)
        return XmlWire(target_namespace if form == 'qualified' else '', name, kind)

    @staticmethod
    def _xsd_description(element):
        """Return the original xs:documentation content, not annotation markup."""
        node = element.find(XS + 'annotation/' + XS + 'documentation')
        return ''.join(node.itertext()).strip() if node is not None else ''

    @staticmethod
    def _xml_occurs(value, pointer, upper):
        """Parse XSD occurrence bound, preserving its unbounded sentinel."""
        if value == 'unbounded' and upper:
            return -1
        if not value.isdigit():
            raise ValueError(f'Invalid XSD occurrence value at {pointer}: {value!r}')
        return int(value)

    @staticmethod
    def _xsd_scalar(name):
        t = (name or '').split(':')[-1]
        if t in ('string', 'normalizedString', 'token', 'anyURI', 'date', 'dateTime'):
            return ScalarKind.STRING
        if t in ('int', 'integer', 'long', 'short', 'positiveInteger', 'nonNegativeInteger'):
            return ScalarKind.INTEGER
        if t in ('decimal', 'float', 'double'):
            return ScalarKind.NUMBER
        if t == 'boolean':
            return ScalarKind.BOOLEAN
        return ScalarKind.ANY
