from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET

from eu.algites.tool.codegen.defs.aic_definition_identity_resolver import AIcDefinitionIdentityResolver
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_definition_reference import AIcdDefinitionReference
from eu.algites.tool.codegen.defs.aicd_enum_value_definition import AIcdEnumValueDefinition
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.tool.codegen.defs.aic_scalar_constraints import defaults, decimal_text
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind


@dataclass(frozen=True)
class _AIcdXmlShape:
    """Internal normalized shape of an XML property or list item."""
    kind: AInValueKind
    item_kind: AInValueKind | None = None
    reference: AIcdDefinitionReference | None = None
    constraints: AIcdValueConstraints = AIcdValueConstraints()
    item_constraints: AIcdValueConstraints = AIcdValueConstraints()


class AIcXmlDefsFrontend:
    """Retain XSD scalar semantics, local restrictions and canonical subschema references."""
    source_kind = AInDefinitionSourceKind.XMLDEFS
    _ns = 'http://www.w3.org/2001/XMLSchema'
    _xs = '{' + _ns + '}'
    _strings = set('string normalizedString token language Name NCName NMTOKEN ID IDREF ENTITY duration dateTime time date gYearMonth gYear gMonthDay gDay gMonth hexBinary base64Binary anyURI QName NOTATION dateTimeStamp yearMonthDuration dayTimeDuration'.split())
    _integers = set('integer nonPositiveInteger negativeInteger long int short byte nonNegativeInteger unsignedLong unsignedInt unsignedShort unsignedByte positiveInteger'.split())

    def __init__(self):
        self._identities = AIcDefinitionIdentityResolver()

    def load(self, request):
        resource = self._parse(request.path)
        root = resource[0]
        version = int(root.attrib['version']) if root.attrib.get('version', '').isdigit() else None
        parsed = self._identities.from_file(request, version)
        identity = root.attrib.get('targetNamespace') or parsed.logical_name
        typ = self._root_type(root)
        values = self._enum_values(typ)
        description = self._documentation(typ) or self._documentation(root)
        if values:
            return AIcdCanonicalDefinition(identity, parsed.version, parsed.logical_name, AInDefinitionKind.ENUM,
                self.source_kind, str(request.path), description, enum_values=values)
        if typ is not None and typ.tag == self._xs + 'complexType':
            props = tuple(self._elements(typ, False, request, resource))
            return AIcdCanonicalDefinition(identity, parsed.version, parsed.logical_name, AInDefinitionKind.OBJECT,
                self.source_kind, str(request.path), description, properties=props)
        element = self._child(root, 'element')
        shape = self._simple_shape(typ, request, resource, set()) if typ is not None else self._shape(element, element.get('type', ''), request, resource, set()) if element is not None else _AIcdXmlShape(AInValueKind.ANY)
        prop = AIcdPropertyDefinition('value', shape.kind, True, element is not None and element.get('nillable') in ('true','1'), shape.item_kind, shape.reference, description, shape.constraints, shape.item_constraints)
        return AIcdCanonicalDefinition(identity, parsed.version, parsed.logical_name, AInDefinitionKind.SCALAR,
            self.source_kind, str(request.path), description, properties=(prop,))

    def _elements(self, parent, optional, request, resource):
        for node in self._children(parent):
            kind = node.tag.removeprefix(self._xs)
            if kind in ('sequence', 'all', 'choice'):
                if kind == 'choice': raise ValueError(f'XSD choice is not represented by the canonical property model: {request.path}')
                yield from self._elements(node, optional or node.get('minOccurs') == '0', request, resource)
            elif kind == 'element':
                if 'name' not in node.attrib: raise ValueError(f'XSD element references require a named canonical property: {request.path}')
                shape = self._shape(node, node.get('type', ''), request, resource, set())
                repeated = node.get('maxOccurs', '1') != '1'
                if repeated and shape.kind is AInValueKind.ARRAY: raise ValueError('Nested XSD lists are not represented by the canonical property model')
                yield AIcdPropertyDefinition(node.get('name'), AInValueKind.ARRAY if repeated else shape.kind,
                    not optional and node.get('minOccurs') != '0', node.get('nillable') in ('true', '1'),
                    shape.kind if repeated else shape.item_kind, shape.reference, self._documentation(node),
                    AIcdValueConstraints() if repeated else shape.constraints,
                    shape.constraints if repeated else shape.item_constraints)

    def _shape(self, context, name, request, resource, visited):
        root, namespaces = resource
        if not name:
            if self._child(context, 'complexType') is not None: return _AIcdXmlShape(AInValueKind.OBJECT)
            simple = self._child(context, 'simpleType')
            return _AIcdXmlShape(AInValueKind.ANY) if simple is None else self._simple_shape(simple, request, resource, visited)
        local = name.split(':')[-1]
        namespace = namespaces[id(context)].get(name.split(':')[0] if ':' in name else '')
        if namespace == self._ns or (':' not in name and namespace is None and self._builtin(local) is not None):
            result = self._builtin(local)
            if result is None: raise ValueError(f"Unknown XSD built-in type '{name}'")
            return result
        key = (request.path.resolve(), namespace, local)
        if key in visited: raise ValueError(f"Circular XSD simple type '{name}'")
        visited.add(key)
        if namespace is None or namespace == root.get('targetNamespace'):
            typ = self._named_type(root, local)
            if typ is not None:
                return self._simple_shape(typ, request, resource, visited) if typ.tag == self._xs + 'simpleType' else _AIcdXmlShape(AInValueKind.OBJECT)
        for imp in self._children(root, 'import', 'include'):
            if imp.tag == self._xs+'import' and imp.get('namespace') != namespace: continue
            if imp.tag == self._xs+'include' and namespace is not None and namespace != root.get('targetNamespace'): continue
            location = imp.get('schemaLocation')
            if not location: continue
            uri = urlsplit(location)
            if uri.scheme and uri.scheme != 'file': raise ValueError(f'XSD imports must resolve locally: {location}')
            path = Path(unquote(uri.path)) if uri.scheme == 'file' else (request.path.resolve().parent / location).resolve()
            imported = self._parse(path); typ = self._named_type(imported[0], local)
            if typ is None: continue
            target = AIcdDefinitionLoadRequest(path, self.source_kind, request.naming_profile)
            enums = self._enum_values(typ)
            if typ.tag == self._xs+'simpleType' and not enums: return self._simple_shape(typ, target, imported, visited)
            raw_version = imported[0].get('version', '')
            parsed = self._identities.from_file(target, int(raw_version) if raw_version.isdigit() else None)
            return _AIcdXmlShape(AInValueKind.REFERENCE, reference=AIcdDefinitionReference(imported[0].get('targetNamespace'),
                parsed.version, parsed.logical_name, AInDefinitionKind.ENUM if enums else AInDefinitionKind.OBJECT))
        raise ValueError(f"Undefined XSD type '{name}' in {request.path}")

    def _simple_shape(self, typ, request, resource, visited):
        restriction = self._child(typ, 'restriction')
        if restriction is not None:
            base = self._shape(restriction, restriction.get('base', ''), request, resource, visited)
            kwargs = {}; values = []
            for facet in self._children(restriction):
                kind = facet.tag.removeprefix(self._xs); value = facet.get('value')
                if kind in ('minInclusive', 'minExclusive'): kwargs.update(minimum=decimal_text(value), exclusive_minimum=kind == 'minExclusive')
                elif kind in ('maxInclusive', 'maxExclusive'): kwargs.update(maximum=decimal_text(value), exclusive_maximum=kind == 'maxExclusive')
                elif kind == 'length': kwargs.update(min_length=int(value), max_length=int(value))
                elif kind == 'minLength': kwargs['min_length'] = int(value)
                elif kind == 'maxLength': kwargs['max_length'] = int(value)
                elif kind == 'pattern': kwargs['pattern'] = value
                elif kind == 'enumeration': values.append(value)
            if values: kwargs['enum_values'] = tuple(values)
            return replace(base, constraints=replace(base.constraints, **kwargs))
        listing = self._child(typ, 'list')
        if listing is not None:
            item = self._shape(listing, listing.get('itemType', ''), request, resource, visited)
            return _AIcdXmlShape(AInValueKind.ARRAY, item.kind, item.reference, item_constraints=item.constraints)
        raise ValueError(f'Unsupported XSD simple type in {request.path}')

    @classmethod
    def _builtin(cls, name):
        if name in cls._strings: return _AIcdXmlShape(AInValueKind.STRING, constraints=defaults(name))
        if name in cls._integers: return _AIcdXmlShape(AInValueKind.INTEGER, constraints=defaults(name))
        if name in ('decimal', 'float', 'double'): return _AIcdXmlShape(AInValueKind.NUMBER, constraints=defaults(name))
        if name == 'boolean': return _AIcdXmlShape(AInValueKind.BOOLEAN, constraints=defaults(name))
        if name in ('NMTOKENS', 'IDREFS', 'ENTITIES'): return _AIcdXmlShape(AInValueKind.ARRAY, AInValueKind.STRING, constraints=defaults(name), item_constraints=defaults('string'))
        if name in ('anyType', 'anySimpleType', 'anyAtomicType'): return _AIcdXmlShape(AInValueKind.ANY, constraints=defaults(None if name == 'anyType' else name))
        return None

    @staticmethod
    def _parse(path):
        contexts = {}; stack = []; pending = {}
        root = None
        for event, value in ET.iterparse(path, events=('start-ns', 'start', 'end')):
            if event == 'start-ns': pending[value[0]] = value[1]
            elif event == 'start':
                scope = dict(stack[-1]) if stack else {}; scope.update(pending); pending.clear()
                contexts[id(value)] = scope; stack.append(scope)
                if root is None: root = value
            else: stack.pop()
        return root, contexts

    @classmethod
    def _root_type(cls, root):
        for element in cls._children(root, 'element'):
            inline = cls._child(element, 'complexType', 'simpleType')
            if inline is not None: return inline
            named = cls._named_type(root, element.get('type', '').split(':')[-1])
            if named is not None: return named
        complex_type = cls._child(root, 'complexType')
        return complex_type if complex_type is not None else cls._child(root, 'simpleType')

    @classmethod
    def _children(cls, node, *names):
        return [] if node is None else [child for child in node if child.tag.startswith(cls._xs) and (not names or child.tag.removeprefix(cls._xs) in names)]

    @classmethod
    def _child(cls, node, *names):
        return next(iter(cls._children(node, *names)), None)

    @classmethod
    def _named_type(cls, root, name):
        return next((node for node in cls._children(root, 'complexType', 'simpleType') if node.get('name') == name), None)

    @classmethod
    def _enum_values(cls, typ):
        return tuple(AIcdEnumValueDefinition(value.get('value'), cls._documentation(value)) for value in cls._children(cls._child(typ, 'restriction'), 'enumeration'))

    @classmethod
    def _documentation(cls, node):
        doc = cls._child(cls._child(node, 'annotation'), 'documentation')
        return ' '.join(''.join(doc.itertext()).split()) or None if doc is not None else None
