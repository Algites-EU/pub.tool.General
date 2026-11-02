from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
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
from eu.algites.tool.codegen.defs.aicd_key_definition import AIcdKeyDefinition
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

    @staticmethod
    def _type_identifier(name, request):
        """Validate a declared or synthetic type name and convert via naming rules.

        Explicit XSD names are parsed against the source profile. Synthetic names
        are formed from schema syntax and validated against that same profile.
        """
        profile = request.source_naming_profile
        catalog = request.naming_profile
        if not profile:
            found = catalog.recognize_filename(request.path.name)
            if found is None:
                raise AIxCodegenValidationException(f'No source naming profile matches {request.path}', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
            profile = found.convention_name
        from .aic_declared_type_identity import canonical_type_identifier
        return canonical_type_identifier(catalog, profile, name)

    def _validate_named_types(self, request, root):
        """Require every globally declared type to follow the input type_name rule."""
        for typ in self._children(root, 'complexType', 'simpleType'):
            if typ.get('name'):
                self._type_identifier(typ.get('name'), request)

    def load(self, request):
        """Read an XSD source and normalize its types, fields and documentation."""
        resource = self._parse(request.path)
        root = resource[0]
        self._validate_named_types(request, root)
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
                raise AIxCodegenValidationException(f'Duplicate XML element/attribute field in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
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
            return None
        branches = self._children(choice)
        if not branches or any(branch.tag not in (self._xs + 'element',
                self._xs + 'sequence') for branch in branches):
            raise AIxCodegenValidationException(f'Unsupported XSD choice branch in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
        alternatives = []
        for branch in branches:
            if branch.get('minOccurs') is not None or branch.get('maxOccurs') is not None:
                raise AIxCodegenValidationException(f'Unsupported XSD choice branch occurrence in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
            if branch.tag == self._xs + 'element':
                fields = tuple(self._elements_fragment(branch, request, resource, frozenset()))
            else:
                fields = tuple(self._elements(branch, False, request, resource, frozenset()))
            if not fields:
                raise AIxCodegenValidationException(f'Empty XSD choice branch in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
            # A named global type may have exactly the same content model as a
            # branch. Discover it structurally, never by a name suffix.
            def equivalent(left, right):
                return (len(left) == len(right) and all(
                    a.source_name == b.source_name and a.data_type == b.data_type
                    and a.xml_field == b.xml_field and a.nullable == b.nullable
                    for a, b in zip(left, right)))
            candidates = []
            for candidate in self._children(resource[0], 'complexType'):
                if candidate is typ:
                    continue
                try:
                    contents = self._complex_properties(candidate, request, resource, frozenset())
                except ValueError:
                    continue
                if equivalent(fields, contents):
                    candidates.append(candidate.get('name'))
            if len(candidates) > 1:
                raise AIxCodegenValidationException(f'Ambiguous structural XSD choice branch in {request.path}: {candidates}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
            if candidates:
                name = candidates[0]
                parsed = self._identities.from_file(request,
                    int(resource[0].get('version')) if resource[0].get('version', '').isdigit() else None)
                alternatives.append(AIcdDataType(AInDataTypeKind.REFERENCE,
                    reference=AIcdDefinitionReference('#@type/' + name,
                        parsed.version, self._type_identifier(name, request),
                        AIcdDataType(AInDataTypeKind.OBJECT))))
            else:
                alternatives.append(AIcdDataType(AInDataTypeKind.OBJECT, properties=fields))
        return AIcdDataType.choice(AInDataTypeKind.ONE_OF, tuple(alternatives))

    def global_element_declarations(self, request):
        """Read all global declarations; do not conflate element identity with type identity."""
        namespaces = {}
        for _, declaration in ET.iterparse(request.path, events=('start-ns',)):
            namespaces[declaration[0]] = declaration[1]
        root = self._parse(request.path)[0]
        target = root.get('targetNamespace', '')
        if root.get('blockDefault', '').strip() or root.get('finalDefault', '').strip():
            raise AIxCodegenValidationException(f'Unsupported XSD substitution/derivation defaults in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        def expanded(lexical):
            if not lexical:
                return '{' + target + '}__root__'
            if ':' in lexical:
                prefix, local = lexical.split(':', 1)
                if prefix not in namespaces:
                    raise AIxCodegenValidationException(f'Undefined XML namespace prefix {prefix!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                return '{' + namespaces[prefix] + '}' + local
            return '{' + (namespaces.get('', target)) + '}' + lexical
        result = []
        seen = set()
        for child in self._children(root, 'element'):
            name = child.get('name', '')
            if not name or name in seen:
                raise AIxCodegenValidationException(f'Duplicate or unnamed global XML element {name!r} in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
            seen.add(name)
            if child.get('block', '').strip() or child.get('final', '').strip():
                raise AIxCodegenValidationException(f'Unsupported XSD substitution/derivation restriction for element {name!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
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
                raise AIxCodegenValidationException(f'Duplicate or unnamed global XSD type in {path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
            names.add(name)
            if typ is not main:
                result.append(name)
        for typ in self._children(root, 'complexType'):
            for ordinal, choice in enumerate(self._descendant_choices(typ), 1):
                if not self._repeated_choice(choice):
                    continue
                synthetic = typ.get('name', '') + 'Choice' + str(ordinal)
                if synthetic in names:
                    raise AIxCodegenValidationException(f'Generated XSD choice type collides with a declared type: {synthetic}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
                names.add(synthetic)
                result.append(synthetic)
        for name, _ in self._inline_content_types(root):
            if name in names:
                raise AIxCodegenValidationException(f'Anonymous XML type collides with global type: {name}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
            names.add(name)
            result.append(name)
        for name, _ in self._synthetic_key_entries(root):
            if name in names:
                raise AIxCodegenValidationException(f'Generated XSD keyed value type collides with declared type: {name}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
            names.add(name)
            result.append(name)
        return tuple(result)

    def _inline_content_types(self, root):
        """Find every non-root anonymous complex type as a nominal sibling contract.

        The deterministic name is the concatenation of surrounding element names,
        anchored at its containing global complex type when applicable. The DOM
        structure, not the XPath selector, establishes the generated type identity.
        """
        parents = {id(child): parent for parent in root.iter() for child in parent}
        primary = self._root_type(root)
        result = []
        for owner in root.iter(self._xs + 'element'):
            content = self._child(owner, 'complexType')
            if content is None or content is primary:
                continue
            parts = []
            cursor = owner
            while cursor is not None:
                if cursor.tag == self._xs + 'element' and cursor.get('name'):
                    parts.insert(0, cursor.get('name'))
                if cursor.tag == self._xs + 'complexType' and cursor.get('name'):
                    parts.insert(0, cursor.get('name'))
                    break
                cursor = parents.get(id(cursor))
            if not parts:
                raise AIxCodegenValidationException('Cannot name anonymous XML complex content', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
            result.append((''.join(parts), content))
        return tuple(result)

    def _synthetic_key_entries(self, root):
        """Discover root-level keyed entries that require generated value contracts."""
        typ = self._root_type(root)
        if typ is None:
            return ()
        root_name = typ.get('name', '')
        if not root_name:
            return ()
        prefix = root_name
        result = []
        for group in self._children(typ, 'sequence', 'all'):
            for child in self._children(group, 'element'):
                if not self._children(child, 'key'):
                    continue
                content = self._child(child, 'complexType')
                if content is None and child.get('type'):
                    content = self._named_type(root, child.get('type').split(':')[-1])
                sequence = self._child(content, 'sequence')
                entries = self._children(sequence, 'element') if sequence is not None else ()
                if len(entries) != 1:
                    raise AIxCodegenValidationException('Cannot identify keyed XSD value contract under ' + child.get('name', ''), 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
                result.append((prefix + child.get('name', '') + 'AdditionalProperties', entries[0]))
        return tuple(result)

    def _descendant_choices(self, typ):
        """Enumerate choice compositors in a named complexType without crossing inline types."""
        result = []
        def visit(parent):
            for node in self._children(parent):
                tag = node.tag.removeprefix(self._xs)
                if tag == 'choice':
                    result.append(node)
                if tag in ('sequence', 'all', 'choice', 'complexContent', 'extension', 'restriction'):
                    visit(node)
        visit(typ)
        return tuple(result)

    @staticmethod
    def _repeated_choice(choice):
        maximum = choice.get('maxOccurs', '1')
        return maximum == 'unbounded' or int(maximum) > 1

    def _synthetic_choice(self, root, name):
        for typ in self._children(root, 'complexType'):
            for ordinal, choice in enumerate(self._descendant_choices(typ), 1):
                if self._repeated_choice(choice) and name == typ.get('name', '') + 'Choice' + str(ordinal):
                    return choice
        return None

    def is_synthetic_choice_type_name(self, path, name):
        """Distinguish generated choice particle types from real XML QName-bearing types."""
        root = self._parse(Path(path))[0]
        return (self._named_type(root, name) is None and
            (self._synthetic_choice(root, name) is not None or
             any(synthetic == name for synthetic, _ in self._synthetic_key_entries(root))))

    def _synthetic_choice_type(self, choice, request, resource):
        """Project one repeated choice item, retaining each branch's XML QName."""
        branches = self._children(choice)
        if any(branch.tag != self._xs + 'element' or branch.get('minOccurs') is not None
               or branch.get('maxOccurs') is not None for branch in branches):
            raise AIxCodegenValidationException(f'Unsupported repeated XSD choice branch in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
        fields = tuple(self._elements(choice, False, request, resource))
        if not fields or len(fields) != len(branches):
            raise AIxCodegenValidationException(f'Invalid repeated XSD choice in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
        return AIcdDataType.choice(AInDataTypeKind.ONE_OF,
            tuple(AIcdDataType(AInDataTypeKind.OBJECT, properties=(field,)) for field in fields))

    def load_named_type(self, request, name):
        """Project a separately declared type without changing the root file contract."""
        resource = self._parse(request.path)
        root = resource[0]
        self._validate_named_types(request, root)
        typ = self._named_type(root, name)
        if typ is None:
            typ = next((content for inline_name, content in self._inline_content_types(root)
                        if inline_name == name), None)
        synthetic = self._synthetic_choice(root, name) if typ is None else None
        keyed_entry = next((entry for synthetic_name, entry in self._synthetic_key_entries(root)
                           if synthetic_name == name), None) if typ is None else None
        if typ is None and synthetic is None and keyed_entry is None:
            raise AIxCodegenValidationException(f'Unknown named XSD type {name!r} in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        version_text = root.get('version', '')
        parsed = self._identities.from_file(request, int(version_text) if version_text.isdigit() else None)
        identity = root.get('targetNamespace') or parsed.logical_name
        logical = self._type_identifier(name, request)
        description = self._documentation(typ)
        title = self._title(typ)
        if keyed_entry is not None:
            inner = self._child(keyed_entry, 'complexType')
            if inner is None:
                raise AIxCodegenValidationException(f'Keyed XML value has no inline complexType in {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
            props = self._complex_properties(inner, request, resource, frozenset())
            return AIcdCanonicalDefinition(identity, parsed.version, logical, self.source_kind,
                str(request.path) + '#@type/' + name, self._documentation(keyed_entry),
                AIcdDataType(AInDataTypeKind.OBJECT, properties=props), (), self._title(keyed_entry))
        if synthetic is not None:
            return AIcdCanonicalDefinition(identity, parsed.version, logical, self.source_kind,
                str(request.path) + '#@type/' + name, self._documentation(synthetic),
                self._synthetic_choice_type(synthetic, request, resource), (), self._title(synthetic))
        values = self._enum_values(typ)
        resource_name = str(request.path) + '#@type/' + name
        if values:
            return AIcdCanonicalDefinition(identity, parsed.version, logical, self.source_kind, resource_name, description, AIcdDataType(AInDataTypeKind.ENUM), values, title)
        if typ.tag == self._xs + 'complexType':
            # xs:key belongs to the element that uses a named complexType,
            # not to the complexType declaration. The latter nevertheless
            # represents the keyed collection's logical type. Preserve the
            # element's physical key field in its XML-specialized value and
            # project the named contract as KEYED_VALUES, as for a JSON/YAML
            # named additionalProperties map. Never infer this from its name.
            keyed_owners = [element for element in root.iter(self._xs + 'element')
                if element.get('type', '').split(':')[-1] == name
                and (self._children(element, 'key') or self._children(element, 'unique'))]
            if keyed_owners:
                mapped = [self._keyed_element_type(element, request, resource)
                          for element in keyed_owners]
                if any(candidate != mapped[0] for candidate in mapped[1:]):
                    raise AIxCodegenValidationException('Incompatible xs:key usages of named type '
                        + name + ' in ' + str(request.path), 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
                return AIcdCanonicalDefinition(identity, parsed.version, logical,
                    self.source_kind, resource_name, description, mapped[0], (), title)
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
            typ = next((content for inline_name, content in self._inline_content_types(resource[0])
                        if inline_name == name), None)
        if typ is None:
            raise AIxCodegenValidationException(f'Unknown named XSD type {name!r} in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
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
            raise AIxCodegenValidationException(f'Missing XML complexContent extension base in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        prefix, separator, local = name.rpartition(':')
        namespace = resource[1][id(branch)].get(prefix if separator else '')
        if separator and namespace is None:
            raise AIxCodegenValidationException(f'Unknown XML base namespace prefix {prefix!r} in {path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
        return '{' + (namespace if namespace is not None else resource[0].get('targetNamespace', '')) + '}' + (local if separator else name)

    def _complex_properties(self, typ, request, resource, visited):
        """Project a conservative same-schema complexContent derivation subset.

        Extensions retain inherited and newly appended fields. Restrictions currently
        support only attribute-only bases and explicit presence tightening; arbitrary
        particle restriction needs an XSD content-model validator, not field merging.
        """
        if self._child(typ, 'anyAttribute', 'simpleContent') is not None:
            raise AIxCodegenValidationException(f'Unsupported XSD attribute group/wildcard/simple content in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
        content = self._child(typ, 'complexContent')
        if content is None:
            return tuple(self._elements(typ, False, request, resource)) + tuple(self._attributes(typ, request, resource))
        if typ.get('mixed') in ('true', '1') or content.get('mixed') in ('true', '1'):
            raise AIxCodegenValidationException(f'Unsupported mixed complexContent derivation in {request.path}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        branch = self._child(content, 'extension', 'restriction')
        if branch is None or len(self._children(content, 'extension', 'restriction')) != 1:
            raise AIxCodegenValidationException(f'Unsupported XSD complexContent derivation in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        base_name = branch.get('base', '')
        prefix, separator, local = base_name.rpartition(':')
        namespace = resource[1][id(branch)].get(prefix if separator else '')
        target_namespace = resource[0].get('targetNamespace', '')
        if not base_name or (separator and namespace is None):
            raise AIxCodegenValidationException(f'Unknown XSD complexContent base QName {base_name!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
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
                    raise AIxCodegenValidationException(f'XSD extension imports must be local: {location}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
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
            raise AIxCodegenValidationException(f'Unknown or non-complex XSD derivation base {base_name!r} in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        identity = (str(base_request.path.resolve()), base.get('name', ''))
        if identity in visited:
            raise AIxCodegenValidationException(f'Circular XSD complexContent derivation at {identity!r} in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        inherited = self._complex_properties(base, base_request, base_resource, visited | {identity})
        if self._child(branch, 'anyAttribute', 'simpleContent', 'complexContent') is not None:
            raise AIxCodegenValidationException(f'Unsupported XSD derivation child in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        local_fields = tuple(self._elements(branch, False, request, resource)) + tuple(self._attributes(branch, request, resource))
        by_name = {field.source_name: field for field in inherited}
        if len(by_name) != len(inherited) or len({p.source_name for p in local_fields}) != len(local_fields):
            raise AIxCodegenValidationException(f'Duplicate derived XML field in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        if branch.tag == self._xs + 'extension':
            if any(field.source_name in by_name for field in local_fields):
                raise AIxCodegenValidationException(f'XSD extension redeclares an inherited field in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            return inherited + local_fields
        # xs:all and xs:sequence share one canonical ordered-property model.
        # Writers use declaration order; lenient readers may match by QName.
        # This is distinct from strict XML Schema sequence validation.
        base_sequence = self._child(base, 'sequence', 'all')
        restricted_sequence = self._child(branch, 'sequence', 'all')
        if self._child(base, 'choice', 'group', 'complexContent') is not None or self._child(branch, 'choice', 'group') is not None:
            raise AIxCodegenValidationException(f'Unsupported XSD complexContent particle restriction in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if (restricted_sequence is not None and base_sequence is None):
            raise AIxCodegenValidationException(f'XSD restriction introduces an unsupported particle group in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if base_sequence is not None:
            if (any(node.tag != self._xs + 'element' for node in self._children(base_sequence))
                    or (restricted_sequence is not None and any(node.tag != self._xs + 'element'
                        for node in self._children(restricted_sequence)))
                    or base_sequence.get('minOccurs', '1') != '1'
                    or base_sequence.get('maxOccurs', '1') != '1'
                    or (restricted_sequence is not None and
                        (restricted_sequence.get('minOccurs', '1') != '1' or restricted_sequence.get('maxOccurs', '1') != '1'))):
                raise AIxCodegenValidationException(f'Unsupported XSD complexContent particle restriction in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            base_order = [node.get('name') for node in self._children(base_sequence)]
            derived_order = [node.get('name') for node in self._children(restricted_sequence)] if restricted_sequence is not None else []
            retained = iter(base_order)
            if any(not any(candidate == name for candidate in retained) for name in derived_order):
                raise AIxCodegenValidationException(f'Unsupported XSD particle restriction: reorders or introduces compositor elements in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        result = dict(by_name)
        from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
        for field in local_fields:
            previous = result.get(field.source_name)
            if previous is None:
                raise AIxCodegenValidationException(f'XSD restriction introduces a new field {field.source_name!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            if (previous.xml_field is None) != (field.xml_field is None) or (
                    previous.xml_field is not None and
                    (previous.xml_field.namespace, previous.xml_field.namespace_local_name, previous.xml_field.value_kind) !=
                    (field.xml_field.namespace, field.xml_field.namespace_local_name, field.xml_field.value_kind)):
                raise AIxCodegenValidationException(f'XSD restriction changes XML attribute/element QName of {field.source_name!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
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
                raise AIxCodegenValidationException(f'XSD restriction changes XML attribute/element QName of {field.source_name!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
            if previous.xml_field is not None:
                old, new = previous.xml_field, field.xml_field
                if (old.min_occurs >= 0 and (new.min_occurs < 0 or new.min_occurs < old.min_occurs)
                        or old.max_occurs >= 0 and (new.max_occurs < 0 or new.max_occurs > old.max_occurs)):
                    raise AIxCodegenValidationException(f'XSD restriction relaxes minOccurs/maxOccurs of {field.source_name!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            if not self._same_type_shape(previous.data_type, field.data_type):
                # An imported named complex type can be represented by the XML
                # frontend as the imported schema's root reference, while the
                # same type within its declaring schema uses a local @type
                # reference. These are identical XSD types when their expanded
                # QNames are equal, so keep the resolved inherited shape.
                def expanded_type(node, node_resource):
                    if node is None or not node.get('type'):
                        return None
                    lexical = node.get('type')
                    prefix, separator, local = lexical.rpartition(':')
                    namespace = node_resource[1][id(node)].get(prefix if separator else '')
                    if separator and namespace is None:
                        return None
                    return (namespace if namespace is not None else
                            node_resource[0].get('targetNamespace', ''),
                            local if separator else lexical)

                inherited_element = next((element for element in
                    self._children(base_sequence) if
                    element.get('name') == field.source_name), None) if base_sequence is not None else None
                restricted_element = next((element for element in
                    self._children(restricted_sequence) if
                    element.get('name') == field.source_name), None) if restricted_sequence is not None else None
                inherited_qname = expanded_type(inherited_element, base_resource)
                restricted_qname = expanded_type(restricted_element, resource)
                if (previous.data_type.kind is AInDataTypeKind.REFERENCE and
                        field.data_type.kind is AInDataTypeKind.REFERENCE and
                        inherited_qname is not None and
                        inherited_qname == restricted_qname):
                    field = replace(field, data_type=previous.data_type)
                else:
                    raise AIxCodegenValidationException(f'XSD restriction changes the type of {field.source_name!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            if previous.data_type.constraints.data_type != field.data_type.constraints.data_type:
                raise AIxCodegenValidationException(f'Unsupported XSD restriction changes the scalar family of {field.source_name!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            self._validate_restriction_facets(previous.data_type.constraints, field.data_type.constraints, request.path)
            if previous.data_type.constraints.pattern != field.data_type.constraints.pattern:
                raise AIxCodegenValidationException(f'Unsupported XSD restriction changes inherited pattern of {field.source_name!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            if previous.presence is AInFieldPresenceKind.REQUIRED and field.presence is not AInFieldPresenceKind.REQUIRED:
                raise AIxCodegenValidationException(f'XSD restriction relaxes a required field {field.source_name!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            if previous.presence is AInFieldPresenceKind.FORBIDDEN and field.presence is not AInFieldPresenceKind.FORBIDDEN:
                raise AIxCodegenValidationException(f'XSD restriction un-forbids {field.source_name!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            result[field.source_name] = field
        # Omitted optional sequence elements (like omitted optional attributes)
        # become forbidden, rather than being silently erased from canonical metadata.
        for name, previous in by_name.items():
            if name not in {field.source_name for field in local_fields}:
                if previous.presence is AInFieldPresenceKind.REQUIRED:
                    raise AIxCodegenValidationException(f'XSD restriction omits a required attribute {name!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
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
            raise AIxCodegenValidationException(f'Invalid XSD occurrence interval in {path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.') from error
        if minimum < 0 or (maximum is not None and (maximum < 0 or maximum < minimum)):
            raise AIxCodegenValidationException(f'Invalid XSD occurrence interval in {path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        if group and maximum == 0:
            raise AIxCodegenValidationException(f'Forbidden XSD compositor must preserve its child model in {path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        return minimum, maximum

    def _resolve_global(self, node, lexical, declaration_kind, request, resource):
        """Resolve one expanded QName through local-only XSD imports and includes.

        Every traversed schemaLocation is parsed without fetching remote resources.
        Ambiguous definitions and inconsistent import namespaces fail explicitly.
        """
        if not lexical or lexical.count(':') > 1:
            raise AIxCodegenValidationException(f'Invalid XSD {declaration_kind} QName {lexical!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
        prefix, separator, local = lexical.rpartition(':')
        namespace = resource[1][id(node)].get(prefix if separator else '')
        if separator and namespace is None:
            raise AIxCodegenValidationException(f'Undefined XSD namespace prefix {prefix!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
        if not local or ':' in local:
            raise AIxCodegenValidationException(f'Invalid XSD {declaration_kind} QName {lexical!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
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
                    raise AIxCodegenValidationException(f'XSD declaration imports must be local files: {location}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                included_path = (Path(unquote(uri.path)) if uri.scheme == 'file'
                                 else path.parent / unquote(uri.path)).resolve()
                if not included_path.is_file():
                    raise AIxCodegenValidationException(f'XSD declaration schemaLocation not found: {included_path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                imported = self._parse(included_path)
                imported_namespace = imported[0].get('targetNamespace', '')
                if include.tag == self._xs + 'import':
                    if include.get('namespace', '') != imported_namespace:
                        raise AIxCodegenValidationException(f'XSD import namespace disagrees with schemaLocation: {location}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                elif imported_namespace != schema.get('targetNamespace', ''):
                    raise AIxCodegenValidationException(f'XSD include namespace disagrees with schemaLocation: {location}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                imported_request = AIcdDefinitionLoadRequest(included_path, self.source_kind,
                                                            request.naming_profile)
                visit(imported_request, imported)

        visit(request, resource)
        if len(found) != 1:
            raise AIxCodegenValidationException(f'{"Ambiguous" if found else "Unknown"} XSD {declaration_kind} '
                             f'reference {lexical!r} in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        return found[0]

    def _key_field_path(self, entry_complex, xpath, request, resource):
        """Resolve one typed XSD key path through declared XML children.

        Paths use the restricted identity-constraint XPath form: child steps
        followed by an attribute or a simple-valued element. Every intermediate
        element must have at most one occurrence; optional intermediate objects
        remain valid and the generated extractor must guard each nullable hop.
        The returned dotted path is a sequence of canonical field names.

        Args:
            entry_complex: Complex type declaration of the selected map item.
            xpath: Nonempty namespace-aware field XPath.
            request: Source context for diagnostics and same-schema type lookup.
            resource: Parsed source and its in-scope namespace declarations.

        Returns:
            Dotted canonical property path preserving the XSD traversal order.

        Raises:
            ValueError: If an XPath step is ambiguous, untyped, out of scope,
                uses unsupported navigation, or selects a repeated intermediate.
        """
        lexical = xpath.removeprefix('./')
        if not lexical or '//' in lexical or any(token in lexical for token in ('|', '[', ']', '*', '(', ')')):
            raise AIxCodegenValidationException(f'Unsupported xs:key field XPath {xpath!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
        steps = lexical.split('/')
        if any(not step or step in ('.', '..') for step in steps):
            raise AIxCodegenValidationException(f'Invalid xs:key field XPath {xpath!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
        root, namespaces = resource
        target_namespace = root.get('targetNamespace', '')
        current_type = entry_complex
        found = []
        for position, step in enumerate(steps):
            attribute = step.startswith('@')
            if attribute and position != len(steps) - 1:
                raise AIxCodegenValidationException(f'An xs:key attribute cannot have descendants: {xpath!r}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
            name = step[1:] if attribute else step
            prefix, separator, local = name.partition(':')
            qualified_name = local if separator else name
            if not qualified_name or not qualified_name.replace('_', 'a').replace('-', 'a').isalnum():
                raise AIxCodegenValidationException(f'Unsupported xs:key field name {step!r} in {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
            # Identity constraints evaluate the effective XSD type, not merely
            # the immediate syntactic children of a complexType declaration.
            # In particular xs:complexContent/xs:extension adds local attributes
            # beneath extension (and can inherit attributes from its base).
            def effective_field_nodes(type_node, seen=None):
                seen = set() if seen is None else seen
                if id(type_node) in seen:
                    raise AIxCodegenValidationException(
                        'Cyclic XML complex type extension while resolving xs:key',
                        'Check the XSD base type definitions for circular inheritance.')
                seen.add(id(type_node))
                selected = []
                content = self._child(type_node, 'complexContent')
                extension = self._child(content, 'extension') if content is not None else None
                if extension is not None:
                    base_name = extension.get('base')
                    if base_name:
                        base_type = self._named_type(root, base_name.split(':')[-1])
                        if base_type is not None:
                            selected.extend(effective_field_nodes(base_type, seen))
                for holder in (type_node, extension):
                    if holder is None:
                        continue
                    if attribute:
                        selected.extend(self._children(holder, 'attribute'))
                    else:
                        selected.extend(element for group in self._children(holder, 'sequence', 'all')
                                        for element in self._children(group, 'element'))
                return selected
            current = effective_field_nodes(current_type)
            matching = []
            for child in current:
                if child.get('name') != qualified_name:
                    continue
                namespace = self._field_namespace(child, root, attribute)
                declared_namespace = namespaces.get(id(child), {}).get(prefix) if separator else ''
                if namespace == declared_namespace:
                    matching.append(child)
            if len(matching) != 1:
                raise AIxCodegenValidationException(f'Unresolved or ambiguous xs:key field step {step!r} in {xpath!r} ({request.path})', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
            child = matching[0]
            found.append(qualified_name)
            if not attribute:
                maximum = child.get('maxOccurs', '1')
                if position < len(steps) - 1 and (maximum == 'unbounded' or int(maximum) > 1):
                    raise AIxCodegenValidationException(f'Repeated intermediate xs:key field {step!r} in {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
            if position < len(steps) - 1:
                current_type = self._child(child, 'complexType')
                if current_type is None and child.get('type'):
                    reference = child.get('type')
                    type_prefix, type_separator, type_local = reference.partition(':')
                    declared_namespace = namespaces.get(id(child), {}).get(type_prefix) if type_separator else target_namespace
                    if declared_namespace == target_namespace:
                        current_type = self._named_type(root, type_local if type_separator else reference)
                if current_type is None:
                    raise AIxCodegenValidationException(f'Intermediate xs:key field is not a resolved complex type: {step!r} in {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
            else:
                if not attribute and child.get('maxOccurs', '1') not in ('1', ''):
                    raise AIxCodegenValidationException(f'xs:key field selects multiple values: {xpath!r}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                value_shape = self._shape(child, child.get('type', ''), request, resource, set())
                if value_shape.kind in (AInDataTypeKind.OBJECT, AInDataTypeKind.ARRAY,
                                        AInDataTypeKind.ANY, AInDataTypeKind.ONE_OF,
                                        AInDataTypeKind.ANY_OF):
                    raise AIxCodegenValidationException(f'xs:key field requires one typed simple value: {xpath!r}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
        return '.'.join(found)

    def _keyed_element_type(self, declaration, request, resource):
        """Preserve a direct XSD xs:key collection as typed KEYED_VALUES.

        A selector must name exactly the one directly repeated child element.
        All XSD keys selecting it become indexed definitions, including composite
        keys. The item's regular XML attribute/element fields remain in its value.
        Other XSD key selectors are constraints outside this mapping and must not
        be silently treated as a multi-mapped list. xs:keyref is a validation-
        only relationship, deliberately ignored by structural code generation.
        """
        # Both xs:key and xs:unique define unique index projections. The latter
        # allows an absent/incomplete key tuple, represented by a null map key.
        keys = list(self._children(declaration, 'key')) + list(self._children(declaration, 'unique'))
        if not keys:
            return None
        complex_type = self._child(declaration, 'complexType')
        if complex_type is None and declaration.get('type'):
            complex_type = self._named_type(resource[0], declaration.get('type').split(':')[-1])
        if complex_type is None:
            raise AIxCodegenValidationException(f'xs:key collection type is not a locally resolved XML complex type: {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
        sequence = self._child(complex_type, 'sequence')
        entries = self._children(sequence, 'element') if sequence is not None else ()
        if len(entries) != 1 or entries[0].get('maxOccurs') not in ('unbounded',) and not (
                entries[0].get('maxOccurs', '1').isdigit() and int(entries[0].get('maxOccurs', '1')) > 1):
            raise AIxCodegenValidationException(f'xs:key does not describe a single repeated XML entry collection: {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
        entry = entries[0]
        entry_name = entry.get('name', '')
        entry_complex = self._child(entry, 'complexType')
        if entry_complex is None and entry.get('type'):
            entry_complex = self._named_type(resource[0], entry.get('type').split(':')[-1])
        if not entry_name or entry_complex is None:
            raise AIxCodegenValidationException(f'xs:key entry must have named, typed XML content: {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
        fields = self._complex_properties(entry_complex, request, resource, frozenset())
        declared_names = {field.source_name for field in fields}
        definitions = []
        target_namespace = resource[0].get('targetNamespace', '')
        entry_qualified = entry.get('form', resource[0].get('elementFormDefault', 'unqualified')) == 'qualified'
        def local_xpath_name(node, lexical, qualified):
            """Resolve a simple XSD identity-constraint XPath with exact namespace semantics."""
            lexical = lexical.removeprefix('./')
            prefix, sep, local = lexical.partition(':')
            if not sep:
                if qualified and target_namespace:
                    raise AIxCodegenValidationException(f'Unqualified XSD XPath cannot select a qualified element: {lexical!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                return lexical
            namespace = resource[1].get(id(node), {}).get(prefix)
            if namespace != target_namespace or not qualified:
                raise AIxCodegenValidationException(f'Wrong namespace for XSD XPath {lexical!r} in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
            return local
        for key in keys:
            selector = self._child(key, 'selector')
            if selector is None or local_xpath_name(selector,
                    selector.get('xpath', ''), entry_qualified) != entry_name:
                raise AIxCodegenValidationException(f'xs:key selector cannot map directly to this collection: {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
            paths = []
            for field in self._children(key, 'field'):
                xpath = field.get('xpath', '')
                path = self._key_field_path(entry_complex, xpath, request, resource)
                if path.split('.', 1)[0] not in declared_names or path in paths:
                    raise AIxCodegenValidationException(f'Unresolved/duplicate xs:key component {path!r} in {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
                paths.append(path)
            if not paths:
                raise AIxCodegenValidationException(f'xs:key requires at least one typed field in {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
            definitions.append(AIcdKeyDefinition(key.get('name', ''), tuple(paths),
                required=(key.tag == self._xs + 'key')))
        if len({item.name for item in definitions}) != len(definitions):
            raise AIxCodegenValidationException(f'Duplicate xs:key identity in {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
        return AIcdDataType(AInDataTypeKind.OBJECT,
            keyed_value_type=AIcdDataType(AInDataTypeKind.OBJECT, properties=fields),
            key_definitions=tuple(definitions))

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
                raise AIxCodegenValidationException(f'Optional XSD compositor cannot be flattened without losing group cardinality in {path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
            raise AIxCodegenValidationException(f'XSD compositor cannot be flattened without losing group cardinality in {path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
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

    def _elements_fragment(self, branch, request, resource, groups):
        """Project exactly one typed XSD choice branch without modifying its context."""
        from xml.etree.ElementTree import Element
        synthetic = Element(self._xs + 'sequence')
        synthetic.append(branch)
        try:
            yield from self._elements(synthetic, True, request, resource, groups)
        finally:
            synthetic.remove(branch)

    def _array_wrapper_type(self, declaration, request, resource):
        """Map one XML wrapper with a single repeated typed child to ARRAY."""
        inner = self._child(declaration, 'complexType')
        if inner is None or self._child(inner, 'attribute', 'anyAttribute', 'choice', 'all') is not None:
            return None
        sequence = self._child(inner, 'sequence')
        members = self._children(sequence, 'element') if sequence is not None else ()
        if len(members) != 1 or len(self._children(sequence)) != 1:
            return None
        member = members[0]
        minimum, maximum = self._validate_occurs(member, False, request.path)
        if maximum == 1:
            return None
        shape = self._shape(member, member.get('type', ''), request, resource, set())
        value = from_source_hints(shape.kind, shape.item_kind, shape.reference,
                   shape.constraints, shape.item_constraints)
        return AIcdDataType(AInDataTypeKind.ARRAY, element_type=value,
            constraints=AIcdValueConstraints(min_items=minimum, max_items=maximum))

    def _elements(self, parent, optional, request, resource, groups=frozenset()):
        """Project leaf XML fields while resolving acyclic local named compositor groups."""
        for xml_order, node in enumerate(self._children(parent)):
            kind = node.tag.removeprefix(self._xs)
            if kind in ('sequence', 'all', 'choice'):
                minimum, maximum = self._validate_occurs(node, True, request.path)
                if kind == 'choice':
                    if not self._repeated_choice(node):
                        # Each branch is required *within its choice* but the
                        # value-level read interface has optional getters for
                        # mutually exclusive branches. Preserve all typed
                        # fields; XML's actual XSD still checks the choice.
                        branches = self._children(node)
                        if not branches or any(child.tag not in
                                (self._xs + 'element', self._xs + 'sequence')
                                for child in branches):
                            raise AIxCodegenValidationException(f'Unsupported nested XSD choice particle: {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
                        all_fields = []
                        for branch in branches:
                            if branch.tag == self._xs + 'element':
                                fields = tuple(self._elements_fragment(branch, request, resource, groups))
                            else:
                                fields = tuple(self._elements(branch, True, request, resource, groups))
                            all_fields.extend(replace(field, presence=AInFieldPresenceKind.ALLOWED)
                                              for field in fields)
                        if len({field.source_name for field in all_fields}) != len(all_fields):
                            raise AIxCodegenValidationException(f'Overlapping nested XSD choices cannot safely project: {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
                        yield from all_fields
                        continue
                    parent_index = {id(child): parent_node for parent_node in resource[0].iter()
                        for child in parent_node}
                    owner = parent_index.get(id(node))
                    while owner is not None and owner.tag != self._xs + 'complexType':
                        owner = parent_index.get(id(owner))
                    if owner is None or not owner.get('name'):
                        raise AIxCodegenValidationException(f'Repeated XSD choice requires a named complexType: {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
                    ordinal = next((index for index, item in enumerate(self._descendant_choices(owner), 1)
                        if item is node), None)
                    if ordinal is None:
                        raise AIxCodegenValidationException('Cannot resolve ordinal of nested XSD choice', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
                    name = owner.get('name') + 'Choice' + str(ordinal)
                    logical = self._type_identifier(name, request)
                    parsed = self._identities.from_file(request,
                        int(resource[0].get('version')) if resource[0].get('version', '').isdigit() else None)
                    choice_type = self._synthetic_choice_type(node, request, resource)
                    reference = AIcdDefinitionReference('#@type/' + name,
                        parsed.version, logical, choice_type)
                    maximum = node.get('maxOccurs', '1')
                    data_type = AIcdDataType(AInDataTypeKind.ARRAY,
                        element_type=AIcdDataType(AInDataTypeKind.REFERENCE, reference=reference),
                        constraints=AIcdValueConstraints(min_items=minimum,
                            max_items=None if maximum == 'unbounded' else int(maximum)))
                    yield AIcdPropertyDefinition('Choice' + str(ordinal), data_type,
                        AInFieldPresenceKind.ALLOWED if optional or minimum == 0 else AInFieldPresenceKind.REQUIRED,
                        False, self._documentation(node), self._title(node), None)
                    continue
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
                        raise AIxCodegenValidationException(f'Invalid XSD element reference declaration in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
                    declaration, declaration_request, declaration_resource = self._resolve_global(
                        node, referenced, 'element', request, resource)
                    local_name = declaration.get('name')
                    global_field = True
                if not local_name:
                    raise AIxCodegenValidationException(f'XSD element references require a named canonical property: {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
                if self._child(declaration, 'alternative') is not None:
                    raise AIxCodegenValidationException(f'Unsupported XSD conditional element type in {request.path}: {local_name}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
                shape = self._shape(declaration, declaration.get('type', ''), declaration_request, declaration_resource, set())
                repeated = maximum is None or maximum > 1
                if repeated and shape.kind is AInDataTypeKind.ARRAY: raise AIxCodegenValidationException('Nested XSD lists are not represented by the canonical property model', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
                data_type = from_source_hints(AInDataTypeKind.ARRAY if repeated else shape.kind,
                    shape.kind if repeated else shape.item_kind, shape.reference,
                    AIcdValueConstraints() if repeated else shape.constraints,
                    shape.constraints if repeated else shape.item_constraints)
                parents = {id(child): parent for parent in resource[0].iter() for child in parent}
                containing_sequence = parents.get(id(node))
                containing_type = parents.get(id(containing_sequence))
                owner = parents.get(id(containing_type))
                mapped_owner = owner if owner is not None and owner.tag == self._xs + 'element' else None
                if mapped_owner is None and containing_type is not None and containing_type.get('name'):
                    # xs:key is declared on the element *using* a named
                    # complexType, not on the type itself. Resolve that owner
                    # without changing the original XML wire representation.
                    type_name = containing_type.get('name')
                    matching_owners = [candidate for candidate in resource[0].iter(self._xs + 'element')
                        if candidate.get('type', '').split(':')[-1] == type_name
                        and (self._children(candidate, 'key') or self._children(candidate, 'unique'))]
                    if len(matching_owners) > 1:
                        raise AIxCodegenValidationException(f'Ambiguous keyed XML owner of named type {type_name!r} in {request.path}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
                    mapped_owner = matching_owners[0] if matching_owners else None
                mapped = (self._keyed_element_type(mapped_owner, request, resource)
                          if mapped_owner is not None else None)
                if not repeated and mapped is not None:
                    raise AIxCodegenValidationException(f'xs:key selects non-repeating XML element: {local_name}', 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
                if repeated:
                    data_type = replace(data_type, constraints=AIcdValueConstraints(
                        min_items=minimum, max_items=maximum),
                        key_definitions=mapped.key_definitions if mapped is not None else ())
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
                    raise AIxCodegenValidationException(f'Unsupported XSD wildcard/group particle {kind!r} in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
                definition, group_request, group_resource = self._resolve_global(
                    node, reference, 'group', request, resource)
                identity = (str(group_request.path.resolve()), definition.get('name'))
                if identity in groups:
                    raise AIxCodegenValidationException(f'Circular XSD group reference {reference!r} in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
                projected = tuple(self._elements(definition, optional,
                    group_request, group_resource, groups | {identity}))
                yield from self._compositor_fields(projected, minimum, maximum, optional, request.path)
            elif kind == 'any':
                minimum, maximum = self._validate_occurs(node, False, request.path)
                namespace_constraint = node.get('namespace', '##any')
                process_contents = node.get('processContents', 'strict')
                if process_contents not in ('skip', 'lax', 'strict'):
                    raise AIxCodegenValidationException(f'Invalid xs:any processContents in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
                if not namespace_constraint.strip():
                    raise AIxCodegenValidationException(f'Invalid xs:any namespace constraint in {request.path}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
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
                raise AIxCodegenValidationException(f'Unsupported XSD content model child {kind!r} '
                                 f'in {request.path}; refusing a partial projection', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')

    def _attributes(self, typ, request, resource, groups=frozenset()):
        """Resolve local named attribute groups while preserving each member's QName."""
        if self._child(typ, 'anyAttribute') is not None:
            raise AIxCodegenValidationException(f'Unsupported XSD attribute wildcard in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        for attribute in self._children(typ, 'attribute', 'attributeGroup'):
            if attribute.tag == self._xs + 'attributeGroup':
                reference = attribute.get('ref', '')
                if not reference or attribute.get('name'):
                    raise AIxCodegenValidationException(f'Invalid XSD attributeGroup reference {reference!r} in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
                definition, group_request, group_resource = self._resolve_global(
                    attribute, reference, 'attributeGroup', request, resource)
                identity = (str(group_request.path.resolve()), definition.get('name'))
                if identity in groups:
                    raise AIxCodegenValidationException(f'Circular XSD attributeGroup reference {reference!r} in {request.path}', 'Check the XSD compositor and group declarations. Use a named XML type for a repeated choice and avoid overlapping or unsupported nested groups.')
                yield from self._attributes(definition, group_request, group_resource, groups | {identity})
                continue
            declaration = attribute
            declaration_request, declaration_resource = request, resource
            reference = attribute.get('ref', '')
            if reference:
                if attribute.get('name') or attribute.get('type') or attribute.get('form'):
                    raise AIxCodegenValidationException(f'Invalid XSD attribute reference {reference!r} in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
                declaration, declaration_request, declaration_resource = self._resolve_global(
                    attribute, reference, 'attribute', request, resource)
            name = declaration.get('name', '')
            if not name:
                raise AIxCodegenValidationException(f'Unnamed XSD attribute in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
            shape = self._shape(declaration, declaration.get('type', ''),
                                declaration_request, declaration_resource, set())
            if shape.kind in (AInDataTypeKind.ARRAY, AInDataTypeKind.OBJECT):
                raise AIxCodegenValidationException(f'XML attribute {name!r} must have a scalar type in {request.path}', 'Check the XSD scalar type and restriction facets. Use supported XML Schema built-in types and consistent upper/lower bounds.')
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
        raise AIxCodegenValidationException(f'Invalid XML Schema field form {form!r}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')

    def _shape(self, context, name, request, resource, visited):
        root, namespaces = resource
        if not name:
            content = self._child(context, 'complexType')
            if content is not None:
                if content is self._root_type(root):
                    return _AIcdXmlShape(AInDataTypeKind.OBJECT)
                inline_name = next((inline_name for inline_name, candidate
                                    in self._inline_content_types(root) if candidate is content), None)
                if inline_name is None:
                    raise AIxCodegenValidationException('Unresolved anonymous XML content type', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
                logical = self._type_identifier(inline_name, request)
                parsed = self._identities.from_file(request,
                    int(root.get('version')) if root.get('version', '').isdigit() else None)
                return _AIcdXmlShape(AInDataTypeKind.REFERENCE,
                    reference=AIcdDefinitionReference('#@type/' + inline_name,
                        parsed.version, logical, AIcdDataType(AInDataTypeKind.OBJECT)))
            simple = self._child(context, 'simpleType')
            return _AIcdXmlShape(AInDataTypeKind.ANY) if simple is None else self._simple_shape(simple, request, resource, visited)
        local = name.split(':')[-1]
        namespace = namespaces[id(context)].get(name.split(':')[0] if ':' in name else '')
        if namespace == self._ns or (':' not in name and namespace is None and self._builtin(local) is not None):
            result = self._builtin(local)
            if result is None: raise AIxCodegenValidationException(f"Unknown XSD built-in type '{name}'", 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
            return result
        key = (request.path.resolve(), namespace, local)
        if key in visited: raise AIxCodegenValidationException(f"Circular XSD simple type '{name}'", 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        visited.add(key)
        if namespace is None or namespace == root.get('targetNamespace'):
            typ = self._named_type(root, local)
            if typ is not None:
                if typ.tag == self._xs + 'simpleType':
                    return self._simple_shape(typ, request, resource, visited)
                # A named complexType is an independently emitted contract.
                # Keep its identity just as JSON $ref does, rather than losing
                # the type and rendering a Map[str, object] / Map<String, Object>.
                logical = self._type_identifier(local, request)
                parsed = self._identities.from_file(request,
                    int(root.get('version')) if root.get('version', '').isdigit() else None)
                # The schema's selected primary type is emitted as the root
                # contract, not as an additional @type sibling.
                primary = typ is self._root_type(root)
                reference = AIcdDefinitionReference('#' if primary else '#@type/' + local,
                    parsed.version, parsed.logical_name if primary else logical,
                    AIcdDataType(AInDataTypeKind.OBJECT))
                return _AIcdXmlShape(AInDataTypeKind.REFERENCE, reference=reference)
        for imp in self._children(root, 'import', 'include'):
            if imp.tag == self._xs+'import' and imp.get('namespace') != namespace: continue
            if imp.tag == self._xs+'include' and namespace is not None and namespace != root.get('targetNamespace'): continue
            location = imp.get('schemaLocation')
            if not location: continue
            uri = urlsplit(location)
            if uri.scheme and uri.scheme != 'file': raise AIxCodegenValidationException(f'XSD imports must resolve locally: {location}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
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
        raise AIxCodegenValidationException(f"Undefined XSD type '{name}' in {request.path}", 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')

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
                    raise AIxCodegenValidationException(f'Duplicate XSD restriction facet {kind!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
                seen.add(category)
                if kind in ('minInclusive', 'minExclusive'):
                    kwargs.update(minimum=decimal_text(value), exclusive_minimum=kind == 'minExclusive')
                elif kind in ('maxInclusive', 'maxExclusive'):
                    kwargs.update(maximum=decimal_text(value), exclusive_maximum=kind == 'maxExclusive')
                elif kind == 'length':
                    if 'minLength' in seen or 'maxLength' in seen:
                        raise AIxCodegenValidationException(f'Conflicting XSD length facets in {request.path}', 'Check the XSD scalar type and restriction facets. Use supported XML Schema built-in types and consistent upper/lower bounds.')
                    kwargs.update(min_length=int(value), max_length=int(value))
                elif kind == 'minLength':
                    if 'length' in seen:
                        raise AIxCodegenValidationException(f'Conflicting XSD length facets in {request.path}', 'Check the XSD scalar type and restriction facets. Use supported XML Schema built-in types and consistent upper/lower bounds.')
                    kwargs['min_length'] = int(value)
                elif kind == 'maxLength':
                    if 'length' in seen:
                        raise AIxCodegenValidationException(f'Conflicting XSD length facets in {request.path}', 'Check the XSD scalar type and restriction facets. Use supported XML Schema built-in types and consistent upper/lower bounds.')
                    kwargs['max_length'] = int(value)
                elif kind == 'pattern':
                    if base.constraints.pattern is not None and base.constraints.pattern != value:
                        raise AIxCodegenValidationException(f'Unsupported conjunction of inherited XSD pattern facets in {request.path}', 'Check the XSD scalar type and restriction facets. Use supported XML Schema built-in types and consistent upper/lower bounds.')
                    kwargs['pattern'] = value
                elif kind == 'enumeration':
                    values.append(value)
                else:
                    raise AIxCodegenValidationException(f'Unsupported XSD restriction facet {kind!r} in {request.path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
            if values:
                kwargs['enum_values'] = tuple(values)
            derived = replace(base.constraints, **kwargs)
            self._validate_restriction_facets(base.constraints, derived, request.path)
            return replace(base, constraints=derived)

        listing = self._child(typ, 'list')
        if listing is not None:
            item = self._shape(listing, listing.get('itemType', ''), request, resource, visited)
            return _AIcdXmlShape(AInDataTypeKind.ARRAY, item.kind, item.reference, item_constraints=item.constraints)
        raise AIxCodegenValidationException(f'Unsupported XSD simple type in {request.path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')

    @staticmethod
    def _validate_restriction_facets(base, derived, path):
        """Require representable facets to narrow inherited XSD simple types."""
        if base.min_items is not None and (derived.min_items is None or derived.min_items < base.min_items):
            raise AIxCodegenValidationException(f'XSD restriction relaxes inherited minOccurs in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if base.max_items is not None and (derived.max_items is None or derived.max_items > base.max_items):
            raise AIxCodegenValidationException(f'XSD restriction relaxes inherited maxOccurs in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if base.minimum is not None and (
            derived.minimum is None or Decimal(derived.minimum) < Decimal(base.minimum) or
            (Decimal(derived.minimum) == Decimal(base.minimum) and
             base.exclusive_minimum and not derived.exclusive_minimum)):
            raise AIxCodegenValidationException(f'XSD restriction relaxes inherited minimum in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if base.maximum is not None and (
            derived.maximum is None or Decimal(derived.maximum) > Decimal(base.maximum) or
            (Decimal(derived.maximum) == Decimal(base.maximum) and
             base.exclusive_maximum and not derived.exclusive_maximum)):
            raise AIxCodegenValidationException(f'XSD restriction relaxes inherited maximum in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if derived.minimum is not None and derived.maximum is not None:
            comparison = Decimal(derived.minimum).compare(Decimal(derived.maximum))
            if comparison > 0 or (comparison == 0 and
                (derived.exclusive_minimum or derived.exclusive_maximum)):
                raise AIxCodegenValidationException(f'Inconsistent XSD numeric restriction bounds in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if base.min_length is not None and (
            derived.min_length is None or derived.min_length < base.min_length):
            raise AIxCodegenValidationException(f'XSD restriction relaxes inherited minLength in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if base.max_length is not None and (
            derived.max_length is None or derived.max_length > base.max_length):
            raise AIxCodegenValidationException(f'XSD restriction relaxes inherited maxLength in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if (derived.min_length is not None and derived.max_length is not None and
                derived.min_length > derived.max_length):
            raise AIxCodegenValidationException(f'Inconsistent XSD length restriction in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if base.enum_values and not derived.enum_values:
            raise AIxCodegenValidationException(f'XSD restriction removes inherited enumeration in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
        if base.enum_values and not set(derived.enum_values).issubset(base.enum_values):
            raise AIxCodegenValidationException(f'XSD restriction widens inherited enumeration in {path}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')

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
            raise AIxCodegenValidationException(f'Expected XML Schema root in {path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        # This loader has no safe, round-trippable model for unrestricted
        # XML values. Reject explicit and implicit xs:anyType *at their source*.
        # The implicit anyType ancestry of valid named complex types is not
        # itself a use of the unrestricted value type and remains supported.
        for node in root.iter():
            local = node.tag.removeprefix('{http://www.w3.org/2001/XMLSchema}')
            lexical = node.get('type', '') or node.get('base', '')
            if lexical:
                prefix, separator, name = lexical.rpartition(':')
                name = name if separator else lexical
                namespace = contexts[id(node)].get(prefix if separator else '')
                if name == 'anyType' and namespace == 'http://www.w3.org/2001/XMLSchema':
                    raise AIxCodegenValidationException(f'Unsupported XSD xs:anyType in {path}: '
                                     f'{local} {node.get("name", "")} (explicit type/base)', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
            if node.tag == '{http://www.w3.org/2001/XMLSchema}element':
                # In XSD, an untyped declaration defaults to xs:anyType
                # (xs:anySimpleType for attributes). Local refs use the global
                # declaration's type, so they are handled at their target.
                if (not node.get('type') and not node.get('ref')
                        and not any(child.tag in (
                            '{http://www.w3.org/2001/XMLSchema}simpleType',
                            '{http://www.w3.org/2001/XMLSchema}complexType')
                            for child in node)):
                    raise AIxCodegenValidationException(f'Unsupported implicit XSD anyType in {path}: '
                                     f'{local} {node.get("name", "")}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        for child in root:
            if child.tag in ('{http://www.w3.org/2001/XMLSchema}redefine',
                             '{http://www.w3.org/2001/XMLSchema}override',
                             '{http://www.w3.org/2001/XMLSchema}defaultOpenContent'):
                raise AIxCodegenValidationException(f'Unsupported XSD schema directive {child.tag!r} in {path}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
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
        element = appinfo.find("{https://defs.dev.algites.eu/api/xmldefs/eu/algites/lib/common/documentation/algites-documentation_1.xsd}title")
        return (element.text or "").strip() or None if element is not None else None

    @classmethod
    def _enum_values(cls, typ):
        return tuple(AIcdEnumValueDefinition(value.get('value'), cls._documentation(value), cls._title(value)) for value in cls._children(cls._child(typ, 'restriction'), 'enumeration'))

    @classmethod
    def _documentation(cls, node):
        doc = cls._child(cls._child(node, 'annotation'), 'documentation')
        return ' '.join(''.join(doc.itertext()).split()) or None if doc is not None else None
