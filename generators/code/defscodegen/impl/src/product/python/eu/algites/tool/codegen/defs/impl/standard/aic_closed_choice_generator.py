"""Generate one sealed Java choice and stable value-record variants per alternative."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.aicd_generated_type_identity import AIcdGeneratedTypeIdentity
from .aic_generation_names import AIcGenerationNames


def json_quote(value: str) -> str:
    """Render an escaped Java string literal for the generated annotation."""
    return json.dumps(value, ensure_ascii=False)


class AIcClosedChoiceGenerator:
    """Generate a contract and separately importable records in its owning package."""

    def __init__(self):
        self.names = AIcGenerationNames()

    def generate(self, request):
        model = request.definition
        choice = model.data_type
        if choice.kind not in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            raise ValueError('Definition is not a closed choice')
        kind = 'oneOf' if choice.kind is AInDataTypeKind.ONE_OF else 'anyOf'
        target = request.target
        cls = self.names.type_name(model, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE)
        stem = self.names.file_stem(model, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
        ext = '.java' if target is AInCodeGenerationTarget.JAVA else '.py'
        path_prefix = request.package_name.replace('.', '/') + '/'
        variants = []
        resolved = []
        for index, alternative in enumerate(choice.alternatives):
            reference = alternative.reference
            if alternative.kind is AInDataTypeKind.REFERENCE and reference is not None:
                label = reference.logical_name
                role = AInDefsNameRole.ENUM_TYPE if reference.targets_enum else AInDefsNameRole.INTERFACE_TYPE
                type_name = self.names.render(reference.logical_name, reference.version, request.naming_profile, role)
                file_role = AInDefsNameRole.ENUM_TYPE_FILE_STEM if role is AInDefsNameRole.ENUM_TYPE else AInDefsNameRole.INTERFACE_TYPE_FILE_STEM
                file_stem = self.names.render(reference.logical_name, reference.version, request.naming_profile, file_role)
                identity = reference.identity
            elif alternative.kind in (AInDataTypeKind.STRING, AInDataTypeKind.INTEGER,
                    AInDataTypeKind.NUMBER, AInDataTypeKind.BOOLEAN, AInDataTypeKind.ANY):
                scalar = {AInDataTypeKind.STRING: ('String', 'str'),
                    AInDataTypeKind.INTEGER: ('Long', 'int'),
                    AInDataTypeKind.NUMBER: ('java.math.BigDecimal', 'Decimal'),
                    AInDataTypeKind.BOOLEAN: ('Boolean', 'bool'),
                    AInDataTypeKind.ANY: ('Object', 'object')}
                types = scalar[alternative.kind]
                type_name = types[0] if target is AInCodeGenerationTarget.JAVA else types[1]
                label, file_stem = f'Alternative{index + 1}', None
                identity = model.identity + '#/' + kind + '/' + str(index)
            elif alternative.kind is AInDataTypeKind.OBJECT:
                # Batch discovery emits each inline branch as a separate contract.
                label = f'Alternative{index + 1}'
                name = model.logical_name + '-' + ('one-of' if kind == 'oneOf' else 'any-of') + '-' + str(index)
                type_name = self.names.render(name, model.version, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE)
                file_stem = self.names.render(name, model.version, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
                identity = model.identity + '#/' + kind + '/' + str(index)
            else:
                raise ValueError(f'Closed choice variant {index} requires a named or inline object type; got {alternative.kind.value}')
            resolved.append((label, type_name, file_stem, identity))
        if len({identity for _, _, _, identity in resolved}) != len(resolved):
            raise ValueError('Closed choice contains repeated alternatives')
        counts = Counter(label.lower() for label, *_ in resolved)
        for label, typ, file, identity in resolved:
            short = 'h' + hashlib.sha256(identity.encode()).hexdigest()[:8] if counts[label.lower()] > 1 else ''
            # Suffix ordering stays outside the canonical logical identifier.
            fragment = label + ('-' + short if short else '')
            logical = model.logical_name + '-' + fragment
            wrapper = self.names.render(logical, model.version, request.naming_profile, AInDefsNameRole.DATA_TYPE)
            wrapper_file = self.names.render(logical, model.version, request.naming_profile, AInDefsNameRole.DATA_TYPE_FILE_STEM)
            variants.append((wrapper, wrapper_file, typ, file))
        if target is AInCodeGenerationTarget.JAVA:
            xml_annotation = ''
            if request.xml_type_qname:
                namespace, local = request.xml_type_qname[1:].split('}', 1)
                xml_annotation = ('@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject('
                    'definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, '
                    f'namespace = {json_quote(namespace)}, namespaceLocalName = {json_quote(local)})\n')
            main = ('package ' + request.package_name + ';\n\n'
                '/** Generated closed ' + kind + ' schema contract. */\n'
                + xml_annotation
                + 'public sealed interface ' + cls
                + (' extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject' if model.source_kind is AInDefinitionSourceKind.XMLDEFS else '')
                + ' permits ' 
                + ', '.join(wrapper for wrapper, *_ in variants) + ' {\n}\n')
        else:
            xml_import = ('from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject\n'
                if model.source_kind is AInDefinitionSourceKind.XMLDEFS else '')
            xml_annotation = ''
            if request.xml_type_qname:
                namespace, local = request.xml_type_qname[1:].split('}', 1)
                xml_import += ('from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject\n'
                    'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind\n')
                xml_annotation = ('    __xml_data_object__ = AIaXmlDataObject('
                    'definition_kind=AInXmlObjectDefinitionKind.TYPE, '
                    f'namespace={namespace!r}, namespace_local_name={local!r})\n')
            main = ('from __future__ import annotations\n' + xml_import + '\n'
                'class ' + cls + ('(AIiXmlDataObject)' if model.source_kind is AInDefinitionSourceKind.XMLDEFS else '') + ':\n'
                + xml_annotation
                + '    """Generated closed ' + kind + ' choice; use a declared value wrapper."""\n'
                + '    __closed_choice_mode__ = ' + repr(kind) + '\n'
                + '    __slots__ = ()\n')
        primary = AIcdGeneratedSource(cls, path_prefix + stem + ext, main,
            (AIcdGeneratedTypeIdentity.from_request(request, cls, path_prefix + stem + ext,
                AInDefsNameRole.INTERFACE_TYPE),))
        generated = [primary]
        if model.source_kind is AInDefinitionSourceKind.XMLDEFS:
            # Unlike JSON/YAML schema discovery, XML particles do not create
            # independent units; emit the nominal read contracts here.
            from .aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
            for index, alternative in enumerate(choice.alternatives):
                if alternative.kind is not AInDataTypeKind.OBJECT:
                    raise ValueError('XML choice requires object branches retaining XML QName')
                logical = model.logical_name + '-' + ('one-of-' if kind == 'oneOf' else 'any-of-') + str(index)
                branch = AIcdCanonicalDefinition(model.identity + '#/' + kind + '/' + str(index), model.version, logical, model.source_kind, model.source_resource, model.description, alternative, (), None)
                subrequest = AIcdCodeGenerationRequest(branch, target, request.package_name, request.naming_profile)
                generated.append(AIcSchemaContractInterfaceGenerator().generate(subrequest))
        for wrapper, wrapper_file, typ, typ_file in variants:
            if target is AInCodeGenerationTarget.JAVA:
                body = ('package ' + request.package_name + ';\n\n'
                    '/** One explicitly selected, statically typed closed-choice alternative. */\n'
                    'public record ' + wrapper + '(' + typ + ' value) implements ' + cls + ' {\n'
                    '    /** Require a non-null selected alternative. */\n'
                    '    public ' + wrapper + ' { java.util.Objects.requireNonNull(value, "value"); }\n'
                    '}\n')
            else:
                body = ('from __future__ import annotations\n'
                    'from dataclasses import dataclass\n'
                    f'from .{stem} import {cls}\n'
                    + (f'from .{typ_file} import {typ}\n' if typ_file else
                       'from decimal import Decimal\n' if typ == 'Decimal' else '') + '\n'
                    '@dataclass(frozen=True, slots=True)\n'
                    f'class {wrapper}({cls}):\n'
                    '    """One explicitly selected closed-choice alternative."""\n'
                    f'    value: {typ}\n\n'
                    '    def __post_init__(self):\n'
                    f'        if not isinstance(self.value, {typ}):\n'
                    f'            raise TypeError("Expected {typ} choice value")\n')
            rel = path_prefix + wrapper_file + ext
            generated.append(AIcdGeneratedSource(wrapper, rel, body,
                (AIcdGeneratedTypeIdentity.from_request(request, wrapper, rel,
                    AInDefsNameRole.DATA_TYPE),)))
        return tuple(generated)
