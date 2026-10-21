from __future__ import annotations
from eu.algites.tool.codegen.defs.impl.standard._source_data_type import from_source_hints

from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET

from eu.algites.tool.codegen.defs.impl.standard.aic_definition_identity_resolver import AIcDefinitionIdentityResolver
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_definition_reference import AIcdDefinitionReference
from eu.algites.tool.codegen.defs.aicd_enum_value_definition import AIcdEnumValueDefinition
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.aicd_xml_field_representation import AIcdXmlFieldRepresentation
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.tool.codegen.defs.aicd_xml_element_declaration import AIcdXmlElementDeclaration
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.impl.standard.aic_scalar_constraints import defaults, decimal_text
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind


@dataclass(frozen=True)
class _AIcdXmlShape:
    """Internal normalized shape of an XML property or list item."""
    kind: AInDataTypeKind
    item_kind: AInDataTypeKind | None = None
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
        """Read an XSD source and normalize its types, fields and documentation."""
        resource = self._parse(request.path)
        root = resource[0]
        version = int(root.attrib['version']) if root.attrib.get('version', '').isdigit() else None
        parsed = self._identities.from_file(request, version)
        identity = root.attrib.get('targetNamespace') or parsed.logical_name
        typ = self._root_type(root)
        values = self._enum_values(typ)
        description = self._documentation(typ) or self._documentation(root)
        title = self._title(typ) or self._title(root)
        if values:
            return AIcdCanonicalDefinition(identity, parsed.version, parsed.logical_name, self.source_kind, str(request.path), description, AIcdDataType(AInDataTypeKind.ENUM), values, title)
        if typ is not None and typ.tag == self._xs + 'complexType':
            choice = self._root_choice(typ, request, resource)
            if choice is not None:
                return AIcdCanonicalDefinition(identity, parsed.version, parsed.logical_name, self.source_kind, str(request.path), description, choice, (), title)
            props = self._complex_properties(typ, request, resource, frozenset())
            names = [prop.source_name for prop in props]
            if len(names) != len(set(names)):
                raise ValueError(f'Duplicate XML element/attribute field in {request.path}')
            return AIcdCanonicalDefinition(identity, parsed.version, parsed.logical_name, self.source_kind, str(request.path), description, AIcdDataType(AInDataTypeKind.OBJECT, properties=props), (), title)
        element = self._child(root, 'element')
        shape = self._simple_shape(typ, request, resource, set()) if typ is not None else self._shape(element, element.get('type', ''), request, resource, set()) if element is not None else _AIcdXmlShape(AInDataTypeKind.ANY)
        prop = AIcdPropertyDefinition('value', from_source_hints(shape.kind, shape.item_kind, shape.reference, shape.constraints, shape.item_constraints), (AInFieldPresenceKind.REQUIRED if True else AInFieldPresenceKind.ALLOWED), element is not None and element.get('nillable') in ('true','1'), description, self._title(element or typ), None)
        return AIcdCanonicalDefinition(identity, parsed.version, parsed.logical_name, self.source_kind, str(request.path), description, prop.data_type, (), title)

    def _root_choice(self, typ, request, resource):
        """Model an exact-one XML choice with each alternative's XML field QName intact.

        Only a direct mandatory, nonrepeating choice of local element declarations is
        supported. Other particles need full XSD content-model validation and fail fast.
        """
        choice = self._child(typ, 'choice')
        if choice is None:
            return None
        if (self._child(typ, 'complexContent', 'simpleContent', 'sequence', 'all', 'group',
                'attribute', 'attributeGroup', 'anyAttribute') is not None
                or len(self._children(typ, 'choice')) != 1
                or choice.get('minOccurs', '1') != '1'
                or choice.get('maxOccurs', '1') != '1'):
            raise ValueError(f'Unsupported mixed or repeated XSD choice in {request.path}')
        branches = self._children(choice)
        if not branches or any(branch.tag != self._xs + 'element' or
                bool(branch.get('name')) == bool(branch.get('ref')) or
                branch.get('minOccurs') or branch.get('maxOccurs') for branch in branches):
            raise ValueError(f'Unsupported XSD choice branch in {request.path}')
        fields = tuple(self._elements(choice, False, request, resource))
        if len(fields) != len(branches):
            raise ValueError(f'Invalid XSD choice projection in {request.path}')
        return AIcdDataType.choice(AInDataTypeKind.ONE_OF,
            tuple(AIcdDataType(AInDataTypeKind.OBJECT, properties=(field,)) for field in fields))

    def global_element_declarations(self, request):
        """Read all global declarations; do not conflate element identity with type identity."""
        namespaces = {}
        for _, declaration in ET.iterparse(request.path, events=('start-ns',)):
            namespaces[declaration[0]] = declaration[1]
        root = self._parse(request.path)[0]
        target = root.get('targetNamespace', '')
        if root.get('blockDefault', '').strip() or root.get('finalDefault', '').strip():
            raise ValueError(f'Unsupported XSD substitution/derivation defaults in {request.path}')
        def expanded(lexical):
            if not lexical:
                return '{' + target + '}__root__'
            if ':' in lexical:
                prefix, local = lexical.split(':', 1)
                if prefix not in namespaces:
                    raise ValueError(f'Undefined XML namespace prefix {prefix!r} in {request.path}')
                return '{' + namespaces[prefix] + '}' + local
            return '{' + (namespaces.get('', target)) + '}' + lexical
        result = []
        seen = set()
        for child in self._children(root, 'element'):
            name = child.get('name', '')
            if not name or name in seen:
                raise ValueError(f'Duplicate or unnamed global XML element {name!r} in {request.path}')
            seen.add(name)
            if child.get('block', '').strip() or child.get('final', '').strip():
                raise ValueError(f'Unsupported XSD substitution/derivation restriction for element {name!r} in {request.path}')
            result.append(AIcdXmlElementDeclaration(name, target,
                expanded(child.get('type')), expanded(child.get('substitutionGroup'))
                if child.get('substitutionGroup') else None,
                child.get('abstract') in ('true', '1'), child.get('nillable') in ('true', '1')))
        return tuple(result)

    def schema_namespace(self, request):
        """Return the declared XML target namespace for a synthetic named type."""
        return self._parse(request.path)[0].get('targetNamespace', '')

    def root_type_qname(self, request):
        """Return the only named XSD root type projected by the current contract loader."""
        root = self._parse(request.path)[0]
        typ = self._root_type(root)
        return '{' + root.get('targetNamespace', '') + '}' + (typ.get('name') if typ is not None and typ.get('name') else '__root__')

    def additional_named_type_names(self, path):
        """List global XSD types not already represented by the primary contract."""
        root = self._parse(path)[0]
        main = self._root_type(root)
        names, result = set(), []
        for typ in self._children(root, 'complexType', 'simpleType'):
            name = typ.get('name', '')
            if not name or name in names:
                raise ValueError(f'Duplicate or unnamed global XSD type in {path}')
            names.add(name)
            if typ is not main:
                result.append(name)
        return tuple(result)

    def load_named_type(self, request, name):
        """Project a separately declared type without changing the root file contract."""
        resource = self._parse(request.path)
        root = resource[0]
        typ = self._named_type(root, name)
        if typ is None:
            raise ValueError(f'Unknown named XSD type {name!r} in {request.path}')
        version_text = root.get('version', '')
        parsed = self._identities.from_file(request, int(version_text) if version_text.isdigit() else None)
        identity = root.get('targetNamespace') or parsed.logical_name
        import re
        logical = re.sub(r'[^A-Za-z0-9]+', '-', re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name)).lower()
        description = self._documentation(typ)
        title = self._title(typ)
        values = self._enum_values(typ)
        resource_name = str(request.path) + '#@type/' + name
        if values:
            return AIcdCanonicalDefinition(identity, parsed.version, logical, self.source_kind, resource_name, description, AIcdDataType(AInDataTypeKind.ENUM), values, title)
        if typ.tag == self._xs + 'complexType':
            choice = self._root_choice(typ, request, resource)
            if choice is not None:
                return AIcdCanonicalDefinition(identity, parsed.version, logical, self.source_kind, resource_name, description, choice, (), title)
            props = self._complex_properties(typ, request, resource, frozenset())
            return AIcdCanonicalDefinition(identity, parsed.version, logical, self.source_kind, resource_name, description, AIcdDataType(AInDataTypeKind.OBJECT, properties=props), (), title)
        shape = self._simple_shape(typ, request, resource, set())
        prop = AIcdPropertyDefinition('value', from_source_hints(shape.kind, shape.item_kind, shape.reference, shape.constraints, shape.item_constraints), (AInFieldPresenceKind.REQUIRED if True else AInFieldPresenceKind.ALLOWED), False, description, title, None)
        return AIcdCanonicalDefinition(identity, parsed.version, logical, self.source_kind, resource_name, description, prop.data_type, (), title)

    def named_type_extension_base_qname(self, request, name):
        """Get the direct named extension parent, independent of the XSD root type."""
        resource = self._parse(request.path)
        typ = self._named_type(resource[0], name)
        if typ is None:
            raise ValueError(f'Unknown named XSD type {name!r} in {request.path}')
        return self._extension_base_qname(resource, typ, request.path)

    def root_extension_base_qname(self, request):
        """Read an XSD complexContent extension's expanded base QName.

        This is used for actual contract inheritance; restrictions stay separate
        because forbidding a base getter cannot be modeled with extends.
        """
        resource = self._parse(request.path)
        return self._extension_base_qname(resource, self._root_type(resource[0]), request.path)

    def _extension_base_qname(self, resource, typ, path):
        content = self._child(typ, 'complexContent')
        branch = self._child(content, 'extension')
        if branch is None:
            return None
        name = branch.get('base', '')
        if not name:
            raise ValueError(f'Missing XML complexContent extension base in {path}')
        prefix, separator, local = name.rpartition(':')
        namespace = resource[1][id(branch)].get(prefix if separator else '')
        if separator and namespace is None:
            raise ValueError(f'Unknown XML base namespace prefix {prefix!r} in {path}')
        return '{' + (namespace if namespace is not None else resource[0].get('targetNamespace', '')) + '}' + (local if separator else name)

    def _complex_properties(self, typ, request, resource, visited):
        """Project a conservative same-schema complexContent derivation subset.

        Extensions retain inherited and newly appended fields. Restrictions currently
        support only attribute-only bases and explicit presence tightening; arbitrary
        particle restriction needs an XSD content-model validator, not field merging.
        """
        if self._child(typ, 'anyAttribute', 'simpleContent') is not None:
            raise ValueError(f'Unsupported XSD attribute group/wildcard/simple content in {request.path}')
        content = self._child(typ, 'complexContent')
        if content is None:
            return tuple(self._elements(typ, False, request, resource)) + tuple(self._attributes(typ, request, resource))
        if typ.get('mixed') in ('true', '1') or content.get('mixed') in ('true', '1'):
            raise ValueError(f'Unsupported mixed complexContent derivation in {request.path}')
        branch = self._child(content, 'extension', 'restriction')
        if branch is None or len(self._children(content, 'extension', 'restriction')) != 1:
            raise ValueError(f'Unsupported XSD complexContent derivation in {request.path}')
        base_name = branch.get('base', '')
        prefix, separator, local = base_name.rpartition(':')
        namespace = resource[1][id(branch)].get(prefix if separator else '')
        target_namespace = resource[0].get('targetNamespace', '')
        if not base_name or (separator and namespace is None):
            raise ValueError(f'Unknown XSD complexContent base QName {base_name!r} in {request.path}')
        base = (self._named_type(resource[0], local if separator else base_name)
                if namespace is None or namespace == target_namespace else None)
        base_resource, base_request = resource, request
        if base is None:
            for imp in self._children(resource[0], 'import', 'include'):
                if imp.tag == self._xs + 'import' and imp.get('namespace', '') != (namespace or ''):
                    continue
                if imp.tag == self._xs + 'include' and namespace not in (None, target_namespace):
                    continue
                location = imp.get('schemaLocation', '')
                if not location:
                    continue
                uri = urlsplit(location)
                if uri.scheme and uri.scheme != 'file':
                    raise ValueError(f'XSD extension imports must be local: {location}')
                path = Path(unquote(uri.path)) if uri.scheme == 'file' else (request.path.resolve().parent / location).resolve()
                imported = self._parse(path)
                if imported[0].get('targetNamespace', '') != (namespace or target_namespace):
                    continue
                found = self._named_type(imported[0], local if separator else base_name)
                if found is None:
                    continue
                base = found
                base_resource = imported
                base_request = AIcdDefinitionLoadRequest(path, self.source_kind, request.naming_profile)
                break
        if base is None or base.tag != self._xs + 'complexType':
            raise ValueError(f'Unknown or non-complex XSD derivation base {base_name!r} in {request.path}')
        identity = (str(base_request.path.resolve()), base.get('name', ''))
        if identity in visited:
            raise ValueError(f'Circular XSD complexContent derivation at {identity!r} in {request.path}')
        inherited = self._complex_properties(base, base_request, base_resource, visited | {identity})
        if self._child(branch, 'anyAttribute', 'simpleContent', 'complexContent') is not None:
            raise ValueError(f'Unsupported XSD derivation child in {request.path}')
        local_fields = tuple(self._elements(branch, False, request, resource)) + tuple(self._attributes(branch, request, resource))
        by_name = {field.source_name: field for field in inherited}
        if len(by_name) != len(inherited) or len({p.source_name for p in local_fields}) != len(local_fields):
            raise ValueError(f'Duplicate derived XML field in {request.path}')
        if branch.tag == self._xs + 'extension':
            if any(field.source_name in by_name for field in local_fields):
                raise ValueError(f'XSD extension redeclares an inherited field in {request.path}')
            return inherited + local_fields
        # xs:all and xs:sequence share one canonical ordered-property model.
        # Writers use declaration order; lenient readers may match by QName.
        # This is distinct from strict XML Schema sequence validation.
        base_sequence = self._child(base, 'sequence', 'all')
        restricted_sequence = self._child(branch, 'sequence', 'all')
        if self._child(base, 'choice', 'group', 'complexContent') is not None or self._child(branch, 'choice', 'group') is not None:
            raise ValueError(f'Unsupported XSD complexContent particle restriction in {request.path}')
        if (restricted_sequence is not None and base_sequence is None):
            raise ValueError(f'XSD restriction introduces an unsupported particle group in {request.path}')
        if base_sequence is not None:
            if (any(node.tag != self._xs + 'element' for node in self._children(base_sequence))
                    or (restricted_sequence is not None and any(node.tag != self._xs + 'element'
                        for node in self._children(restricted_sequence)))
                    or base_sequence.get('minOccurs', '1') != '1'
                    or base_sequence.get('maxOccurs', '1') != '1'
                    or (restricted_sequence is not None and
                        (restricted_sequence.get('minOccurs', '1') != '1' or restricted_sequence.get('maxOccurs', '1') != '1'))):
                raise ValueError(f'Unsupported XSD complexContent particle restriction in {request.path}')
            base_order = [node.get('name') for node in self._children(base_sequence)]
            derived_order = [node.get('name') for node in self._children(restricted_sequence)] if restricted_sequence is not None else []
            retained = iter(base_order)
            if any(not any(candidate == name for candidate in retained) for name in derived_order):
                raise ValueError(f'Unsupported XSD particle restriction: reorders or introduces compositor elements in {request.path}')
        result = dict(by_name)
        from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
        for field in local_fields:
            previous = result.get(field.source_name)
            if previous is None:
                raise ValueError(f'XSD restriction introduces a new field {field.source_name!r} in {request.path}')
            if (previous.xml_field is None) != (field.xml_field is None) or (
                    previous.xml_field is not None and
                    (previous.xml_field.namespace, previous.xml_field.namespace_local_name, previous.xml_field.value_kind) !=
                    (field.xml_field.namespace, field.xml_field.namespace_local_name, field.xml_field.value_kind)):
                raise ValueError(f'XSD restriction changes XML attribute/element QName of {field.source_name!r} in {request.path}')
            if field.presence is AInFieldPresenceKind.FORBIDDEN and field.data_type.kind is AInDataTypeKind.ANY and field.data_type.referenced_definition() is None:
                # XSD permits use=prohibited without repeating the base attribute type.
                # Keep the inherited contract and change only its presence restriction.
                field = replace(previous, presence=AInFieldPresenceKind.FORBIDDEN,
                    xml_field=replace(previous.xml_field, min_occurs=0, max_occurs=0)
                    if previous.xml_field is not None else None)
            if (previous.xml_field is None) != (field.xml_field is None) or (
                    previous.xml_field is not None and
                    (previous.xml_field.namespace, previous.xml_field.namespace_local_name, previous.xml_field.value_kind) !=
                    (field.xml_field.namespace, field.xml_field.namespace_local_name, field.xml_field.value_kind)):
                raise ValueError(f'XSD restriction changes XML attribute/element QName of {field.source_name!r} in {request.path}')
            if previous.xml_field is not None:
                old, new = previous.xml_field, field.xml_field
                if (old.min_occurs >= 0 and (new.min_occurs < 0 or new.min_occurs < old.min_occurs)
                        or old.max_occurs >= 0 and (new.max_occurs < 0 or new.max_occurs > old.max_occurs)):
                    raise ValueError(f'XSD restriction relaxes minOccurs/maxOccurs of {field.source_name!r} in {request.path}')
            if not self._same_type_shape(previous.data_type, field.data_type):
                raise ValueError(f'XSD restriction changes the type of {field.source_name!r} in {request.path}')
            if previous.data_type.constraints.data_type != field.data_type.constraints.data_type:
                raise ValueError(f'Unsupported XSD restriction changes the scalar family of {field.source_name!r} in {request.path}')
            self._validate_restriction_facets(previous.data_type.constraints, field.data_type.constraints, request.path)
            if previous.data_type.constraints.pattern != field.data_type.constraints.pattern:
                raise ValueError(f'Unsupported XSD restriction changes inherited pattern of {field.source_name!r} in {request.path}')
            if previous.presence is AInFieldPresenceKind.REQUIRED and field.presence is not AInFieldPresenceKind.REQUIRED:
                raise ValueError(f'XSD restriction relaxes a required field {field.source_name!r} in {request.path}')
            if previous.presence is AInFieldPresenceKind.FORBIDDEN and field.presence is not AInFieldPresenceKind.FORBIDDEN:
                raise ValueError(f'XSD restriction un-forbids {field.source_name!r} in {request.path}')
            result[field.source_name] = field
        # Omitted optional sequence elements (like omitted optional attributes)
        # become forbidden, rather than being silently erased from canonical metadata.
        for name, previous in by_name.items():
            if name not in {field.source_name for field in local_fields}:
                if previous.presence is AInFieldPresenceKind.REQUIRED:
                    raise ValueError(f'XSD restriction omits a required attribute {name!r} in {request.path}')
                result[name] = replace(previous, presence=AInFieldPresenceKind.FORBIDDEN,
                    xml_field=replace(previous.xml_field, min_occurs=0, max_occurs=0)
                    if previous.xml_field is not None else None)
        return tuple(result.values())

    @classmethod
    def _same_type_shape(cls, base, derived):
        """Compare nested scalar families, references and choice branches, not just outer kinds."""
        if base.kind is not derived.kind or base.constraints.data_type != derived.constraints.data_type:
            return False
        if base.kind is AInDataTypeKind.ARRAY:
            return cls._same_type_shape(base.element_type, derived.element_type)
        if base.kind is AInDataTypeKind.REFERENCE:
            return base.reference == derived.reference
        if base.kind is AInDataTypeKind.OBJECT:
            return base.properties == derived.properties
        if base.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            return len(base.alternatives) == len(derived.alternatives) and all(
                cls._same_type_shape(left, right) for left, right in zip(base.alternatives, derived.alternatives))
        return True

    @staticmethod
    def _validate_occurs(node, group, path):
        """Validate occurrence intervals before the lossless compositor projection.

        A repeated single-leaf group may map to a bounded array, but repeated
        correlated multi-field groups must be rejected by _compositor_fields.
        """
        try:
            minimum = int(node.get('minOccurs', '1'))
            maximum_text = node.get('maxOccurs', '1')
            maximum = None if maximum_text == 'unbounded' else int(maximum_text)
        except ValueError as error:
            raise ValueError(f'Invalid XSD occurrence interval in {path}') from error
        if minimum < 0 or (maximum is not None and (maximum < 0 or maximum < minimum)):
            raise ValueError(f'Invalid XSD occurrence interval in {path}')
        if group and maximum == 0:
            raise ValueError(f'Forbidden XSD compositor must preserve its child model in {path}')
        return minimum, maximum

    def _resolve_global(self, node, lexical, declaration_kind, request, resource):
        """Resolve one expanded QName through local-only XSD imports and includes.

        Every traversed schemaLocation is parsed without fetching remote resources.
        Ambiguous definitions and inconsistent import namespaces fail explicitly.
        """
        if not lexical or lexical.count(':') > 1:
            raise ValueError(f'Invalid XSD {declaration_kind} QName {lexical!r} in {request.path}')
        prefix, separator, local = lexical.rpartition(':')
        namespace = resource[1][id(node)].get(prefix if separator else '')
        if separator and namespace is None:
            raise ValueError(f'Undefined XSD namespace prefix {prefix!r} in {request.path}')
        if not local or ':' in local:
            raise ValueError(f'Invalid XSD {declaration_kind} QName {lexical!r} in {request.path}')
        target = namespace if namespace is not None else resource[0].get('targetNamespace', '')
        found = []
        visited = set()

        def visit(candidate_request, candidate_resource):
            path = candidate_request.path.resolve()
            if path in visited:
                return
            visited.add(path)
            schema, _ = candidate_resource
            if schema.get('targetNamespace', '') == target:
                for declaration in self._children(schema, declaration_kind):
                    if declaration.get('name') == local:
                        found.append((declaration, candidate_request, candidate_resource))
            for include in self._children(schema, 'import', 'include'):
                location = include.get('schemaLocation', '')
                if not location:
                    continue
                uri = urlsplit(location)
                if uri.scheme not in ('', 'file') or uri.netloc or uri.query or uri.fragment:
                    raise ValueError(f'XSD declaration imports must be local files: {location}')
                included_path = (Path(unquote(uri.path)) if uri.scheme == 'file'
                                 else path.parent / unquote(uri.path)).resolve()
                if not included_path.is_file():
                    raise ValueError(f'XSD declaration schemaLocation not found: {included_path}')
                imported = self._parse(included_path)
                imported_namespace = imported[0].get('targetNamespace', '')
                if include.tag == self._xs + 'import':
                    if include.get('namespace', '') != imported_namespace:
                        raise ValueError(f'XSD import namespace disagrees with schemaLocation: {location}')
                elif imported_namespace != schema.get('targetNamespace', ''):
                    raise ValueError(f'XSD include namespace disagrees with schemaLocation: {location}')
                imported_request = AIcdDefinitionLoadRequest(included_path, self.source_kind,
                                                            request.naming_profile)
                visit(imported_request, imported)

        visit(request, resource)
        if len(found) != 1:
            raise ValueError(f'{"Ambiguous" if found else "Unknown"} XSD {declaration_kind} '
                             f'reference {lexical!r} in {request.path}')
        return found[0]

    @staticmethod
    def _compositor_fields(projected, minimum, maximum, inherited_optional, path):
        """Expand a compositor only when its flattened field counts remain equivalent.

        A repeating compositor containing exactly one mandatory, nonrepeating
        element is an ordinary repeated sibling field. Multiple children (or a
        repeating child) would lose correlated group boundaries, and therefore
        are not projected as independent arrays.
        """
        fields = tuple(projected)
        if minimum == 1 and maximum == 1:
            return fields
        if (len(fields) != 1 or fields[0].presence is not AInFieldPresenceKind.REQUIRED
                or fields[0].data_type.kind is AInDataTypeKind.ARRAY):
            if minimum == 0 and maximum == 1:
                raise ValueError(f'Optional XSD compositor cannot be flattened without losing group cardinality in {path}')
            raise ValueError(f'XSD compositor cannot be flattened without losing group cardinality in {path}')
        field = fields[0]
        if field.xml_field is not None:
            # The wire occurrence count belongs to the leaf's QName, not to its
            # possibly nested XSD list item cardinality.
            base_min = max(0, field.xml_field.min_occurs)
            base_max = field.xml_field.max_occurs
            if maximum is None or base_max < 0:
                result_max = -1
            else:
                result_max = base_max * maximum
            field = replace(field, xml_field=replace(field.xml_field,
                min_occurs=0 if inherited_optional else base_min * minimum, max_occurs=result_max))
        if maximum is None or maximum > 1:
            data_type = AIcdDataType(AInDataTypeKind.ARRAY, element_type=field.data_type,
                constraints=AIcdValueConstraints(min_items=0 if inherited_optional else minimum,
                    max_items=maximum))
        else:
            data_type = field.data_type
        return (replace(field, data_type=data_type,
            presence=AInFieldPresenceKind.ALLOWED if inherited_optional or minimum == 0
                     else AInFieldPresenceKind.REQUIRED),)

    def _elements(self, parent, optional, request, resource, groups=frozenset()):
        """Project leaf XML fields while resolving acyclic local named compositor groups."""
        for xml_order, node in enumerate(self._children(parent)):
            kind = node.tag.removeprefix(self._xs)
            if kind in ('sequence', 'all', 'choice'):
                minimum, maximum = self._validate_occurs(node, True, request.path)
                if kind == 'choice': raise ValueError(f'XSD choice is not represented by the canonical property model: {request.path}')
                projected = tuple(self._elements(node, optional, request, resource, groups))
                yield from self._compositor_fields(projected, minimum, maximum, optional, request.path)
            elif kind == 'element':
                minimum, maximum = self._validate_occurs(node, False, request.path)
                declaration = node
                declaration_request, declaration_resource = request, resource
                local_name = node.get('name', '')
                referenced = node.get('ref', '')
                global_field = False
                if referenced:
                    if local_name or node.get('type') or node.get('nillable'):
                        raise ValueError(f'Invalid XSD element reference declaration in {request.path}')
                    declaration, declaration_request, declaration_resource = self._resolve_global(
                        node, referenced, 'element', request, resource)
                    local_name = declaration.get('name')
                    global_field = True
                if not local_name:
                    raise ValueError(f'XSD element references require a named canonical property: {request.path}')
                if self._child(declaration, 'alternative') is not None:
                    raise ValueError(f'Unsupported XSD conditional element type in {request.path}: {local_name}')
                shape = self._shape(declaration, declaration.get('type', ''), declaration_request, declaration_resource, set())
                repeated = maximum is None or maximum > 1
                if repeated and shape.kind is AInDataTypeKind.ARRAY: raise ValueError('Nested XSD lists are not represented by the canonical property model')
                data_type = from_source_hints(AInDataTypeKind.ARRAY if repeated else shape.kind,
                    shape.kind if repeated else shape.item_kind, shape.reference,
                    AIcdValueConstraints() if repeated else shape.constraints,
                    shape.constraints if repeated else shape.item_constraints)
                if repeated:
                    data_type = replace(data_type, constraints=AIcdValueConstraints(
                        min_items=minimum, max_items=maximum))
                yield AIcdPropertyDefinition(local_name, data_type,
                    AInFieldPresenceKind.FORBIDDEN if maximum == 0 else
                    (AInFieldPresenceKind.REQUIRED if not optional and minimum > 0 else AInFieldPresenceKind.ALLOWED),
                    declaration.get('nillable') in ('true', '1'),
                    self._documentation(node) or self._documentation(declaration),
                    self._title(node) or self._title(declaration),
                    AIcdXmlFieldRepresentation(declaration_resource[0].get('targetNamespace', '') if global_field
                        else self._field_namespace(node, resource[0], False),
                        local_name, AInXmlValueKind.ELEMENT, minimum, maximum if maximum is not None else -1))
            elif kind == 'group':
                minimum, maximum = self._validate_occurs(node, True, request.path)
                reference = node.get('ref', '')
                if not reference or node.get('name'):
                    raise ValueError(f'Unsupported XSD wildcard/group particle {kind!r} in {request.path}')
                definition, group_request, group_resource = self._resolve_global(
                    node, reference, 'group', request, resource)
                identity = (str(group_request.path.resolve()), definition.get('name'))
                if identity in groups:
                    raise ValueError(f'Circular XSD group reference {reference!r} in {request.path}')
                projected = tuple(self._elements(definition, optional,
                    group_request, group_resource, groups | {identity}))
                yield from self._compositor_fields(projected, minimum, maximum, optional, request.path)
            elif kind == 'any':
                minimum, maximum = self._validate_occurs(node, False, request.path)
                namespace_constraint = node.get('namespace', '##any')
                process_contents = node.get('processContents', 'strict')
                if process_contents not in ('skip', 'lax', 'strict'):
                    raise ValueError(f'Invalid xs:any processContents in {request.path}')
                if not namespace_constraint.strip():
                    raise ValueError(f'Invalid xs:any namespace constraint in {request.path}')
                name = f'AnyXmlElement{xml_order + 1}'
                repeated = maximum is None or maximum > 1
                primitive = AIcdDataType(AInDataTypeKind.ANY)
                data_type = (AIcdDataType(AInDataTypeKind.ARRAY, element_type=primitive,
                    constraints=AIcdValueConstraints(min_items=minimum, max_items=maximum))
                    if repeated else primitive)
                yield AIcdPropertyDefinition(name, data_type,
                    AInFieldPresenceKind.FORBIDDEN if maximum == 0 else
                    AInFieldPresenceKind.REQUIRED if not optional and minimum > 0 else AInFieldPresenceKind.ALLOWED,
                    False, 'Complete XML subtrees accepted by xs:any.', 'XML extension elements',
                    AIcdXmlFieldRepresentation(resource[0].get('targetNamespace', ''), name,
                        AInXmlValueKind.ELEMENT, minimum, -1 if maximum is None else maximum,
                        namespace_constraint, process_contents))
            elif kind == 'annotation':
                continue
            elif kind in ('attribute', 'attributeGroup', 'anyAttribute',
                          'simpleContent', 'complexContent') and parent.tag in (
                    self._xs + 'complexType', self._xs + 'extension',
                    self._xs + 'restriction'):
                # These members are handled by the enclosing complex-type parser.
                continue
            else:
                raise ValueError(f'Unsupported XSD content model child {kind!r} '
                                 f'in {request.path}; refusing a partial projection')

    def _attributes(self, typ, request, resource, groups=frozenset()):
        """Resolve local named attribute groups while preserving each member's QName."""
        if self._child(typ, 'anyAttribute') is not None:
            raise ValueError(f'Unsupported XSD attribute wildcard in {request.path}')
        for attribute in self._children(typ, 'attribute', 'attributeGroup'):
            if attribute.tag == self._xs + 'attributeGroup':
                reference = attribute.get('ref', '')
                if not reference or attribute.get('name'):
                    raise ValueError(f'Invalid XSD attributeGroup reference {reference!r} in {request.path}')
                definition, group_request, group_resource = self._resolve_global(
                    attribute, reference, 'attributeGroup', request, resource)
                identity = (str(group_request.path.resolve()), definition.get('name'))
                if identity in groups:
                    raise ValueError(f'Circular XSD attributeGroup reference {reference!r} in {request.path}')
                yield from self._attributes(definition, group_request, group_resource, groups | {identity})
                continue
            declaration = attribute
            declaration_request, declaration_resource = request, resource
            reference = attribute.get('ref', '')
            if reference:
                if attribute.get('name') or attribute.get('type') or attribute.get('form'):
                    raise ValueError(f'Invalid XSD attribute reference {reference!r} in {request.path}')
                declaration, declaration_request, declaration_resource = self._resolve_global(
                    attribute, reference, 'attribute', request, resource)
            name = declaration.get('name', '')
            if not name:
                raise ValueError(f'Unnamed XSD attribute in {request.path}')
            shape = self._shape(declaration, declaration.get('type', ''),
                                declaration_request, declaration_resource, set())
            if shape.kind in (AInDataTypeKind.ARRAY, AInDataTypeKind.OBJECT):
                raise ValueError(f'XML attribute {name!r} must have a scalar type in {request.path}')
            use = attribute.get('use', declaration.get('use', 'optional'))
            yield AIcdPropertyDefinition(name,
                from_source_hints(shape.kind, shape.item_kind, shape.reference, shape.constraints, shape.item_constraints),
                AInFieldPresenceKind.FORBIDDEN if use == 'prohibited' else
                AInFieldPresenceKind.REQUIRED if use == 'required' else AInFieldPresenceKind.ALLOWED,
                False, self._documentation(attribute) or self._documentation(declaration),
                self._title(attribute) or self._title(declaration),
                AIcdXmlFieldRepresentation(declaration_resource[0].get('targetNamespace', '') if reference
                    else self._field_namespace(attribute, resource[0], True), name, AInXmlValueKind.ATTRIBUTE, 1 if use == 'required' else 0, 0 if use == 'prohibited' else 1))

    @staticmethod
    def _field_namespace(field, schema, is_attribute):
        """Resolve local element/attribute qualification according to XML Schema form defaults."""
        form = field.get('form') or schema.get('attributeFormDefault' if is_attribute else 'elementFormDefault', 'unqualified')
        if form == 'qualified':
            return schema.get('targetNamespace', '')
        if form == 'unqualified':
            return ''
        raise ValueError(f'Invalid XML Schema field form {form!r}')

    def _shape(self, context, name, request, resource, visited):
        root, namespaces = resource
        if not name:
            if self._child(context, 'complexType') is not None: return _AIcdXmlShape(AInDataTypeKind.OBJECT)
            simple = self._child(context, 'simpleType')
            return _AIcdXmlShape(AInDataTypeKind.ANY) if simple is None else self._simple_shape(simple, request, resource, visited)
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
                return self._simple_shape(typ, request, resource, visited) if typ.tag == self._xs + 'simpleType' else _AIcdXmlShape(AInDataTypeKind.OBJECT)
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
            return _AIcdXmlShape(AInDataTypeKind.REFERENCE, reference=AIcdDefinitionReference(imported[0].get('targetNamespace'),
                parsed.version, parsed.logical_name, AIcdDataType(AInDataTypeKind.ENUM if enums else AInDataTypeKind.OBJECT)))
        raise ValueError(f"Undefined XSD type '{name}' in {request.path}")

    def _simple_shape(self, typ, request, resource, visited):
        restriction = self._child(typ, 'restriction')
        if restriction is not None:
            base = self._shape(restriction, restriction.get('base', ''), request, resource, visited)
            kwargs = {}; values = []
            seen = set()
            for facet in self._children(restriction):
                kind = facet.tag.removeprefix(self._xs)
                if kind == 'annotation':
                    continue
                value = facet.get('value')
                category = ('lowerBound' if kind in ('minInclusive', 'minExclusive') else
                    'upperBound' if kind in ('maxInclusive', 'maxExclusive') else kind)
                if category in seen and kind != 'enumeration':
                    raise ValueError(f'Duplicate XSD restriction facet {kind!r} in {request.path}')
                seen.add(category)
                if kind in ('minInclusive', 'minExclusive'):
                    kwargs.update(minimum=decimal_text(value), exclusive_minimum=kind == 'minExclusive')
                elif kind in ('maxInclusive', 'maxExclusive'):
                    kwargs.update(maximum=decimal_text(value), exclusive_maximum=kind == 'maxExclusive')
                elif kind == 'length':
                    if 'minLength' in seen or 'maxLength' in seen:
                        raise ValueError(f'Conflicting XSD length facets in {request.path}')
                    kwargs.update(min_length=int(value), max_length=int(value))
                elif kind == 'minLength':
                    if 'length' in seen:
                        raise ValueError(f'Conflicting XSD length facets in {request.path}')
                    kwargs['min_length'] = int(value)
                elif kind == 'maxLength':
                    if 'length' in seen:
                        raise ValueError(f'Conflicting XSD length facets in {request.path}')
                    kwargs['max_length'] = int(value)
                elif kind == 'pattern':
                    if base.constraints.pattern is not None and base.constraints.pattern != value:
                        raise ValueError(f'Unsupported conjunction of inherited XSD pattern facets in {request.path}')
                    kwargs['pattern'] = value
                elif kind == 'enumeration':
                    values.append(value)
                else:
                    raise ValueError(f'Unsupported XSD restriction facet {kind!r} in {request.path}')
            if values:
                kwargs['enum_values'] = tuple(values)
            derived = replace(base.constraints, **kwargs)
            self._validate_restriction_facets(base.constraints, derived, request.path)
            return replace(base, constraints=derived)

        listing = self._child(typ, 'list')
        if listing is not None:
            item = self._shape(listing, listing.get('itemType', ''), request, resource, visited)
            return _AIcdXmlShape(AInDataTypeKind.ARRAY, item.kind, item.reference, item_constraints=item.constraints)
        raise ValueError(f'Unsupported XSD simple type in {request.path}')

    @staticmethod
    def _validate_restriction_facets(base, derived, path):
        """Require representable facets to narrow inherited XSD simple types."""
        if base.min_items is not None and (derived.min_items is None or derived.min_items < base.min_items):
            raise ValueError(f'XSD restriction relaxes inherited minOccurs in {path}')
        if base.max_items is not None and (derived.max_items is None or derived.max_items > base.max_items):
            raise ValueError(f'XSD restriction relaxes inherited maxOccurs in {path}')
        if base.minimum is not None and (
            derived.minimum is None or Decimal(derived.minimum) < Decimal(base.minimum) or
            (Decimal(derived.minimum) == Decimal(base.minimum) and
             base.exclusive_minimum and not derived.exclusive_minimum)):
            raise ValueError(f'XSD restriction relaxes inherited minimum in {path}')
        if base.maximum is not None and (
            derived.maximum is None or Decimal(derived.maximum) > Decimal(base.maximum) or
            (Decimal(derived.maximum) == Decimal(base.maximum) and
             base.exclusive_maximum and not derived.exclusive_maximum)):
            raise ValueError(f'XSD restriction relaxes inherited maximum in {path}')
        if derived.minimum is not None and derived.maximum is not None:
            comparison = Decimal(derived.minimum).compare(Decimal(derived.maximum))
            if comparison > 0 or (comparison == 0 and
                (derived.exclusive_minimum or derived.exclusive_maximum)):
                raise ValueError(f'Inconsistent XSD numeric restriction bounds in {path}')
        if base.min_length is not None and (
            derived.min_length is None or derived.min_length < base.min_length):
            raise ValueError(f'XSD restriction relaxes inherited minLength in {path}')
        if base.max_length is not None and (
            derived.max_length is None or derived.max_length > base.max_length):
            raise ValueError(f'XSD restriction relaxes inherited maxLength in {path}')
        if (derived.min_length is not None and derived.max_length is not None and
                derived.min_length > derived.max_length):
            raise ValueError(f'Inconsistent XSD length restriction in {path}')
        if base.enum_values and not derived.enum_values:
            raise ValueError(f'XSD restriction removes inherited enumeration in {path}')
        if base.enum_values and not set(derived.enum_values).issubset(base.enum_values):
            raise ValueError(f'XSD restriction widens inherited enumeration in {path}')

    @classmethod
    def _builtin(cls, name):
        if name in cls._strings: return _AIcdXmlShape(AInDataTypeKind.STRING, constraints=defaults(name))
        if name in cls._integers: return _AIcdXmlShape(AInDataTypeKind.INTEGER, constraints=defaults(name))
        if name in ('decimal', 'float', 'double'): return _AIcdXmlShape(AInDataTypeKind.NUMBER, constraints=defaults(name))
        if name == 'boolean': return _AIcdXmlShape(AInDataTypeKind.BOOLEAN, constraints=defaults(name))
        if name in ('NMTOKENS', 'IDREFS', 'ENTITIES'): return _AIcdXmlShape(AInDataTypeKind.ARRAY, AInDataTypeKind.STRING, constraints=defaults(name), item_constraints=defaults('string'))
        if name in ('anyType', 'anySimpleType', 'anyAtomicType'): return _AIcdXmlShape(AInDataTypeKind.ANY, constraints=defaults(None if name == 'anyType' else name))
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
        if root is None or root.tag != '{http://www.w3.org/2001/XMLSchema}schema':
            raise ValueError(f'Expected XML Schema root in {path}')
        for child in root:
            if child.tag in ('{http://www.w3.org/2001/XMLSchema}redefine',
                             '{http://www.w3.org/2001/XMLSchema}override',
                             '{http://www.w3.org/2001/XMLSchema}defaultOpenContent'):
                raise ValueError(f'Unsupported XSD schema directive {child.tag!r} in {path}')
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
    def _title(cls, element):
        """Read a title from the Algites XML documentation annotation namespace."""
        if element is None:
            return None
        annotation = cls._child(element, "annotation")
        appinfo = cls._child(annotation, "appinfo")
        if appinfo is None:
            return None
        element = appinfo.find("{urn:eu:algites:documentation:1}title")
        return (element.text or "").strip() or None if element is not None else None

    @classmethod
    def _enum_values(cls, typ):
        return tuple(AIcdEnumValueDefinition(value.get('value'), cls._documentation(value), cls._title(value)) for value in cls._children(cls._child(typ, 'restriction'), 'enumeration'))

    @classmethod
    def _documentation(cls, node):
        doc = cls._child(cls._child(node, 'annotation'), 'documentation')
        return ' '.join(''.join(doc.itertext()).split()) or None if doc is not None else None
