"""Independent YAMLDEFS/JSONDEFS/XMLDEFS canonical frontend for the next Defs generator.

Input syntax becomes seven canonical node kinds; temporary references use a
resolution state, never another kind. The legacy ``.old`` implementation is
not imported. No XML->MAP mapping or patternProperties support. Local
xs:key/xs:unique is supported only for direct typed child lists; xs:keyref and
global identity constraints remain unsupported.
"""
from __future__ import annotations

from collections.abc import Mapping
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import replace
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

from eu.algites.tool.codegen.common.naming_profiles import AIcdCodegenNamingProfile
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgd_jElement_1 as Element, AIcgd_jElementList_1 as ElementList,
    AIcgd_jList_1 as ListNode, AIcgd_jMap_1 as MapNode,
    AIcgd_jScalar_1 as Scalar, AIcgd_jEnum_1 as EnumNode,
    AIcgd_jEnumValue_1 as EnumValue, AIcgd_jType_1 as TypeNode,
    AIcgd_jSourceBinding_1 as Binding,
    AIcgd_jKeyDefinition_1 as KeyDefinition,
    AIcgd_jXmlWireName_1 as XmlWire,
    AIigComposition_1 as Composition, AIigMapKind_1 as MapKind,
    AIigResolutionState_1 as Resolution, AIigScalarKind_1 as ScalarKind,
    AIigSourceInputKind_1 as SourceKind, AIigTypeOrigin_1 as Origin,
    freeze_bindings)

XS_URI = 'http://www.w3.org/2001/XMLSchema'
XS = '{' + XS_URI + '}'
SCALAR_TYPES = {'string': ScalarKind.STRING, 'integer': ScalarKind.INTEGER,
                'number': ScalarKind.NUMBER, 'boolean': ScalarKind.BOOLEAN,
                'null': ScalarKind.NULL}


def _pointer(name: str) -> str:
    """Escape one JSON Pointer segment, preserving the exact property location."""
    return name.replace('~', '~0').replace('/', '~1')


class AIcDefsCodegenCanonicalSchemaFrontend:
    """Constructs canonical immutable nodes with configured synthetic type names."""

    def __init__(self, naming: AIcdCodegenNamingProfile):
        if not isinstance(naming, AIcdCodegenNamingProfile):
            raise TypeError('A resolved Common and Defs naming profile is required')
        self.naming = naming

    @staticmethod
    def _binding(kind, resource, pointer, representation):
        return freeze_bindings({kind: [Binding(resource, pointer, representation)]})

    def _synthetic(self, owner, name, pointer, role, structure, kind, resource, index=None):
        """Synthesize a TYPE before normalization and retain its semantic path."""
        return TypeNode(resource + pointer + '#synthetic:' + role,
            self.naming.synthetic_type_name(role, owner, name, index), Origin.SYNTHETIC,
            (owner, role, name) + (() if index is None else (str(index),)),
            (), structure, Resolution.RESOLVED, self._binding(kind, resource, pointer, role))

    def load_json_or_yaml(self, source: Mapping[str, Any], resource: str, kind: SourceKind):
        """Return one declared TYPE; JSONDEFS and YAMLDEFS follow identical rules."""
        if kind not in (SourceKind.JSONDEFS, SourceKind.YAMLDEFS):
            raise ValueError('Source family must be JSONDEFS or YAMLDEFS')
        if not isinstance(source, Mapping):
            raise TypeError('Schema must be a mapping')
        name = str(source.get('title') or PurePosixPath(resource).name.split('.')[0])
        identity = str(source.get('x-algites-schema-id') or source.get('$id') or resource)
        inherited = tuple(x['$ref'] for x in source.get('allOf', ())
                          if isinstance(x, Mapping) and isinstance(x.get('$ref'), str))
        node = self._json_node(source, name, '#', kind, resource)
        return TypeNode(identity, name, Origin.DECLARED, (name,),
            inherited, node, Resolution.RESOLVED, self._binding(kind, resource, '#', 'root'),
            schema_version=str(source.get('x-algites-schema-version', '')),
            description=str(source.get('description') or ''))

    def load_json_or_yaml_types(self, source: Mapping[str, Any], resource: str,
                                kind: SourceKind):
        """Load every named $defs declaration plus the optional document root.

        A library schema containing only $defs produces only its named definitions;
        a normal schema produces its root first, followed by ordered declarations.
        No declaration is overwritten by another definition with a similar name.
        """
        if not isinstance(source, Mapping):
            raise TypeError('Schema must be a mapping')
        if kind not in (SourceKind.JSONDEFS, SourceKind.YAMLDEFS):
            raise ValueError('Source family must be JSONDEFS or YAMLDEFS')
        roots = []
        if any(field in source for field in ('type', 'properties', 'additionalProperties',
                                             'items', 'prefixItems', '$ref', 'oneOf', 'anyOf', 'enum',
                                             'required', 'minItems', 'maxItems', 'allOf')) \
                or not ('$defs' in source or 'definitions' in source):
            roots.append(self.load_json_or_yaml(source, resource, kind))
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
                inherited = tuple(part['$ref'] for part in definition.get('allOf', ())
                                  if isinstance(part, Mapping) and isinstance(part.get('$ref'), str))
                roots.append(TypeNode(definition_id, str(name),
                    Origin.DECLARED, (str(name),), inherited, structure, Resolution.RESOLVED,
                    self._binding(kind, resource, pointer, container),
                    schema_version=str(definition.get('x-algites-schema-version',
                        source.get('x-algites-schema-version', ''))),
                    description=str(definition.get('description') or '')))
        return tuple(roots)

    def _json_node(self, obj, owner, path, kind, resource):
        if not isinstance(obj, Mapping):
            raise ValueError('Expected inline schema mapping at ' + path)
        unsupported = {'not', 'if', 'then', 'else', 'contains', 'unevaluatedItems',
                       'unevaluatedProperties', 'patternProperties', 'dependentSchemas',
                       'propertyNames', '$dynamicRef', '$recursiveRef', 'const',
                       'dependencies', 'additionalItems',
                       'minLength', 'maxLength', 'pattern', 'contentEncoding', 'contentMediaType', 'contentSchema', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf', 'uniqueItems', 'minProperties', 'maxProperties', 'dependentRequired', 'minContains', 'maxContains', 'readOnly', 'writeOnly'}
        unknown = unsupported.intersection(obj)
        if unknown:
            raise NotImplementedError('Unsupported schema keywords at ' + path + ': '
                                      + ', '.join(sorted(unknown)))
        if 'allOf' in obj and any(not isinstance(part, Mapping) or '$ref' not in part
                                  for part in obj['allOf']):
            raise NotImplementedError('Inline allOf is not yet canonicalized at ' + path)
        if isinstance(obj.get('$ref'), str):
            ref = obj['$ref']
            return TypeNode(ref, ref.rsplit('/', 1)[-1], Origin.DECLARED,
                (owner, ref), (), None, Resolution.REFERENCE,
                self._binding(kind, resource, path, '$ref'))
        if 'anyOf' in obj:
            raise NotImplementedError('Unsupported oneOf/anyOf: anyOf may match multiple branches; CHOICE cannot represent it at ' + path)
        t = obj.get('type')
        if isinstance(t, list):
            # Taking the first non-null branch silently loses JSON Schema union
            # semantics, including nullable values. Do not miscompile them.
            if len(t) != 1 or not isinstance(t[0], str):
                raise NotImplementedError('JSON Schema type unions (including nullable types) '
                                          'are not yet canonicalized at ' + path)
            t = t[0]
        if t is not None and (not isinstance(t, str) or t not in
                              ('object', 'array', 'string', 'integer', 'number', 'boolean', 'null')):
            raise ValueError('Unknown JSON Schema type at ' + path + ': ' + repr(t))
        if isinstance(obj.get('additionalProperties'), bool) and obj['additionalProperties']:
            raise NotImplementedError('Explicit additionalProperties:true cannot be '
                                      'represented losslessly at ' + path)
        if isinstance(obj.get('items'), bool):
            raise NotImplementedError('Boolean items constraints are not yet canonicalized at ' + path)
        if 'enum' in obj:
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
            return EnumNode(base, tuple(EnumValue(str(item).lower() if isinstance(item, bool)
                                                  else str(item)) for item in items))
        for choice in ('oneOf',):
            if choice in obj:
                branches = obj[choice]
                if not isinstance(branches, list) or not branches:
                    raise ValueError('Invalid ' + choice + ' at ' + path)
                children = []
                for i, branch in enumerate(branches):
                    pointer = f'{path}/{choice}/{i}'
                    node = self._json_node(branch, owner, pointer, kind, resource)
                    generated = self._synthetic(owner, choice, pointer,
                        'synthetic_choice_variant_type', node, kind, resource, i)
                    name = self.naming.method_name('positional_item_synthetic_getter',
                                                  position=str(self.naming.positional_number(i)))
                    children.append(Element(name, generated,
                        source_bindings=self._binding(kind, resource, pointer, choice)))
                return ElementList(Composition.CHOICE, tuple(children))
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
            for name, child in properties.items():
                pointer = path + '/properties/' + _pointer(str(name))
                node = self._json_node(child, owner, pointer, kind, resource)
                if isinstance(node, ElementList):
                    node = self._synthetic(owner, str(name), pointer,
                        'synthetic_property_type', node, kind, resource)
                members.append(Element(str(name), node,
                    source_bindings=self._binding(kind, resource, pointer, 'properties'),
                    min_occurs=int(name in required), max_occurs=1,
                    description=str(child.get('description') or '') if isinstance(child, Mapping) else ''))
            additional = obj.get('additionalProperties')
            if isinstance(additional, Mapping):
                pointer = path + '/additionalProperties'
                value = self._json_node(additional, owner, pointer, kind, resource)
                if isinstance(value, ElementList):
                    value = self._synthetic(owner, 'additionalProperties', pointer,
                        'synthetic_map_value_type', value, kind, resource)
                key = Scalar(ScalarKind.STRING)
                # Integrated property maps are direct ELEMENTLIST children, not
                # synthetic ELEMENT wrappers. This preserves the seven-kind model.
                members.append(MapNode('additionalProperties',
                    MapKind.INTEGRATED_PROPERTY_MAP, key, value,
                    self._binding(kind, resource, pointer, 'additionalProperties')))
            return ElementList(Composition.SEQUENCE, tuple(members))
        if t == 'array' or 'items' in obj or 'prefixItems' in obj:
            minimum = obj.get('minItems', 0)
            maximum = obj.get('maxItems', -1)
            if (type(minimum) is not int or type(maximum) is not int
                    or minimum < 0 or maximum < -1 or (maximum != -1 and maximum < minimum)):
                raise ValueError('Invalid minItems/maxItems bounds at ' + path)
            if 'prefixItems' in obj and ('minItems' in obj or 'maxItems' in obj):
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
                if isinstance(node, ElementList):
                    node = self._synthetic(owner, 'item', pointer,
                        'synthetic_list_item_type', node, kind, resource)
                rest = ListNode('items', node, minimum, maximum)
                if not items:
                    return rest
                items.append(rest)
            if not items:
                # In Draft 2020-12 an unconstrained array still allows items.
                return ListNode('items', Scalar(ScalarKind.ANY), minimum, maximum)
            if 'items' not in obj:
                # Prefix items do not close the tuple; additional items are allowed.
                items.append(ListNode('items', Scalar(ScalarKind.ANY)))
            return ElementList(Composition.SEQUENCE, tuple(items))
        if 'required' in obj:
            raise ValueError('required is valid only for object schemas at ' + path)
        if 'minItems' in obj or 'maxItems' in obj:
            raise ValueError('minItems/maxItems require an array schema at ' + path)
        return Scalar(SCALAR_TYPES.get(t, ScalarKind.ANY), str(obj.get('format') or ''))

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

    def load_xsd(self, text: str | bytes, resource: str):
        """Read named XSD types while retaining sequence/all/choice and list semantics.

        XML→MAP and keyref interpretation are intentionally not performed.
        Local xs:key/xs:unique rules are linked only to inline, directly
        repeated list members; incomplete or global constraints fail closed.
        """
        # Namespace prefixes in QName-valued XSD attributes are lexical, not
        # part of the type name. Preserve each element's in-scope declarations.
        xml = text.encode('utf-8') if isinstance(text, str) else text
        parser = ET.iterparse(BytesIO(xml), events=('start-ns', 'start', 'end'))
        scopes: dict[int, dict[str, str]] = {}
        stack: list[dict[str, str]] = []
        pending: dict[str, str] = {}
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
        schema = parser.root
        if schema.tag != XS + 'schema':
            raise ValueError('Expected an xs:schema')
        # Global elements are not part of the named-type frontend. Never
        # silently discard their identity constraints. Local key/unique rules
        # are bound to an inline typed container below in _xml_node().
        if any(node.tag in (XS + 'keyref', XS + 'identityConstraint') for node in schema.iter()):
            raise NotImplementedError('XSD keyref/identityConstraint needs a dedicated resolver')
        if any(node.tag in (XS + 'key', XS + 'unique') for child in schema
               if child.tag == XS + 'element' for node in child.iter()):
            raise NotImplementedError('Global XML element identity constraints require global-element loading')
        for child in schema:
            if child.tag in (XS + 'include', XS + 'import', XS + 'redefine', XS + 'override'):
                raise NotImplementedError('External XML schema composition requires a schema resolver')
        if schema.get('elementFormDefault', 'unqualified') not in ('qualified', 'unqualified') or schema.get('attributeFormDefault', 'unqualified') not in ('qualified', 'unqualified'):
            raise ValueError('Invalid XSD element/attribute form default')
        self._xml_element_form = schema.get('elementFormDefault', 'unqualified')
        self._xml_attribute_form = schema.get('attributeFormDefault', 'unqualified')
        named = [child for child in schema if child.tag in (XS + 'complexType', XS + 'simpleType')
                 and child.get('name')]
        declared = {child.get('name') for child in named}
        namespace = schema.get('targetNamespace', '')
        result = []
        for child in named:
            name = child.get('name')
            node = self._xml_node(child, name, '/schema/' + name, resource,
                                  declared, namespace, scopes)
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
                    schema.get('x-algites-schema-version') or ''),
                description=self._xsd_description(child)))
        return tuple(result)

    @staticmethod
    def _xml_type_reference(element, qname, declared, target_namespace, scopes):
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
        raise NotImplementedError(f'Unresolved or external XSD QName {qname!r} (namespace {uri!r})')

    def _xml_node(self, element, owner, pointer, resource, declared, namespace, scopes):
        kind = SourceKind.XMLDEFS
        tag = element.tag[len(XS):]
        if tag == 'simpleType':
            restriction = element.find(XS + 'restriction')
            if restriction is not None:
                unsupported = [child.tag[len(XS):] for child in restriction
                               if child.tag.startswith(XS) and child.tag not in
                               (XS + 'enumeration', XS + 'annotation')]
                if unsupported:
                    raise NotImplementedError('Unsupported XML restriction facets: ' + ', '.join(unsupported))
                values = restriction.findall(XS + 'enumeration')
                source, value = self._xml_type_reference(
                    restriction, restriction.get('base'), declared, namespace, scopes)
                if source != 'builtin':
                    raise NotImplementedError('Named XSD simpleType restrictions are not yet canonicalized')
                scalar = self._xsd_scalar(value)
                if scalar is ScalarKind.ANY and value not in ('anyType', 'anySimpleType'):
                    raise NotImplementedError('Unsupported XSD scalar base ' + value)
                return (EnumNode(scalar, tuple(EnumValue(item.get('value', '')) for item in values))
                        if values else Scalar(scalar))
            if any(child.tag != XS + 'annotation' for child in element):
                raise NotImplementedError('Unsupported XML simpleType without xs:restriction at ' + pointer)
            return Scalar(ScalarKind.ANY)
        if tag in ('sequence', 'all', 'choice'):
            composition = {'sequence': Composition.SEQUENCE, 'all': Composition.ALL,
                           'choice': Composition.CHOICE}[tag]
            children = []
            for i, child in enumerate(element):
                if child.tag in (XS + 'element', XS + 'sequence', XS + 'all', XS + 'choice'):
                    children.append(self._xml_node(child, owner,
                        pointer + '/' + tag + '/' + str(i), resource, declared, namespace, scopes))
                elif child.tag != XS + 'annotation':
                    raise NotImplementedError('Unsupported XML group child ' + str(child.tag) + ' at ' + pointer)
            minimum = self._xml_occurs(element.get('minOccurs', '1'), pointer, False)
            maximum = self._xml_occurs(element.get('maxOccurs', '1'), pointer, True)
            return ElementList(composition, tuple(children), minimum, maximum)
        if tag in ('complexType', 'complexContent', 'extension', 'restriction'):
            groups = []
            for child in element:
                if child.tag in (XS + 'sequence', XS + 'all', XS + 'choice',
                                 XS + 'complexContent', XS + 'extension', XS + 'restriction'):
                    groups.append(self._xml_node(child, owner, pointer + '/' + child.tag[len(XS):],
                                                  resource, declared, namespace, scopes))
                elif child.tag == XS + 'attribute':
                    groups.append(self._xml_node(child, owner, pointer + '/attribute/' + child.get('name', '?'),
                                                 resource, declared, namespace, scopes))
                elif child.tag != XS + 'annotation' and child.tag.startswith(XS):
                    raise NotImplementedError('Unsupported XML complexType child: ' + child.tag[len(XS):])
            return (groups[0] if len(groups) == 1 and isinstance(groups[0], ElementList) else
                    ElementList(Composition.SEQUENCE, tuple(groups)))
        if tag == 'attribute':
            if element.get('ref') or element.get('default') is not None or element.get('fixed') is not None:
                raise NotImplementedError('Referenced/defaulted/fixed XML attribute requires more semantics at ' + pointer)
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
                    value = TypeNode(type_name, element.get('type').rsplit(':', 1)[-1], Origin.DECLARED,
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
            return Element(name, value, source_bindings=self._binding(kind, resource, pointer, 'xs:attribute'),
                           min_occurs=1 if usage == 'required' else 0, max_occurs=1,
                           description=self._xsd_description(element), xml_wire=wire)
        if tag == 'element':
            unsupported = ('default', 'fixed', 'nillable', 'substitutionGroup')
            if any(option in element.attrib for option in unsupported):
                raise NotImplementedError('Unsupported XSD element facet at ' + pointer + ': ' +
                    ', '.join(option for option in unsupported if option in element.attrib))
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
                    value = TypeNode(type_name, raw_type.rsplit(':', 1)[-1], Origin.DECLARED,
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
            if key_nodes:
                if raw_type or not isinstance(value, ElementList):
                    raise NotImplementedError('Local XSD keys require an inline complexType at ' + pointer)
                children = list(value.children)
                for key_index, constraint in enumerate(key_nodes):
                    identifier = constraint.get('name', '')
                    selector_nodes = constraint.findall(XS + 'selector')
                    fields = constraint.findall(XS + 'field')
                    if len(selector_nodes) != 1 or not fields or not identifier:
                        raise ValueError('XSD key/unique requires a name, selector and fields at ' + pointer)
                    selector = selector_nodes[0].get('xpath', '')
                    if not selector or any(not field.get('xpath') for field in fields):
                        raise ValueError('Missing XSD key XPath at ' + pointer)
                    source_pointer = pointer + '/' + constraint.tag[len(XS):] + '/' + str(key_index)
                    key = KeyDefinition(identifier, selector, source_pointer,
                                        tuple(field.get('xpath') for field in fields),
                                        constraint.tag == XS + 'key')
                    selected = selector.removeprefix('./')
                    hits = [i for i, child in enumerate(children)
                            if isinstance(child, ListNode) and child.name == selected]
                    if len(hits) != 1:
                        raise NotImplementedError('XSD key selector must target exactly one directly repeated element: '
                                                  + selector + ' at ' + pointer)
                    index = hits[0]
                    children[index] = replace(children[index],
                        key_definitions=children[index].key_definitions + (key,))
                value = replace(value, children=tuple(children))
                if len(key_nodes) != len({key.get('name') for key in key_nodes}):
                    raise ValueError('Repeated XSD key identity within ' + pointer)
            if nested is not None and isinstance(value, ElementList):
                value = self._synthetic(owner, name, pointer,
                    'synthetic_property_type', value, kind, resource)
            minimum = self._xml_occurs(element.get('minOccurs', '1'), pointer, False)
            maximum = self._xml_occurs(element.get('maxOccurs', '1'), pointer, True)
            wire = self._xml_wire(element, name, namespace, 'ELEMENT')
            if maximum == -1 or maximum > 1:
                return ListNode(name, value, minimum, maximum, xml_wire=wire)
            return Element(name, value, source_bindings=self._binding(kind, resource, pointer, 'xs:element'),
                           min_occurs=minimum, max_occurs=maximum, description=self._xsd_description(element),
                           xml_wire=wire)
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
