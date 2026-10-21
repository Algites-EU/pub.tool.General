"""Generate nominal XML element contracts without introducing artificial packages."""
from __future__ import annotations
import re
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.aicd_generated_type_identity import AIcdGeneratedTypeIdentity
from .aic_generation_names import AIcGenerationNames

_XSD = 'http://www.w3.org/2001/XMLSchema'
_SCALARS = {'string': ('String', 'str'), 'normalizedString': ('String', 'str'),
    'token': ('String', 'str'), 'boolean': ('Boolean', 'bool'), 'integer': ('Long', 'int'),
    'int': ('Long', 'int'), 'long': ('Long', 'int'), 'decimal': ('java.math.BigDecimal', 'Decimal'),
    'double': ('Double', 'float'), 'float': ('Double', 'float'), 'date': ('String', 'str'),
    'dateTime': ('String', 'str'), 'anyURI': ('String', 'str')}


class AIcXmlElementContractGenerator:
    """Encode element substitution as interface inheritance, not a data type alias."""

    def generate(self, request, element, types: dict[str, str], elements: dict[str, str], value_types=frozenset()):
        """Generate one public element interface using validated QName-to-contract indexes."""
        names = AIcGenerationNames()
        profile = request.naming_profile
        logical = xml_identifier(element.local_name)
        version = request.definition.version
        role = AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE
        element_convention = (profile.selected(role) if hasattr(profile, 'selected')
                              else request.naming_convention)
        name = names.render(logical, version, profile, role)
        language = request.target
        stem = names.render(logical, version, profile, AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM)
        ext = '.java' if language is AInCodeGenerationTarget.JAVA else '.py'
        path = request.package_name.replace('.', '/') + '/' + stem + ext
        head = elements.get(element.substitution_head_qname) if element.substitution_head_qname else None
        if element.substitution_head_qname and head is None:
            raise ValueError('Unresolved XML substitution head ' + element.substitution_head_qname)
        base = types.get(element.type_qname)
        scalar_type = element.type_qname in value_types
        builtin = None
        if element.type_qname.startswith('{' + _XSD + '}'):
            builtin = _SCALARS.get(element.type_qname.split('}', 1)[1])
            if builtin is None:
                raise ValueError('Unsupported XML scalar element type: ' + element.type_qname)
        elif base is None:
            raise ValueError('XML element content type is not a generated contract: ' + element.type_qname)
        elif scalar_type:
            builtin = (base, base.rsplit('.', 1)[-1])
        if language is AInCodeGenerationTarget.JAVA:
            extends = [value for value in (None if scalar_type else base, head) if value is not None]
            if not extends: extends = ['eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject']
            if len(set(extends)) != len(extends): extends = list(dict.fromkeys(extends))
            annotation = ('@eu.algites.lib.data.dataobject.AIaDataObject(schemaId = '
                + _java_quote(element.namespace + '#' + element.local_name) + ', schemaVersion = '
                + str(version if version is not None else -1) + ', namingConvention = ' + _java_quote(element_convention) + ')')
            xml_annotation = ('@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject('
                'definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.ELEMENT, '
                'namespace = ' + _java_quote(element.namespace) + ', namespaceLocalName = '
                + _java_quote(element.local_name) + ')')
            getter = ''
            if builtin is not None:
                typ = builtin[0]
                getter = ('    /** Value of global XML element ' + logical + '. */\n'
                    + '    @eu.algites.lib.data.dataobject.AIaDataObjectField(fieldName = '
                    + _java_quote(element.local_name)
                    + ', presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = '
                    + str(element.nillable).lower() + ')\n'
                    + '    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField(namespace = '
                    + _java_quote(element.namespace) + ', namespaceLocalName = '
                    + _java_quote(element.local_name) + ', order = 0)\n'
                    + '    ' + typ + ' ' + names.getter_name(logical, request.naming_profile, AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE) + '();\n')
            source = ('package ' + request.package_name + ';\n\n'
                + '/** Generated nominal contract of global XML element ' + logical + '. */\n'
                + annotation + '\n' + xml_annotation + '\n'
                + 'public interface ' + name + ' extends ' + ', '.join(extends) + ' {\n'
                + getter + '}\n')
        else:
            imports = ['from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject']
            scalar = builtin is not None
            superclass_names = []
            # Put the more specific substitution head before its content base to respect Python MRO.
            for qualified in (head, None if scalar_type else base):
                if qualified:
                    module, cls = qualified.rsplit('.', 1)
                    imports.append(f'from {module} import {cls}')
                    if cls not in superclass_names: superclass_names.append(cls)
            if not superclass_names:
                imports.append('from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject')
                superclass_names = ['AIiXmlDataObject']
            if scalar:
                imports.extend(['from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField',
                    'from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind'])
                if builtin[1] == 'Decimal': imports.append('from decimal import Decimal')
            if scalar_type:
                module, cls = base.rsplit('.', 1)
                imports.append(f'from {module} import {cls}')
            imports += ['from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject',
                'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind']
            body = (f'    __data_object__ = AIcdDataObject(schema_id={element.namespace + "#" + logical!r}, '
                f'schema_version={version if version is not None else -1}, '
                f'naming_convention={element_convention!r})\n'
                '    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.ELEMENT, '
                f'namespace={element.namespace!r}, namespace_local_name={element.local_name!r})\n'
                '    __slots__ = ()\n')
            if scalar:
                imports.append('from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField')
                body += (f'    __xml_data_object_fields__ = {{{element.local_name!r}: '
                    f'AIaXmlDataObjectField(namespace={element.namespace!r}, namespace_local_name={element.local_name!r})}}\n')
                getter_name = names.getter_name(logical, request.naming_profile, AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE)
                body += (f'    __data_object_fields__ = (AIcdDataObjectField(field_name={element.local_name!r}, '
                    f'presence=AInFieldPresenceKind.REQUIRED, allows_null={element.nillable}, '
                    f'getter_name={getter_name!r}),)\n'
                    f'    def {getter_name}(self) -> {builtin[1]}:\n'
                    '        raise NotImplementedError\n')
            source = ('from __future__ import annotations\n' + '\n'.join(sorted(set(imports)))
                + '\n\n' + f'class {name}({", ".join(superclass_names)}):\n' + body)
        return AIcdGeneratedSource(name, path, source,
            (AIcdGeneratedTypeIdentity.from_request(request, name, path, role),))


def xml_identifier(name: str) -> str:
    """Normalize XML local names to the existing lower-kebab canonical input grammar."""
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1-\2', name)
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name)
    return re.sub(r'[^A-Za-z0-9]+', '-', name).strip('-').lower()


def _java_quote(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
