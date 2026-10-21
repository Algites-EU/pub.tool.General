"""Generate XML-only namespace contracts and project xs:any onto typed XML objects."""
from __future__ import annotations
import re
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from .aic_generation_names import AIcGenerationNames


def namespace_identifier(namespace: str) -> str:
    """Create a deterministic, readable identifier for a full namespace URI."""
    tokens = re.findall(r'[A-Za-z0-9]+', namespace)
    return ''.join(token[0].upper() + token[1:] for token in tokens) or 'Local'


def namespace_contract(request, namespace: str) -> tuple[str, str, str]:
    """Render the XML namespace type and filename via their own selected naming roles."""
    names = AIcGenerationNames()
    identifier = namespace_identifier(namespace)
    canonical = identifier
    canonical = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', canonical)
    canonical = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1-\2', canonical).lower()
    profile = request.naming_profile
    type_name = names.render(canonical, None, profile,
        AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE)
    stem = names.render(canonical, None, profile,
        AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM)
    return type_name, stem, request.package_name + '.' + stem


def namespace_of_wildcard(constraint: str, target: str) -> str | None:
    """Return a single constrained URI, or None for an unconstrained namespace union."""
    parts = constraint.split()
    if parts == ['##targetNamespace']:
        return target
    if len(parts) == 1 and not parts[0].startswith('##'):
        return parts[0]
    return None


def source(request, namespace: str) -> tuple[str, str, str]:
    """Emit a namespace interface in the same Java/Python XML generation root."""
    from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
    type_name, stem, module = namespace_contract(request, namespace)
    package = request.package_name
    if request.target is AInCodeGenerationTarget.JAVA:
        import json
        value = json.dumps(namespace, ensure_ascii=False)
        code = ('package ' + package + ';\n\n'
            '/** XML namespace contract for ' + namespace.replace('*/', '* /')
            + '; implemented by all generated XML objects in this namespace. */\n'
            '@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject(namespace = ' + value + ')\n'
            'public interface ' + type_name + ' extends '
            'eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObjectNamespace {\n}\n')
        path = package.replace('.', '/') + '/' + type_name + '.java'
    else:
        code = ('from __future__ import annotations\n'
            'from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object_namespace import AIiXmlDataObjectNamespace\n'
            'from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject\n\n'
            'class ' + type_name + '(AIiXmlDataObjectNamespace):\n'
            '    """Interface for XML objects belonging to this exact XML namespace."""\n'
            '    __xml_data_object__ = AIaXmlDataObject(namespace=' + repr(namespace) + ')\n'
            '    __slots__ = ()\n')
        path = package.replace('.', '/') + '/' + stem + '.py'
    return type_name, path, code


def decorate(generated: str, request, marker: str, fields: dict[str, str], python: bool) -> str:
    """Add namespace inheritance and XML wildcard object getter projections."""
    from .aic_generation_names import AIcGenerationNames
    names = AIcGenerationNames()
    own_name = marker.rsplit('.', 1)[-1]
    if python:
        own_name = marker.rsplit('.', 1)[-1]
        marker_mod = marker.rsplit('.', 1)[0]
        generated = generated.replace('from __future__ import annotations\n',
            'from __future__ import annotations\nfrom ' + marker_mod + ' import ' + own_name + '\n')
        declaration = re.search(r'^(class [A-Za-z_][A-Za-z_0-9]*\()([^)]*)(\):)', generated, re.M)
        if declaration:
            bases = [part.strip() for part in declaration.group(2).split(',') if part.strip()]
            bases = [base for base in bases if base != 'AIiXmlDataObject']
            if own_name not in bases:
                bases.insert(0, own_name) if bases == ['ABC'] else bases.append(own_name)
            generated = generated[:declaration.start()] + declaration.group(1) + ', '.join(bases) + declaration.group(3) + generated[declaration.end():]
    else:
        declaration = re.search(
            r'^(public (?:sealed )?interface [A-Za-z_][A-Za-z_0-9]* extends )([^\n{]*?)(?= permits | \{)',
            generated, re.M)
        if declaration and marker not in declaration.group(2):
            generated = (generated[:declaration.end(2)] + ', ' + marker
                         + generated[declaration.end(2):])
    for name, qualified in fields.items():
        if python:
            module, target = qualified.rsplit('.', 1)
            generated = generated.replace('from __future__ import annotations\n',
                'from __future__ import annotations\nfrom ' + module + ' import ' + target + '\n')
            typ = target
            property_name = names.property_name(name, request.naming_profile)
            prop_name = re.sub('[^A-Za-z0-9_]', '_', property_name)
            field_re = r'(^    ' + re.escape(prop_name) + r': )[^\n]+'
            def re_field(match):
                previous = match.group(0)
                return match.group(1) + ('tuple[' + typ + ', ...]' if 'tuple[' in previous else typ)
            generated = re.sub(field_re, re_field, generated, count=1, flags=re.M)
            getter_name = names.getter_name(name, request.naming_profile)
            pattern = r'(    def ' + re.escape(getter_name) + r'\(self\))(?: -> [^:]+)?(:)'
            declared = re.search(pattern, generated)
            if declared:
                original = re.search(field_re, generated, re.M)
                field_type = original.group(0).split(': ',1)[1] if original else typ
                generated = re.sub(pattern, r'\1 -> '+field_type+r'\2', generated, count=1)
        else:
            # Methods use configured property identifiers, not hardcoded get-prefixes.
            property_name = names.property_name(name, request.naming_profile)
            pattern = r'(^    )[^\n]*?(' + re.escape(names.getter_name(name, request.naming_profile)) + r'\(\);$)'
            def replace_getter(match):
                original = match.group(0)
                return match.group(1) + ('java.util.List<? extends ' + qualified + '>'
                    if 'java.util.List<' in original else qualified) + ' ' + match.group(2)
            generated, changed = re.subn(pattern, replace_getter, generated, count=1, flags=re.M)
            if not changed:
                raise ValueError('XML wildcard getter not found: ' + property_name)
    return generated
